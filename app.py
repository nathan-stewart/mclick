
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit

parameters = {
'tempo' : 120,
'measure_length' : 4,
'measure_options' : [2,3,4,6,9,12],
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
    return render_template('index.html', parameters=parameters)

@socketio.on('connect')
def on_update(fields):
    print('connect: ' + str(fields))

@socketio.on('Slider value changed')
def value_changed(message):
    values[message['who']] = message['data']
    emit('update value', message, broadcast=True)

@socketio.on('value changed')
def on_disconnect(data):
    print('value changed: ' + str(data))

@socketio.on('disconnect')
def on_disconnect():
    print('Disconnected')

if __name__ == "__main__":
    socketio.run(app)
