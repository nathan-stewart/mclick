#!/usr/bin/env python3
from dataclasses import dataclass, field
import mido

settings = {
    "midi_backend"    : "mido.backends.rtmidi/LINUX_ALSA",
    "midi_port"       : "UMC1820:UMC1820 MIDI 1",
    "midi_ports"      : mido.get_output_names(),
    "tempo"           : 60,
    "num_beats"       : 4,
    "measure"         : { "note": 77, "volume": 127 },
    "measure_options" : [2,3,4,6,9,12],
    "beat"            : { "note": 76, "volume": 63 },
    "eighths"         : { "note":51, "volume": 0},
    "swing"           : 0.0,
    "sixteenths"      : { "note":42, "volume":0},
    "clock"           : False
}

