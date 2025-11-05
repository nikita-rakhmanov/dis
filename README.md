# AI Music Generation with Gesture Control

A real-time music generation and performance system that combines:
- 🎵 **RNN-based MIDI music generation** using TensorFlow
- 👋 **Hand gesture recognition** for real-time effects control
- 🎛️ **DAW integration** via MIDI for professional music production
- 🌐 **3D visualization** of music notes in real-time

## Features

### Music Generation
- Real-time MIDI note generation using trained RNN model
- Configurable temperature, velocity, and timing parameters
- Supports any MIDI-compatible DAW (Ableton Live, Logic Pro, FL Studio, etc.)
- Virtual MIDI port creation for easy routing

### Gesture Control
- Hand tracking using MediaPipe
- Real-time gesture recognition (Open Palm, Closed Fist, Peace Sign, Rock On, etc.)
- Gesture-to-MIDI CC mapping for effects control
- Smooth, low-latency control of audio effects

### Integrated System
- **Simultaneous operation**: Music generation + gesture control
- **Thread-safe MIDI**: Both systems share the same MIDI port
- **Dual-track routing**: Notes go to instrument, CC goes to effects
- **WebSocket visualization**: See generated notes in 3D

## Project Structure

```
dis/
├── integrated_music_gesture_control.py  # Main integrated system
├── realtime_midi_generator.py           # Standalone MIDI generator
├── train_music_rnn.py                   # Model training script
├── test_gesture_midi.py                 # Test gesture control (webcam)
├── test_gesture_midi_sim.py             # Test MIDI CC (no webcam)
├── gesture_control/
│   ├── hand_tracker.py                  # Hand tracking module
│   ├── README.md                        # Module documentation
│   ├── QUICKSTART.md                    # Quick start guide
│   └── __init__.py
├── GESTURE_CONTROL_GUIDE.md             # Detailed DAW setup guide
├── ABLETON_MAPPING_GUIDE.md             # Ableton-specific guide
├── QUICK_ABLETON_SETUP.md               # 5-minute Ableton setup
├── SETUP_LOCAL_MACHINE.md               # Local/webcam setup
├── VISUALIZATION_README.md              # 3D visualization docs
├── daw_cc_config.json                   # DAW configuration examples
├── requirements.txt                     # Python dependencies
└── README.md                            # This file
```

## Installation

### Prerequisites

- Python 3.8+
- Webcam (for gesture control)
- DAW with MIDI support (Ableton Live, Logic Pro, FL Studio, Reaper, etc.)

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `tensorflow` - RNN model
- `mido` + `python-rtmidi` - MIDI I/O
- `mediapipe` - Hand tracking
- `opencv-python` - Video capture
- `websockets` - Real-time visualization

## Quick Start

### 1. Train the Model (Optional)

If you want to train your own model:

```bash
python train_music_rnn.py
```

This will create `music_rnn_model.keras` and `seed_sequence.npy`.

### 2. Test Gesture Control

Before running the full system, test that gesture control works:

```bash
python test_gesture_midi.py
```

Move your hand in front of the webcam and observe:
- **X movement** (left-right) → Filter Cutoff (CC 74)
- **Y movement** (up-down) → Reverb Level (CC 91)
- **Pinch gesture** → Resonance (CC 71)
- **Open Palm** → Chorus Max
- **Closed Fist** → Effects Off

### 3. Run Integrated System

Launch both music generation and gesture control:

```bash
python integrated_music_gesture_control.py --model music_rnn_model.keras
```

You'll see:
1. MIDI port selection menu
2. Music generation starting
3. Gesture control window opening
4. Real-time note generation with gesture control active

### 4. Setup Your DAW

**For Ableton Live users:** See **[ABLETON_MAPPING_GUIDE.md](ABLETON_MAPPING_GUIDE.md)** for detailed step-by-step instructions!

**For other DAWs:** See **[GESTURE_CONTROL_GUIDE.md](GESTURE_CONTROL_GUIDE.md)**

Quick setup:
1. Create **two MIDI tracks** in your DAW
2. **Track 1**: Route to instrument (receives notes)
3. **Track 2**: Route CC to effects (receives control messages)
4. Add **Audio Effects Rack** with:
   - Low Pass Filter (map Frequency to CC 74, Resonance to CC 71)
   - Reverb/Delay (map Wet/Dry to CC 91)
   - Chorus (map Amount to CC 93)

## Usage Examples

### Full System (Music + Gestures)

```bash
# Default settings
python integrated_music_gesture_control.py

# Custom temperature and velocity
python integrated_music_gesture_control.py --temperature 1.5 --velocity 100

# Specific MIDI port
python integrated_music_gesture_control.py --port "IAC Driver Bus 1"

# Disable visualization (lower CPU usage)
python integrated_music_gesture_control.py --no-visualization
```

### Music Generation Only (No Gestures)

```bash
python integrated_music_gesture_control.py --no-gesture
# Or use the original script
python realtime_midi_generator.py
```

### Gesture Control Only (No Music Generation)

```bash
python test_gesture_midi.py
```

## MIDI CC Mappings

The gesture control system sends the following MIDI CC messages:

| Gesture/Movement | CC# | Parameter | Value Range |
|------------------|-----|-----------|-------------|
| Hand X Position | 74 | Filter Cutoff | 0-127 |
| Hand Y Position | 91 | Reverb/Delay | 0-127 |
| Thumb-Index Distance | 71 | Resonance | 0-127 |
| Open Palm | 93 | Chorus | 127 |
| Closed Fist | 93, 1 | Chorus, Mod | 0 |
| Peace Sign | 1 | Modulation | 64 |
| Rock On | 1 | Modulation | 127 |

