#!/usr/bin/python3
import mido
from sortedcontainers import SortedList
from settings import settings
from plotMeasure import plot_midi

class AbstimeMessage:
    def __init__(self, t, m):
        self.t = t
        self.m = m

    def __lt__(self, other):
        return self.t < other.t

def make_template_measure(params, ppq=480):
    rhythmq = SortedList()
    eight_track = SortedList()

    def enqueue(que, partname, events):
        last_t = 0
        last_t = 0
        for t in events:
            msg = None
            if partname == 'clock':
                msg = mido.Message('clock',time=t-last_t)
            else:
                v  = params[partname]['volume']
                n = params[partname]['note']
                msg = mido.Message('note_on',
                                    channel=9,
                                    note=n,
                                    velocity=v,
                                    time=t-last_t)
            if msg:
                que.add(AbstimeMessage(t,msg))
            last_t = t

    beat_count = params['num_beats']
    clock = [int(n * ppq / 24.0) for n in range(24 * beat_count)]
    enqueue(rhythmq,'clock', clock)
    enqueue(rhythmq,'measure', [0])

    skip = False
    if 'skip' in params['beat'].keys():
        skip = params['beat']['skip']
    swing = min(1.0, max(0.0, params['swing'] / 100.0))
    compound = True if beat_count in [6,9,12] else False
    #print('Time Signature = %d %s %s %s' % (beat_count, 'swing' if swing > 0 else 'straight',  'compound' if compound else 'simple', 'skip' if skip else ''))

    # don't play the one - it's played by the measure
    beats = [int(b * ppq)  for b in range(1,beat_count) ]
    if skip and beat_count == 3: # in 3/4 time, skip beat plays the 3
        beats = [2 * ppq]
    elif skip and  beat_count == 4: # in 4/4 time skip beat plays 2 and 4
        beats = [b * ppq for b in [1,3]]
    elif compound:
        # signatures considered compound
        # we play beats on 1, 4, 7, 10 and 8ths elsewhere
        beats = [int(b * ppq) for b in range(1,beat_count) if not b%3]
    enqueue(rhythmq, 'beat', beats)

    if compound:
        # compounds play eights as weak beats - they're not half beats
        # we skipped these beats above
        eighths = [ int(ppq * n) for n in range(beat_count) if n%3 ]
    else:
        eights = [ int(ppq * n /2.0) for n in range(beat_count * 2)]
        # capping swing at dotted eighth as a hard swing
        sw_adj = int(ppq / 4.0 * swing)
        eighths = [ int(ppq * n/2.0 +(n%2)*sw_adj) for n in range(beat_count * 2) ]
    enqueue(eight_track, 'eighths', eighths)

    subdivide = True if ((params['sixteenths']['volume'] > 0) and
                         (params['eighths']['volume'] > 0) and
                         not compound) else False
    if subdivide:
        # change the eight notes to the same sound as sixteenths
        for abstime in eight_track:
            abstime.m.note = params['sixteenths']['note']

    sixteenths = []
    if compound:
        sw_adj = int(ppq / 4.0  * swing)
        sixteenths = [int(ppq * n /2.0 + sw_adj*(n%2)) for n in range(beat_count * 2) ]
    else:
        # if time signature is simple and we are swinging eighth's don't play 16ths
        if swing <= 0.001:
            sixteenths = [int(ppq * n / 4.0) for n in range(beat_count * 4)]
    enqueue(rhythmq, 'sixteenths', sixteenths)

    # we kept the eighths separate until now - merge them into the priority queue
    for e in eight_track:
        rhythmq.add(e)

    percussion = mido.MidiTrack()
    while rhythmq:
        percussion.append(rhythmq.pop(0).m)
    return percussion

if __name__ == "__main__":
    m = make_template_measure(settings)
    f = mido.MidiFile()
    f.tracks.append(m)
    plot_midi(f)
