#!/usr/bin/python3
import mido
from sortedcontainers import SortedList
from settings import settings

def make_template_measure(params, ppq=480):
    rhythm = []

    def add_track(partname, events):

        last_t = 0
        track = mido.MidiTrack()
        for t in events:
            msg = None
            if partname == 'clock':
                msg = mido.Message('clock',time=t-last_t)
            else:
                v = params[partname]['volume']
                n = params[partname]['note']
                msg = mido.Message('note_on',
                                    channel=9,
                                    note=n,
                                    velocity=v,
                                    time=t-last_t)
            if msg:
                track.append(msg)
            last_t = t
        return track

    ts = params['time_signature']
    tpb = int(ppq * 4 / ts[1])
    clock = [int(n * tpb / 24.0) for n in range(24 * ts[0])]
    rhythm.append(add_track('clock', clock))
    rhythm.append(add_track('measure', [0]))
    #print('measure (%d) = ' % (params['measure']['note']), [0])

    skip = False
    if 'skip' in params['beat'].keys():
        skip = params['beat']['skip']
    swing = min(1.0, max(0.0, params['swing'] / 100.0))
    compound = True if ts[0] in [6,9,12] else False

    # don't play the one - it's played by the measure
    beats = [int(b * tpb)  for b in range(1,ts[0]) ]
    if skip and ts[0] == 3: # in 3/4 time, skip beat plays the 3
        beats = [2 * tpb]
    elif skip and ts[0] == 4: # in 4/4 time skip beat plays 2 and 4
        beats = [b * tpb for b in [1,3]]
    elif compound:
        # signatures considered compound
        # we play beats on 1, 4, 7, 10 and 8ths elsewhere
        beats = [int(b * tpb) for b in range(1,ts[0]) if not b%3]
    #print('beat(%d) = ' % (params['beat']['note']), beats)
    rhythm.append(add_track('beat', beats))

    if compound:
        # compounds play eights as weak beats - they're not half beats
        # we skipped these beats above
        eighths = [ int(n * tpb) for n in range(ts[0]) if n % 3 ]
    else:
        eights = [ int(n * tpb  /2.0) for n in range(ts[0]* 2)]
        # capping swing at dotted eighth as a hard swing
        sw_adj = int(tpb * swing / 4.0)
        eighths = [ int(n * tpb /2.0 +(n % 2) * sw_adj) for n in range(ts[0] * 2) ]
    #print('eighths(%d) = ' % (params['eighths']['note']), eighths)
    rhythm.append(add_track('eighths', eighths))

    subdivide = True if ((params['sixteenths']['volume'] > 0) and
                         (params['eighths']['volume'] > 0) and
                         not compound) else False
    if subdivide:
        # change the eight notes to the same sound as sixteenths
        for m in rhythm[-1]:
            if hasattr(m, 'note'):
             m.note = params['sixteenths']['note']

    sixteenths = []
    if compound:
        sw_adj = int(tpb / 4.0  * swing)
        sixteenths = [int(n * tpb  /2.0 + sw_adj*(n%2)) for n in range(ts[0] * 2) ]
    else:
        # if time signature is simple and we are swinging eighth's don't play 16ths
        if swing <= 0.001:
            sixteenths = [int(n * ppq / 4.0) for n in range(ts[0] * 4)]
    #print('sixteenths(%d) = ' % (params['sixteenths']['note']), sixteenths)
    rhythm.append(add_track('sixteenths', sixteenths))
    
    return mido.merge_tracks(rhythm)

if __name__ == "__main__":
    from plotMeasure import plot_midi, plot_midi_events
    for ts in settings['measure_options']:
        settings['time_signature'] = ts
        settings['measure']['note'] = 10
        settings['measure']['volume'] = 127
        settings['beat']['note'] = 11
        settings['beat']['volume'] = 63
        settings['eighths']['note'] = 12
        settings['eighths']['volume'] = 31
        settings['sixteenths']['note']= 13
        settings['sixteenths']['volume']= 0
        settings['swing'] = 0
        m = make_template_measure(settings, ppq=100)
        plot_midi(m)
        print(m)
    
    

