#!/usr/bin/env python3
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import ticker, mido, logging

settings = {
'tempo'           : 60,
'beats'           :  4,
'measure'         : 64,
'beat'            : 48,
'eighths'         : 24,
'swing'           :  0,
'sixteenths'      :  0,
'measure_options' : "2,3,4,6,9,12",
'midi_port'       : 'UMC1820:UMC1820 MIDI 1 28:0',
'midi_ports'      : set(mido.get_output_names())
}
string_fields = ['measure_options', 'midi_port', 'midi_ports']

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/mclick')
def index():
    return render_template('index.html', parameters=settings)

@socketio.on('connect')
def on_connect():
    global settings
    ticker.launch(settings)

@socketio.on('push_params')
def on_update(parameters):
    global settings
    # they seem to get converted to strings in the transporter
    for key in parameters.keys():
        if key in string_fields:
            settings[key] = parameters[key]
        else:
            settings[key] = int(parameters[key])
    ticker.launch(settings)

@socketio.on('disconnect')
def on_disconnect():
    ticker.shutdown()

@socketio.on('log')
def on_log(msg):
    logging.info('log: ' + str(msg))

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
