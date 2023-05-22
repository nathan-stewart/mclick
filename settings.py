#!/usr/bin/env python3
from dataclasses import dataclass, field
import mido
import json

class Settings:
    def __init__(self):
        self.data = {
            "midi_backend"    : "mido.backends.rtmidi/LINUX_ALSA",
            "midi_port"       : "UMC1820:UMC1820 MIDI 1",
            "midi_ports"      : mido.get_output_names(),
            "tempo"           : 60,
            "time_signature"  : "4/4",
            "measure_options" : [ "2/2", "3/4", "4/4", "6/8", "9/8", "12/8" ],
            "measure"         : { "note": 77, "volume": 127 },
            "beat"            : { "note": 76, "volume": 63, 'skip':False },
            "eighths"         : { "note":51, "volume": 120},
            "swing"           : 0.0,
            "sixteenths"      : { "note":42, "volume":0}
        }

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, index, value):
        self.data[index] = value

    def midi_changed(self, params):
        return not ((self.data['midi_port'] == params.data['midi_port']) and
                    (self.data['midi_backend'] == params.data['midi_backend']))

    def time_signature_changed(self, params):
        return self.data['time_signature'] != params.data['time_signature']

    def tempo_changed(self, params):
        return self.data['tempo'] != params.data['tempo']

    def swing_changed(self, params):
        return self.data['swing'] != params.data['swing']

    def beat_invariant(self, params):
        return not (self.time_signature_changed(params) or
                    self.swing_changed(params))

    def to_json(self):
        return json.dumps(self.data, sort_keys=True)

if __name__ == '__main__':
    settings = Settings()
    print(settings.to_json())
