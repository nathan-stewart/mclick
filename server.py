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
import mido, logging, json
from settings import settings
from ticker import Ticker

app = Flask(__name__)
socketio = SocketIO(app)

ticker = None

@app.before_first_request
def check_socketio_server():
    if not socketio.server:
        abort(500, 'SocketIO server is not loaded')

@socketio.on('error')
def handle_render_error(data):
    abort(500, 'Client side error: ' + {data})

@app.route('/mclick')
def index():
    return render_template('index.html', parameters=json.dumps(settings))

@socketio.on('connect')
def on_connect(data = None):
    global settings
    global ticker
    if ticker:
        ticker.stop()
        ticker.join()
        ticker = None
    ticker = Ticker(settings)
    print('server:on_connect() : ', data)
    ticker.start()

@socketio.on('update_from_gui')
def on_update(parameters):
    global settings
    global ticker
    print('server:on_update()')
    settings = parameters
    ticker.stop()
    print('server:waiting on thread to finish')
    ticker.join()
    ticker = None

    print('starting new instance')
    ticker = Ticker(settings)
    ticker.start()

@socketio.on('disconnect')
def on_disconnect():
    print('server:on_disconnect')
    if ticker:
        ticker.stop()

@socketio.on('log')
def on_log(msg):
    print('log: ' + str(msg))

if __name__ == "__main__":
    try:
        socketio.run(app, host='0.0.0.0', port=5000,use_reloader=False)
    except:
        print('Server launch error')
        sys.exit(-1)
