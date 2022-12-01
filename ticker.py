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
play = True
mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')
OUTPUT_PORT='UMC1820:UMC1820 MIDI 1 28:0'

@dataclass
class Event:
    period      : float
    played      : bool = True
    velocity    : int = 0
    def test_and_fire(self, now, swing = 0):
        delta = math.fmod(now, 2*self.period)
        t0 = 0.0
        t1 = self.period + self.period * swing/200.0

        # test for the first note for both swung and unswung
        if (t0 <= delta <= window) or (t1 <= delta <=  (t1+ window)):
            if not self.played:
                self.played = True
                return True
        else:
            self.played = False
        return False


events = {
    'measure'    : Event(period=2.0),
    'beat'       : Event(period=0.5),
    'eighths'    : Event(period=0.25),
    'sixteenths' : Event(period=0.125),
    'midi_clock' : Event(period=0.5 / 24.0)
    }

def update_settings(params):
    global events
    global settings
    global first
    global output


    settings = params
    beat = 60.0 / float(params['tempo'])
    events = {
        'measure'    : Event(period=beat * settings['beats'], velocity=settings['measure']),
        'beat'       : Event(period=beat,                     velocity=settings['beat']),
        'eighths'    : Event(period=beat / 2,                 velocity=settings['eighths']),
        'sixteenths' : Event(period=beat / 4,                 velocity=settings['sixteenths']),
        'midi_clock' : Event(period=beat / 24,                velocity=127)
        }

    # don't care what we got - that's just for the gui - but midi_port has to be one we can see
    available_midi_ports = mido.get_output_names()
    if output:
        output.close()
        output = None

    if (settings['midi_port'] and settings['midi_port'] in available_midi_ports):
        output = mido.open_output(settings['midi_port'])
        clock = True
        play = True
        print('MIDI out set to: ', settings['midi_port'])

    else:
        print('Could not find MIDI output port: ', settings['midi_port'], ' in ', available_midi_ports)

    if not output:
        clock = False
        play = False
    else:
        if clock:
            output.send(mido.Message('start'))
    print('midi out: ', output)
    print('clock   : ', clock)
    print('play    :', play)

def Ticker():
    global stop
    global settings
    global notes
    global events
    global clock
    global play
    global output

    last_measure = time.time()
    since_one = 0

    while True:
        if stop:
            break

        now = time.time()
        if play and output:
            if events['measure'].test_and_fire(now):
                output.send(mido.Message('note_on', channel=9, note=notes['kick'], velocity=settings['measure']))
            if events['beat'].test_and_fire(now):
                output.send(mido.Message('note_on', channel=9, note=notes['side stick'], velocity=settings['beat']))
            if events['eighths'].test_and_fire(now, settings['swing']):
                output.send(mido.Message('note_on', channel=9, note=notes['ride'], velocity=settings['eighths']))
            if events['sixteenths'].test_and_fire(now):
                output.send(mido.Message('note_on', channel=9, note=notes['closed hat'], velocity=settings['sixteenths']))
        if clock and output:
            if events['midi_clock'].test_and_fire(now):
                #output.send(mido.Message('note_on', channel=9, note=notes['closed hat'], velocity=127))
                output.send(mido.Message('clock'))
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
