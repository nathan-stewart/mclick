#!/usr/bin/env python3
import eventlet, sys
eventlet.monkey_patch()
'''
TODO:
    Finish MIDI configuration:
       * Click on logo configures MIDI interface, channel
       * Fix Measure Buttons/graphic
       * Click on icon changes the MIDI note for that subdivision
'''

from flask import Flask, render_template, request, abort
from flask_socketio import SocketIO, send, emit
import ticker, mido, logging
from settings import Settings

app = Flask(__name__)
socketio = SocketIO(app)
settings = Settings()

@app.before_first_request
def check_socketio_server():
    if not socketio.server:
        abort(500, 'SocketIO server is not loaded')

@socketio.on('error')
def handle_render_error(data):
    abort(500, 'Client side error: ' + {data})

@app.route('/mclick')
def index():
    return render_template('index.html', parameters=settings.toJSON())

@socketio.on('connect')
def on_connect():
    #print('connected')
    ticker.launch()

@socketio.on('push_params')
def on_update(parameters):
    global settings
    print('push_params')
    print(settings)
    # they seem to get converted to strings in the transporter
    for key in parameters.keys():
        if key in ['measure_options', 'midi_port', 'midi_ports']:
            settings[key] = parameters[key]
        else:
            settings[key] = int(parameters[key])
    print('push_params')
    socketio.emit('update', settings.toJSON())
    ticker.update_settings(settings)

@socketio.on('disconnect')
def on_disconnect():
    print('disconnect')
    ticker.shutdown()

@socketio.on('log')
def on_log(msg):
    print('log: ' + str(msg))

if __name__ == "__main__":
    try:
        socketio.run(app, host='0.0.0.0', port=5000,use_reloader=False)
    except:
        print('Server launch error')
        sys.exit(-1)
