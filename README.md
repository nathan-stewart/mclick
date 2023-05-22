# MClick

## Intro
MClick (MIDI Click) is a web service controlled MIDI Metronome. 
The idea is that the service runs on a Linux box, when you connect to the web page it serves, 
it begins to publish MIDI note information to function as a metronome. Whenever parameters are
changed, it sends the data back to the web server and it updates the ticker app.

It also publishes MIDI clock data to synchronize effects pedals which can receive MIDI clock
(so your delay pedal is automatically in sync with the metronome). 

Closing the browser stops the metronome.

MIDI file playback while doing metronome functions
MClick now supports loading MIDI files, time signature and measure detection, handles anacrusis, and
can play them back while generating a metronome pattern, synced to the Tempo slider.

MClick now handles Simple and Compount meters, with compound meters downgrading the weak beats to 
the 8th note pattern (as these are all x/8 anyway).

Additionally it supports skip beat patterns in 3/4 and 4/4, playing 1 and 3 and 2 and 4 respectively 
on the beat sound.

Swing now disables 16th notes in the gui, except in compound meters, in which case it it swings 16ths in
6/8 and 12/8. Additionally, 16th notes will disable swing if enabled in simple meters. 

## TBD:
Transport Controls for Repeat, Forward/Rewind, Next/Previous song. I'm not planning to add a track list editor,
deferring that to the user. Point it to the folder you wish to practice instead.

## Issues:
MClick handles anacrusis, adding an a full measure for the count in. It currently has a bug where the final short
measure is missing. The intent is to repeat back to the intro measure which will thus be a full measure, and only
play the final short measure when not repeating. 

MIDI Clock is currently disabled due to the way MIDO handles MIDI clock and tracks. This needs to be a separate timer,
rather than a MIDO track.
