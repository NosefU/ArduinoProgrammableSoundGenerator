# This is fork of [ArduinoProgrammableSoundGenerator](https://github.com/Benjamin-Lapointe-Pinel/ArduinoProgrammableSoundGenerator)
An Arduino NES inspired multichannel sounds generator library.

<p align="center">
<a href="http://www.youtube.com/watch?feature=player_embedded&v=bedD4nGP4NM" target="_blank"><img src="http://img.youtube.com/vi/bedD4nGP4NM/0.jpg" alt="HEY, LISTEN!" width="480" height="360" border="10" /></a>
</p> 

# My modifications
* the use of progmem for storing melodies has been greatly optimized; 
* it's now possible to apply a smooth fading of notes to each track;
* bonus: dynamic led indication for each channel.

Besides, I wrote python script that converts specially prepared midi files to melody arrays. Unfortunately, at the moment the delays have to be selected manually.

# How to prepare midi file
5 simple rules:
  * one note at one time for each track. No overlaps
  * minimal note length - 1/32
  * two identical notes running in a row on the same channel will sound like one long note
  * midi file must be contain 5 tracks
  * track with drums must be named "Drums"

I recommend to use multiplatform midi editor Aria Maestosa.

# How to use converter script
```
python mididump_v3.py <midi file> -old_method
```
Copy array from console and insert it to melodies.h

# How to use it
Plug a speaker to pin 3, then init the sound generator in the setup function.
```
#include "APSG.h"

void setup()
{
  init_SID();
}
```
Play a 440Hz triangle wave for 1 second, then stop.
```
triangle.note = N_A4;
delay(1000);
triangle.note = N_NOP;
```
Play 2 tones at the same time.
```
squares[0].note = N_A4;
squares[1].note = N_A5;
```
Set volume for specific channel to maximum.
```
noise.volume = 15;
```
Sweep a channel down to low frequency.
```
sawtooth.sweep_direction = SWEEP_DOWN;
sawtooth.sweep_shift = 1;
sawtooth.sweep_speed = SWEEP_SPEED(8);
```
There are other examples in the ino file. For instance, a couple of multichannel melodies. Try them out!
