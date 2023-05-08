#!/usr/bin/env python3
import mido
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict


def build_plottables(events):
    """
    Builds plottable objects for MIDI events.
    """
    # Collect note numbers for all events
    note_numbers = sorted(list(set(n for ch_events in events.values() for n, *_ in ch_events)))

    # Create a list of channel names for the plot legend
    channel_names = [f"Ch {ch}" for ch in sorted(events.keys())]

    # Create a 2D array of note durations for each channel and note
    note_durations = np.zeros((len(channel_names), len(note_numbers)))
    time_values = None  # Placeholder for time values

    for i, ch in enumerate(sorted(events.keys())):
        try:
            for note, start_time, duration in events[ch]:
                if time_values is None:
                    time_values = np.zeros(len(events[ch]))

                if duration == 0:
                    # Assign a default duration value for notes without a corresponding note-off event
                    duration = 1
                try:
                    note_durations[i, note_numbers.index(note)] = duration
                    time_values[note_numbers.index(note)] = start_time
                except ValueError:
                    continue
        except ValueError:
            continue
    return time_values, note_durations, channel_names


def plot_midi_events(events):
    """
    Plots MIDI events organized by channel and note number.
    """
    print_events(events)
    import sys
    sys.exit(0)
    # Build the plottable objects
    time_values, note_durations, channel_names = build_plottables(events)

    # Plot the note durations using a stacked bar plot
    fig, ax = plt.subplots()
    ax.bar(time_values, note_durations[0], align='center')

    for i in range(1, len(channel_names)):
        ax.bar(
            time_values,
            note_durations[i],
            bottom=np.sum(note_durations[:i], axis=0),
            align='center'
        )

    # Format the plot
    ax.set_xlabel("Time")
    ax.set_ylabel("Duration")
    ax.legend(channel_names, loc='upper right')
    plt.show()

def print_events(events):
    for channel in sorted(events.keys()):
        print('channel = %d' % channel)
    import sys
    sys.exit(0)

def parse_midi_file(mid):
    """
    Parse the contents of a mido.MidiFile into a dictionary of events.

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
        return next((n for n in notes if n[1]), None)

    def silence(event):
        if event:
            start = event[0]
            event.clear()
            event = (start, cumulative_ticks)

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

def plot_midi_file(m):
    plot_midi_events(parse_midi_file(m))

if __name__ == '__main__':
    f = mido.MidiFile('demo/cwm_rhondda.mid')
    plot_midi_file(f)
