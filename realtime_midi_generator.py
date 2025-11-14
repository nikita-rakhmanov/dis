#!/usr/bin/env python3
"""
Real-time MIDI music generator using a trained RNN model.
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

SEQUENCE_LENGTH = 50
VOCAB_SIZE = 128
KEY_ORDER = ['pitch', 'step', 'duration']


def mse_with_positive_pressure(y_true, y_pred):
    """Custom loss function needed for model loading."""
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)


class RealtimeMusicGenerator:
    """Generate and play music in real-time via MIDI."""

    def __init__(self, model_path, midi_port_name=None, enable_websocket=True, ws_port=8765):
        print(f"Loading model from {model_path}...")
        self.model = tf.keras.models.load_model(
            model_path,
            custom_objects={'mse_with_positive_pressure': mse_with_positive_pressure}
        )
        print("✓ Model loaded successfully!\n")

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

        if available_ports:
            try:
                idx = int(input("\nSelect port number (or press Enter to create virtual): ").strip() or -1)
                if 0 <= idx < len(available_ports):
                    self.midi_out = mido.open_output(available_ports[idx])
                    print(f"✓ Connected to: {available_ports[idx]}\n")
                    return
            except:
                pass

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
        print(f"🌐 Visualization client connected from {client_ip} (total: {len(self.ws_clients)})")
        try:
            await websocket.wait_closed()
        finally:
            self.ws_clients.remove(websocket)
            print(f"🌐 Visualization client disconnected (total: {len(self.ws_clients)})")

    async def broadcast_note(self, note_data):
        """Broadcast note data to all connected WebSocket clients."""
        if self.ws_clients:
            message = json.dumps(note_data)
            await asyncio.gather(
                *[client.send(message) for client in self.ws_clients],
                return_exceptions=True
            )

    def start_websocket_server(self):
        """Start WebSocket server in a background thread."""
        if not self.enable_websocket:
            return

        def run_ws_server():
            self.ws_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ws_loop)

            async def server():
                async with websockets.serve(self.ws_handler, "0.0.0.0", self.ws_port):
                    print(f"🌐 WebSocket server started on ws://localhost:{self.ws_port}")
                    print("   Open visualization.html in your browser to see the 3D visualization\n")
                    await asyncio.Future()

            self.ws_loop.run_until_complete(server())

        ws_thread = threading.Thread(target=run_ws_server, daemon=True)
        ws_thread.start()
        time.sleep(0.5)

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
        """Send MIDI note on/off."""
        pitch = max(0, min(127, pitch))
        velocity = max(0, min(127, velocity))
        
        self.midi_out.send(Message('note_on', note=pitch, velocity=velocity))
        time.sleep(duration)
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
        """Send note data to visualization via WebSocket."""
        if self.enable_websocket and self.ws_loop and self.ws_clients:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_note(note_data),
                self.ws_loop
            )

    def generate(self, num_notes=None, temperature=2.0, velocity=80,
                 min_duration=0.1, max_duration=2.0):
        """Generate and play notes in real-time."""
        self.start_websocket_server()

        print("\n" + "=" * 60)
        print(f"Starting generation (temperature={temperature}, velocity={velocity})")
        print("Press Ctrl+C to stop")
        print("=" * 60 + "\n")

        count = 0
        try:
            while num_notes is None or count < num_notes:
                pitch, step, duration = self.predict_next_note(temperature)
                duration = max(min_duration, min(max_duration, duration))

                note_name = self._pitch_to_name(pitch)
                print(f"♪ {count+1:4d}: {note_name:4s} (pitch={pitch:3d}) "
                      f"step={step:5.3f}s dur={duration:5.3f}s")

                note_data = {
                    'type': 'note',
                    'pitch': int(pitch),
                    'step': float(step),
                    'duration': float(duration),
                    'velocity': int(velocity),
                    'note_name': note_name,
                    'timestamp': datetime.now().isoformat(),
                    'index': count
                }
                self.send_to_visualization(note_data)

                self.play_note(pitch, duration, velocity)

                self.update_sequence(pitch, step, duration)
                self.prev_start += step
                count += 1

        except KeyboardInterrupt:
            print("\n" + "=" * 60)
            print("Stopping...")
        finally:
            for note in range(128):
                self.midi_out.send(Message('note_off', note=note, velocity=0))
            self.midi_out.close()
            print("✓ MIDI port closed")
            print("=" * 60)
    
    @staticmethod
    def _pitch_to_name(pitch):
        """Convert MIDI pitch to note name."""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return f"{notes[pitch % 12]}{pitch // 12 - 1}"


def main():
    parser = argparse.ArgumentParser(description='Real-time MIDI music generator with 3D visualization')
    parser.add_argument('--model', default='music_rnn_model.keras',
                        help='Path to trained model')
    parser.add_argument('--seed', default='seed_sequence.npy',
                        help='Path to seed sequence (optional)')
    parser.add_argument('--port', default=None,
                        help='MIDI port name (interactive if not specified)')
    parser.add_argument('--temperature', type=float, default=2.0,
                        help='Sampling temperature (higher = more random)')
    parser.add_argument('--velocity', type=int, default=80,
                        help='MIDI velocity (0-127)')
    parser.add_argument('--num-notes', type=int, default=None,
                        help='Number of notes to generate (infinite if not set)')
    parser.add_argument('--min-duration', type=float, default=0.1,
                        help='Minimum note duration in seconds')
    parser.add_argument('--max-duration', type=float, default=2.0,
                        help='Maximum note duration in seconds')
    parser.add_argument('--no-visualization', action='store_true',
                        help='Disable WebSocket server for visualization')
    parser.add_argument('--ws-port', type=int, default=8765,
                        help='WebSocket port for visualization (default: 8765)')

    args = parser.parse_args()

    generator = RealtimeMusicGenerator(
        args.model,
        args.port,
        enable_websocket=not args.no_visualization,
        ws_port=args.ws_port
    )

    generator.load_seed_sequence(args.seed)

    generator.generate(
        num_notes=args.num_notes,
        temperature=args.temperature,
        velocity=args.velocity,
        min_duration=args.min_duration,
        max_duration=args.max_duration
    )


if __name__ == "__main__":
    main()