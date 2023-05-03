#!/usr/bin/python3
from sortedcontainers import SortedList
import threading
import time
import math
import mido
import sys
import os

from settings import settings
from buildMeasure import make_template_measure

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

    def make_rhythm_from_song(self):
        self.rhythm_track.clear()
        self.rhythm_track.name = 'MClick'
        self.song.tracks.append(self.rhythm_track)
        self.rhythmq.clear()
        ticks_per_beat = self.song.ticks_per_beat
        num_beats = 4
        measure_count = 0
        if self.song.tracks:
            songtrack = self.song.tracks[0]
            measure_elapsed = 0
            ticks_per_measure = num_beats * ticks_per_beat
            for sm in songtrack:
                if sm.is_meta:
                    if sm.type == 'time_signature':
                        measure_elapsed = 0
                        new_meas = settings
                        new_meas['num_beats'] = num_beats
                        self.rhythmq.append(make_template_measure(new_meas))
                else:
                    measure_elapsed += sm.time
                    if measure_elapsed >= ticks_per_measure:
                        measure_elapsed = 0
                        new_meas = settings
                        new_meas['num_beats'] = num_beats
                        self.rhythmq.append(make_template_measure(new_meas))
        else:
            self.rhythmq.append(make_template_measure(self.settings))

        for meas in self.rhythmq:
            mcopy = meas.copy()
            while mcopy:
                m = mcopy.pop(0)
                self.rhythm_track.append(mcopy.pop(0))

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

        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file() and  entry.name.endswith('.mid'):
                    self.playlist.append(entry)
        if len(self.playlist) > 0:
            self.play_index = 0

if __name__ == '__main__':
    t = Ticker(settings)
    #t.load_song('/home/nps/projects/hymns/cwm_rhondda.mid')
    t.open_files('demo')
    try:
        t.run()
    except KeyboardInterrupt:
        t.stop()
