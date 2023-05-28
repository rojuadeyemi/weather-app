import os
from flask import Flask, request, render_template
from weather_app.greeting import greet, get_local_IP_address

app = Flask(__name__)

@app.route('/')
def main():
    ip_address = get_local_IP_address()

    return render_template('index.html', weather_info=greet(ip_address))

if __name__ == '__main__':
    app.run()
