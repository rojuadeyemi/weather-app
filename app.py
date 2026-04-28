from flask import Flask, render_template,request
from weather_app.weather_info import process_weather_forecast
from weather_app.auxiliary import get_location
from flask_socketio import SocketIO
import logging
import time

clients = {}
last_weather_cache = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Therebelxy'

socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*",logger=True)

# Initialize logging
logging.basicConfig(filename='Log.txt',level=logging.INFO,
                    format=' %(asctime)s - %(levelname)s- %(message)s')

@app.route("/")
def main():
    return render_template("index.html")

def weather_worker():
    while True:
        try:
            for sid, payload in list(clients.items()):
                lat, lon = resolve_location(payload)

                if lat is None or lon is None:
                    continue

                weather_data = process_weather_forecast(lat=lat, lon=lon)

                new_payload = {
                    "header": weather_data['headline'],
                    "climatic": weather_data['climatic'],
                    "symbol": weather_data.get("symbol"),
                    "timestamp": int(time.time())
                }

                # ONLY SEND IF CHANGED
                if last_weather_cache.get(sid) != new_payload:
                    socketio.emit('live_update', new_payload, to=sid)
                    last_weather_cache[sid] = new_payload

        except Exception as e:
            print("Weather worker error:", e)

        socketio.sleep(15)  # faster but lighter

def start_worker():
    socketio.start_background_task(weather_worker)

@socketio.on('connect')
def handle_connect():
    clients[request.sid] = {"lat": None, "lon": None}
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
    lat, lon = resolve_location(data)

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


def resolve_location(payload):
    source = payload.get("source")

    # Case 1: Good GPS
    if source == "gps" and payload.get("lat") and payload.get("lon"):
        return payload["lat"], payload["lon"]

    # Case 2: fallback to IP
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    location = get_location(ip)

    return location["lat"], location["lon"]

if __name__ == "__main__":
    start_worker()
    socketio.run(app, host="0.0.0.0", port=5000)
