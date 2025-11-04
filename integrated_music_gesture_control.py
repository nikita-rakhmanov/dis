#!/usr/bin/env python3
"""
Integrated Music Generation with Gesture Control

This script combines:
1. Real-time MIDI music generation (RNN model)
2. Hand tracking for gesture-based effects control

The music generator plays notes via MIDI while hand tracking
sends MIDI CC (Control Change) messages to control audio effects
in your DAW (delays, filters, reverb, etc.)
"""

import numpy as np
import tensorflow as tf
import mido
from mido import Message
import time
import argparse
import asyncio
import websockets
import json
import threading
from datetime import datetime
import cv2
import sys
from collections import deque

# Import hand tracker
from gesture_control.hand_tracker import HandTracker

# Configuration
SEQUENCE_LENGTH = 25
VOCAB_SIZE = 128
KEY_ORDER = ['pitch', 'step', 'duration']


def mse_with_positive_pressure(y_true, y_pred):
    """Custom loss function needed for model loading."""
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)


class GestureMIDIController:
    """
    Maps hand tracking data to MIDI CC messages for effects control.
    """

    # MIDI CC mapping
    CC_FILTER_CUTOFF = 74  # Brightness/Filter Cutoff
    CC_RESONANCE = 71      # Filter Resonance
    CC_REVERB = 91         # Reverb/Delay Level
    CC_CHORUS = 93         # Chorus/Modulation
    CC_MODULATION = 1      # Modulation Wheel
    CC_EXPRESSION = 11     # Expression

    def __init__(self, midi_out, update_rate=20):
        """
        Initialize gesture MIDI controller.

        Args:
            midi_out: MIDI output port
            update_rate: Hz rate for sending CC messages (default 20Hz)
        """
        self.midi_out = midi_out
        self.update_rate = update_rate
        self.last_cc_values = {}
        self.midi_lock = threading.Lock()

        # Smoothing buffers
        self.position_buffer_x = deque(maxlen=5)
        self.position_buffer_y = deque(maxlen=5)

    def normalize_to_midi(self, value, min_val=0.0, max_val=1.0):
        """Normalize a value to MIDI range (0-127)."""
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))
        return int(normalized * 127)

    def smooth_value(self, buffer, new_value):
        """Apply smoothing to reduce jitter."""
        buffer.append(new_value)
        return sum(buffer) / len(buffer)

    def send_cc(self, cc_number, value, channel=0):
        """
        Send MIDI CC message with duplicate suppression.

        Args:
            cc_number: MIDI CC number (0-127)
            value: CC value (0-127)
            channel: MIDI channel (0-15)
        """
        # Only send if value changed significantly (threshold of 2)
        key = (cc_number, channel)
        if key in self.last_cc_values:
            if abs(self.last_cc_values[key] - value) < 2:
                return

        self.last_cc_values[key] = value

        with self.midi_lock:
            msg = Message('control_change', control=cc_number, value=value, channel=channel)
            self.midi_out.send(msg)

    def process_hand_data(self, hand_landmarks, hand_label, gesture):
        """
        Process hand tracking data and send appropriate MIDI CC messages.

        Args:
            hand_landmarks: MediaPipe hand landmarks
            hand_label: "Left" or "Right"
            gesture: Detected gesture name
        """
        # Get wrist position as reference
        wrist = hand_landmarks[0]
        index_tip = hand_landmarks[8]
        thumb_tip = hand_landmarks[4]

        # Smooth X and Y positions
        x_pos = self.smooth_value(self.position_buffer_x, index_tip.x)
        y_pos = self.smooth_value(self.position_buffer_y, index_tip.y)

        # Map hand X position (0-1) to Filter Cutoff (CC 74)
        # Left = dark/closed, Right = bright/open
        cutoff_value = self.normalize_to_midi(x_pos, 0.0, 1.0)
        self.send_cc(self.CC_FILTER_CUTOFF, cutoff_value)

        # Map hand Y position to Reverb/Delay (CC 91)
        # Up = more effect, Down = less effect
        reverb_value = self.normalize_to_midi(1.0 - y_pos, 0.0, 1.0)  # Invert Y
        self.send_cc(self.CC_REVERB, reverb_value)

        # Calculate distance between thumb and index for Resonance (CC 71)
        distance = np.sqrt((thumb_tip.x - index_tip.x)**2 +
                          (thumb_tip.y - index_tip.y)**2)
        resonance_value = self.normalize_to_midi(distance, 0.0, 0.3)
        self.send_cc(self.CC_RESONANCE, resonance_value)

        # Gesture-based control
        if gesture == "Open Palm":
            # Open palm = Maximum chorus/modulation
            self.send_cc(self.CC_CHORUS, 127)
        elif gesture == "Closed Fist":
            # Closed fist = Minimum effects
            self.send_cc(self.CC_CHORUS, 0)
            self.send_cc(self.CC_MODULATION, 0)
        elif gesture == "Peace Sign":
            # Peace sign = Medium modulation
            self.send_cc(self.CC_MODULATION, 64)
        elif gesture == "Rock On":
            # Rock on = Maximum modulation
            self.send_cc(self.CC_MODULATION, 127)


