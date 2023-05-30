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
from settings import Settings
from ticker import Ticker

app = Flask(__name__)
socketio = SocketIO(app)

defaults = Settings()
ticker = Ticker()
ticker.start()

@app.before_first_request
def check_socketio_server():
    if not socketio.server:
        abort(500, 'SocketIO server is not loaded')

@socketio.on('error')
def handle_render_error(data):
    abort(500, 'Client side error: ' + {data})

@app.route('/')
def index():
    return render_template('index.html', parameters=defaults.to_json())

@socketio.on('update_from_gui')
def on_update(parameters):
    global ticker 
    ticker.update(parameters)
    # TBD - save settings

@socketio.on('connect')
def on_connect():
    global ticker
    global defaults 
    ticker.update(defaults)

@app.route('/file-dialog', methods=['GET', 'POST'])
def file_dialog():
    if request.method == 'POST':
        selected_files = request.form.getlist('files')
    return render_template('file-dialog.html')

@socketio.on('transport')
def on_transport(source):
    global ticker
    if source == 'id_load':
        emit('open_file_dialog')
    ticker.transport_action(source)

@socketio.on('disconnect')
def on_disconnect():
    global ticker
    print('disconnect')
    ticker.update(None)

@socketio.on('log')
def on_log(msg):
    print('log: ' + str(msg))

if __name__ == "__main__":
    try:
        socketio.run(app, host='0.0.0.0', port=5000)
    except:
        print('Server launch error')
        sys.exit(-1)
