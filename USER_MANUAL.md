# User Manual

## Prerequisites

- Python 3.8+
- Webcam
- DAW with MIDI support (e.g., Ableton Live)
- Virtual MIDI driver: IAC Driver (macOS) or loopMIDI (Windows)

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python integrated_music_gesture_control.py
```

Select a MIDI port when prompted. The system will:
1. Load the RNN model
2. Open the gesture control webcam window
3. Begin generating MIDI notes
4. Send gesture-controlled CC messages

## DAW Setup

1. Set MIDI input to the virtual port (e.g., "IAC Driver Bus 1")
2. Create a MIDI track with an instrument
3. Add audio effects (Filter, Reverb, Chorus)
4. Use MIDI Learn to map effects to CC numbers

## Gesture Controls

| Input | CC | Effect |
|-------|-----|--------|
| Left hand X | 74 | Filter cutoff |
| Left hand Y | 91 | Reverb |
| Pinch distance | 71 | Resonance |
| Open palm | 93 | Chorus on |
| Closed fist | 93 | Chorus off |
| Right hand Y | 14 | Arpeggiator rate |

## Command Line Options

| Option | Description |
|--------|-------------|
| `--model PATH` | Model file (default: music_rnn_model.keras) |
| `--temperature FLOAT` | Randomness 0.1-3.0 (default: 2.0) |
| `--velocity INT` | Note velocity 0-127 (default: 80) |
| `--no-gesture` | Disable gesture control |
| `--polyphony` | Enable two-voice generation |


