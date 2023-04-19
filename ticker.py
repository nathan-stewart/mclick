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
    def __init__(self, midi):
        self.events = {}
        self.midi_out = midi
        self.last_measure = time.time() * 1e3
        self.measure_duration = 0
        self.elapsed_time = self.last_measure

    def __getitem__(self, index):
        if index not in self.events.keys():
            self.events[index] = TickerEvent()
        return self.events[index]

    def clear(self, ms):
        self.events = {}
        self.start_of_measure = time.time() * 1e3 # convert to ms
        self.measure_duration = ms

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
        self.elapsed_time = time.time() * 1e3 - self.start_of_measure
    
        # early out if we have no events
        tsteps = sorted(self.events.keys())
        if len(tsteps) < 1:
            return self.measure_duration # nothing to do
        
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
                    self.midi_out.send(m)
                    pass

        pending = max(pending, self.check_measure_done())
        return pending


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
        self.events = Events(self.midi_out) 
        self.build_event_table()

    def stop(self):
        print('ticker:stop()')
        self.stopping.set()

    def run(self):
        if self.settings['clock']:
            self.midi_out.send(mido.Message('start'))
        
        self.events.check_measure_done(force=True)
        snooze = 0
        while not self.stopping.is_set():
            snooze = self.events.time_to_next_event()
            if snooze > window:
                delay = max(0.5, (snooze - window)*1e-3)
                time.sleep(delay)

        self.midi_stop()
        print('ticker:run main thread exit')

    def build_event_table(self):
        beat_ms = 60.0e+3/ float(self.settings['tempo'])
        measure_duration = beat_ms * self.settings['num_beats']
        
        self.events.clear(measure_duration)

        self.events[0].add_message(mido.Message('note_on', channel=9, 
                                            note=self.settings['measure']['note'], 
                                            velocity=self.settings['measure']['volume']))

        for b in range(self.settings['num_beats']):
            if self.settings['clock']:
                for n in range(24):
                    tn = int(b * beat_ms + n * beat_ms/ 24)
                    self.events[tn].add_message(mido.Message('clock'))

            t0 = int(b * beat_ms)
            if self.settings['beat']['volume'] > 0:
                self.events[t0].add_message( mido.Message('note_on', channel=9, 
                                        note=self.settings['beat']['note'], 
                                        velocity=self.settings['beat']['volume']))

            if self.settings['eighths']['volume'] > 0:
                self.events[t0].add_message( mido.Message('note_on', channel=9, 
                                        note=self.settings['eighths']['note'], 
                                        velocity=self.settings['eighths']['volume']))
        
                # 2nd eighth may be swung
                t1 = int(t0 + beat_ms * (0.5 + self.settings['swing']/200.0))  
                # range goes from 0 = half of a beat to 100 = all the way on the next beat
                # the slider shouldn't allow 100, but hard swing can be above 90% and this
                # makes the math more clear
                self.events[t1].add_message(mido.Message('note_on', channel=9, 
                                                          note=self.settings['eighths']['note'], 
                                                          velocity=self.settings['eighths']['volume']))

            if self.settings['sixteenths']['volume'] > 0:
                for n in range(4):
                    tn = int(b * beat_ms + n * beat_ms / 4)
                    self.events[tn].add_message( mido.Message('note_on', channel=9, 
                                            note=self.settings['sixteenths']['note'], 
                                            velocity=self.settings['sixteenths']['volume']))

