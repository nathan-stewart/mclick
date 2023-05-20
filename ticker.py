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
from buildMeasure import make_rhythm_track
from events import EventQue
from plotMeasure import plot_midi

''' TBD - move midi clock out of midi file into its own thread'''

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
        self.shuffle = False
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
        if self.rhythm_track in self.song.tracks:
            self.song.tracks.remove(self.rhythm_track)

        self.rhythm = self.song.tracks.append(make_rhythm_track(self.song, settings))
        
    def update(self, params):
        if params:
            self.settings = params
        else:
            self.settings = Settings()

    def run(self):
        self.midi_setup()
        self.play_index = -1
        while not self.stopping.is_set():
            if self.playlist:
                if self.shuffle:
                    self.play_index = random.randint(0,len(self.playlist)) - 1
                else:
                    self.play_index += 1
                    if self.play_index >=  len(self.playlist):
                        self.play_index = -1
                self.song = mido.MidiFile(self.playlist[self.play_index])
                print(self.song.filename)
            else:
                self.song = mido.MidiFile()
            self.make_rhythm_from_song()
            #plot_midi(self.song)
            for msg in self.song.play():
                if self.stopping.is_set():
                    break # break only goes out one loop
                self.midi_out.send(msg)

            if self.stopping.is_set():
                break

            if self.play_index >= len(self.playlist):
                self.play_index = -1


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


if __name__ == '__main__':
    t = Ticker(settings)
    # still breaks on Regent Square
    # redeemed speeds up on final measure

    # tell me the story of jesus parses as one measure of 4/4 and one measure of 96/4
    # the midi file looks ok in musescore
    t.open_files('demo')
    try:
        t.run()
    except KeyboardInterrupt:
        t.stop()
