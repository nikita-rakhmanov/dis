# Getting Started

A step-by-step guide to set up and run the AI Music Generation with Gesture Control project.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10, 3.11, or 3.12** installed (TensorFlow does not support Python 3.13 yet)
- **Webcam** (required for gesture control)
- **DAW** with MIDI support (Ableton Live, Logic Pro, FL Studio, Reaper, etc.)

---

## Step 1: Clone the Repository (if needed)

If you haven't already cloned the project:

```bash
git clone <repository-url>
cd dis
```

Or navigate to your existing project directory:

```bash
cd /path/to/dis
```

---

## Step 2: Create a Virtual Environment

Creating a virtual environment isolates project dependencies from your system Python.

### macOS / Linux

```bash
# Check your Python version first
python3 --version

# If Python 3.13+, use python3.12 explicitly:
python3.12 -m venv venv

# Or if your default Python is 3.10-3.12:
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

### Windows

```bash
# Check your Python version first
python --version

# If Python 3.13+, use py launcher with specific version:
py -3.12 -m venv venv

# Or if your default Python is 3.10-3.12:
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

> **Note:** When the virtual environment is active, you'll see `(venv)` at the beginning of your terminal prompt.

To deactivate the virtual environment when you're done:

```bash
deactivate
```

---

## Step 3: Install Dependencies

With your virtual environment activated, install all required packages:

```bash
pip install -r requirements.txt
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| tensorflow | RNN model for music generation |
| mido + python-rtmidi | MIDI I/O |
| mediapipe | Hand tracking |
| opencv-python | Video capture |
| websockets | Real-time visualization |

### Verify Installation

```bash
python -c "import cv2, mediapipe, mido, tensorflow; print('All imports OK!')"
```

---

## Step 4: Test Individual Components

### 4.1 Test Hand Tracking (Webcam)

Verify the webcam and hand tracking work:

```bash
python gesture_control/hand_tracker.py
```

You should see your webcam feed with hand tracking overlay. Press `q` to quit.

### 4.2 Test Gesture-to-MIDI

Test gesture control with MIDI output:

```bash
python test_gesture_midi.py
```

Move your hand in front of the webcam and observe:
- **Left/Right movement** → Filter Cutoff (CC 74)
- **Up/Down movement** → Reverb Level (CC 91)
- **Pinch gesture** → Resonance (CC 71)

---

## Step 5: Run the Full System

Launch the integrated music generation and gesture control system:

```bash
python integrated_music_gesture_control.py --model music_rnn_model.keras
```

### Available Command Line Options

```bash
# Default settings
python integrated_music_gesture_control.py

# Custom temperature and velocity
python integrated_music_gesture_control.py --temperature 1.5 --velocity 100

# Specific MIDI port
python integrated_music_gesture_control.py --port "IAC Driver Bus 1"

# Disable visualization (lower CPU usage)
python integrated_music_gesture_control.py --no-visualization

# Music generation only (no gestures)
python integrated_music_gesture_control.py --no-gesture
```

---

## Step 6: Set Up Your DAW

### Quick MIDI Routing Setup

1. Create two MIDI tracks in your DAW
2. **Track 1**: Route to instrument (receives notes)
3. **Track 2**: Route CC to effects (receives control messages)
4. Add Audio Effects Rack with:
   - Low Pass Filter (map Frequency to CC 74, Resonance to CC 71)
   - Reverb/Delay (map Wet/Dry to CC 91)
   - Chorus (map Amount to CC 93)

### DAW-Specific Guides

- **Ableton Live**: See [ABLETON_MAPPING_GUIDE.md](ABLETON_MAPPING_GUIDE.md)
- **Other DAWs**: See [docs/GESTURE_CONTROL_GUIDE.md](docs/GESTURE_CONTROL_GUIDE.md)

---

## Troubleshooting

### "Module not found" errors

Make sure your virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Webcam permission errors (macOS)

1. Go to **System Preferences → Security & Privacy → Camera**
2. Allow Terminal/Python to access camera

### "Could not open webcam"

- Check webcam permissions
- Verify device exists: `ls /dev/video*` (Linux/macOS)
- Close other apps using the camera (Zoom, Skype, etc.)
- Try a different camera index: edit the script to use `cv2.VideoCapture(1)` instead of `cv2.VideoCapture(0)`

### "MIDI port not found"

List available MIDI ports:

```bash
python -c "import mido; print(mido.get_output_names())"
```

Create a virtual MIDI port:
- **macOS**: Enable IAC Driver in Audio MIDI Setup
- **Windows**: Use loopMIDI software

---