class IntegratedMusicGestureSystem:
    """
    Main system that integrates MIDI generation with gesture control.
    """

    def __init__(self, model_path, midi_port_name=None, enable_websocket=True,
                 ws_port=8765, enable_gesture=True):
        """
        Initialize the integrated system.

        Args:
            model_path: Path to trained RNN model
            midi_port_name: MIDI port name (interactive if None)
            enable_websocket: Enable WebSocket visualization
            ws_port: WebSocket port number
            enable_gesture: Enable gesture control
        """
        # Load model
        print(f"Loading model from {model_path}...")
        self.model = tf.keras.models.load_model(
            model_path,
            custom_objects={'mse_with_positive_pressure': mse_with_positive_pressure}
        )
        print("✓ Model loaded successfully!\n")

        # Setup MIDI
        self._setup_midi(midi_port_name)

        self.seq_length = SEQUENCE_LENGTH
        self.vocab_size = VOCAB_SIZE
        self.current_notes = None
        self.prev_start = 0

        # WebSocket setup
        self.enable_websocket = enable_websocket
        self.ws_port = ws_port
        self.ws_clients = set()
        self.ws_server = None
        self.ws_loop = None

        # Gesture control setup
        self.enable_gesture = enable_gesture
        self.gesture_controller = None
        self.hand_tracker = None
        self.gesture_thread = None
        self.gesture_running = False

        if self.enable_gesture:
            self.gesture_controller = GestureMIDIController(self.midi_out)
            self.hand_tracker = HandTracker(max_hands=1)
            print("✓ Gesture control initialized\n")

    def _setup_midi(self, port_name):
        """Setup MIDI output port."""
        available_ports = mido.get_output_names()
        print("Available MIDI ports:")
        for i, port in enumerate(available_ports):
            print(f"  [{i}] {port}")

        if port_name:
            try:
                self.midi_out = mido.open_output(port_name)
                print(f"\n✓ Connected to: {port_name}\n")
                return
            except:
                print(f"\n✗ Could not open port '{port_name}'")

        # Interactive selection or create virtual port
        if available_ports:
            try:
                idx = int(input("\nSelect port number (or press Enter to create virtual): ").strip() or -1)
                if 0 <= idx < len(available_ports):
                    self.midi_out = mido.open_output(available_ports[idx])
                    print(f"✓ Connected to: {available_ports[idx]}\n")
                    return
            except:
                pass

        # Create virtual port
        print("\nCreating virtual MIDI port...")
        self.midi_out = mido.open_output('RNN Music Generator', virtual=True)
        print("✓ Virtual port 'RNN Music Generator' created\n")

    def load_seed_sequence(self, seed_file=None):
        """Load or create seed sequence."""
        if seed_file:
            try:
                seed = np.load(seed_file)
                self.current_notes = seed / np.array([self.vocab_size, 1, 1])
                print(f"✓ Loaded seed sequence from {seed_file}")
                return
            except:
                print(f"✗ Could not load {seed_file}, using default seed")

        # Create default C major scale seed
        seed_notes = []
        c_major = [0, 2, 4, 5, 7, 9, 11, 12]
        for i in range(self.seq_length):
            pitch = 60 + c_major[i % len(c_major)]
            step = 0.5
            duration = 0.4
            seed_notes.append([pitch, step, duration])

        seed_notes = np.array(seed_notes)
        self.current_notes = seed_notes / np.array([self.vocab_size, 1, 1])
        print("✓ Using default C major scale seed")

    async def ws_handler(self, websocket):
        """Handle WebSocket connections."""
        self.ws_clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'
        print(f"🌐 Visualization client connected from {client_ip}")
        try:
            await websocket.wait_closed()
        finally:
            self.ws_clients.remove(websocket)
            print(f"🌐 Visualization client disconnected")

    async def broadcast_note(self, note_data):
        """Broadcast note data to WebSocket clients."""
        if self.ws_clients:
            message = json.dumps(note_data)
            await asyncio.gather(
                *[client.send(message) for client in self.ws_clients],
                return_exceptions=True
            )

    def start_websocket_server(self):
        """Start WebSocket server in background thread."""
        if not self.enable_websocket:
            return

        def run_ws_server():
            self.ws_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ws_loop)

            async def server():
                async with websockets.serve(self.ws_handler, "0.0.0.0", self.ws_port):
                    print(f"🌐 WebSocket server started on ws://localhost:{self.ws_port}")
                    await asyncio.Future()

            self.ws_loop.run_until_complete(server())

        ws_thread = threading.Thread(target=run_ws_server, daemon=True)
        ws_thread.start()
        time.sleep(0.5)

    def gesture_control_loop(self):
        """Run hand tracking and send MIDI CC in separate thread."""
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("✗ Could not open webcam for gesture control")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Give camera time to initialize
        print("Initializing gesture control camera...")
        time.sleep(1.0)

        # Warmup: read and discard first few frames
        for i in range(5):
            ret, _ = cap.read()
            if not ret:
                print(f"Warning: Camera warmup frame {i+1}/5 failed")

        print("✓ Gesture control started (webcam active)")
        print("   Hand position controls Filter (X) and Reverb (Y)")
        print("   Gestures: Open Palm, Closed Fist, Peace, Rock On")
        print("   Note: Webcam window disabled (macOS compatibility)")
        print()

        frame_interval = 1.0 / self.gesture_controller.update_rate
        last_update = time.time()

        while self.gesture_running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            results, _ = self.hand_tracker.process_frame(frame)

            # Process hand data for MIDI CC
            current_time = time.time()
            if current_time - last_update >= frame_interval:
                if results.multi_hand_landmarks:
                    for hand_landmarks, handedness in zip(
                        results.multi_hand_landmarks,
                        results.multi_handedness
                    ):
                        hand_label = handedness.classification[0].label
                        gesture = self.hand_tracker.recognize_gesture(
                            hand_landmarks.landmark, hand_label
                        )

                        self.gesture_controller.process_hand_data(
                            hand_landmarks.landmark,
                            hand_label,
                            gesture
                        )

                last_update = current_time

            # Note: cv2.imshow removed - causes crashes on macOS when called from background thread
            # Gesture control works fine without the window display

        cap.release()
        self.hand_tracker.release()
        print("✓ Gesture control stopped")

    def start_gesture_control(self):
        """Start gesture control in background thread."""
        if not self.enable_gesture:
            return

        self.gesture_running = True
        self.gesture_thread = threading.Thread(
            target=self.gesture_control_loop,
            daemon=True
        )
        self.gesture_thread.start()

        # Wait for camera to fully initialize before starting music
        print("Waiting for gesture control to initialize...")
        time.sleep(3.0)  # Give camera time to fully initialize

    def stop_gesture_control(self):
        """Stop gesture control thread."""
        if self.gesture_running:
            self.gesture_running = False
            if self.gesture_thread:
                self.gesture_thread.join(timeout=2.0)

    def predict_next_note(self, temperature=1.0):
        """Generate next note."""
        inputs = tf.expand_dims(self.current_notes, 0)
        predictions = self.model.predict(inputs, verbose=0)

        pitch_logits = predictions['pitch'] / temperature
        pitch = tf.random.categorical(pitch_logits, num_samples=1)
        pitch = tf.squeeze(pitch, axis=-1)
        step = tf.maximum(0, tf.squeeze(predictions['step'], axis=-1))
        duration = tf.maximum(0, tf.squeeze(predictions['duration'], axis=-1))

        return int(pitch), float(step), float(duration)

    def play_note(self, pitch, duration, velocity=80):
        """Send MIDI note with thread-safe locking."""
        pitch = max(0, min(127, pitch))
        velocity = max(0, min(127, velocity))

        with self.gesture_controller.midi_lock if self.gesture_controller else threading.Lock():
            self.midi_out.send(Message('note_on', note=pitch, velocity=velocity))

        time.sleep(duration)

        with self.gesture_controller.midi_lock if self.gesture_controller else threading.Lock():
            self.midi_out.send(Message('note_off', note=pitch, velocity=0))

    def update_sequence(self, pitch, step, duration):
        """Update the rolling input sequence."""
        input_note = np.array([pitch, step, duration])
        self.current_notes = np.delete(self.current_notes, 0, axis=0)
        self.current_notes = np.append(
            self.current_notes,
            np.expand_dims(input_note / np.array([self.vocab_size, 1, 1]), 0),
            axis=0
        )

    def send_to_visualization(self, note_data):
        """Send note data to WebSocket visualization."""
        if self.enable_websocket and self.ws_loop and self.ws_clients:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_note(note_data),
                self.ws_loop
            )

    def generate(self, num_notes=None, temperature=2.0, velocity=80,
                 min_duration=0.1, max_duration=2.0, speed=1.0):
        """Generate and play music with gesture control."""
        # Start services
        self.start_websocket_server()
        self.start_gesture_control()

        print("\n" + "=" * 70)
        print(f"🎵 INTEGRATED MUSIC GENERATION WITH GESTURE CONTROL")
        print("=" * 70)
        print(f"Temperature: {temperature} | Velocity: {velocity} | Speed: {speed}x")
        if self.enable_gesture:
            print("Gesture Control: ACTIVE - Move hands to control effects!")
        print("Press Ctrl+C to stop")
        print("=" * 70 + "\n")

        count = 0
        try:
            while num_notes is None or count < num_notes:
                # Generate note
                pitch, step, duration = self.predict_next_note(temperature)
                duration = max(min_duration, min(max_duration, duration))

                # Apply speed multiplier (higher speed = slower playback)
                # speed=2.0 means twice as slow (multiply durations by 2)
                duration_adjusted = duration * speed
                step_adjusted = step * speed

                # Display
                note_name = self._pitch_to_name(pitch)
                print(f"♪ {count+1:4d}: {note_name:4s} (pitch={pitch:3d}) "
                      f"step={step_adjusted:5.3f}s dur={duration_adjusted:5.3f}s")

                # Broadcast to visualization
                note_data = {
                    'type': 'note',
                    'pitch': int(pitch),
                    'step': float(step_adjusted),
                    'duration': float(duration_adjusted),
                    'velocity': int(velocity),
                    'note_name': note_name,
                    'timestamp': datetime.now().isoformat(),
                    'index': count
                }
                self.send_to_visualization(note_data)

                # Play note (with adjusted duration)
                self.play_note(pitch, duration_adjusted, velocity)

                # Update sequence (with original values, not adjusted)
                self.update_sequence(pitch, step, duration)
                self.prev_start += step
                count += 1

        except KeyboardInterrupt:
            print("\n" + "=" * 70)
            print("Stopping...")
        finally:
            # Cleanup
            self.stop_gesture_control()

            # Send all notes off
            for note in range(128):
                self.midi_out.send(Message('note_off', note=note, velocity=0))

            # Reset all CCs
            for cc in [1, 11, 71, 74, 91, 93]:
                self.midi_out.send(Message('control_change', control=cc, value=0))

            self.midi_out.close()
            print("✓ MIDI port closed")
            print("=" * 70)

    @staticmethod
    def _pitch_to_name(pitch):
        """Convert MIDI pitch to note name."""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return f"{notes[pitch % 12]}{pitch // 12 - 1}"


