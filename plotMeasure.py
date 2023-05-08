#!/usr/bin/env python3
import mido
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

import matplotlib.pyplot as plt

def plot_midi_events(events):
    # Extract note numbers from events dictionary
    note_numbers = [note for channel_events in events.values() for note in channel_events]
    print(note_numbers)
    # Check if note_numbers is empty
    if not note_numbers:
        print("No MIDI events to plot.")
        return

    min_note_number = min(note_numbers)
    max_note_number = max(note_numbers)
    # Prepare data for plotting
    channels = sorted(events.keys())
    note_numbers = set()
    data = {}

    # Collect note numbers with actual note information
    for channel in channels:
        data[channel] = []
        for note_number, note_events in events[channel].items():
            if any(note_event[1] is not None for note_event in note_events):
                data[channel].append(note_number)
                note_numbers.add(note_number)

    # Plotting
    plt.figure(figsize=(12, 6))

    min_note_number = min(note_numbers)
    max_note_number = max(note_numbers)

    for channel in channels:
        if channel not in data:
            continue
        for note_number in data[channel]:
            note_events = events[channel][note_number]
            for note_event in note_events:
                start_time = note_event[0]
                stop_time = note_event[1]
                if stop_time is not None:
                    duration = stop_time - start_time
                    plt.barh(note_number, duration, left=start_time, height=0.7, alpha=0.7,
                             color=f'C{channel}')
                else:
                    plt.scatter(start_time, note_number, marker='|', color=f'C{channel}', s=100)

    # Configure plot
    plt.xlabel('Time')
    plt.ylabel('Channel')
    plt.title('MIDI Events')
    plt.yticks(list(range(len(channels))), [f'Ch {channel}' for channel in channels])
    plt.ylim(min_note_number - 1, max_note_number + 1)
    plt.grid(True)
    plt.tight_layout()

    # Display or save the plot
    plt.show()

def print_events(events):
    for channel in sorted(events.keys()):
        print('Ch % 2d: [' % channel)
        for nn in sorted(events[channel].keys()):
            notes = '% 2d: ' % nn
            count = 0
            for ne in events[channel][nn]:
                if ne[1]:
                    notes += '%03d - %03d' % (ne[0], ne[1])
                else:
                    notes += '%03d      ' % ne[0]
                notes += '   '
                count += 1
                if count > 5:
                    break
            print('           %s' % notes)
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


if __name__ == '__main__':
    events = {
    0: {
        60: [[0, 100], [200, None], [300, 150]],
        62: [[100, 120], [250, None]],
        64: [[150, None]]
    },
    1: {
        65: [[50, 80], [180, 110]],
        67: [[120, 130], [220, 140], [270, None]]    },
    9: {
        38: [[0, None], [180, None]],
        62: [[120, None], [220, None], [270, None]]    }}

    # first note_on in cwm_rhondda is 
    #>>> f.tracks[0][10]
    #Message('note_on', channel=0, note=55, velocity=110, time=0)
    # and turns off at 
    #>>> f.tracks[0][13]
    #Message('note_on', channel=0, note=55, velocity=0, time=455)

    # but seeing no note_offs and times are wrong
    # 55: 000         025         025         013         025         000


    #plot_midi_events(events)
    #print_events(events)
    f = mido.MidiFile('demo/cwm_rhondda.mid')
    #f = mido.MidiFile()
    #t = mido.MidiTrack()
    #f.tracks.append(t)
    #t.append(mido.Message('note_on', channel=0, note=55, velocity=110, time=0))
    #t.append(mido.Message('note_on', channel=0, note=55, velocity=0, time=455))
    e = parse_midi_file(f)
    print_events(e)
    plot_midi_events(e)
