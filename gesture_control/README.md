# Gesture Control Module

A Python module for hand tracking and gesture recognition using MediaPipe and OpenCV.

Integrated with the music generation system to provide real-time MIDI CC control via hand gestures.

## Features

- **Real-time hand tracking** using webcam
- **Multi-hand detection** (up to 2 hands simultaneously)
- **Gesture recognition** with labeled bounding boxes
- **Visual feedback** with hand landmarks and connections
- **MIDI CC output** for DAW effect control

## Supported Gestures

- **Open Palm** - All fingers extended
- **Closed Fist** - All fingers folded
- **Pointing** - Index finger extended
- **Peace Sign** - Index and middle fingers extended
- **Thumbs Up** - Only thumb extended
- **OK Sign** - Thumb and index touching, others extended
- **Rock On** - Index and pinky extended
- **Three/Four Fingers** - Multiple fingers extended

## Usage

### Standalone Application

Run the hand tracking application directly:

```bash
python gesture_control/hand_tracker.py
```

### As a Module

Import and use in your Python code:

```python
from gesture_control import HandTracker
import cv2

# Initialize tracker
tracker = HandTracker(max_hands=2)

# Capture video
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Process frame
    results, _ = tracker.process_frame(frame)

    # Draw hand information
    frame = tracker.draw_hand_info(frame, results)

    # Display
    cv2.imshow('Hand Tracking', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
tracker.release()
```

## Controls

- **'q'** - Quit the application
- **'s'** - Save current frame as image

## Requirements

- OpenCV (cv2)
- MediaPipe
- NumPy

Install with:
```bash
pip install opencv-python mediapipe numpy
```

## Music Integration

This module is integrated with the main music generation application for real-time effect control:

- **Hand X Position** → Filter Cutoff (CC 74)
- **Hand Y Position** → Reverb/Delay (CC 91)
- **Pinch Gesture** → Resonance (CC 71)
- **Open Palm** → Chorus Max (CC 93)
- **Closed Fist** → Effects Off

See the main README.md and GESTURE_CONTROL_GUIDE.md for full integration details.

## Technical Details

### HandTracker Class

**Parameters:**
- `max_hands` (int): Maximum number of hands to detect (default: 2)
- `detection_confidence` (float): Minimum confidence for detection (default: 0.7)
- `tracking_confidence` (float): Minimum confidence for tracking (default: 0.7)

**Methods:**
- `process_frame(frame)`: Process video frame to detect hands
- `recognize_gesture(landmarks, handedness)`: Recognize gesture from landmarks
- `draw_hand_info(frame, results)`: Draw annotations on frame
- `release()`: Clean up resources

## Architecture

```
gesture_control/
├── __init__.py          # Package initialization
├── hand_tracker.py      # Main hand tracking implementation
└── README.md           # This file
```
