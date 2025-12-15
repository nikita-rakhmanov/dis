#!/usr/bin/env python3
"""
Standalone Visualization Test Script

Simulates note data and hand tracking without requiring the ML model or webcam.
Just run this script and open visualization.html in a browser.

Usage:
    python test_visualization.py
    python test_visualization.py --notes-per-second 2 --hand-speed 0.5
"""

import asyncio
import websockets
import json
import math
import random
import argparse
from datetime import datetime

# Default WebSocket port (same as the main system)
WS_PORT = 8765


class MockHandTracker:
    """Simulates hand movements for testing."""
    
    def __init__(self, speed=1.0):
        self.speed = speed
        self.start_time = None
        self.start_gesture_duration = 6.0  # Seconds to hold peace signs at start (increased for browser connect time)
    
    def get_hand_data(self, elapsed_time):
        """
        Generate mock hand positions.
        First 6 seconds: Both hands hold peace sign in center (to trigger start gesture)
        After: Left hand moves in circular pattern, right hand oscillates vertically
        """
        t = elapsed_time * self.speed
        
        # For first few seconds, hold peace signs in center to trigger start gesture
        # Increased to 6 seconds to ensure browser has time to connect
        if elapsed_time < self.start_gesture_duration:
            # Both hands centered with peace sign
            left_x = 0.5  # Exactly center
            left_y = 0.5
            right_x = 0.5  # Exactly center  
            right_y = 0.5
            left_gesture = 'Peace Sign'
            right_gesture = 'Peace Sign'
        else:
            # Normal animation after start gesture is complete
            adjusted_t = (elapsed_time - self.start_gesture_duration) * self.speed
            
            # Left hand - circular motion for filter/reverb control
            left_x = 0.3 + 0.15 * math.sin(adjusted_t * 0.7)
            left_y = 0.5 + 0.2 * math.cos(adjusted_t * 0.5)
            
            # Right hand - vertical oscillation for tempo control
            right_x = 0.7 + 0.05 * math.sin(adjusted_t * 0.3)
            right_y = 0.5 + 0.4 * math.sin(adjusted_t * 0.4)  # 0.1 to 0.9 range
            
            left_gesture = random.choice(['Open Palm', 'Closed Fist', 'Peace Sign', None])
            right_gesture = random.choice(['Open Palm', 'Closed Fist', 'Peace Sign', None])
        
        # Calculate derived values (matching real gesture controller)
        filter_cutoff = int(left_x * 127)
        reverb = int((1.0 - left_y) * 127)
        
        # Speed formula: 4.0 * (0.0625)^y_pos
        tempo_speed = 4.0 * pow(0.0625, max(0, min(1, right_y)))
        
        return {
            'type': 'hand_data',
            'left_hand': {
                'x': left_x,
                'y': left_y,
                'visible': True,
                'filter_cutoff': filter_cutoff,
                'reverb': reverb,
                'gesture': left_gesture
            },
            'right_hand': {
                'x': right_x,
                'y': right_y,
                'visible': True,
                'tempo_speed': round(tempo_speed, 2),
                'gesture': right_gesture
            },
            'timestamp': datetime.now().isoformat()
        }



class MockNoteGenerator:
    """Generates random musical notes for testing."""
    
    def __init__(self, notes_per_second=1.5):
        self.notes_per_second = notes_per_second
        self.note_index = 0
        self.last_pitch = 60  # Start at middle C
        
        # Musical scales for more pleasing random notes
        self.c_major = [0, 2, 4, 5, 7, 9, 11]  # C major scale intervals
    
    def get_note(self, tempo_speed=1.0):
        """Generate a random note with musical constraints."""
        
        # Random walk in a scale for more musical results
        step_direction = random.choice([-1, 0, 1, 1])  # Slight upward bias
        scale_step = random.randint(0, 6)
        
        base_pitch = 48 + self.c_major[scale_step]  # C3 to B3
        octave_offset = random.choice([0, 12, 24])  # Add octave variety
        pitch = base_pitch + octave_offset
        
        # Clamp to valid MIDI range
        pitch = max(36, min(96, pitch))
        
        velocity = random.randint(60, 120)
        duration = random.uniform(0.2, 0.8) / tempo_speed
        step = random.uniform(0.3, 0.7) / tempo_speed
        
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note_name = f"{note_names[pitch % 12]}{pitch // 12 - 1}"
        
        # Occasionally add harmony
        harmony_pitch = None
        harmony_name = None
        if random.random() > 0.6:  # 40% chance of harmony
            interval = random.choice([3, 4, 5, 7])  # Third, fourth, fifth, seventh
            harmony_pitch = pitch + interval
            if harmony_pitch <= 127:
                harmony_name = f"{note_names[harmony_pitch % 12]}{harmony_pitch // 12 - 1}"
        
        self.note_index += 1
        self.last_pitch = pitch
        
        note_data = {
            'type': 'note',
            'pitch': pitch,
            'step': round(step, 3),
            'duration': round(duration, 3),
            'velocity': velocity,
            'note_name': note_name,
            'timestamp': datetime.now().isoformat(),
            'index': self.note_index
        }
        
        if harmony_pitch:
            note_data['harmony_pitch'] = harmony_pitch
            note_data['harmony_name'] = harmony_name
        
        return note_data


