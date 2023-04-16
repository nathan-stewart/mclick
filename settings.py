#!/usr/bin/env python3
from dataclasses import dataclass, field
import mido
import json

def create_default_ports() -> list[str]:
    return list(set(mido.get_output_names()))

def create_default_measures() -> list[int]:
    return [2,3,4,6,9,12]

@dataclass 
class Note:
    note  : int = 0
    volume: int = 0
    
    def __init__(self, nn, vol):
        self.note = nn
        self.volume = vol

    def __hash__(self):
        return hash(repr(self))

    def toJSON(self):
        dumpable = {}
        for k in self.__dict__.keys():
            dumpable[k] = json.dumps(self.__dict__[k])
        return dumpable 


@dataclass
class Settings:
    midi_port       : str = 'UMC1820:UMC1820 MIDI 1'
    midi_ports      : list[str] = field(default_factory=create_default_ports)
    tempo           : int = 60
    num_beats       : int =  4
    measure         : Note = Note(77, 127)
    measure_options : list[int] = field(default_factory=create_default_measures)
    beat            : Note = Note(76, 63)
    eighths         : Note = Note(51, 31)
    swing           : float = 10.0
    sixteenths      : Note = Note(42, 15)
    clock           : bool = False

    def toJSON(self):
        dumpable = {}
        for k in self.__dict__.keys():
            value = self.__dict__[k]
            if isinstance(value, Note):
                dumpable[k] = value.toJSON()
            else:
                dumpable[k] = value
        return dumpable 
