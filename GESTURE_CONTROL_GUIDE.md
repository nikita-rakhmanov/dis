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

### Disable Gesture Control (Music Only)

```bash
python integrated_music_gesture_control.py --no-gesture
```

### Disable Visualization (Gesture + Music Only)

```bash
python integrated_music_gesture_control.py --no-visualization
```

## Hand Gestures Reference

Position your hand in front of the webcam:

- **Open Palm** (all fingers extended)
  - Activates maximum chorus effect
  - Good for ambient, spacey sounds

- **Closed Fist** (no fingers extended)
  - Minimizes all effects
  - Returns to dry signal

- **Peace Sign** (index + middle finger)
  - Medium modulation
  - Subtle movement effect

- **Rock On** (index + pinky)
  - Maximum modulation
  - Intense effect modulation

- **Pointing** (index finger only)
  - Use for precise X/Y control
  - Best for filter sweeps

- **Pinch** (thumb + index close together)
  - Controls resonance
  - Pinch tight = low resonance
  - Spread wide = high resonance

## Tips for Best Results

1. **Lighting**: Ensure good lighting for hand tracking
2. **Background**: Use a plain background for better detection
3. **Distance**: Position hand 1-2 feet from camera
4. **Smoothing**: The system includes smoothing to reduce jitter
5. **Calibration**: Move hand slowly at first to understand mapping range

## Troubleshooting

### Hand Not Detected
- Check webcam is working (`ls /dev/video*`)
- Ensure good lighting
- Move hand closer to camera
- Try adjusting `detection_confidence` in code

### MIDI CC Not Working in DAW
- Verify MIDI port connection in DAW
- Enable MIDI input on effects track
- Check MIDI monitor to see if CC messages are being received
- Try MIDI Learn mode instead of manual mapping

### Jittery Effect Control
- Increase smoothing buffer size in `GestureMIDIController.__init__`
- Reduce `update_rate` (default 20Hz)
- Keep hand movements smooth and slow

### Notes Playing But No Effects
- Ensure CC messages are routed to effects track
- Check that effects are on the audio track (not MIDI track)
- Verify MIDI CC mappings in effect parameters

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Integrated System                           │
│                                                              │
│  ┌────────────────────┐         ┌─────────────────────┐    │
│  │  RNN Generator     │         │   Hand Tracker      │    │
│  │  (Main Thread)     │         │   (Background Thread) │    │
│  └─────────┬──────────┘         └──────────┬──────────┘    │
│            │                               │                │
│            │ MIDI Notes                    │ MIDI CC        │
│            │ (Note On/Off)                 │ (CC 1,71,74,   │
│            │                               │  91,93)        │
│            └───────────┬───────────────────┘                │
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  MIDI Port  │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │     DAW     │
                  │             │
                  │  Track 1:   │──► Instrument Rack
                  │  (Notes)    │
                  │             │
                  │  Track 2:   │──► Audio Effects Rack
                  │  (CC)       │    (Filter, Reverb, etc.)
                  └─────────────┘
```

## Advanced Customization

### Change CC Mappings

Edit `integrated_music_gesture_control.py`:

```python
class GestureMIDIController:
    # MIDI CC mapping - Change these numbers
    CC_FILTER_CUTOFF = 74  # Change to your DAW's filter CC
    CC_RESONANCE = 71      # Change to your resonance CC
    CC_REVERB = 91         # Change to your reverb CC
    CC_CHORUS = 93         # Change to your chorus CC
    CC_MODULATION = 1      # Standard modulation wheel
```

### Adjust Smoothing

Increase buffer size for smoother control (more lag):

```python
self.position_buffer_x = deque(maxlen=10)  # Default: 5
self.position_buffer_y = deque(maxlen=10)  # Default: 5
```

### Change Update Rate

Reduce CC message frequency (less CPU):

```python
update_rate=10  # Default: 20Hz, try 10Hz or 15Hz
```

## Performance Optimization

- **CPU Usage**: If high, reduce `update_rate` to 10-15Hz
- **Latency**: For lower latency, increase `update_rate` to 30Hz
- **Webcam FPS**: Set camera to 30fps for best balance
- **MIDI Buffer**: Adjust DAW MIDI buffer size if experiencing jitter

## Example Workflow

1. **Start DAW** and create two MIDI tracks
2. **Setup MIDI routing** as described above
3. **Load instrument** on Track 1
4. **Add effects rack** on audio track
5. **Map CC numbers** to effect parameters
6. **Run script**: `python integrated_music_gesture_control.py`
7. **Select MIDI port** when prompted
8. **Start moving hands** to control effects
9. **Record output** or perform live

## Credits

- Hand tracking: MediaPipe (Google)
- Music generation: TensorFlow RNN model
- MIDI: mido library
- Visualization: WebSocket + Three.js (optional)
