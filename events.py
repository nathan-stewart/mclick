#!/usr/bin/env python3
import mido
from sortedcontainers import SortedList
from collections import defaultdict
import math

# Takes a list of note on/off events for a single channel/note number
# Returns the oldest one without a stop event [start,stop]
def newest_ringing(notes):
    for n in reversed(notes):
        if not n[1]:
            return n
    return None

# This class builds a time ordered representation of midi events
# It's essentially a different view of a Midi file
class EventQue:
    def ticks_per_beat(self, nominal):
        # ppq is fixed - obtained early in __init__()
        return int(self.ppq * 4 / nominal)

    def silence(self, event, now):
        if event:
            start = event[0]
            event.clear()
            event.extend( [start, now] )

    def count_measures(self, midi):
        self.ppq = midi.ticks_per_beat
        self.duration = 0
        self.measures = []
        ts = (4,4)
        measure_elapsed = 0
        ticks_per_measure = ts[0] * self.ticks_per_beat(ts[1])
        for msg in mido.merge_tracks(midi.tracks):
            if msg.type == 'clock':
                continue 

            if hasattr(msg, 'time'):
                measure_elapsed += msg.time
            
            if measure_elapsed >= ticks_per_measure:
                measure_elapsed -= ticks_per_measure
                self.measures.append(ts)

            if msg.type == 'time_signature':
                ts = (msg.numerator, msg.denominator)
                ticks_per_measure = ts[0] * self.ticks_per_beat(ts[1])
                measure_elapsed = 0
        
        # if time remains, add that measure
        if measure_elapsed > 0:
            self.measures.append(
                    (math.ceil(measure_elapsed / self.ticks_per_beat(ts[1])), ts[1]))

        self.duration = sum(m[0] for m in self.measures * self.ticks_per_beat(ts[1]))

    def __init__(self, midi = None):
        """
        Returns:
            A dictionary where each key is a MIDI channel, and the value is a nested dictionary.
            All tracks processed, but it is assumed that one track = one channel and vice versa
            The nested dictionary has note numbers as keys, and the values are lists of timestamp
            tuples (start_ticks, stop_ticks) in ticks where stop_ticks is None if no note off occured
        """
        if not midi:
            midi = mido.MidiFile()
        self.ppq = midi.ticks_per_beat
        self.events = defaultdict(lambda: defaultdict(list))
        ts = (4,4)

        self.count_measures(midi)

        for i, track in enumerate(midi.tracks):
            ticks_per_measure = ts[0] * self.ticks_per_beat(ts[1]) 
            position = 0
            for msg in track:
                if hasattr(msg, 'time'):
                    position += msg.time

                    if msg.type == 'time_signature':
                        ts = (msg.numerator, msg.denominator)
                    
                    elif msg.type == 'note_on' or msg.type == 'note_off':
                        notes = self.events[msg.channel][msg.note]
                        if (msg.type == 'note_on' and msg.velocity > 0): # note on
                            notes.append( [position, None] )
                        else:
                            ringing = newest_ringing(notes)
                            self.silence(ringing, position)
        
        if self.events and not self.measures:
            #print(midi.filename)
            print('ticks_per_measure = %d' % ticks_per_measure)
            print('ticks_per_beat = %d' % self.ticks_per_beat(ts[1]))
            print('time_signature = %d'% ts)
            print('measure_elapsed = %d'% measure_elapsed)
            print(position)
            raise RuntimeError

    def channels(self):
        return self.events
    
    def notes(self, channel):
        return self.events[channel].keys()

    def note_events(self, channel, note):
        return self.events[channel][note]
    
    def unique_note_set(self):
        notes = set()
        for ch in sorted(self.events.keys()):
            for nn in sorted(self.events[ch].keys()):
                notes.add( (ch,nn) )
        return sorted(notes)

    def channel_note_ranges(self):
        ranges = {}
        for ch,nn in self.unique_note_set():
            if ch not in ranges.keys():
                ranges[ch] = [nn,nn]
            else:
                ranges[ch][0] = min(ranges[ch][0],nn)
                ranges[ch][1] = max(ranges[ch][1],nn)
        return ranges 
    
    def __str__(self):
        s = ''
        for channel in sorted(self.events.keys()):
            s = 'Ch % 2d: [ ' % channel
            for nn in sorted(self.events[channel].keys()):
                notes = '% 2d: ' % nn
                notes += ' '
                for i, ne in enumerate(self.events[channel][nn]):
                    if ne[1]:
                        notes += '%03d - %03d' % (ne[0], ne[1])
                    else:
                        notes += '%03d      ' % ne[0]
                    notes += '   '
                    if (i> 1 and i % 5 == 0):
                        notes += '\n'
                        notes += '      '
                s += '%s\n' % notes
            s += '         ]\n'
        s += 'duration = %d\n' % self.duration
        s += 'measures = ' + ', '.join([str(t) for t in self.measures])
        return s

if __name__ == "__main__":
    import os
    with os.scandir('demo') as it:
        for entry in it:
            if entry.is_file() and  entry.name.endswith('cross.mid'):
                print(entry)
                m = mido.MidiFile(entry)
                eq = EventQue(m)
                print(eq.measures)
                print('%d bars' % len(eq.measures))
