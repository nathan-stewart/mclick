#!/usr/bin/python3
import mido
from sortedcontainers import SortedList
from settings import Settings
from events import EventQue 

def track_length(track):
    if not isinstance(track, mido.MidiTrack):
        raise TypeError
    t = 0
    for m in track:
        if hasattr(m, 'time'):
            t += m.time
    return t

def handle_anacrusis(measures):
    if not isinstance(measures, list):
        raise TypeError

    if not measures:
        return []

    if len(measures) < 2:
        return measures.copy()

    # look for ordinary anacrusis - first and last measure form whole measure
    # This meter must be the same as the 2nd measure
    first = measures[0]
    second = measures[1]
    last = measures[-1]

    modified = []
    if (first[1] == second[1] == last[1] and
        first[0] != second[0] and
        first[0] + last[0]) == second[0]:
        modified.append(measures[1]) # Add an extra count in measure in place of the short one
    else:
        modified.append(first)
    # Now if anacrusis is present, the final measure will be short but the initial
    # measure will be whole. Play repeats using the first measure, finish using the last

    # look for internal anacrusis - typically a verse/chorus split mid measure
    # internal anacrusis by definition can't be at the endpoints, and requires
    # at least one one full measure on either side - so it has a minimum of
    # six measures - first, full, short_a, short_b, full, last}
    if len(measures) < 6:
        modified += measures[1:]
        return modified

    for i,m in enumerate(measures[1:-2], start=1):
        previous  = measures[i-1]
        following = measures[i+1]

        if m[1] != following[1]: # don't merge if denominator changes
            modified.append(m)
            continue
        if m[0] + following[0] == previous[0]:
            # first submeasure
            modified.append(previous)
        elif m[0] + previous[0] == following[0]:
            # second submeasure - skip it
            continue
        else:
            modified.append(m)

    modified.append(measures[-1])
    return modified



def make_template_measures(params, measures, ppq=480):
    parts = [mido.MidiTrack() for t in range(4)]
    part_idx = { 'measure' : 0, 'beat': 1, 'eighths':2, 'sixteenths':3 }
    
    # extends the scope for final measure
    ts = None
    ticks_per_beat = None
    measure_length = None

    def add_track(partname, events):

        last_t = 0
        t = 0
        track = parts[ part_idx [partname ] ] 
        for t in events:
            v = params[partname]['volume']
            n = params[partname]['note']
            if v > 0:
                msg = mido.Message('note_on',
                                    channel=9,
                                    note=n,
                                    velocity=v,
                                    time=t-last_t)
                track.append(msg)
            last_t = t
        track.append(mido.Message('note_on', channel=9, note=0, velocity=0, time=measure_length - t))

    for ts in measures:
        ticks_per_beat = int(ppq * 4 / ts[1])
        measure_length = ts[0] * ticks_per_beat
        add_track('measure', [0])

        skip = False
        if 'skip' in params['beat'].keys():
            skip = params['beat']['skip']
        swing = min(1.0, max(0.0, params['swing'] / 100.0))
        compound = True if ts[0] in [6,9,12] else False

        # don't play the one - it's played by the measure
        beats = [int(b * ticks_per_beat)  for b in range(1,ts[0]) ]
        if skip and ts[0] == 3: # in 3/4 time, skip beat plays the 3
            beats = [2 * ticks_per_beat]
        elif skip and ts[0] == 4: # in 4/4 time skip beat plays 2 and 4
            beats = [b * ticks_per_beat for b in [1,3]]
        elif compound:
            # signatures considered compound
            # we play beats on 1, 4, 7, 10 and 8ths elsewhere
            beats = [int(b * ticks_per_beat) for b in range(1,ts[0]) if not b%3]
        add_track('beat', beats)

        if compound:
            # compounds play eights as weak beats - they're not half beats
            # we skipped these beats above
            eighths = [ int(n * ticks_per_beat) for n in range(ts[0]) if n % 3 ]
        else:
            eights = [ int(n * ticks_per_beat  /2.0) for n in range(ts[0]* 2)]
            # capping swing at dotted eighth as a hard swing
            sw_adj = int(ticks_per_beat * swing / 4.0)
            eighths = [ int(n * ticks_per_beat /2.0 +(n % 2) * sw_adj) for n in range(ts[0] * 2) ]
        add_track('eighths', eighths)

        subdivide = True if ((params['sixteenths']['volume'] > 0) and
                             (params['eighths']['volume'] > 0) and
                             not compound) else False
        if subdivide:
            # change the eight notes to the same sound as sixteenths
            for m in parts[-1]:
                if hasattr(m, 'note') and m.note == params['eighths']['note']:
                    m['note'] = params['sixteenths']['note']

        sixteenths = []
        if compound:
            sw_adj = int(ticks_per_beat / 4.0  * swing)
            sixteenths = [int(n * ticks_per_beat  /2.0 + sw_adj*(n%2)) for n in range(ts[0] * 2) ]
        else:
            # if time signature is simple and we are swinging eighth's don't play 16ths
            if swing <= 0.001:
                sixteenths = [int(n * ppq / 4.0) for n in range(ts[0] * 4)]
        add_track('sixteenths', sixteenths)
    return mido.merge_tracks(parts)


def make_rhythm_track(song, params):
    if not isinstance(song, mido.MidiFile):
        raise TypeError

    measures = []
    if len(song.tracks) == 0:
        ts = params['time_signature']
        measures = [ ts ]
        song.tracks.append(mido.MidiTrack())
        song.tracks[0].append(
                mido.MetaMessage('time_signature', numerator=ts[0], denominator=ts[1], time=0))
    
    if not measures:
        events = EventQue(song)
        measures = handle_anacrusis(events.measures)
    rhythm = make_template_measures(params, measures)
    return rhythm


if __name__ == "__main__":
    from plotMeasure import plot_midi, plot_midi_events
    params = Settings()
    for ts in params['measure_options']:
        params['time_signature'] = ts
        params['measure']['note'] = 10
        params['measure']['volume'] = 127
        params['beat']['note'] = 11
        params['beat']['volume'] = 63
        params['eighths']['note'] = 12
        params['eighths']['volume'] = 31
        params['sixteenths']['note']= 13
        params['sixteenths']['volume']= 0
        params['swing'] = 0

        m = mido.MidiFile()

        m.tracks.append(make_rhythm_track(m, params))
        plot_midi(m, title=ts)

    m = mido.MidiFile('demo/cwm_rhondda.mid')
    m.tracks.append( make_rhythm_track(m, params))
    plot_midi(m, title=m.filename)
    
    

