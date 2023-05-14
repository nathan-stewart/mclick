#!/usr/bin/env python3
import mido
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from events import EventQue

def plot_midi_events(events):
    # Prepare data for plotting
    ranges = events.channel_note_ranges()
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray']
    
    y = 0
    y_values = []
    y_labels = []
    channels = sorted(ranges.keys())
    for ch_idx,channel in enumerate(channels):
        for nn_idx in range(ranges[channel][1] - ranges[channel][0]):
            nn = ranges[channel][0] + nn_idx
            if nn in events.events[channel].keys():
                y_values.append(y)
                y_labels.append('Ch %d:% 3d' % (channel, nn))
                x_range = events.events[channel][nn]
                
                if isinstance(x_range, list):
                    for range_element in x_range:
                        start = range_element[0]
                        end = range_element[1]
                        if not end:
                            end = start + 480/8
                        plt.barh(y, width=end-start, left=start, color=colors[ch_idx])
            y += 1
    plt.yticks(y_values, y_labels)
    # Set x-axis label
    plt.xlabel('Time')
    plt.tight_layout()
    plt.show()

def plot_midi(f):
    m = None
    if isinstance(f, str):
        m = mido.MidiFile(f)
    elif isinstance(f, mido.MidiFile):
        m = f
    elif isinstance(f, mido.MidiTrack):
        m = mido.MidiFile()
        m.tracks.append(f)
    else:
        raise TypeError
    eventq = EventQue(m)
    print(eventq)
    plot_midi_events(eventq)

if __name__ == '__main__':
    mf = mido.MidiFile('demo/redeemed.mid')
    eventq = EventQue(mf)
    plot_midi_events(eventq)