class VisualizationTestServer:
    """WebSocket server for testing visualization."""
    
    def __init__(self, port=WS_PORT, notes_per_second=1.5, hand_speed=1.0):
        self.port = port
        self.clients = set()
        self.hand_tracker = MockHandTracker(speed=hand_speed)
        self.note_generator = MockNoteGenerator(notes_per_second=notes_per_second)
        self.notes_per_second = notes_per_second
        self.running = False
    
    async def handler(self, websocket):
        """Handle WebSocket connections."""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'
        print(f"[OK] Visualization client connected from {client_ip}")
        print(f"  Total clients: {len(self.clients)}")
        
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print(f"[--] Client disconnected. Remaining: {len(self.clients)}")
    
    async def broadcast(self, message):
        """Send message to all connected clients."""
        if self.clients:
            data = json.dumps(message)
            await asyncio.gather(
                *[client.send(data) for client in self.clients],
                return_exceptions=True
            )
    
    async def data_generator(self):
        """Generate and broadcast mock data continuously."""
        last_note_time = None
        note_interval = 1.0 / self.notes_per_second
        hand_interval = 0.05  # 20Hz hand updates
        last_hand_time = 0
        
        print("\nWaiting for visualization client to connect...")
        print("Open visualization.html in your browser\n")
        
        # Wait for first client to connect
        while not self.clients and self.running:
            await asyncio.sleep(0.1)
        
        if not self.running:
            return
            
        print("[OK] Client connected! Starting peace sign phase...")
        print(f"Hold PEACE SIGN for {self.hand_tracker.start_gesture_duration}s")
        print("(Both hands centered with peace sign)\n")
        
        # NOW start the timer after client connected
        start_time = asyncio.get_event_loop().time()
        self.hand_tracker.start_time = start_time
        last_note_time = start_time
        last_hand_time = start_time
        startup_complete_printed = False
        
        while self.running:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time
            
            # Print startup phase progress
            if elapsed < self.hand_tracker.start_gesture_duration:
                remaining = self.hand_tracker.start_gesture_duration - elapsed
                # Print once per second roughly
                if int(remaining * 2) != int((remaining + 0.05) * 2):
                    print(f"Peace sign phase: {remaining:.1f}s remaining...")
            elif not startup_complete_printed:
                print("Startup complete! Switching to normal mode.\n")
                startup_complete_printed = True
            
            # Broadcast hand data at 20Hz
            if current_time - last_hand_time >= hand_interval:
                hand_data = self.hand_tracker.get_hand_data(elapsed)
                await self.broadcast(hand_data)
                last_hand_time = current_time
                
                # Get current tempo for note timing
                tempo_speed = hand_data['right_hand']['tempo_speed']
            else:
                tempo_speed = 1.0
            
            # Broadcast note data at configured rate
            if current_time - last_note_time >= note_interval:
                note_data = self.note_generator.get_note(tempo_speed)
                await self.broadcast(note_data)
                
                # Print note info
                harmony_info = ""
                if 'harmony_pitch' in note_data:
                    harmony_info = f" +{note_data['harmony_name']}"
                print(f"Note {note_data['index']:3d}: {note_data['note_name']}{harmony_info} "
                      f"| pitch={note_data['pitch']} vel={note_data['velocity']} "
                      f"| speed={tempo_speed:.2f}x")
                
                last_note_time = current_time
            
            await asyncio.sleep(0.01)  # Small sleep to prevent busy loop
    
    async def run(self):
        """Start the server and data generator."""
        self.running = True
        
        async with websockets.serve(self.handler, "0.0.0.0", self.port):
            print("=" * 60)
            print("VISUALIZATION TEST SERVER")
            print("=" * 60)
            print(f"WebSocket server running on ws://localhost:{self.port}")
            print(f"\nOpen visualization.html in your browser")
            print("=" * 60)
            
            try:
                await self.data_generator()
            except asyncio.CancelledError:
                print("\nShutting down...")
            finally:
                self.running = False


def main():
    parser = argparse.ArgumentParser(
        description='Test visualization with mock data (no ML model needed)'
    )
    parser.add_argument('--port', type=int, default=WS_PORT,
                       help=f'WebSocket port (default: {WS_PORT})')
    parser.add_argument('--notes-per-second', type=float, default=1.5,
                       help='Rate of note generation (default: 1.5)')
    parser.add_argument('--hand-speed', type=float, default=1.0,
                       help='Speed of simulated hand movements (default: 1.0)')
    args = parser.parse_args()
    
    server = VisualizationTestServer(
        port=args.port,
        notes_per_second=args.notes_per_second,
        hand_speed=args.hand_speed
    )
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nServer stopped")


if __name__ == "__main__":
    main()
