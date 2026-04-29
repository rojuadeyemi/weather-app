from flask import Flask, render_template, request
from flask_socketio import SocketIO
from weather_app.weather_info import process_weather_forecast
from weather_app.auxiliary import get_location
import logging
import time

# APP SETUP
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Therebelxy'

socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins="*"
)

logging.basicConfig(
    filename='Log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# STATE (per client)
clients = {}
last_weather_cache = {}

# ROUTES
@app.route("/")
def main():
    return render_template("index.html")

def get_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")

    if forwarded:
        # first IP is the real client
        return forwarded.split(",")[0].strip()

    return request.remote_addr

# SAFE LOCATION RESOLVER
def resolve_location(payload, sid=None):
    logging.info(f"detected ip: {clients.get(sid, {}).get('ip')}")
    # 1. GPS preferred
    if payload.get("source") == "gps":
        lat = payload.get("lat")
        lon = payload.get("lon")
        if lat and lon:
            return lat, lon

    # 2. fallback: cached client location
    cached = clients.get(sid, {})
    if cached.get("lat") and cached.get("lon"):
        return cached["lat"], cached["lon"]
    
    # 3. fallback: IP lookup (ONLY if available)
    try:
        ip = payload.get("ip") or cached.get("ip")
        if ip:
            loc = get_location(ip)
            return loc["lat"], loc["lon"]
    except Exception as e:
        logging.warning(f"IP fallback failed: {e}")

    return None, None

# BACKGROUND WORKER
def weather_worker():
    while True:
        try:
            for sid, payload in list(clients.items()):

                lat, lon = resolve_location(payload, sid)
                tz = payload.get("timezone")

                if not lat or not lon:
                    continue

                weather_data = process_weather_forecast(lat=lat, lon=lon,tz=tz)

                update = {
                    "header": weather_data["headline"],
                    "climatic": weather_data["climatic"],
                    "symbol": weather_data.get("symbol"),
                    "timestamp": int(time.time())
                }

                # avoid unnecessary emits
                if last_weather_cache.get(sid) != update:
                    socketio.emit("live_update", update, to=sid)
                    last_weather_cache[sid] = update

        except Exception as e:
            logging.error(f"Worker error: {e}")

        socketio.sleep(15)

# SAFE WORKER START
worker_started = False

def start_worker_once():
    global worker_started
    if not worker_started:
        socketio.start_background_task(weather_worker)
        worker_started = True

# SOCKET EVENTS
@socketio.on("connect")
def handle_connect():
    if not clients:
        start_worker_once()

    clients[request.sid] = {
        "lat": None,
        "lon": None,
        "ip": get_ip()
    }
    logging.info("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    clients.pop(request.sid, None)
    last_weather_cache.pop(request.sid, None)
    logging.info("Client disconnected")


@socketio.on("set_location")
def set_location(data):
    clients[request.sid].update({
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "timezone": data.get("timezone"),
        "source": data.get("source")
    })


@socketio.on("start_stream")
def start_stream(data):
    lat, lon = resolve_location(data, request.sid)

    if not lat or not lon:
        return

    tz = data.get("timezone")
    weather_data = process_weather_forecast(lat=lat, lon=lon,tz=tz)

    socketio.emit("live_update", {
        "header": weather_data["headline"],
        "climatic": weather_data["climatic"],
        "graph1": weather_data["graphs"]["24h"],
        "graph2": weather_data["graphs"]["10d"],
        "icons": weather_data["weather_icons"],
        "forecast": weather_data["forecast"],
        "symbol": weather_data.get("symbol")
    }, to=request.sid)

# APP START
if __name__ == "__main__":
    start_worker_once()
    socketio.run(app, host="0.0.0.0", port=5000)
