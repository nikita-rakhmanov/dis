# AI Music Generation with Gesture Control

A real-time music generation and performance system combining RNN-based MIDI generation with hand gesture recognition for expressive control of audio effects.

**Repository:** https://github.com/nikita-rakhmanov/dis

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Installation](#2-installation)
3. [Project Structure](#3-project-structure)
4. [Quick Start Guide](#4-quick-start-guide)
5. [Training Your Own Model](#5-training-your-own-model)
6. [Running the Application](#6-running-the-application)
7. [DAW Configuration](#7-daw-configuration)
8. [Gesture Controls Reference](#8-gesture-controls-reference)
9. [Command Line Options](#9-command-line-options)
10. [Troubleshooting](#10-troubleshooting)
11. [Advanced Configuration](#11-advanced-configuration)

---

## 1. System Requirements

### Hardware
- **CPU:** Modern multi-core processor (Intel i5/AMD Ryzen 5 or better recommended)
- **RAM:** 8GB minimum, 16GB recommended
- **Webcam:** Any USB webcam or built-in camera (required for gesture control)
- **Audio Interface:** Optional but recommended for low-latency audio

### Software
- **Operating System:** macOS 10.15+, Windows 10+, or Linux (Ubuntu 20.04+)
- **Python:** Version 3.8 or higher
- **DAW:** Any MIDI-compatible DAW:
  - Ableton Live (recommended)
  - Logic Pro
  - FL Studio
  - Reaper
  - Any other DAW with MIDI input support

### MIDI Setup
- **macOS:** IAC Driver (built-in, needs to be enabled in Audio MIDI Setup)
- **Windows:** loopMIDI (free virtual MIDI driver) or similar
- **Linux:** ALSA MIDI or JACK

---

## 2. Installation

### Step 1: Clone or Extract the Project

If you have the zip file:
```bash
unzip submission.zip -d ai-music-gesture
cd ai-music-gesture
```

Or clone from GitHub:
```bash
git clone https://github.com/nikita-rakhmanov/dis.git
cd dis
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the following key packages:
| Package | Version | Purpose |
|---------|---------|---------|
| tensorflow | ≥2.13.0 | Neural network framework for RNN model |
| numpy | ≥1.24.0 | Numerical computing |
| mido | ≥1.3.0 | MIDI message handling |
| python-rtmidi | ≥1.5.0 | Real-time MIDI I/O |
| mediapipe | ≥0.10.0 | Hand tracking (Google) |
| opencv-python | ≥4.8.0 | Video capture and processing |
| websockets | ≥11.0.0 | Real-time visualization server |
| pretty_midi | ≥0.2.10 | MIDI file parsing (for training) |

### Step 4: Verify Installation

```bash
python -c "import tensorflow as tf; import mido; import mediapipe; print('All dependencies installed successfully!')"
```

---

## 3. Project Structure

```
dis/
├── integrated_music_gesture_control.py  # Main application (run this)
├── train_music_rnn.py                   # Model training script
├── train_improved_rnn.py                # Improved model training
├── dual_model_polyphony.py              # Two-voice polyphony system
│
├── gesture_control/                     # Gesture recognition module
│   ├── __init__.py
│   └── hand_tracker.py                  # MediaPipe hand tracking
│
├── music_rnn_model.keras                # Pre-trained melody model
├── improved_melody_model.keras          # Improved melody model
├── harmony_model.keras                  # Harmony generation model
├── seed_sequence.npy                    # Initial sequence for generation
│
├── visualization.html                   # 3D WebGL visualization
├── visualization.js                     # Visualization logic
├── visualization.css                    # Visualization styles
│
├── docs/                                # Additional documentation
│   ├── ABLETON_MAPPING_GUIDE.md        # Detailed Ableton setup
│   ├── GESTURE_CONTROL_GUIDE.md        # DAW configuration guide
│   └── GETTING_STARTED.md              # Quick start guide
│
├── requirements.txt                     # Python dependencies
└── README.md                            # This user manual
```

---

## 4. Quick Start Guide

### Step 1: Set Up Virtual MIDI (First Time Only)

**macOS:**
1. Open **Audio MIDI Setup** (Applications → Utilities)
2. Go to **Window → Show MIDI Studio**
3. Double-click **IAC Driver**
4. Check **Device is online**
5. Add a port named "IAC Driver Bus 1"

**Windows:**
1. Download and install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
2. Create a new virtual MIDI port

### Step 2: Run the Application

```bash
python integrated_music_gesture_control.py
```

### Step 3: Select MIDI Port

The application will display available MIDI ports:
```
Available MIDI ports:
  [0] IAC Driver Bus 1
  [1] USB MIDI Device

Select port number (or press Enter to create virtual):
```

Enter the number of your virtual MIDI port (e.g., `0`).

### Step 4: Configure Your DAW

1. Open your DAW
2. Create a MIDI track
3. Set MIDI input to the virtual port (e.g., "IAC Driver Bus 1" or "RNN Music Generator")
4. Add an instrument (synth, piano, etc.)
5. Arm the track for recording

### Step 5: Start Performing!

- The RNN will generate MIDI notes automatically
- Move your hands in front of the webcam to control effects
- Press `Ctrl+C` to stop

---

## 5. Training Your Own Model

Pre-trained models are included, but you can train your own:

### Step 1: Download Training Data

The training script automatically downloads the MAESTRO dataset (classical piano MIDI):

```bash
python train_music_rnn.py
```

### Step 2: Training Process

Training parameters (in `train_music_rnn.py`):
- **EPOCHS:** 50 (default)
- **BATCH_SIZE:** 256
- **SEQUENCE_LENGTH:** 50 notes
- **NUM_TRAINING_FILES:** 1000 MIDI files

Training outputs:
- `music_rnn_model.keras` - The trained model
- `seed_sequence.npy` - Initial sequence for generation
- `training_checkpoints/` - Checkpoint weights

### Step 3: Monitor Training

Training progress is displayed in the terminal. Checkpoints are saved after each epoch.

---

## 6. Running the Application

### Basic Usage

```bash
# Run with default settings
python integrated_music_gesture_control.py

# Run with specific model
python integrated_music_gesture_control.py --model improved_melody_model.keras

# Run without gesture control (music only)
python integrated_music_gesture_control.py --no-gesture

# Run with custom settings
python integrated_music_gesture_control.py --temperature 1.5 --velocity 100
```

### With Polyphony (Two Voices)

```bash
python integrated_music_gesture_control.py --polyphony --harmony-style classical
```

Harmony styles: `classical`, `jazz`, `modern`

### With 3D Visualization

1. Run the application (WebSocket server starts automatically)
2. Open `visualization.html` in a web browser
3. Notes appear as 3D objects in real-time

---

## 7. DAW Configuration

### Ableton Live Setup

#### Track Structure
Create two tracks:

| Track | Type | Purpose |
|-------|------|---------|
| Track 1 | MIDI | Receives notes → Instrument |
| Track 2 | Audio | Audio effects processing |

#### MIDI Configuration
1. **Preferences → Link/Tempo/MIDI**
2. Enable **Track** and **Remote** for your MIDI port
3. Set Track 1 MIDI Input to your virtual port
4. Set Monitor to "In"

#### Effects Mapping (MIDI Learn)
1. Add effects to Track 2: Auto Filter, Reverb, Chorus
2. Press `Cmd+M` (Mac) or `Ctrl+M` (Win) for MIDI Map mode
3. Click on effect parameter (e.g., Filter Frequency)
4. Move your hand to send CC message
5. Ableton automatically maps the CC
6. Exit MIDI Map mode

See [docs/ABLETON_MAPPING_GUIDE.md](docs/ABLETON_MAPPING_GUIDE.md) for detailed instructions.

### Other DAWs

| DAW | MIDI Learn Method |
|-----|-------------------|
| Logic Pro | Smart Controls → Learn |
| FL Studio | Right-click parameter → Link to Controller |
| Reaper | Actions → Show Action List → Learn |
| Studio One | Right-click → Assign MIDI Control |

---

## 8. Gesture Controls Reference

### Left Hand: Audio Effects Control

| Movement/Gesture | MIDI CC | Effect | Behavior |
|------------------|---------|--------|----------|
| X position (left-right) | CC 74 | Filter Cutoff | Center = bright, edges = dark |
| Y position (up-down) | CC 91 | Reverb/Delay | Up = more reverb |
| Thumb-index pinch | CC 71 | Resonance | Pinch = high resonance |
| Open Palm | CC 93 | Chorus | Maximum (127) |
| Closed Fist | CC 93, CC 1 | Bypass | Minimum (0) |
| Peace Sign ✌️ | CC 1 | Modulation | Medium (64) |

### Right Hand: Tempo/Arpeggiator Control

| Movement | MIDI CC | Effect | Behavior |
|----------|---------|--------|----------|
| Y position (up) | CC 14 | Arpeggiator Rate | Fast (127) |
| Y position (middle) | CC 14 | Arpeggiator Rate | Normal (64) |
| Y position (down) | CC 14 | Arpeggiator Rate | Slow (0) |

### Gestures Visual Guide

```
Open Palm (5 fingers)     Closed Fist (0 fingers)    Peace Sign (2 fingers)
    🖐️                         ✊                         ✌️
 Chorus ON               Effects OFF               Modulation Mid

Rock On (2 fingers)      Pointing (1 finger)        Pinch (thumb+index)
    🤘                         👆                         🤏
Modulation Max            (reserved)                Resonance
```

---

## 9. Command Line Options

```
python integrated_music_gesture_control.py [OPTIONS]

Model Options:
  --model PATH              Path to trained model (default: music_rnn_model.keras)
  --seed PATH               Path to seed sequence (default: seed_sequence.npy)

MIDI Options:
  --port NAME               MIDI port name (interactive if not specified)

Generation Options:
  --temperature FLOAT       Sampling randomness 0.1-3.0 (default: 2.0)
  --velocity INT            Note velocity 0-127 (default: 80)
  --num-notes INT           Notes to generate (default: infinite)
  --min-duration FLOAT      Min note length in seconds (default: 0.1)
  --max-duration FLOAT      Max note length in seconds (default: 2.0)

Feature Toggles:
  --no-gesture              Disable gesture control
  --no-visualization        Disable WebSocket server

Polyphony Options:
  --polyphony               Enable two-voice generation
  --harmony-style STYLE     classical, jazz, or modern (default: classical)
  --harmony-mode MODE       simple or learned (default: simple)

Visualization:
  --ws-port INT             WebSocket port (default: 8765)
```

### Examples

```bash
# Slow, expressive generation
python integrated_music_gesture_control.py --temperature 0.8 --velocity 60

# Fast, energetic generation
python integrated_music_gesture_control.py --temperature 2.5 --velocity 110

# Jazz-style polyphony
python integrated_music_gesture_control.py --polyphony --harmony-style jazz

# Headless mode (no webcam needed)
python integrated_music_gesture_control.py --no-gesture --no-visualization
```

---

## 10. Troubleshooting

### "Could not open webcam"

**Causes:**
- No webcam connected
- Webcam in use by another application
- Permission denied

**Solutions:**
```bash
# Check available cameras (Linux)
ls /dev/video*

# Run without gesture control
python integrated_music_gesture_control.py --no-gesture
```

On macOS, check **System Preferences → Security & Privacy → Camera** permissions.

### "Hand not detected"

**Solutions:**
- Ensure good lighting (avoid backlighting)
- Use a plain background
- Keep hand 30-60cm from camera
- Avoid shadows on hands

### "MIDI port not found"

**Check available ports:**
```bash
python -c "import mido; print(mido.get_output_names())"
```

**Solutions:**
- Enable IAC Driver (macOS) or install loopMIDI (Windows)
- The application can create a virtual port if none exist

### "Effects not responding to gestures"

**Checklist:**
1. ✅ MIDI CC messages being sent (check with MIDI monitor app)
2. ✅ DAW receiving from correct MIDI port
3. ✅ Effects mapped to correct CC numbers
4. ✅ Track is armed and monitoring is "In"

### "Model fails to load"

**Solution:** Ensure TensorFlow version matches:
```bash
pip install tensorflow>=2.13.0
```

---

## 11. Advanced Configuration

### Changing CC Mappings

Edit `integrated_music_gesture_control.py`:

```python
class GestureMIDIController:
    CC_FILTER_CUTOFF = 74      # Change these values
    CC_RESONANCE = 71          # to match your DAW
    CC_REVERB = 91
    CC_CHORUS = 93
    CC_MODULATION = 1
    CC_ARPEGGIATOR_RATE = 14
```

### Adjusting Smoothing

For smoother control (less responsive):
```python
self.position_buffer_x = deque(maxlen=10)  # Increase from 5
self.position_buffer_y = deque(maxlen=10)
```

For faster response (more jittery):
```python
self.position_buffer_x = deque(maxlen=3)   # Decrease from 5
```

### Custom Gestures

Add new gesture recognition in `gesture_control/hand_tracker.py`:

```python
def recognize_gesture(self, landmarks, handedness) -> str:
    fingers = self.get_finger_state(landmarks, handedness)
    
    # Add your custom gesture
    if fingers['thumb'] and fingers['pinky'] and not fingers['index']:
        return "My Custom Gesture"
```

---

