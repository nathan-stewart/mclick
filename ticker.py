#!/usr/bin/python3
from sortedcontainers import SortedList
import threading
import time
import math
import mido
import sys
import random
import os
from settings import Settings
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
        self.pause = threading.Event()
        self.rhythmq = [] # list of SortedLists
        self.rhythm_track = mido.MidiTrack()
        self.rhythm_track.name = 'MClick'
        self.song = mido.MidiFile()
        self.shuffle = False
        if params:
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
        if self.settings:
            mido.set_backend(self.settings['midi_backend'])
            if self.midi_out:
                self.midi_teardown()

            port = self.settings['midi_port']
            if port and any (port in listed for listed in mido.get_output_names()):
                self.midi_out = mido.open_output(port)
                self.midi_out.send(mido.Message('start'))

    def make_rhythm_from_song(self):
        if not self.settings:
            raise RuntimeError('No settings')

        if self.rhythm_track in self.song.tracks:
            self.song.tracks.remove(self.rhythm_track)

        self.rhythm = self.song.tracks.append(make_rhythm_track(self.song, self.settings))
        
    def update(self, params):
        if params:
            self.midi_setup()
            #mido.bpm2tempo(self.settings['tempo'])
        else:
            self.midi_teardown()
        self.settings = params

    def load_song(self, filename = None):
        self.song = mido.MidiFile(filename)
        initial_tempo = 120
        for msg in self.song:
            # any tempo change which occurs after the first note is not an 'initial' tempo
            if msg.type == 'note_on':
                break 

            if msg.type == 'set_tempo':
                initial_tempo = mido.tempo2bpm(msg.tempo)
                break;
        self.song.initial_tempo = initial_tempo
        self.settings['tempo'] = initial_tempo
    
    def transport_action(self, source):
        if source == 'id_prev_song':
            pass
        elif source == 'id_begin_song':
            pass
        elif source == 'id_play':        
            self.pause.clear()
        elif source == 'id_pause':        
            self.pause.set()
        elif source == 'id_next_song':
            pass

    def run(self):
        self.play_index = -1
        while not self.stopping.is_set():
            if not self.settings:
                time.sleep(0.5)
                continue

            if self.playlist:
                if self.shuffle:
                    self.play_index = random.randint(0,len(self.playlist)) - 1
                else:
                    self.play_index += 1
                    if self.play_index >=  len(self.playlist):
                        self.play_index = -1
                self.load_song(self.playlist[self.play_index])
                print(self.song.filename)
            else:
                self.load_song()

            self.make_rhythm_from_song()
            #plot_midi(self.song)
            
            for msg in self.song.play():
                if self.stopping.is_set():
                    break

                while self.pause.is_set():
                    if self.stopping.is_set():
                        break
                    time.sleep(0.1)
                
                if self.midi_out:
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
    t = Ticker(Settings())
    # still breaks on Regent Square
    # redeemed speeds up on final measure

    # tell me the story of jesus parses as one measure of 4/4 and one measure of 96/4
    # the midi file looks ok in musescore
    t.open_files('demo')
    try:
        t.run()
    except KeyboardInterrupt:
        t.stop()
