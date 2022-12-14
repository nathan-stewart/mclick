#!/usr/bin/env python3
from dataclasses import dataclass
from threading import Thread
import time, math, mido

'''
I'm not trying to create an entire drum machine. These sounds were chosen for
their metronome functions with some choices.
'''
output = None

notes  = {
'kick'           : 36,
'snare'          : 38,
'side stick'     : 37,
'closed hat'     : 42,
'openhat'        : 46,
'ride'           : 51,
'ride bell'      : 53,
'cow bell'       : 56,
'ride 2'         : 59,
'hi wood block'  : 76,
'low wood block' : 77,
'mute triangle'  : 80,
'open triangle'  : 81
}

window = 3e-3    # 3mS window - if we're later than this value drop it
stop  = True     # used to exit the thread
settings = None  # the parameters to use
clock = True
mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')
OUTPUT_PORT='UMC1820:UMC1820 MIDI 1'

@dataclass
class Event:
    period      : float
    message     : mido.messages.messages.Message
    swing       : float
    played      : bool
    mute        : bool

    def __init__(self, period, message=None, swing=0):
        self.period = period
        self.message = message
        self.swing = swing
        self.played = False
        if 'velocity=0' in str(self.message):
            self.mute = True
        else:
            self.mute = False

    def test_and_fire(self, now):
        if self.mute:
            return False

        delta = math.fmod(now, 2*self.period)
        t0 = 0.0
        t1 = self.period + self.period * self.swing/200.0

        # test for the first note for both swung and unswung
        if (t0 <= delta <= window) or (t1 <= delta <=  (t1+ window)):
            if not self.played:
                self.played = True
                return True
        else:
            self.played = False
        return False


events = None

def update_settings(params):
    global events
    global settings
    global first
    global output
    global clock

    settings = params
    beat = 60.0 / float(params['tempo'])
    events = {
        'measure'    : Event(period=beat * settings['beats'], message=mido.Message('note_on', channel=9, note=notes['kick'],        velocity=settings['measure'])),
        'beat'       : Event(period=beat,                     message=mido.Message('note_on', channel=9, note=notes['side stick'],  velocity=settings['beat'])),
        'eighths'    : Event(period=beat / 2,                 message=mido.Message('note_on', channel=9, note=notes['ride'],        velocity=settings['eighths']), swing=settings['swing']),
        'sixteenths' : Event(period=beat / 4,                 message=mido.Message('note_on', channel=9, note=notes['closed hat'], velocity=settings['sixteenths'])),
        'midi_clock' : Event(period=beat / 24,                message=mido.Message('clock'))
    }

    def port_is_available(p):
        # don't care what we got - that's just for the gui - but midi_port has to be one we can see
        matches = [ pm for pm in mido.get_output_names() if p in pm]
        return matches[0]

    if output:
        if clock:
            output.send(mido.Message('stop'))

        # check before we close to see if it changed
        if params['midi_port'] not in str(output):
            print('Setting MIDI output port to: ' + params['midi_port'])
        output.close()
        output = None

    settings = params
    if (settings['midi_port'] and  port_is_available (settings['midi_port'] )):
        output = mido.open_output(settings['midi_port'])
        clock = True
    else:
        print('Could not find MIDI output port: ', settings['midi_port'], ' in ', available_midi_ports)

    if not output:
        clock = False
    else:
        if clock:
            output.send(mido.Message('start'))

def Ticker():
    global stop
    global settings
    global notes
    global events
    global clock
    global output

    last_measure = time.time()
    since_one = 0

    while not stop:
        now = time.time()
        if output:
            for e in events:
                event = events[e]
                if event.test_and_fire(now):                
                    output.send(event.message)
        time.sleep(0)

scheduler = None
stop = True

def launch(params):
    global stop
    global settings
    global scheduler

    update_settings(params)

    if not scheduler:
        scheduler = Thread(target=Ticker)
        stop = False
        scheduler.start()

def shutdown():
    global stop
    global scheduler

    print('Stop')
    stop = True
    scheduler.join()
    output.send(mido.Message('stop'))
    output.panic()
    output.close()
    scheduler = None
