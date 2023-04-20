#!/usr/bin/env python3
from dataclasses import dataclass
import threading
import time, math, mido, sys
from settings import settings

window = 3.0    # 3mS window - if we're later than this value drop it

@dataclass
class TickerEvent:
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
    def __init__(self, settings):
        self.events = {}
        self.count = 0
        self.start_of_measure = time.time() * 1e3 # convert to ms
        self.elapsed_time = self.start_of_measure
        self.build_event_table(settings)

    def __getitem__(self, index):
        if index not in self.events.keys():
            self.events[index] = TickerEvent()
        return self.events[index]

    def reset_played(self):
        for k in self.events.keys():
            self.events[k].played = False

    def check_measure_done(self, force = False):
        if force:
            self.reset_played()
            self.start_of_measure = time.time() * 1e3
            return 0

        # if we have wrapped a measure, back out the measure time from elapsed
        if self.elapsed_time > self.measure_duration:
            self.reset_played()
            while self.elapsed_time > self.measure_duration:
                self.elapsed_time -= self.measure_duration
                self.count

        # if all events have been played, return remaining time
        measure_finished = True
        for k in self.events.keys():
            if not self.events[k].played:
                measure_finished = False
                break

        if all([self.events[k].played for k in self.events.keys()]):
        
            self.start_of_measure += self.measure_duration
            self.reset_played()
            pending = self.measure_duration - self.elapsed_time
            return pending
        return 0

         
    def time_to_next_event(self):
        messages = []
        self.elapsed_time = time.time() * 1e3 - self.start_of_measure
    
        # early out if we have no events
        tsteps = sorted(self.events.keys())
        if len(tsteps) < 1:
            return (self.measure_duration, messages) # nothing to do
        
        pending = self.measure_duration # initialize to measure duration
        for t in tsteps:
            pending = max(0,min(pending, float(t) - self.elapsed_time))
            event = self.events[t]
            if event.played or self.elapsed_time >= t + window:
                # either already played or we missed the window
                continue

            if pending > window:
                break

            if not event.played and self.elapsed_time >= float(t):
                event.played = True
                for m in event.messages:
                    messages.append(m)
                    pass

        pending = max(pending, self.check_measure_done())
        return (pending, messages)

    def build_event_table(self, settings):
        beat_ms = 60.0e+3/ float(settings['tempo'])
        self.measure_duration = beat_ms * settings['num_beats']
        self[0].add_message(mido.Message('note_on', channel=9, 
                                            note=settings['measure']['note'], 
                                            velocity=settings['measure']['volume']))

        for b in range(settings['num_beats']):
            if settings['clock']:
                for n in range(24):
                    tn = int(b * beat_ms + n * beat_ms/ 24)
                    self.events[tn].add_message(mido.Message('clock'))

            t0 = int(b * beat_ms)
            if settings['beat']['volume'] > 0:
                self[t0].add_message( mido.Message('note_on', channel=9, 
                                        note=settings['beat']['note'], 
                                        velocity=settings['beat']['volume']))

            if settings['eighths']['volume'] > 0:
                self[t0].add_message( mido.Message('note_on', channel=9, 
                                        note=settings['eighths']['note'], 
                                        velocity=settings['eighths']['volume']))
        
                # 2nd eighth may be swung
                t1 = int(t0 + beat_ms * (0.5 + settings['swing']/200.0))  
                # range goes from 0 = half of a beat to 100 = all the way on the next beat
                # the slider shouldn't allow 100, but hard swing can be above 90% and this
                # makes the math more clear
                self[t1].add_message(mido.Message('note_on', channel=9, 
                                                          note=settings['eighths']['note'], 
                                                          velocity=settings['eighths']['volume']))

            if settings['sixteenths']['volume'] > 0:
                for n in range(4):
                    tn = int(b * beat_ms + n * beat_ms / 4)
                    self[tn].add_message( mido.Message('note_on', channel=9, 
                                            note=settings['sixteenths']['note'], 
                                            velocity=settings['sixteenths']['volume']))


class Ticker(threading.Thread):
    def open_midi_port(self):
        port = self.settings['midi_port']
        found = any (port in listed for listed in mido.get_output_names()) 
        if port and found:
            self.midi_out = mido.open_output(port)
        
    def midi_stop(self):
        self.midi_out.send(mido.Message('stop'))
        self.midi_out.panic()
        self.midi_out.close()
        self.midi_out = None

    def __init__(self, params):
        super().__init__()
        self.stopping = threading.Event()
        self.settings = params 
        mido.set_backend(self.settings['midi_backend'])
        self.open_midi_port()
        self.events = Events(self.settings)

    def stop(self):
        print('ticker:stop()')
        self.stopping.set()

    def run(self):
        print('starting new ticker instance')
        if self.settings['clock']:
            self.midi_out.send(mido.Message('start'))
        
        self.events.check_measure_done(force=True)
        snooze = 0
        while not self.stopping.is_set():
            snooze,msg  = self.events.time_to_next_event()
            for m in msg:
                self.midi_out.send(m)

            if snooze > window:
                delay = max(0.5, (snooze - window)*1e-3)
                time.sleep(delay)

        self.midi_stop()
        self.stopping.clear() # 
        print('ticker:run main thread exit')

