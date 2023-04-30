#!/usr/bin/python3 
from collections import deque
import threading
import time
import math
import mido
import sys

from settings import settings
from buildMeasure import make_template_measure

class Ticker(threading.Thread):
    def __init__(self, params):
        super().__init__()
        self.lock = threading.Lock()
        self.stopping = threading.Event() # this is only used to exit
        self.settings = None
        self.trackmap = {}
        self.midi_out = None
        self.measure = None  # this is the base pattern for the metronome
        self.song = None                # this is the song being played (future support)
        self.playlist = mido.MidiFile() # this is what actually gets sent to the MIDI interface
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

    def copy_measure_to_playlist(self):
        print('copy_measure_to_playlist')
        if not self.measure:
            return
            
        # if there's already a track with channel 10 content, add to that one
        rhythm = None
        added = False
        for pt in self.playlist.tracks:
            for msg in pt:
                if msg.channel == 9:
                    rhythm = pt
                    break
            if rhythm:
                break
        if not rhythm:
            rhythm = mido.MidiTrack()
            added = True

        # we now have a track to hold the metronome functions - copy into it
        measure_copy = self.measure.copy()
        while measure_copy:
            rhythm.append(measure_copy.pop(0))
        if added:
            self.playlist.tracks.append(rhythm)
                
    def copy_song(self):
        self.playlist = mido.MidiFile()
        ticks_per_beat = self.song.ticks_per_beat
        for st in self.song.tracks:
            pt = mido.MidiTrack()
            ts = 4,4            
            measure_elapsed = 0
            tpm = ts[0] * ticks_per_beat
            for sm in st:
                if sm.is_meta:
                    if   sm.type == 'time_signature':
                        ts = sm.numerator,sm.denominator
                        measure_elaped = 0
                        self.copy_measure_to_playlist()
                pt.append(sm)
                measure_elapsed += sm.time
                if measure_elapsed >= tpm:
                    measure_elapsed = 0
                    self.copy_measure_to_playlist()
            self.playlist.tracks.append(pt)
            
        #print(self.playlist)
        # default to time signature from the song
        # after loading song, copy the metronome track to match                
        # loading song may be discontinuous        

    def load_song(self, name):
        self.song = mido.MidiFile(name)
        self.copy_song()
                
        
    def update(self, params):
        self.measure = make_template_measure(params)
        self.settings = params

    def run(self):
        self.midi_setup()
        if not self.song:
            print('no song, just metronome')
            self.copy_measure_to_playlist()
        print(self.playlist)
        while not self.stopping.is_set():
            for msg in self.playlist.play():
                if self.stopping.is_set():
                    break # break only goes out one loop
                self.midi_out.send(msg)
                
            if self.stopping.is_set():
                break

if __name__ == '__main__':
    t = Ticker(settings)
    #t.load_song('/home/nps/projects/hymns/cwm_rhondda.mid')
    try:
        t.run()
    except KeyboardInterrupt:
        t.stop()
