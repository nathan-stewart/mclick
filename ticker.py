#!/usr/bin/env python3
import threading, heapq
import time, math, mido, sys
from settings import settings
import cProfile, pstats

# all times will be converted to integer chunks of 100uS for efficiency
window = 1e-3 # close enough - play it now

class Message:
    def __init__(self, t, m, n):
        self.time = t
        self.message = m
        self.name = n

    def __eq__(self, t):
        if isinstance(t, Message):
            return self.time == t.time
        return self.time == t

    def __gt__(self, t):
        if isinstance(t, Message):
            return self.time > t.time
        return self.time > t

class Events:
    def __init__(self, s):
        self.lock = threading.Lock()
        self.events = []
        self.settings = None
        self.midi_out = None
        self.playing = []
        self.midi_queue = []
        self.start = int(time.time() * 1e4) # convert to 100us
        self.apply_settings(s)

    # if getitem doesn't find t, add an empty Message at that timestamp
    def __getitem__(self, t):
        for i in self.events:
            if i == t:
                return i
        i = Message(t)
        return i

    def seconds_to_next_event(self):
        elapsed_time = (int(time.time() * 1e4) - self.start) % self.duration
        self.midi_queue.clear()
        if self.playing:
            next_time = self.playing[0].time
            while self.playing and self.playing[0].time == next_time:
                self.midi_queue.append(heapq.heappop(self.playing).message)
            return (next_time - elapsed_time)/1e4
        else: # if playing is empty that means we played the measure
            self.playing = self.events.copy()
        return (self.duration - elapsed_time)/1e4

    def open_midi_port(self):
        mido.set_backend(self.settings['midi_backend'])
        port = self.settings['midi_port']
        found = any (port in listed for listed in mido.get_output_names()) 
        if port and found:
            self.midi_out = mido.open_output(port)
        
    def midi_start(self):
        self.start = int(time.time() * 1e4)
        if not self.midi_out:
            self.open_midi_port()

        if self.settings['clock']:
            self.midi_out.send(mido.Message('start'))

    def midi_stop(self):
        if self.midi_out:
            self.midi_out.send(mido.Message('stop'))
            self.midi_out.panic()
            self.midi_out.close()
            self.midi_out = None

    def drain_queue(self):
        with self.lock:
            while self.midi_queue:
                self.midi_out.send(self.midi_queue.pop())

    def apply_settings(self, params):
        with self.lock:
            beat_ms = 60 * 10.0e+3/ float(params['tempo'])
            self.duration = beat_ms * params['num_beats']

            self.events.clear()
            heapq.heappush(self.events,Message(0, mido.Message('note_on', channel=9, 
                                                     note=params['measure']['note'], 
                                                     velocity=params['measure']['volume']), 'measure'))

            for b in range(params['num_beats']):
                if params['clock']:
                    for n in range(24):
                        tn = int(b * beat_ms + n * beat_ms/ 24.0)
                        heapq.heappush(self.events,Message(tn, mido.Message('clock'), 'clock'))

                t0 = int(b * beat_ms)
                if params['beat']['volume'] > 0:
                    heapq.heappush(self.events,Message(t0,
                        mido.Message('note_on', 
                             channel=9, note=params['beat']['note'], 
                             velocity=params['beat']['volume']), 'beat'))

                if params['eighths']['volume'] > 0:
                    # don't play the eight on the beat
                    #self[t0].add_message( mido.Message('note_on', channel=9, 
                    #                        note=params['eighths']['note'], 
                    #                        velocity=params['eighths']['volume']))
            
                    # 2nd eighth may be swung
                    t1 = int(t0 + beat_ms * (0.5 + params['swing']/200.0))  
                    # range goes from 0 = half of a beat to 100 = all the way on the next beat
                    # the slider shouldn't allow 100, but hard swing can be above 90% and this
                    # makes the math more clear
                    heapq.heappush(self.events,Message(t1, mido.Message('note_on', channel=9, 
                                                        note=params['eighths']['note'], 
                                                        velocity=params['eighths']['volume']), 
                                                        'eighths'))

                if params['sixteenths']['volume'] > 0:
                    for n in range(4):
                        tn = int(b * beat_ms + n * beat_ms / 4)
                        # only add the sixteenths not on eights
                        if n%2:
                            heapq.heappush(self.events,Message(tn,
                                           mido.Message('note_on', channel=9, 
                                                       note=params['sixteenths']['note'], 
                                                       velocity=params['sixteenths']['volume']),
                                                        'sixteenths'))
                midi_changed = False
                if (not self.settings 
                    or (self.settings['midi_backend'] != params['midi_backend'])
                    or (self.settings['midi_port']    != params['midi_port'])):
                    self.midi_stop()
                    midi_changed = True
        self.settings = params
        if midi_changed:
            self.midi_start()


class Ticker(threading.Thread):
    def __init__(self, params):
        super().__init__()
        self.stopping = threading.Event()
        self.events = Events(params)
        self.updated = threading.Event()

    def stop(self):
        self.stopping.set()

    def update(self, params):
        self.events.apply_settings(params)
        self.updated.set()

    def run(self):
        self.events.midi_start()
        while not self.stopping.is_set():
            snooze = self.events.seconds_to_next_event()
            if snooze >= 0.0:
                if self.updated.is_set():
                    self.events.midi_queue.clear()
                    self.events.playing.clear()
                    self.updated.clear()
                else:
                    self.updated.wait(timeout=snooze)
            self.events.drain_queue()



