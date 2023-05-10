#!/usr/bin/env python3
import mido
from sortedcontainers import SortedList
from collections import defaultdict

# Takes a list of note on/off events for a single channel/note number
# Returns the oldest one without a stop event [start,stop]
def oldest_ringing(notes):
    for n in notes:
        if not n[1]:
            return n
    return None

# This class builds a time ordered representation of midi events
# It's essentially a different view of a Midi file
class EventQue:
    def __init__(self):
        self.events = defaultdict(lambda: defaultdict(list))
        self.duration = 0

    def silence(self, event):
        if event:
            start = event[0]
            event.clear()
            event.extend( [start, self.cumulative_ticks] )

    def parse_midi(self, mid):
        """
        Returns:
            A dictionary where each key is a MIDI channel, and the value is a nested dictionary.
            All tracks processed, but it is assumed that one track = one channel and vice versa
            The nested dictionary has note numbers as keys, and the values are lists of timestamp
            tuples (start_ticks, stop_ticks) in ticks where stop_ticks is None if no note off occured
        """
        ticks_per_beat = mid.ticks_per_beat
        self.cumulative_ticks = 0
        self.measure_count = 0
        num_beats = 4
        for i, track in enumerate(mid.tracks):
            cumulative_ticks = 0
            measure_count = 0
            ticks_per_measure = ticks_per_beat * num_beats
            for msg in track:
                if msg.type == 'time_signature':
                    measure_elapsed = 0
                    num_beats = msg.numerator
                    ticks_per_measure = ticks_per_beat * num_beats
                    #self.rhythmq.append(make_template_measure(new_meas,ppq = ticks_per_beat))
                elif not msg.is_meta:
                    cumulative_ticks += msg.time
                    if msg.type == 'note_on' or msg.type == 'note_off':
                        notes = self.events[msg.channel][msg.note]
                        if (msg.type == 'note_on' and msg.velocity > 0): # note on
                            notes.append( [cumulative_ticks, None] )
                        else:
                            self.silence(oldest_ringing(notes))
                if measure_elapsed >= ticks_per_measure:
                    print('new measure = measure #%d on track %d' % (measure_count, i))
                    measure_elapsed = 0
                    new_meas = settings
                    measure_count += 1
                    self.rhythmq.append(make_template_measure(new_meas,ppq = ticks_per_beat))
                self.measure_count = max(self.measure_count, measure_count)
                self.cumulative_ticks = max(self.cumulative_ticks, cumulative_ticks)
        return (self.events, self.cumulative_ticks)



    def __str__(self):
        s = ''
        for channel in sorted(self.events.keys()):
            s = 'Ch % 2d: [' % channel
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
                s += '%s' % notes
            s += '       ]'
        return s

if __name__ == "__main__":
    eq = EventQue()
    eq.parse_midi(mido.MidiFile('demo/cwm_rhondda.mid'))
    print(str(eq))



