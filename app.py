#!/usr/bin/env python3
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit

import ticker

settings = {
'tempo'           : 60,
'beats'           :  4,
'measure'         : 100,
'beat'            : 80,
'eighths'         :  0,
'swing'           :  0,
'sixteenths'      :  0,
'measure_options' : "2,3,4,6,9,12"
}

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/mclick')
def index():
    return render_template('index.html', parameters=settings)

@socketio.on('connect')
def on_connect():
    global settings
    print('start')
    ticker.launch(settings)

@socketio.on('push_params')
def on_update(parameters):
    global settings
    # they seem to get converted to strings in the transporter
    for key in parameters.keys():
        if key != 'measure_options':
            settings[key] = int(parameters[key])
    ticker.launch(settings)

@socketio.on('disconnect')
def on_disconnect():
    print('stopping')
    ticker.shutdown()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