def main():
    parser = argparse.ArgumentParser(
        description='Integrated Music Generation with Gesture Control'
    )
    parser.add_argument('--model', default='music_rnn_model.keras',
                       help='Path to trained model')
    parser.add_argument('--seed', default='seed_sequence.npy',
                       help='Path to seed sequence')
    parser.add_argument('--port', default=None,
                       help='MIDI port name')
    parser.add_argument('--temperature', type=float, default=2.0,
                       help='Sampling temperature')
    parser.add_argument('--velocity', type=int, default=80,
                       help='MIDI velocity (0-127)')
    parser.add_argument('--num-notes', type=int, default=None,
                       help='Number of notes to generate')
    parser.add_argument('--min-duration', type=float, default=0.1,
                       help='Minimum note duration')
    parser.add_argument('--max-duration', type=float, default=2.0,
                       help='Maximum note duration')
    parser.add_argument('--no-visualization', action='store_true',
                       help='Disable WebSocket visualization')
    parser.add_argument('--no-gesture', action='store_true',
                       help='Disable gesture control')
    parser.add_argument('--ws-port', type=int, default=8765,
                       help='WebSocket port')
    parser.add_argument('--speed', type=float, default=1.0,
                       help='Playback speed multiplier (higher = slower, e.g., 2.0 = half speed)')

    args = parser.parse_args()

    # Create integrated system
    system = IntegratedMusicGestureSystem(
        args.model,
        args.port,
        enable_websocket=not args.no_visualization,
        ws_port=args.ws_port,
        enable_gesture=not args.no_gesture
    )

    # Load seed
    system.load_seed_sequence(args.seed)

    # Generate music with gesture control
    system.generate(
        num_notes=args.num_notes,
        temperature=args.temperature,
        velocity=args.velocity,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        speed=args.speed
    )


if __name__ == "__main__":
    main()
