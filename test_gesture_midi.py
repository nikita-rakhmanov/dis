#!/usr/bin/env python3
"""
Quick test script to verify gesture control MIDI CC output.
This script tracks your hand and sends MIDI CC messages without music generation.
Use this to test your DAW setup and CC mappings.
"""

import cv2
import mido
import time
import sys
from collections import deque
from gesture_control.hand_tracker import HandTracker

class SimpleMIDITest:
    """Simple test for MIDI CC from gesture control."""

    CC_FILTER_CUTOFF = 74
    CC_RESONANCE = 71
    CC_REVERB = 91
    CC_CHORUS = 93
    CC_MODULATION = 1

    def __init__(self, midi_port_name=None):
        """Initialize MIDI port."""
        available_ports = mido.get_output_names()
        print("Available MIDI ports:")
        for i, port in enumerate(available_ports):
            print(f"  [{i}] {port}")

        if midi_port_name:
            try:
                self.midi_out = mido.open_output(midi_port_name)
                print(f"\n✓ Connected to: {midi_port_name}\n")
                return
            except:
                print(f"\n✗ Could not open port '{midi_port_name}'")

        # Interactive selection
        if available_ports:
            try:
                idx = int(input("\nSelect port number (or press Enter for virtual): ").strip() or -1)
                if 0 <= idx < len(available_ports):
                    self.midi_out = mido.open_output(available_ports[idx])
                    print(f"✓ Connected to: {available_ports[idx]}\n")
                    return
            except:
                pass

        # Create virtual port
        print("\nCreating virtual MIDI port...")
        self.midi_out = mido.open_output('Gesture Control Test', virtual=True)
        print("✓ Virtual port 'Gesture Control Test' created\n")

    def normalize_to_midi(self, value, min_val=0.0, max_val=1.0):
        """Normalize value to MIDI range (0-127)."""
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))
        return int(normalized * 127)

    def send_cc(self, cc_number, value, channel=0):
        """Send MIDI CC message."""
        value = max(0, min(127, value))
        msg = mido.Message('control_change', control=cc_number, value=value, channel=channel)
        self.midi_out.send(msg)

    def test_gesture_control(self):
        """Run hand tracking and send MIDI CC."""
        print("Attempting to open webcam...")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("\n" + "=" * 70)
            print("✗ ERROR: Could not open webcam")
            print("=" * 70)
            print("\nPossible causes:")
            print("  1. No webcam connected to this system")
            print("  2. Webcam is being used by another application")
            print("  3. Permission denied (check camera permissions)")
            print("  4. Running on a server/remote system without camera")
            print("\nSolutions:")
            print("  • If no webcam: Use test_gesture_midi_sim.py instead")
            print("  • Check available cameras: ls /dev/video*")
            print("  • Close other apps using the camera")
            print("  • On Linux: check permissions with v4l2-ctl --list-devices")
            print("\nFor testing without a webcam:")
            print("  python test_gesture_midi_sim.py")
            print("=" * 70)
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Give camera time to initialize and warm up
        print("Initializing camera...")
        time.sleep(1.0)

        # Read and discard first few frames (camera warmup)
        for i in range(5):
            ret, _ = cap.read()
            if not ret:
                print(f"Warning: Camera warmup frame {i+1}/5 failed")

        print("✓ Camera ready!")

        tracker = HandTracker(max_hands=1)

        print("=" * 70)
        print("GESTURE CONTROL MIDI CC TEST")
        print("=" * 70)
        print("\nControls:")
        print("  - Move hand LEFT/RIGHT → Filter Cutoff (CC 74)")
        print("  - Move hand UP/DOWN → Reverb Level (CC 91)")
        print("  - PINCH fingers → Resonance (CC 71)")
        print("  - OPEN PALM → Chorus Max (CC 93 = 127)")
        print("  - CLOSED FIST → Effects Off (CC 93 = 0)")
        print("  - ROCK ON → Modulation Max (CC 1 = 127)")
        print("\nPress 'q' to quit\n")
        print("=" * 70)

        # Buffers for smoothing
        buffer_x = deque(maxlen=5)
        buffer_y = deque(maxlen=5)
        last_cc_values = {}

        frame_count = 0
        start_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("\n✗ ERROR: Failed to read frame from webcam")
                    print("Webcam may have disconnected or encountered an error")
                    break

                frame = cv2.flip(frame, 1)
                results, _ = tracker.process_frame(frame)

                # Process hand data
                if results.multi_hand_landmarks:
                    for hand_landmarks, handedness in zip(
                        results.multi_hand_landmarks,
                        results.multi_handedness
                    ):
                        hand_label = handedness.classification[0].label
                        landmarks = hand_landmarks.landmark

                        # Get positions
                        index_tip = landmarks[8]
                        thumb_tip = landmarks[4]

                        # Smooth positions
                        buffer_x.append(index_tip.x)
                        buffer_y.append(index_tip.y)
                        x_pos = sum(buffer_x) / len(buffer_x)
                        y_pos = sum(buffer_y) / len(buffer_y)

                        # Calculate values
                        cutoff = self.normalize_to_midi(x_pos, 0.0, 1.0)
                        reverb = self.normalize_to_midi(1.0 - y_pos, 0.0, 1.0)

                        # Calculate pinch distance
                        distance = ((thumb_tip.x - index_tip.x)**2 +
                                  (thumb_tip.y - index_tip.y)**2)**0.5
                        resonance = self.normalize_to_midi(distance, 0.0, 0.3)

                        # Send CC messages (with change detection)
                        for cc_num, value in [(self.CC_FILTER_CUTOFF, cutoff),
                                             (self.CC_REVERB, reverb),
                                             (self.CC_RESONANCE, resonance)]:
                            if cc_num not in last_cc_values or abs(last_cc_values[cc_num] - value) >= 2:
                                self.send_cc(cc_num, value)
                                last_cc_values[cc_num] = value

                        # Recognize gesture
                        gesture = tracker.recognize_gesture(landmarks, hand_label)

                        # Gesture-based CC
                        if gesture == "Open Palm":
                            self.send_cc(self.CC_CHORUS, 127)
                            last_cc_values[self.CC_CHORUS] = 127
                        elif gesture == "Closed Fist":
                            self.send_cc(self.CC_CHORUS, 0)
                            self.send_cc(self.CC_MODULATION, 0)
                            last_cc_values[self.CC_CHORUS] = 0
                            last_cc_values[self.CC_MODULATION] = 0
                        elif gesture == "Rock On":
                            self.send_cc(self.CC_MODULATION, 127)
                            last_cc_values[self.CC_MODULATION] = 127

                        # Display values on frame
                        info_y = 90
                        cv2.putText(frame, f"Filter (CC74): {cutoff}", (10, info_y),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        cv2.putText(frame, f"Reverb (CC91): {reverb}", (10, info_y + 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        cv2.putText(frame, f"Resonance (CC71): {resonance}", (10, info_y + 60),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        cv2.putText(frame, f"Gesture: {gesture}", (10, info_y + 90),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                # Draw hand visualization
                frame = tracker.draw_hand_info(frame, results)

                # Add title
                cv2.putText(frame, "MIDI CC Test - Gesture Control", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame, "Press 'q' to quit", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                # Show frame
                cv2.imshow('MIDI CC Test', frame)

                frame_count += 1

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            print("\n\nStopping...")

        finally:
            # Calculate stats
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0

            # Cleanup
            cap.release()
            cv2.destroyAllWindows()
            tracker.release()

            # Reset all CCs
            print("\nResetting MIDI CC values...")
            for cc in [self.CC_FILTER_CUTOFF, self.CC_RESONANCE,
                      self.CC_REVERB, self.CC_CHORUS, self.CC_MODULATION]:
                self.send_cc(cc, 0)

            self.midi_out.close()

            print(f"\n✓ Test completed")
            print(f"  Frames processed: {frame_count}")
            print(f"  Average FPS: {fps:.1f}")
            print(f"  Duration: {elapsed:.1f}s")
            print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Test gesture control MIDI CC output')
    parser.add_argument('--port', default=None, help='MIDI port name')
    args = parser.parse_args()

    tester = SimpleMIDITest(args.port)
    tester.test_gesture_control()


if __name__ == "__main__":
    main()
