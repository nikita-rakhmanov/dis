# Running on Your Local Machine (with Webcam)

## Quick Setup

Since webcam features require local hardware, you need to set up the project on your local machine.

### 1. Clone or Pull Latest Changes

On your local machine:

```bash
cd /path/to/dis
git pull origin main
```

Or if you're cloning for the first time:

```bash
git clone <repository-url>
cd dis
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Test Webcam

First, verify the webcam works with the standalone hand tracker:

```bash
python gesture_control/hand_tracker.py
```

You should see your webcam feed with hand tracking. Press 'q' to quit.

### 4. Test MIDI CC Output

Now test the MIDI CC with webcam:

```bash
python test_gesture_midi.py
```

You should see:
- Webcam window opening
- Hand tracking active
- Real-time CC values displayed
- MIDI CC messages being sent

Move your hand:
- LEFT/RIGHT → Filter Cutoff (CC 74)
- UP/DOWN → Reverb (CC 91)
- PINCH → Resonance (CC 71)

### 5. Run Full Integration

Once testing works, run the full system:

```bash
python integrated_music_gesture_control.py --model music_rnn_model.keras
```

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Webcam permission errors (macOS)
- System Preferences → Security & Privacy → Camera
- Allow Terminal/Python to access camera

### Webcam in use by another app
- Close other apps using the camera (Zoom, Skype, etc.)
- Try different camera index:
  ```python
  # Edit test_gesture_midi.py, line 70:
  cap = cv2.VideoCapture(1)  # Try 1 instead of 0
  ```

### Script exits immediately (0 frames)
This means the webcam is not accessible. Try:

```bash
# Check if webcam is available
ls /dev/video*

# Try a different camera index in the code
# Edit test_gesture_midi.py and change cv2.VideoCapture(0) to cv2.VideoCapture(1)
```

## Files You Need

Make sure these files exist after pulling:

- `integrated_music_gesture_control.py` (main system)
- `test_gesture_midi.py` (webcam test)
- `test_gesture_midi_sim.py` (no webcam needed)
- `gesture_control/hand_tracker.py` (hand tracking)
- `ABLETON_MAPPING_GUIDE.md` (Ableton setup)

## Workflow: Remote + Local

**Remote server (no webcam):**
- Train models
- Test code logic
- Use `test_gesture_midi_sim.py` for MIDI testing

**Local machine (with webcam):**
- Test gesture recognition
- Run full integrated system
- Perform live with DAW

## Quick Check

Run this to verify everything is ready:

```bash
# Check you have the latest code
git status

# Check files exist
ls -la integrated_music_gesture_control.py test_gesture_midi.py

# Check dependencies
python -c "import cv2, mediapipe, mido; print('All imports OK')"

# Test webcam
python gesture_control/hand_tracker.py
```

If all checks pass, the system is ready to use.
