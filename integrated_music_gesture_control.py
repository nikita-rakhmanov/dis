#!/usr/bin/env python3
"""
Integrated Music Generation with Gesture Control

"""

import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

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

from gesture_control.hand_tracker import HandTracker
from dual_model_polyphony import DualModelPolyphonySystem

SEQUENCE_LENGTH = 50
VOCAB_SIZE = 128
KEY_ORDER = ['pitch', 'step', 'duration']


def mse_with_positive_pressure(y_true, y_pred):
    """Custom loss function needed for model loading."""
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)


class GestureMIDIController:
    """Maps hand tracking data to MIDI CC messages for effects control."""

    CC_FILTER_CUTOFF = 74
    CC_RESONANCE = 71
    CC_REVERB = 91
    CC_CHORUS = 93
    CC_MODULATION = 1
    CC_EXPRESSION = 11
    CC_ARPEGGIATOR_RATE = 14  # For controlling Ableton arpeggiator rate

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

        # Left hand position buffers (for MIDI effects)
        self.position_buffer_x = deque(maxlen=5)
        self.position_buffer_y = deque(maxlen=5)
        
        # Right hand position buffers (for tempo control)
        self.right_hand_buffer_y = deque(maxlen=8)  # More smoothing for tempo
        
        # Speed control state
        self.current_speed = 1.0
        self.min_speed = 0.125  # 8x slower at bottom
        self.max_speed = 8.0    # 8x faster at top

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
        """Send MIDI CC message with duplicate suppression."""
        key = (cc_number, channel)
        if key in self.last_cc_values:
            if abs(self.last_cc_values[key] - value) < 2:
                return

        self.last_cc_values[key] = value

        with self.midi_lock:
            msg = Message('control_change', control=cc_number, value=value, channel=channel)
            self.midi_out.send(msg)

    def process_hand_data(self, hand_landmarks, hand_label, gesture):
        """Process hand tracking data and send appropriate MIDI CC messages."""
        wrist = hand_landmarks[0]
        index_tip = hand_landmarks[8]
        thumb_tip = hand_landmarks[4]

        x_pos = self.smooth_value(self.position_buffer_x, index_tip.x)
        y_pos = self.smooth_value(self.position_buffer_y, index_tip.y)

        # Map filter cutoff to peak at center (x=0.5), minimum at edges
        # Distance from center: 0 at center, 0.5 at edges
        # Filter value: 1.0 at center, 0.0 at edges
        center_proximity = 1.0 - abs(0.5 - x_pos) * 2.0
        cutoff_value = self.normalize_to_midi(center_proximity, 0.0, 1.0)
        self.send_cc(self.CC_FILTER_CUTOFF, cutoff_value)

        reverb_value = self.normalize_to_midi(1.0 - y_pos, 0.0, 1.0)
        self.send_cc(self.CC_REVERB, reverb_value)

        distance = np.sqrt((thumb_tip.x - index_tip.x)**2 +
                          (thumb_tip.y - index_tip.y)**2)
        resonance_value = self.normalize_to_midi(distance, 0.0, 0.3)
        self.send_cc(self.CC_RESONANCE, resonance_value)

        if gesture == "Open Palm":
            self.send_cc(self.CC_CHORUS, 127)
        elif gesture == "Closed Fist":
            self.send_cc(self.CC_CHORUS, 0)
            self.send_cc(self.CC_MODULATION, 0)
        elif gesture == "Peace Sign":
            self.send_cc(self.CC_MODULATION, 64)
        elif gesture == "Rock On":
            self.send_cc(self.CC_MODULATION, 127)

    def process_right_hand_data(self, hand_landmarks):
        """
        Process right hand tracking data for tempo/speed control and arpeggiator rate.
        
        Hand position Y controls speed and arpeggiator rate:
        - Top (y=0.0) = 4x faster, arpeggiator rate CC = 127 (fastest)
        - Middle (y=0.5) = normal speed, arpeggiator rate CC = 64
        - Bottom (y=1.0) = 0.25x (4x slower), arpeggiator rate CC = 0 (slowest)
        """
        index_tip = hand_landmarks[8]
        
        # Smooth the Y position
        self.right_hand_buffer_y.append(index_tip.y)
        y_pos = sum(self.right_hand_buffer_y) / len(self.right_hand_buffer_y)
        
        # Clamp Y to 0-1 range
        y_pos = max(0.0, min(1.0, y_pos))
        
        # Exponential mapping for symmetric feel:
        # y=0 -> speed=4.0, y=0.5 -> speed=1.0, y=1.0 -> speed=0.25
        # Formula: speed = max_speed * (min_speed/max_speed)^y
        # = 4.0 * (0.25/4.0)^y = 4.0 * (0.0625)^y
        self.current_speed = self.max_speed * pow(self.min_speed / self.max_speed, y_pos)
        
        # Send arpeggiator rate CC: hand up = 127 (fast), hand down = 0 (slow)
        # Inverted from y_pos since y=0 is top of frame (hand up)
        arp_rate_value = self.normalize_to_midi(1.0 - y_pos, 0.0, 1.0)
        self.send_cc(self.CC_ARPEGGIATOR_RATE, arp_rate_value)
        
        return self.current_speed


