#!/usr/bin/env python3
import mido
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def plot_midi_events(events):
    """
    Plots MIDI events organized by channel and note number.
    """
    # Collect note numbers for all events
    all_notes = sorted(list(set(n for ch_events in events.values() for n, _, _ in ch_events)))
    
    # Create a list of channel names for the plot legend
    channel_names = [f"Ch {ch}" for ch in sorted(events.keys())]
    
    # Create a 2D array of note durations for each channel and note
    note_durations = np.zeros((len(channel_names), len(all_notes)))
    for i, ch in enumerate(sorted(events.keys())):
        for note, start_time, duration in events[ch]:
            note_durations[i, all_notes.index(note)] = duration
    
    # Plot the note durations using a stacked bar plot
    fig, ax = plt.subplots()
    ax.bar(np.arange(len(all_notes)), note_durations[0], align='center')
    for i in range(1, len(channel_names)):
        ax.bar(np.arange(len(all_notes)), note_durations[i], bottom=np.sum(note_durations[:i], axis=0), align='center')
    
    # Format the plot
    ax.set_xticks(np.arange(len(all_notes)))
    ax.set_xticklabels(all_notes)
    ax.set_xlabel("Note Number")
    ax.set_ylabel("Time (ticks)")
    ax.legend(channel_names, loc='upper right')
    plt.show()

def plot_midi_file(mid):
    """
    Parse the contents of a MIDI file into a dictionary of events.

    Returns:
        A dictionary where each key is a MIDI channel number (0-15), and the value is a list of tuples
        representing the note events on that channel. Each tuple contains (note number, tick time since last event).
    """
    events = defaultdict(list)
    note_start_times = {}
    
    for i, track in enumerate(mid.tracks):
        for msg in track:
            cumulative_ticks = 0
            if not msg.is_meta:
                event = events.get(msg.channel)
                if event:
                    cumulative_ticks = event[0][1]
                    for channel in events:
                        events[channel].insert(0, (events[channel][0][0], events[channel][0][1] - cumulative_ticks))
                if msg.type == 'note_on':
                    if msg.velocity != 0:
                        if msg.channel not in events:
                            events[msg.channel] = []
                        if msg.note not in note_start_times:
                            note_start_times[msg.note] = msg.time
                        else:
                            note_duration = msg.time - note_start_times[msg.note]
                            events[msg.channel].append((msg.note, note_start_times[msg.note], note_duration))
                            del note_start_times[msg.note]
                elif msg.type == 'note_off':
                    if msg.channel in events:
                        for i, (note, tick, _) in enumerate(reversed(events[msg.channel])):
                            if note == msg.note:
                                events[msg.channel][-i - 1] = (note, tick, msg.time)
                                break
                else:
                    for channel in events:
                        events[channel][0] = (events[channel][0][0], events[channel][0][1] + msg.time)
                        
        # End any notes that were started on this track but not explicitly ended
        for note, start_time in note_start_times.items():
            if not msg.is_meta:
                events[msg.channel].append((note, start_time, mid.length - start_time))
                del note_start_times[note]
        
        # Reverse each track so that the notes are in chronological order
        for channel in events:
            events[channel] = list(reversed(events[channel]))
    return events 


def parse_midi_file(file_path):
    midi_file = mido.MidiFile(file_path)
    events = defaultdict(list)
    for i, track in enumerate(midi_file.events):
        cumulative_ticks = 0
        for msg in track:
            cumulative_ticks += msg.time
            if msg.type == 'note_on':
                events[msg.channel].append((msg.note, cumulative_ticks))
            elif msg.type == 'note_off':
                for i, (note, tick) in enumerate(reversed(events[msg.channel])):
                    if note == msg.note:
                        duration = cumulative_ticks - tick
                        events[msg.channel][-1-i] = (note, tick, duration)
                        break
                else:
                    print(f"Warning: Note off with no corresponding note on. Channel: {msg.channel}, Note: {msg.note}")
    return events

if __name__ == '__main__':
    f = mido.MidiFile('demo/cwm_rhondda.mid')
    plot_midi_file(f)

