#!/usr/bin/env python3
import mido
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

import matplotlib.pyplot as plt

def plot_midi_events(events):
    # Prepare data for plotting
    channels = sorted(events.keys())
    data = {}

    # Collect note numbers with actual note information
    for channel in channels:
        data[channel] = []
        for note_number, note_events in events[channel].items():
            if any(note_event[1] is not None for note_event in note_events):
                data[channel].append(note_number)
    # Plotting
    plt.figure(figsize=(12, 6))

    current_time = 0  # Current time position

    for channel, channel_data in events.items():
        for note_number, note_events in channel_data.items():
            for note_event in note_events:
                start_time = current_time + note_event[0]
                stop_time = None if note_event[1] is None else current_time + note_event[1]

                if stop_time is not None:
                    duration = stop_time - start_time
                    plt.barh(note_number, duration, left=start_time, height=0.7, alpha=0.7, color=f'C{channel}')
                else:
                    plt.scatter(start_time, note_number, marker='|', color=f'C{channel}', s=100)
                current_time += note_event[0]

    # Configure plot
    plt.xlabel('Time')
    plt.ylabel('Note Number')
    plt.title('MIDI Events')
    plt.yticks(list(range(len(events.keys()))), [f'Ch {channel}' for channel in events.keys()])
    plt.grid(True)
    plt.tight_layout()

    # Display or save the plot
    plt.show()

def print_events(events):
    for channel in sorted(events.keys()):
        print('Ch % 2d: [' % channel)
        for nn in sorted(events[channel].keys()):
            notes = '% 2d: ' % nn
            notes += ' '
            for i, ne in enumerate(events[channel][nn]):
                if ne[1]:
                    notes += '%03d - %03d' % (ne[0], ne[1])
                else:
                    notes += '%03d      ' % ne[0]
                notes += '   '
                if (i> 1 and i % 5 == 0):
                    notes += '\n'
                    notes += '      '
            print('%s' % notes)
        print('       ]')

def parse_midi_file(mid):
    """
    Returns:
        A dictionary where each key is a MIDI channel, and the value is a nested dictionary.
        All tracks processed, but it is assumed that one track = one channel and vice versa
        The nested dictionary has note numbers as keys, and the values are lists of timestamp
        tuples (start_ticks, stop_ticks) in ticks where stop_ticks is None if no note off occured
    """
    events = defaultdict(lambda: defaultdict(list))
    cumulative_ticks = 0

    # Takes a list of note on/off events for a single channel/note number
    # Returns the oldest one without a stop event [start,stop]
    def oldest_ringing(notes):
        for n in notes:
            if not n[1]:
                return n
        return None

    def silence(event):
        if event:
            start = event[0]
            event.clear()
            event.extend( [start, cumulative_ticks] )

    for i, track in enumerate(mid.tracks):
        cumulative_ticks = 0
        for msg in track:
            cumulative_ticks = 0
            if not msg.is_meta:
                cumulative_ticks += msg.time
                if msg.type == 'note_on' or msg.type == 'note_off':
                    notes = events[msg.channel][msg.note]
                    if (msg.type == 'note_on' and msg.velocity > 0): # note on
                        notes.append( [cumulative_ticks, None] )
                    else: 
                        silence(oldest_ringing(notes))
    return events

def plot_midi(f):
    m = None
    if isinstance(f, str):
        m = mido.MidiFile(f)
    elif isinstance(f, mido.MidiFile):
        m = f
    else:
        raise TypeError

    e = parse_midi_file(m)
    print_events(e)
    plot_midi_events(e)

if __name__ == '__main__':
    f = mido.MidiFile('demo/cwm_rhondda.mid')
    events = parse_midi_file(f)
    plot_midi_events(events)
