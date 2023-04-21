#McLick

McLick (MIDI Click) is a web service controlled MIDI Metronome. 
The idea is that the service runs on a Linux box, when you connect to the web page it serves, 
it begins to publish MIDI note information to function as a metronome. Whenever parameters are
changed, it sends the data back to the web server and it updates the ticker app.

It also publishes MIDI clock data to synchronize effects pedals which can receive MIDI clock
(so your delay pedal is automatically in sync with the metronome).

Closing the browser stops the metronome.

TBD:
Priority queue lowered cpu usage but needs a new solution for responsiveness
implement MIDI note change
Without becoming a full fledged drum machine, consider putting a checkbox for skipping %2 == 0 beats for all subdivisions

Requirements:

Bravura Font

