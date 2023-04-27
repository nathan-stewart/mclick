import threading, heapq
import time, math, mido, sys
from settings import settings

import numpy as np
import matplotlib.pyplot as pp

def plot_measure(series, width=6, height=0.5):
    fig, ax = pp.subplots()
    for i, label in enumerate(series.keys()):
        t = 0
        times = []
        for msg in series[label]:
            t += msg.time
            times.append(t)
        ax.plot(times, np.zeros_like(times) + i, '|', markersize=10, label=label)
    ax.set_yticks(range(len(series)))
    ax.set_yticklabels(list(series.keys()), fontsize=12)
    ax.tick_params(axis='both', labelsize=12)
    ax.autoscale(enable=True, axis='x', tight=True)
    fig.set_size_inches(width, len(series) * height)
    pp.subplots_adjust(left=0.2, right=0.95, top=0.95, bottom=0.1)
    pp.xlabel('Time', fontsize=14)
    pp.show()

def build_midi_from_settings(params):
    def add_track(partname, events):
        track = mido.MidiTrack()
        last_t = 0
        for t in events:
            if partname == 'clock':                
                track.append(mido.Message('clock',time=t - last_t ))
            else:
                v  = params[partname]['volume']
                if v > 0:
                    n = params[partname]['note']
                    track.append(mido.Message('note_on', channel=9, note=n, velocity=v, time=t-last_t))
            last_t = t
        return track
    
    trackmap = {}
    ppq = 100
    beat = 60.0 / float(params['tempo'])
    beat_count = params['num_beats']

    clock = [int(n * ppq * beat / 24.0) for n in range(24 * beat_count)]
    trackmap['clock'] = add_track('clock', clock)
    trackmap['measure']= add_track('measure', [0])
    
    skip = params['beat']['skip']
    swing = min(1.0, max(0.0, params['swing'] / 100.0))
    compound = True if beat_count in [6,9,12] else False
    print('Time Signature = %d %s %s %s' % (beat_count,
        'swing' if swing > 0 else '',
        'compound' if compound else '',
        'skip' if skip else ''))

    # don't play the one - it's played by the measure 
    beats = [int(b * ppq * beat)  for b in range(1,beat_count) ] 
    if skip and beat_count == 3: # in 3/4 time, skip beat plays the 3
        beats = [2 * ppq * beat]
    elif skip and  beat_count == 4: # in 4/4 time skip beat plays 2 and 4
        beats = [b * ppq * beat for b in [1,3]]
    elif compound: 
        # signatures considered compound
        # we play beats on 1, 4, 7, 10 and 8ths elsewhere
        beats = [int(b * ppq * beat) for b in range(1,beat_count) if not b%3]
    trackmap['beat'] = add_track('beat', beats)

    if compound:
        # compounds play eights as weak beats - they're not half beats 
        # we skipped these beats above
        eighths = [ int(ppq * beat * n) for n in range(beat_count) if n%3 ]
    else:
        eights = [ int(ppq * beat * n /2.0) for n in range(beat_count * 2)] 
        # capping swing at dotted eighth as a hard swing
        sw_adj = int(ppq * beat / 4.0 * swing)
        eighths = [ int(ppq * beat * n/2.0 +(n%2)*sw_adj) for n in range(beat_count * 2) ]
    trackmap['eighths'] = add_track('eighths', eighths)

    subdivide = True if ((params['sixteenths']['volume'] > 0) and 
                         (params['eighths']['volume'] > 0) and 
                         not compound) else False
    if subdivide:
        # change the eight notes to the same sound as sixteenths
        for m in trackmap['eighths']:
            m.note = params['sixteenths']['note']

    sixteenths = []
    if compound:
        sw_adj = int(ppq * beat / 4.0  * swing)
        sixteenths = [int(ppq * n * beat/2.0 + sw_adj*(n%2)) for n in range(beat_count * 2) ]
    else:
        # if time signature is simple and we are swinging eighth's don't play 16ths
        if swing <= 0.001:
            sixteenths = [int(ppq * n * beat/4.0) for n in range(beat_count * 4)]
    trackmap['sixteenths'] = add_track('sixteenths', sixteenths)
    print(trackmap.keys())
    return trackmap

class Ticker(threading.Thread):
    def __init__(self, params):
        super().__init__()
        self.lock = threading.Lock()
        self.stopping = threading.Event() # this is only used to exit
        self.updated = threading.Event()
        self.trackmap = {}
        self.midi_out = None

        self.measure = mido.MidiFile()  # this is the base pattern for the metronome
        self.song = None                # this is the song being played (future support)
        self.playlist = mido.MidiFile() # this is what actually gets sent to the MIDI interface
        self.update(params)

    def stop(self):
        self.stopping.set()


        self.settings = params
        self.midi_setup()
        self.updated.set()

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

    def update(self):
        pass

    def run(self):
        self.midi_setup()
        while not self.stopping.is_set():
            for msg in self.playlist.play():
                if self.stopping.is_set() or self.updated.is_set():
                    break
                if self.updated.is_set(): 
                    self.midi_out.send(msg)
            if self.stopping.is_set():
                break

if __name__ == "__main__":
    trackmap = build_midi_from_settings(settings)
    plot_measure(trackmap)
