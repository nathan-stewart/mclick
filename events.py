#!/usr/bin/env python3
import mido
from sortedcontainers import SortedList
from collections import defaultdict

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
    def silence(self, event):
        if event:
            start = event[0]
            event.clear()
            event.extend( [start, self.duration] )

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

        self.events = defaultdict(lambda: defaultdict(list))
        ticks_per_beat = midi.ticks_per_beat
        self.duration = 0
        self.measure_count = 0
        num_beats = 4        
        for i, track in enumerate(midi.tracks):
            duration = 0
            measure_count = 0
            ticks_per_measure = ticks_per_beat * num_beats
            for msg in track:
                if hasattr(msg, 'time'):
                    duration += msg.time
                    self.duration= max(self.duration, duration)
                    if msg.type == 'note_on' or msg.type == 'note_off':
                        notes = self.events[msg.channel][msg.note]
                        if (msg.type == 'note_on' and msg.velocity > 0): # note on
                            notes.append( [duration, None] )
                        else:
                            ringing = newest_ringing(notes)
                            self.silence(ringing)
                if msg.type == 'time_signature':
                    measure_elapsed = 0
                    num_beats = msg.numerator
                    ticks_per_measure = ticks_per_beat * num_beats
                    #self.rhythmq.append(make_template_measure(new_meas,ppq = ticks_per_beat))
                if duration >= ticks_per_measure:
                    duration = 0
                    measure_count += 1
                self.measure_count = max(self.measure_count, measure_count)

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
    
    def get_channel_ranges(self):
        ranges = {}
        for ch, nn in self.unique_note_set():
            if ch not in ranges:
                ranges[ch] = [nn,nn]
            else:
                channel = ranges[ch]
                channel[0] = min(nn,channel[0])
                channel[1] = max(nn,channel[1])
        chlist = []
        for c in ranges.keys():
            chlist.append( ranges[c] )
        return chlist

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
        s += 'duration = %d' % self.duration
        return s

if __name__ == "__main__":
    m = mido.MidiFile('demo/redeemed.mid')
    for n in m.tracks[0]:
        print(n)
    eq = EventQue(m)
    print(str(eq))
    print(eq.get_channel_ranges())