## Command Line Options

### integrated_music_gesture_control.py

```
--model PATH              Path to trained model (default: music_rnn_model.keras)
--seed PATH               Path to seed sequence (default: seed_sequence.npy)
--port NAME               MIDI port name (interactive if not specified)
--temperature FLOAT       Sampling temperature (default: 2.0)
--velocity INT            MIDI velocity 0-127 (default: 80)
--num-notes INT           Number of notes to generate (infinite if not set)
--min-duration FLOAT      Minimum note duration in seconds (default: 0.1)
--max-duration FLOAT      Maximum note duration in seconds (default: 2.0)
--no-visualization        Disable WebSocket server
--no-gesture              Disable gesture control
--ws-port INT             WebSocket port (default: 8765)
```

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Integrated Music Gesture System                 │
│                                                         │
│  ┌──────────────┐              ┌──────────────┐       │
│  │ RNN Generator│              │ Hand Tracker │       │
│  │ (Main Thread)│              │   (Thread)   │       │
│  └──────┬───────┘              └──────┬───────┘       │
│         │                             │                │
│         │ MIDI Notes                  │ MIDI CC        │
│         │ (Note On/Off)               │ (74,71,91,93)  │
│         └──────────┬────────────────┬─┘                │
│                    │                │                  │
│                    ▼                ▼                  │
│              ┌──────────────────────┐                  │
│              │   Shared MIDI Port   │                  │
│              │  (Thread-Safe Lock)  │                  │
│              └──────────┬───────────┘                  │
└─────────────────────────┼───────────────────────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │   DAW    │
                    ├──────────┤
                    │ Track 1: │──► Instrument (Notes)
                    │ Notes    │
                    │          │
                    │ Track 2: │──► Effects Rack (CC)
                    │ CC       │    - Filter
                    │          │    - Reverb
                    │          │    - Chorus
                    └──────────┘
```

## Performance Tips

### Latency Optimization
- Use low-latency mode in your DAW
- Set audio buffer to 128-256 samples
- Reduce `update_rate` in code if needed (default: 20Hz)

### CPU Optimization
- Disable visualization with `--no-visualization`
- Reduce webcam resolution (default: 640x480)
- Lower gesture control update rate

### Hand Tracking Quality
- Ensure good lighting
- Use plain background
- Keep hand 1-2 feet from camera
- Avoid shadows and backlighting

## Troubleshooting

### "Could not open webcam"
- Check webcam permissions
- Verify device exists: `ls /dev/video*`
- Try different camera index in code

### "Hand not detected"
- Improve lighting
- Move hand closer to camera
- Check MediaPipe confidence settings

### "MIDI port not found"
- List ports: `python -c "import mido; print(mido.get_output_names())"`
- Create IAC Driver (macOS) or loopMIDI (Windows)
- Use virtual port option

### "Effects not responding to gestures"
- Verify MIDI CC messages with MIDI monitor
- Check DAW MIDI routing
- Ensure effects track is receiving CC from correct source
- Try MIDI Learn mode in DAW

### "Music playing but no gesture control"
- Check webcam is not in use by other app
- Verify gesture window opened
- Check console for error messages

## Advanced Customization

### Change CC Mappings

Edit `integrated_music_gesture_control.py`:

```python
class GestureMIDIController:
    CC_FILTER_CUTOFF = 74  # Change to your desired CC number
    CC_RESONANCE = 71
    CC_REVERB = 91
    CC_CHORUS = 93
    CC_MODULATION = 1
```

### Adjust Smoothing

Increase buffer size for smoother control:

```python
self.position_buffer_x = deque(maxlen=10)  # Default: 5
self.position_buffer_y = deque(maxlen=10)
```

### Add Custom Gestures

Edit `gesture_control/hand_tracker.py` to add new gesture recognition logic.

## Files Generated

- `music_rnn_model.keras` - Trained RNN model
- `seed_sequence.npy` - Initial sequence for generation
- `training_history.png` - Training metrics visualization
- `generated_music.mid` - Sample MIDI output (from training)

## Credits and Technologies

- **TensorFlow** - Neural network framework
- **MediaPipe** - Hand tracking (Google)
- **mido** - MIDI library for Python
- **OpenCV** - Video capture and processing
- **WebSockets** - Real-time visualization
- **Three.js** - 3D graphics (visualization.html)

## License

MIT License - Feel free to use and modify for your projects.

## Contributing

Contributions welcome! Areas for improvement:
- Additional gesture recognition patterns
- Multi-hand control (stereo effects)
- MIDI velocity control from hand speed
- Gesture-based note triggering
- Machine learning for custom gesture training

## Support

For issues, questions, or suggestions:
1. Check [GESTURE_CONTROL_GUIDE.md](GESTURE_CONTROL_GUIDE.md) or [ABLETON_MAPPING_GUIDE.md](ABLETON_MAPPING_GUIDE.md)
2. Review troubleshooting section above
3. Check [SETUP_LOCAL_MACHINE.md](SETUP_LOCAL_MACHINE.md) for webcam setup

## Roadmap

- [ ] Multi-hand stereo control (left hand = reverb, right hand = filter)
- [ ] Hand velocity → note velocity mapping
- [ ] Custom gesture training interface
- [ ] Preset system for different effect configurations
- [ ] OSC support for additional DAWs
- [ ] Mobile app for remote control
- [ ] AI-powered gesture suggestion based on music style

---

**Enjoy creating music with your hands!** 🎵👋
