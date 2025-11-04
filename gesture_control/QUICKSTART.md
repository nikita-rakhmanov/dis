# Gesture Control - Quick Start Guide

This guide will help you get started with the hand tracking and gesture recognition module.

## Installation

1. **Install dependencies:**
   ```bash
   pip install opencv-python mediapipe numpy
   ```

   Or install all project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   ```bash
   python -m gesture_control.test_import
   ```

   You should see all checkmarks indicating successful installation.

## Running the Application

### Basic Usage

Run the hand tracking application from the project root:

```bash
python gesture_control/hand_tracker.py
```

or

```bash
python -m gesture_control.hand_tracker
```

### What to Expect

- A window will open showing your webcam feed
- When you place your hand(s) in view, you'll see:
  - Green bounding boxes around detected hands
  - Hand landmarks (key points) connected with lines
  - Blue circle at the wrist center
  - Gesture labels showing which hand (Left/Right) and the detected gesture

### Supported Gestures

Try these gestures in front of your camera:

1. **Open Palm** - Spread all fingers wide
2. **Closed Fist** - Make a fist with all fingers folded
3. **Pointing** - Extend only your index finger
4. **Peace Sign** - Extend index and middle fingers (V shape)
5. **Thumbs Up** - Extend only your thumb upward
6. **OK Sign** - Touch thumb and index fingertips, extend other fingers
7. **Rock On** - Extend index and pinky fingers
8. **Three/Four Fingers** - Extend 3 or 4 fingers

### Controls

- **Press 'q'** to quit the application
- **Press 's'** to save the current frame as an image

## Using as a Python Module

You can also import and use the HandTracker in your own code:

```python
from gesture_control import HandTracker
import cv2

# Initialize
tracker = HandTracker(max_hands=2)
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Process frame
    results, _ = tracker.process_frame(frame)

    # Draw annotations
    frame = tracker.draw_hand_info(frame, results)

    # Your custom logic here
    # Access results.multi_hand_landmarks for hand data
    # Access results.multi_handedness for left/right info

    cv2.imshow('My App', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
tracker.release()
```

## Troubleshooting

### "Could not open webcam" error
- Check if another application is using your webcam
- On Linux, you might need to grant camera permissions
- Try changing the camera index: `cv2.VideoCapture(1)` or `cv2.VideoCapture(2)`

### Low FPS or laggy performance
- Close other applications to free up CPU
- Reduce camera resolution in the code
- Use fewer max_hands (set to 1 instead of 2)

### Gesture not detected correctly
- Ensure good lighting
- Position your hand clearly in front of the camera
- Keep your hand at a moderate distance (30-60cm)
- Make gestures clearly and hold them for a moment

### Import errors
- Make sure to run from the project root directory
- Use `python -m gesture_control.hand_tracker` instead of navigating to the folder

## Next Steps

This module is designed to eventually control the music generation application.
Future integration possibilities:

- Use gestures to start/stop music generation
- Control tempo with hand movements
- Switch between different musical modes with specific gestures
- Adjust volume and dynamics with hand positions

## Technical Details

- **Hand Detection**: Uses MediaPipe Hands solution
- **Tracking**: Supports up to 2 hands simultaneously
- **FPS**: Typically 20-30 FPS depending on your hardware
- **Latency**: Real-time (~30-50ms)
- **Resolution**: Configurable (default 1280x720)

For more details, see the README.md file in the gesture_control directory.
