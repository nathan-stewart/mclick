#!/usr/bin/python3
from sortedcontainers import SortedList
import threading
import time
import math
import mido
import sys
import random
import os
from settings import settings
from buildMeasure import make_template_measure
from events import EventQue
from plotMeasure import plot_midi

class Ticker(threading.Thread):
    def __init__(self, params = None):
        super().__init__()
        self.lock = threading.Lock()
        self.stopping = threading.Event() # this is only used to exit
        self.settings = None
        self.trackmap = {}
        self.midi_out = None
        self.playlist = []
        self.play_index = None
        self.rhythmq = [] # list of SortedLists
        self.rhythm_track = mido.MidiTrack()
        self.rhythm_track.name = 'MClick'
        self.song = mido.MidiFile()
        self.update(params)

    def stop(self):
        self.stopping.set()
        self.midi_teardown()

    def midi_teardown(self):
        if self.midi_out:
            self.midi_out.send(mido.Message('stop'))
            self.midi_out.panic()
            self.midi_out.close()
            self.midi_out = None

    def midi_setup(self):
        mido.set_backend(self.settings['midi_backend'])
        if self.midi_out:
            self.midi_teardown()

        port = self.settings['midi_port']
        if port and any (port in listed for listed in mido.get_output_names()):
            self.midi_out = mido.open_output(port)
            self.midi_out.send(mido.Message('start'))

    def handle_anacrusis(self, measures):
        if not isinstance(measures, list):
            raise TypeError

        if not measures:
            return []

        if len(measures) < 2:
            return measures.copy()
        
        # look for ordinary anacrusis - first and last measure form whole measure 
        # This meter must be the same as the 2nd measure
        first = measures[0]
        second = measures[1]
        last = measures[-1]

        modified = []
        if (first[1] == second[1] == last[1] and first[0] + last[0]) == second[0]:
            modified.append(measures[1]) # Add an extra count in measure
        else:
            modified.append(first)
        # Now if anacrusis is present, the final measure will be short but the initial 
        # measure will be whole. Play repeats using the first measure, finish using the last

        # look for internal anacrusis - typically a verse/chorus split mid measure
        # internal anacrusis by definition can't be at the endpoints, and requires 
        # at least one one full measure on either side - so it has a minimum of 
        # six measures - first, full, short_a, short_b, full, last}
        if len(measures) < 6:
            modified += measures[1:] 
            return modified

        for i,m in enumerate(measures[1:-2], start=1):
            previous  = measures[i-1]
            following = measures[i+1]

            if m[1] != following[1]: # don't merge if denominator changes
                modified.append(m)
                continue 
            if m[0] + following[0] == previous[0]:
                # first submeasure
                modified.append(previous)
            elif m[0] + previous[0] == following[0]:
                # second submeasure - skip it
                continue
            else:
                modified.append(m)

        modified.append(measures[-1])
        return modified

    def make_rhythm_from_song(self):
        self.rhythmq.clear()
        self.rhythm_track.clear()
        self.rhythm_track = self.song.add_track('MClick')
        ticks_per_beat = self.song.ticks_per_beat # actually ppq
        if self.song.tracks:
            events = EventQue(self.song)
            params = self.settings 
            modified = self.handle_anacrusis(events.measures)
            #print(modified)
            previous = None
            for m in modified:
                if m != previous:
                    previous = m
                    params['num_beats'] = m[0]
                self.rhythmq.append(make_template_measure(params,ppq = ticks_per_beat))
        else:
            self.rhythmq.append(make_template_measure(self.settings))
        #print('rhythmq = ', self.rhythmq)
        for meas in self.rhythmq:
            mcopy = meas.copy()
            while mcopy:
                m = mcopy.pop(0)
                self.rhythm_track.append(m)

    def update(self, params):
        if params:
            self.settings = params
        else:
            self.settings = Settings()

    def run(self):
        self.midi_setup()
        self.play_index = 0
        while not self.stopping.is_set():
            if self.playlist:
                self.song = mido.MidiFile(self.playlist[self.play_index])
            else:
                self.song = mido.MidiFile()
            self.make_rhythm_from_song()
            plot_midi(self.song)
            for msg in self.song.play():
                if self.stopping.is_set():
                    break # break only goes out one loop
                self.midi_out.send(msg)

            self.play_index += 1
            if self.play_index >= len(self.playlist):
                self.play_index = 0

            if self.stopping.is_set():
                break

    def open_files(self, path):
        self.playlist.clear()
        self.play_index = None
        if os.path.isdir(path):
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_file() and  entry.name.endswith('.mid'):
                        self.playlist.append(entry)
        elif os.path.isfile(path):
            self.playlist = [path]

        if len(self.playlist) > 0:
            self.play_index = 0
        self.play_index = random.randint(0,len(self.playlist))

if __name__ == '__main__':
    t = Ticker(settings)
    #t.open_files('/home/nps/projects/hymns/cwm_rhondda.mid')
    t.open_files('demo')
    try:
        t.run()
    except KeyboardInterrupt:
        t.stop()
