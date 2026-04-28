from flask import Flask, render_template, request
from weather_app.weather_info import process_weather_forecast
from flask_socketio import SocketIO
import logging
import time

clients = {}
last_weather_cache = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Therebelxy'

socketio = SocketIO(
    app,
    async_mode='gevent',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Logging
logging.basicConfig(
    filename='Log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route("/")
def main():
    return render_template("index.html")

def get_location(ip_address: str) -> dict:
    """Get city, country, latitude, longitude and timezone information for a
    location, based on IP address.

    Args:
        ip_address (str): An IPv4/IPv6 address, or a domain name.

    Returns:
        dict: Location details.
    """
    location_info = requests.get(
        f"http://ip-api.com/json/{ip_address}",
        headers={"User-Agent": "Aderoju"},
    timeout=5).json()

    return {
        key: location_info[key]
        for key in ("city", "country", "lat", "lon", "timezone")
    }
# SAFE LOCATION RESOLVER
def resolve_location(payload, sid=None):
    source = payload.get("source")

    # 1. GPS (preferred)
    if source == "gps" and payload.get("lat") and payload.get("lon"):
        return payload["lat"], payload["lon"]

    # 2. IP fallback (ONLY if we are inside request context)
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        location = get_location(ip)
        return location["lat"], location["lon"]
    except RuntimeError:
        # worker thread fallback (NO request context here)
        cached = clients.get(sid, {})
        if cached.get("lat") and cached.get("lon"):
            return cached["lat"], cached["lon"]

        return None, None

# BACKGROUND WORKER
def weather_worker():
    while True:
        try:
            for sid, payload in list(clients.items()):

                lat, lon = resolve_location(payload, sid=sid)

                if lat is None or lon is None:
                    continue

                weather_data = process_weather_forecast(lat=lat, lon=lon)

                new_payload = {
                    "header": weather_data['headline'],
                    "climatic": weather_data['climatic'],
                    "symbol": weather_data.get("symbol"),
                    "timestamp": int(time.time())
                }

                # only emit if changed
                if last_weather_cache.get(sid) != new_payload:
                    socketio.emit('live_update', new_payload, to=sid)
                    last_weather_cache[sid] = new_payload

        except Exception as e:
            print("Weather worker error:", e)

        socketio.sleep(15)

# START WORKER ONCE
def start_worker():
    socketio.start_background_task(weather_worker)


start_worker()


# SOCKET EVENTS
@socketio.on('connect')
def handle_connect():
    clients[request.sid] = {"lat": None, "lon": None, "source": "gps"}
    logging.info('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    clients.pop(request.sid, None)
    last_weather_cache.pop(request.sid, None)
    logging.info('Client disconnected')


@socketio.on('set_location')
def set_location(data):
    clients[request.sid] = {
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "source": data.get("source")
    }


@socketio.on('start_stream')
def start_stream(data):
    lat, lon = resolve_location(data, sid=request.sid)

    if lat is None or lon is None:
        return

    weather_data = process_weather_forecast(lat=lat, lon=lon)

    socketio.emit('live_update', {
        "header": weather_data['headline'],
        "climatic": weather_data['climatic'],
        "graph1": weather_data['graphs']["24h"],
        "graph2": weather_data['graphs']["10d"],
        "icons": weather_data['weather_icons'],
        "forecast": weather_data['forecast'],
        "symbol": weather_data.get("symbol")
    }, to=request.sid)


# RUN APP
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
