# Gesture Control for Music Effects - Setup Guide

## Overview

The integrated system combines:
1. **Real-time MIDI generation** (RNN model) → Plays musical notes
2. **Hand tracking** (MediaPipe) → Controls audio effects via MIDI CC

Both systems run simultaneously, sending data to your DAW.

## MIDI CC Mappings

The hand tracking data is mapped to MIDI Control Change (CC) messages:

| Hand Movement | MIDI CC | CC Number | Effect Control |
|--------------|---------|-----------|----------------|
| **Hand X Position** (left-right) | Filter Cutoff/Brightness | CC 74 | Left = Dark/Closed, Right = Bright/Open |
| **Hand Y Position** (up-down) | Reverb/Delay Level | CC 91 | Up = More Effect, Down = Less Effect |
| **Thumb-Index Distance** (pinch) | Filter Resonance | CC 71 | Close = Low, Far = High Resonance |
| **Open Palm** gesture | Chorus Level | CC 93 | Sets to Maximum (127) |
| **Closed Fist** gesture | Mute/Bypass | CC 93, CC 1 | Sets to Minimum (0) |
| **Peace Sign** gesture | Modulation | CC 1 | Medium Modulation (64) |
| **Rock On** gesture | Modulation | CC 1 | Maximum Modulation (127) |

## DAW Setup Instructions

### 1. Create MIDI Tracks in Your DAW

You need **two MIDI tracks**:

#### Track 1: Music Generation (Notes)
- Receives MIDI notes from the RNN generator
- Connect to your MIDI instrument rack
- Route to your instrument (synth, piano, etc.)

#### Track 2: Gesture Control (CC Messages)
- Receives MIDI CC messages from hand tracking
- Route this to your **Audio Effects Rack**
- Does NOT need an instrument

### 2. Setup Audio Effects Rack

Create an audio effects rack with the following effects and MIDI mappings:

#### Ableton Live Example:

1. **Create an Audio Effects Rack**:
   - Add to an audio track (processing your instrument output)
   - Click "Show/Hide MIDI Mappings"

2. **Add and Map Effects**:
   ```
   - Low Pass Filter
     → Frequency: Map to CC 74 (Filter Cutoff)
     → Resonance: Map to CC 71 (Filter Resonance)

   - Reverb/Delay
     → Dry/Wet Mix: Map to CC 91 (Reverb Level)

   - Chorus
     → Amount: Map to CC 93 (Chorus Level)

   - LFO/Modulation Effect
     → Rate/Depth: Map to CC 1 (Modulation)
   ```

3. **MIDI Routing**:
   - Set Track 2 input to receive from "RNN Music Generator" port
   - Enable "MIDI" button on Track 2
   - Route Track 2 output → "Track 1" (for CC messages only)

#### Other DAWs:

- **Logic Pro**: Use Smart Controls and MIDI Learn
- **FL Studio**: Right-click effect parameters → Link to Controller
- **Reaper**: Parameter Modulation → Link to MIDI CC
- **Studio One**: External Devices → Map CC to parameters

### 3. Alternative: Use MIDI Learn

Most DAWs support MIDI Learn mode:

1. Run the integrated script
2. In your DAW, enter MIDI Learn mode
3. Move your hand and click the parameter to map
4. The DAW will automatically detect the CC number

## Usage

### Basic Command

```bash
python integrated_music_gesture_control.py --model music_rnn_model.keras
```

### With Options

```bash
python integrated_music_gesture_control.py \
    --model music_rnn_model.keras \
    --port "Your MIDI Port" \
    --temperature 2.0 \
    --velocity 80
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--model` | Path to trained RNN model | `music_rnn_model.keras` |
| `--seed` | Path to seed sequence | `seed_sequence.npy` |
| `--port` | MIDI port name | Interactive selection |
| `--temperature` | Sampling temperature (higher = more random) | 2.0 |
| `--velocity` | MIDI note velocity (0-127) | 80 |
| `--num-notes` | Number of notes to generate | Infinite |
| `--min-duration` | Minimum note duration (seconds) | 0.1 |
| `--max-duration` | Maximum note duration (seconds) | 2.0 |
| `--no-visualization` | Disable WebSocket visualization | Enabled |
| `--no-gesture` | Disable gesture control | Enabled |
| `--ws-port` | WebSocket port for visualization | 8765 |

