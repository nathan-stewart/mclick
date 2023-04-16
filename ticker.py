#!/usr/bin/env python3
from dataclasses import dataclass
from threading import Thread
import time, math, mido, sys
from settings import Settings

midi_out = None
window = 3.0    # 3mS window - if we're later than this value drop it
stop  = True    # used to exit the thread
mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')
OUTPUT_PORT='UMC1820:UMC1820 MIDI 1'

@dataclass
class Event:
    messages    : list[mido.messages.messages.Message]
    played      : bool

    def __init__(self):
        self.messages = None
        self.played = False

    def add_message(self, m):
        if not self.messages:
            self.messages = []
        self.messages.append(m)

class Events:
    def __init__(self):
        self.events = {}
        self.last_measure = time.time() * 1e3
        self.measure_duration = 0

    def __getitem__(self, index):
        if index not in self.events.keys():
            self.events[index] = Event()
        return self.events[index]

    def clear(self, ms):
        self.events = {}
        self.start_of_measure = time.time() * 1e3 # convert to ms
        self.measure_duration = ms

    def measure_done(self):
        for k in self.events.keys():
            if not self.events[k].played:
                return False
        self.start_of_measure += self.measure_duration
        for k in self.events.keys():
            self.events[k].played = False
         
    def time_to_next_event(self):
        elapsed_time = time.time() * 1e3 - self.start_of_measure

        # early out if we have no events
        tsteps = sorted(self.events.keys())
        if len(tsteps) < 1:
            return self.measure_duration # nothing to do

        pending = self.measure_duration # initialize to measure duration
        for t in tsteps:
            pending = max(0,min(pending, float(t) - elapsed_time))
            event = self.events[t]
            if event.played or elapsed_time >= t + window:
                # either already played or we missed the window
                continue

            if pending > window:
                break

            if not event.played and elapsed_time >= float(t):
                event.played = True
                for m in event.messages:
                    midi_out.send(m)

                played = ''
                for p in tsteps:
                   if self.events[p].played:
                       played += 'Y ' 
                   else:
                        played += 'N '
        
        if self.measure_done():
            pending = self.measure_duration - elapsed_time
        return pending


events = Events()

def update_settings(params):
    global events
    global midi_out

    settings = params
    def valid_midi_port(port):
        return port and any (port in port_found for port_found in settings.midi_ports)

    beat_ms = 60.0e+3/ float(params.tempo)
    measure_duration = beat_ms * params.num_beats 
    # Build the Table of events for an entire measure
    # key is the time delta in milliseconds after the start of the measure
    events.clear(measure_duration)

    events[0].add_message(mido.Message('note_on', channel=9, note=settings.measure.note, velocity=settings.measure.volume))

    for b in range(settings.num_beats):
        if settings.clock:
            for n in range(24):
                tn = int(b * beat_ms + n * beat_ms/ 24)
                events[tn].add_message(mido.Message('clock'))

        t0 = int(b * beat_ms)
        if settings.beat.volume > 0:
            events[t0].add_message(mido.Message('note_on', channel=9, note=settings.beat.note, velocity=settings.beat.volume))
        if settings.eighths.volume > 0:
            events[t0].add_message(mido.Message('note_on', channel=9, note=settings.eighths.note, velocity=settings.eighths.volume))
            
            # 2nd eighth may be swung
            t1 = int(t0 + beat_ms * (0.5 + settings.swing/200.0))  # range goes from 0 = half of a beat to 100 = all the way on the next beat
                                                             # the slider shouldn't allow 100, but hard swing can be above 90% and this
                                                             # makes the math more clear
            events[t1].add_message(mido.Message('note_on', channel=9, note=settings.eighths.note, velocity=settings.eighths.volume))
        if settings.sixteenths.volume > 0:
            for n in range(4):
                tn = int(b * beat_ms + n * beat_ms / 4)
                events[tn].add_message(mido.Message('note_on', channel=9, note=settings.sixteenths.note, velocity=settings.sixteenths.volume))
    
    if midi_out:
        if settings.clock:
            midi_out.send(mido.Message('stop'))

        # check before we close to see if it changed
        if params.midi_port not in str(midi_out):
            print('Setting MIDI output port to: ' + params.midi_port)
        midi_out.close()
        midi_out = None

    if (valid_midi_port(settings.midi_port)):
        midi_out = mido.open_output(settings.midi_port)
    else:
        print('Could not find MIDI output port: ', settings.midi_port, ' in ', settings.midi_ports)
    if settings.clock:
        midi_out.send(mido.Message('start'))

def Ticker():
    global stop
    global events
    global midi_out 

    if not midi_out:
        while not stop:
            time.sleep(0.1) # we're not doing anything but want to be responsive to changes
    while not stop:
        snooze = events.time_to_next_event()
        if snooze > window:
            delay = snooze - window
            time.sleep(delay/1e3)

scheduler = None
stop = True

def launch():
    global stop
    global scheduler

    update_settings(Settings())        

    if not scheduler:
        scheduler = Thread(target=Ticker)
        stop = False
        scheduler.start()

def shutdown():
    global stop
    global scheduler

    stop = True
    try:
        midi_out.send(mido.Message('stop'))
        midi_out.panic()
        midi_out.close()
    except:
        print('Error closing MIDI')
    
    if scheduler:
        scheduler.join()
        scheduler = None
        print('Ticker Stopped')

if __name__ == '__main__':
    launch()
