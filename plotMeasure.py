#!/usr/bin/env python3
import mido
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

import matplotlib.pyplot as plt
from events import EventQue

def plot_midi_events(events):
    # Prepare data for plotting
    note_numbers = events.unique_note_set()

    # Create a binary matrix to represent the piano roll grid
    matrix = np.zeros((events.duration, len(note_numbers)))

    for channel, note_number in note_numbers:
        for start_time, stop_time in events.events[channel][note_number]:
            if stop_time:
                matrix[start_time:stop_time, note_numbers.index((channel, note_number))] = 1
            else:
                matrix[start_time, note_numbers.index((channel, note_number))] = 1

    # Set the desired number of pixels for the y-axis
    pixels_per_note = 20  # Adjust as needed

    # Create the subplots
    fig, ax = plt.subplots()

    # Plot the piano roll grid
    ax.imshow(matrix.T, aspect='auto', cmap='binary', origin='lower', interpolation='nearest')

    # Set the y-axis tick positions and labels
    ax.set_yticks(np.arange(len(note_numbers)))
    ax.set_yticklabels(note_numbers)

    # Set the x-axis label
    ax.set_xlabel('Time')

    # Set the plot title
    ax.set_title('MIDI Events - Piano Roll')

    # Adjust the figure height based on the number of notes and desired pixels per note
    figure_height = len(note_numbers) * pixels_per_note
    fig.set_figheight(figure_height)

    plt.tight_layout()
    plt.show()

def plot_midi(f):
    m = None
    if isinstance(f, str):
        m = mido.MidiFile(f)
    elif isinstance(f, mido.MidiFile):
        m = f
    else:
        raise TypeError

    events, duration = parse_midi_file(m)
    print_events(events)
    plot_midi_events(events, duration)

if __name__ == '__main__':
    mf = mido.MidiFile()
    mf.tracks.append(mido.MidiTrack())
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=80, time=0, note=72))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=0, time=100, note=72))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=80, time=0, note=74))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=0, time=100, note=74))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=80, time=0, note=72))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=0, time=100, note=72))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=80, time=400, note=32))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=80, time=0, note=42))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=0, time=100, note=32))
    mf.tracks[0].append(mido.Message('note_on', channel=0, velocity=0, time=00, note=42))
    eventq = EventQue(mf)
    print(str(eventq))

    plot_midi_events(eventq)

    mf = mido.MidiFile('demo/redeemed-melody.mid')
    eventq = EventQue(mf)
    plot_midi_events(eventq)

