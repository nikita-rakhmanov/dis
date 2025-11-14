"""
Hand tracking and gesture recognition using MediaPipe and OpenCV.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import List, Tuple, Optional, Dict
import math


class HandTracker:
    """Hand tracking and gesture recognition using MediaPipe."""

    def __init__(self, max_hands=2, detection_confidence=0.7, tracking_confidence=0.7):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

        self.WRIST = 0
        self.THUMB_TIP = 4
        self.INDEX_TIP = 8
        self.MIDDLE_TIP = 12
        self.RING_TIP = 16
        self.PINKY_TIP = 20

        self.INDEX_PIP = 6
        self.MIDDLE_PIP = 10
        self.RING_PIP = 14
        self.PINKY_PIP = 18
        self.THUMB_IP = 3

    def process_frame(self, frame):
        """Process a video frame to detect hands."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        results = self.hands.process(rgb_frame)

        rgb_frame.flags.writeable = True
        return results, rgb_frame

    def get_finger_state(self, landmarks, handedness) -> Dict[str, bool]:
        """Determine which fingers are extended."""
        fingers = {
            'thumb': False,
            'index': False,
            'middle': False,
            'ring': False,
            'pinky': False
        }

        # Thumb uses x-coordinate comparison due to orientation
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]

        if handedness == "Right":
            fingers['thumb'] = thumb_tip.x < thumb_ip.x
        else:
            fingers['thumb'] = thumb_tip.x > thumb_ip.x

        fingers['index'] = landmarks[self.INDEX_TIP].y < landmarks[self.INDEX_PIP].y
        fingers['middle'] = landmarks[self.MIDDLE_TIP].y < landmarks[self.MIDDLE_PIP].y
        fingers['ring'] = landmarks[self.RING_TIP].y < landmarks[self.RING_PIP].y
        fingers['pinky'] = landmarks[self.PINKY_TIP].y < landmarks[self.PINKY_PIP].y

        return fingers

    def calculate_distance(self, point1, point2) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    def recognize_gesture(self, landmarks, handedness) -> str:
        """Recognize hand gesture based on finger positions."""
        fingers = self.get_finger_state(landmarks, handedness)
        extended_count = sum(fingers.values())

        if all(fingers.values()):
            return "Open Palm"

        if extended_count == 0:
            return "Closed Fist"

        if fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            return "Peace Sign"

        if fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            return "Pointing"

        if fingers['thumb'] and extended_count == 1:
            return "Thumbs Up"

        thumb_index_dist = self.calculate_distance(
            landmarks[self.THUMB_TIP],
            landmarks[self.INDEX_TIP]
        )
        if thumb_index_dist < 0.05 and fingers['middle'] and fingers['ring'] and fingers['pinky']:
            return "OK Sign"

        if fingers['index'] and fingers['pinky'] and not fingers['middle'] and not fingers['ring']:
            return "Rock On"

        if extended_count == 3:
            return "Three Fingers"

        if extended_count == 4:
            return "Four Fingers"

        return f"{extended_count} Fingers Extended"

    def draw_hand_info(self, frame, results):
        """Draw hand landmarks and gesture information on the frame."""
        if not results.multi_hand_landmarks:
            return frame

        h, w, c = frame.shape

        for idx, (hand_landmarks, handedness) in enumerate(
            zip(results.multi_hand_landmarks, results.multi_handedness)
        ):
            self.mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )

            hand_label = handedness.classification[0].label
            gesture = self.recognize_gesture(hand_landmarks.landmark, hand_label)

            x_coords = [lm.x for lm in hand_landmarks.landmark]
            y_coords = [lm.y for lm in hand_landmarks.landmark]

            x_min = int(min(x_coords) * w)
            x_max = int(max(x_coords) * w)
            y_min = int(min(y_coords) * h)
            y_max = int(max(y_coords) * h)

            padding = 20
            x_min = max(0, x_min - padding)
            x_max = min(w, x_max + padding)
            y_min = max(0, y_min - padding)
            y_max = min(h, y_max + padding)

            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            label_text = f"{hand_label} Hand: {gesture}"

            text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            text_x = x_min
            text_y = y_min - 10

            if text_y - text_size[1] - 10 < 0:
                text_y = y_min + text_size[1] + 10

            cv2.rectangle(
                frame,
                (text_x, text_y - text_size[1] - 5),
                (text_x + text_size[0] + 5, text_y + 5),
                (0, 255, 0),
                -1
            )

            cv2.putText(
                frame,
                label_text,
                (text_x + 2, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2
            )

            wrist = hand_landmarks.landmark[self.WRIST]
            center_x = int(wrist.x * w)
            center_y = int(wrist.y * h)
            cv2.circle(frame, (center_x, center_y), 10, (255, 0, 0), -1)

        return frame

    def release(self):
        """Release MediaPipe resources."""
        self.hands.close()


def main():
    """Run the hand tracking application."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    tracker = HandTracker(max_hands=2)

    print("Hand Tracking Started!")
    print("Controls:")
    print("  - Press 'q' to quit")
    print("  - Press 's' to save current frame")
    print("\nDetectable Gestures:")
    print("  - Open Palm")
    print("  - Closed Fist")
    print("  - Pointing")
    print("  - Peace Sign")
    print("  - Thumbs Up")
    print("  - OK Sign")
    print("  - Rock On")
    print("  - Three/Four Fingers")

    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to capture frame")
            break

        frame = cv2.flip(frame, 1)

        results, _ = tracker.process_frame(frame)

        frame = tracker.draw_hand_info(frame, results)

        cv2.putText(
            frame,
            "Press 'q' to quit | 's' to save frame",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        frame_count += 1
        cv2.putText(
            frame,
            f"Frame: {frame_count}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.imshow('Hand Tracking - Gesture Control', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("Quitting...")
            break
        elif key == ord('s'):
            filename = f'hand_tracking_frame_{frame_count}.jpg'
            cv2.imwrite(filename, frame)
            print(f"Saved frame as {filename}")

    cap.release()
    cv2.destroyAllWindows()
    tracker.release()
    print("Hand tracking stopped.")


if __name__ == "__main__":
    main()