class IntegratedMusicGestureSystem:
    """Integrates MIDI generation with gesture control."""

    def __init__(self, model_path, midi_port_name=None, enable_websocket=True,
                 ws_port=8765, enable_gesture=True, enable_polyphony=False,
                 harmony_style='classical', harmony_mode='simple', harmony_model_path=None):
        """
        Initialize the integrated system.

        Args:
            model_path: Path to trained RNN model
            midi_port_name: MIDI output port name (interactive if None)
            enable_websocket: Enable WebSocket visualization
            ws_port: WebSocket port number
            enable_gesture: Enable gesture control
            enable_polyphony: Enable dual-model polyphony (2-voice)
            harmony_style: Harmony style for polyphony ('classical', 'jazz', 'modern')
            harmony_mode: Harmony generation mode ('simple', 'learned')
            harmony_model_path: Path to trained harmony model
        """
        # Load model
        print(f"Loading model from {model_path}...")
        self.model = tf.keras.models.load_model(
            model_path,
            custom_objects={'mse_with_positive_pressure': mse_with_positive_pressure}
        )
        print("Model loaded successfully!\n")

        self._setup_midi(midi_port_name)

        self.seq_length = SEQUENCE_LENGTH
        self.vocab_size = VOCAB_SIZE
        self.current_notes = None
        self.prev_start = 0

        self.enable_websocket = enable_websocket
        self.ws_port = ws_port
        self.ws_clients = set()
        self.ws_server = None
        self.ws_loop = None

        self.enable_gesture = enable_gesture
        self.gesture_controller = None
        self.hand_tracker = None
        self.gesture_thread = None
        self.gesture_running = False

        if self.enable_gesture:
            self.gesture_controller = GestureMIDIController(self.midi_out)
            self.hand_tracker = HandTracker(max_hands=2)  # Enable both hands
            print("✓ Gesture control initialized (2-hand tracking)")
            print("  Left hand: MIDI effects | Right hand: Tempo control\n")

        # Start gesture detection state
        self.start_gesture_completed = False
        self.start_gesture_hold_start = None
        self.start_gesture_hold_time = 1.5  # seconds to hold peace signs

        # Polyphony setup
        self.enable_polyphony = enable_polyphony
        self.polyphony_system = None

        if self.enable_polyphony:
            self.polyphony_system = DualModelPolyphonySystem(
                melody_generator=self,
                harmony_mode=harmony_mode,
                harmony_model_path=harmony_model_path,
                harmony_style=harmony_style
            )
            print(f"✓ Polyphony enabled (2-voice, Mode: {harmony_mode}, Style: {harmony_style})\n")

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
        print(f"Visualization client connected from {client_ip}")
        try:
            await websocket.wait_closed()
        finally:
            self.ws_clients.remove(websocket)
            print(f"Visualization client disconnected")

    async def broadcast_note(self, note_data):
        """Broadcast note data to WebSocket clients."""
        if self.ws_clients:
            message = json.dumps(note_data)
            await asyncio.gather(
                *[client.send(message) for client in self.ws_clients],
                return_exceptions=True
            )

    def broadcast_hand_data(self, left_hand=None, right_hand=None):
        """Broadcast hand tracking data to WebSocket clients for visualization."""
        if not self.ws_clients or not self.ws_loop:
            return
        
        hand_data = {
            'type': 'hand_data',
            'left_hand': left_hand,
            'right_hand': right_hand,
            'timestamp': datetime.now().isoformat()
        }
        
        message = json.dumps(hand_data)
        for client in list(self.ws_clients):
            try:
                asyncio.run_coroutine_threadsafe(
                    client.send(message),
                    self.ws_loop
                )
            except Exception:
                pass

    def start_websocket_server(self):
        """Start WebSocket server in background thread."""
        if not self.enable_websocket:
            return

        def run_ws_server():
            self.ws_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ws_loop)

            async def server():
                async with websockets.serve(self.ws_handler, "0.0.0.0", self.ws_port):
                    print(f"WebSocket server started on ws://localhost:{self.ws_port}")
                    await asyncio.Future()

            self.ws_loop.run_until_complete(server())

        ws_thread = threading.Thread(target=run_ws_server, daemon=True)
        ws_thread.start()
        time.sleep(0.5)

    def gesture_control_loop(self):
        """Run hand tracking and send MIDI CC in separate thread."""
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Could not open webcam for gesture control")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        print("Initializing gesture control camera...")
        time.sleep(1.0)

        for i in range(5):
            ret, _ = cap.read()
            if not ret:
                print(f"Warning: Camera warmup frame {i+1}/5 failed")

        print("Gesture control started (webcam active)")
        print("Hand position controls Filter (X) and Reverb (Y)")
        print("Gestures: Open Palm, Closed Fist, Peace, Rock On")
        print()

        frame_interval = 1.0 / self.gesture_controller.update_rate
        last_update = time.time()

        while self.gesture_running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            results, _ = self.hand_tracker.process_frame(frame)

            current_time = time.time()
            if current_time - last_update >= frame_interval:
                # Track hand data for visualization
                left_hand_data = None
                right_hand_data = None
                
                if results.multi_hand_landmarks:
                    for hand_landmarks, handedness in zip(
                        results.multi_hand_landmarks,
                        results.multi_handedness
                    ):
                        hand_label = handedness.classification[0].label
                        # Get index finger tip position (landmark 8)
                        index_tip = hand_landmarks.landmark[8]
                        
                        if hand_label == "Left":
                            # Left hand controls MIDI effects
                            gesture = self.hand_tracker.recognize_gesture(
                                hand_landmarks.landmark, hand_label
                            )
                            self.gesture_controller.process_hand_data(
                                hand_landmarks.landmark,
                                hand_label,
                                gesture
                            )
                            # Collect for visualization
                            left_hand_data = {
                                'x': index_tip.x,
                                'y': index_tip.y,
                                'visible': True,
                                'filter_cutoff': self.gesture_controller.last_cc_values.get(74, 64),
                                'reverb': self.gesture_controller.last_cc_values.get(91, 64),
                                'gesture': gesture
                            }
                        elif hand_label == "Right":
                            # Right hand controls tempo/speed
                            speed = self.gesture_controller.process_right_hand_data(
                                hand_landmarks.landmark
                            )
                            # Get gesture for right hand too
                            right_gesture = self.hand_tracker.recognize_gesture(
                                hand_landmarks.landmark, hand_label
                            )
                            # Collect for visualization
                            right_hand_data = {
                                'x': index_tip.x,
                                'y': index_tip.y,
                                'visible': True,
                                'tempo_speed': round(speed, 2),
                                'gesture': right_gesture
                            }

                # Check for start gesture (both hands peace sign in center)
                if not self.start_gesture_completed:
                    left_ready = (left_hand_data and 
                                  left_hand_data.get('gesture') == 'Peace Sign' and
                                  0.25 <= left_hand_data.get('x', 0) <= 0.75)
                    right_ready = (right_hand_data and 
                                   right_hand_data.get('gesture') == 'Peace Sign' and
                                   0.25 <= right_hand_data.get('x', 0) <= 0.75)
                    
                    if left_ready and right_ready:
                        if self.start_gesture_hold_start is None:
                            self.start_gesture_hold_start = time.time()
                        elif time.time() - self.start_gesture_hold_start >= self.start_gesture_hold_time:
                            self.start_gesture_completed = True
                            print("\n✓ Start gesture detected! Music generation starting...\n")
                    else:
                        self.start_gesture_hold_start = None

                # Broadcast hand data to visualization
                if self.enable_websocket and (left_hand_data or right_hand_data):
                    self.broadcast_hand_data(left_hand_data, right_hand_data)
                    
                last_update = current_time

        cap.release()
        self.hand_tracker.release()
        print("Gesture control stopped")

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

        print("Waiting for gesture control to initialize...")
        time.sleep(3.0)

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
        self.start_websocket_server()
        self.start_gesture_control()
        
        # Store base speed for fallback when no gesture
        self.base_speed = speed

        print("\n" + "=" * 70)
        print(f"🎵 INTEGRATED MUSIC GENERATION WITH GESTURE CONTROL")
        print("=" * 70)
        print(f"Temperature: {temperature} | Velocity: {velocity} | Base Speed: {speed}x")
        if self.enable_polyphony:
            print(f"Polyphony: 2-VOICE ENABLED")
        print("Gesture Control: ACTIVE")
        print("  → Left hand: MIDI effects | Right hand: Tempo + Arp Rate CC14 (up=fast, down=slow)")
        if self.enable_gesture:
            print("\n✋ Waiting for START GESTURE: Both hands Peace Sign ✌️ in center area...")
        print("Press Ctrl+C to stop")
        print("=" * 70 + "\n")

        # Wait for start gesture before generating music
        if self.enable_gesture:
            while not self.start_gesture_completed and self.gesture_running:
                time.sleep(0.1)

        count = 0
        try:
            while num_notes is None or count < num_notes:
                # Get effective speed (gesture-controlled or base)
                if self.enable_gesture and self.gesture_controller:
                    effective_speed = self.gesture_controller.current_speed
                else:
                    effective_speed = self.base_speed
                
                if self.enable_polyphony:
                    # POLYPHONIC MODE: Generate melody + harmony
                    melody_note, harmony_note = self.polyphony_system.predict_next_notes(temperature)
                    pitch, step, duration = melody_note
                    harmony_pitch, harmony_step, harmony_duration = harmony_note

                    # Clamp durations
                    duration = max(min_duration, min(max_duration, duration))
                    harmony_duration = max(min_duration, min(max_duration, harmony_duration))

                    # Apply BASE speed multiplier first (from --speed argument)
                    # Then gesture control adjusts within this base
                    base_multiplier = speed  # This is the --speed argument
                    step_base = step * base_multiplier
                    duration_base = duration * base_multiplier
                    harmony_duration_base = harmony_duration * base_multiplier
                    
                    # Apply gesture-controlled speed on top of base
                    # effective_speed: hand up (y=0) = 4x, middle = 1x, down = 0.25x
                    # We DIVIDE by speed so: hand up = faster (shorter notes), hand down = slower (longer notes)
                    # Base of 4s / effective_speed: 4s/4 = 1s (hand up), 4s/1 = 4s (middle), 4s/0.25 = 16s (hand down)
                    base_duration = 4.0  # 4 second baseline
                    duration_adjusted = base_duration / effective_speed
                    step_adjusted = step_base / effective_speed  # Step also scales with speed
                    harmony_duration_adjusted = base_duration / effective_speed

                    # Display
                    note_name = self._pitch_to_name(pitch)
                    harmony_name = self._pitch_to_name(harmony_pitch)
                    print(f"Note {count+1:4d}: {note_name:4s}+{harmony_name:4s} "
                          f"(melody={pitch:3d}, harmony={harmony_pitch:3d}) "
                          f"step={step_adjusted:5.3f}s dur={duration_adjusted:5.3f}s "
                          f"speed={effective_speed:.2f}x")

                    # Broadcast to visualization (melody)
                    note_data = {
                        'type': 'note',
                        'pitch': int(pitch),
                        'step': float(step_adjusted),
                        'duration': float(duration_adjusted),
                        'velocity': int(velocity),
                        'note_name': note_name,
                        'timestamp': datetime.now().isoformat(),
                        'index': count,
                        'harmony_pitch': int(harmony_pitch),
                        'harmony_name': harmony_name
                    }
                    self.send_to_visualization(note_data)

                    # Play both notes simultaneously
                    self.polyphony_system.play_notes(
                        (pitch, step_adjusted, duration_adjusted),
                        (harmony_pitch, harmony_step, harmony_duration_adjusted),
                        velocity
                    )

                    # Update sequence (melody only)
                    self.update_sequence(pitch, step, duration)
                    self.prev_start += step

                else:
                    # MONOPHONIC MODE: Original single-note generation
                    pitch, step, duration = self.predict_next_note(temperature)
                    duration = max(min_duration, min(max_duration, duration))

                    # Apply BASE speed multiplier first (from --speed argument)
                    base_multiplier = speed
                    step_base = step * base_multiplier
                    duration_base = duration * base_multiplier
                    
                    # Apply gesture-controlled speed on top of base
                    # hand up = faster (shorter notes), hand down = slower (longer notes)
                    base_duration = 4.0  # 4 second baseline
                    duration_adjusted = base_duration / effective_speed
                    step_adjusted = step_base / effective_speed

                    # Display
                    note_name = self._pitch_to_name(pitch)
                    print(f"Note {count+1:4d}: {note_name:4s} (pitch={pitch:3d}) "
                          f"step={step_adjusted:5.3f}s dur={duration_adjusted:5.3f}s "
                          f"speed={effective_speed:.2f}x")

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

                    # Play note
                    self.play_note(pitch, duration_adjusted, velocity)

                    # Update sequence
                    self.update_sequence(pitch, step, duration)
                    self.prev_start += step

                count += 1

        except KeyboardInterrupt:
            print("\n" + "=" * 70)
            print("Stopping...")
        finally:
            self.stop_gesture_control()

            for note in range(128):
                self.midi_out.send(Message('note_off', note=note, velocity=0))

            for cc in [1, 11, 14, 71, 74, 91, 93]:
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
    parser.add_argument('--speed', type=float, default=4.0,
                       help='Playback speed multiplier (higher = slower, default: 4.0)')
    parser.add_argument('--polyphony', action='store_true',
                       help='Enable 2-voice polyphony (melody + harmony)')
    parser.add_argument('--harmony-style', default='classical',
                       choices=['classical', 'jazz', 'modern'],
                       help='Harmony style for polyphony mode')

    parser.add_argument('--harmony-mode', default='simple',
                       choices=['simple', 'learned'],
                       help="Harmony generation mode: 'simple' (rule-based) or 'learned' (neural network)")
    parser.add_argument('--harmony-model', default='harmony_model.keras',
                       help='Path to trained harmony model (for learned mode)')

    args = parser.parse_args()

    # Auto-switch to learned mode if model exists and mode not explicitly set (optional, but safer to be explicit)
    # For now, we respect the default 'simple' unless user changes it.

    system = IntegratedMusicGestureSystem(
        args.model,
        args.port,
        enable_websocket=not args.no_visualization,
        ws_port=args.ws_port,
        enable_gesture=not args.no_gesture,
        enable_polyphony=args.polyphony,
        harmony_style=args.harmony_style,
        harmony_mode=args.harmony_mode,
        harmony_model_path=args.harmony_model
    )

    system.load_seed_sequence(args.seed)

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
