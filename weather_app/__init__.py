from flask import Flask, render_template
from weather_app.weather_info import get_external_IP_address, process_weather_forecast
from flask_socketio import SocketIO
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Therebelxy'
socketio = SocketIO(app, max_http_buffer_size=10000000)

# Initialize logging
logging.basicConfig(filename='Log.txt',level=logging.INFO,
                    format=' %(asctime)s - %(levelname)s- %(message)s')

@app.route("/")
def main():
    return render_template("index.html")

@socketio.on('connect')
def handle_connect():
    logging.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected')

@socketio.on('fetch_data')
def handle_fetch_data():
    try:
        ip_address = get_external_IP_address()
        
        weather_data = process_weather_forecast(ip_address)
        
        data = {
            "climatic": weather_data['climatic'],
            "header": weather_data['headline']
        }
        
        socketio.emit("header_data", data)
    except Exception as e:
        logging.error(f"Error in handle_fetch_data: {e}")

@socketio.on('request_data')
def handle_request_data():
    try:
        ip_address = get_external_IP_address()
        weather_data = process_weather_forecast(ip_address)
        
        data = {
            "graph1": weather_data['graphs']["24h"],
            "graph2": weather_data['graphs']["10d"],
            "icons": weather_data['weather_icons'],
            "forecast": weather_data['forecast']
        }

        socketio.emit('update_data', data)
        logging.info('Client received data')
    except Exception as e:
        logging.error(f"Error in handle_request_data: {e}")

if __name__ == '__main__':
    socketio.run(app,debug=True)
