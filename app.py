#!/usr/bin/env python3
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit

import ticker

settings = {
'tempo' : 96,
'measure_length' : 4,
'measure_options' : "2,3,4,6,9,12",
'measure_volume' : 80,
'beat_volume': 80,
'eighth_volume' : 0,
'swing_value' : 0,
'sixteenth_volume' : 0
}

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html', parameters=settings)

@socketio.on('connect')
def on_connect():
    print('start')
    ticker.launch(settings)

@socketio.on('push_params')
def on_update(parameters):
    print('push_params: ' + str(parameters))
    ticker.launch(parameters)

@socketio.on('disconnect')
def on_disconnect():
    print('stopping')
    ticker.stop()

@socketio.on('log')
def on_log(msg):
    print('log: ' + str(msg))

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
