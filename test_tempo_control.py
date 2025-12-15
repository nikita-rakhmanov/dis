#!/usr/bin/env python3
"""
Test script to simulate right hand tempo control without webcam.
Simulates hand moving up and down to change tempo.
"""

import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import time
import math
import argparse

from integrated_music_gesture_control import IntegratedMusicGestureSystem, GestureMIDIController


def simulate_hand_movement(system, num_notes=50, cycle_duration=10.0):
    """
    Simulate hand movement and test tempo control.
    Hand position oscillates between top (fast) and bottom (slow).
    """
    print("\n" + "=" * 70)
    print("🧪 TEMPO CONTROL TEST - Simulating hand movement")
    print("=" * 70)
    print(f"Hand position will cycle up/down over {cycle_duration}s")
    print("Watch the step/duration times change!")
    print("=" * 70 + "\n")
    
    # Get the gesture controller
    controller = system.gesture_controller
    
    # Start websocket for visualization
    system.start_websocket_server()
    
    start_time = time.time()
    count = 0
    
    try:
        while count < num_notes:
            elapsed = time.time() - start_time
            
            # Simulate hand Y position (0=top/fast, 1=bottom/slow)
            # Oscillates using sine wave
            y_position = (math.sin(elapsed * 2 * math.pi / cycle_duration) + 1) / 2
            
            # Calculate speed using the same formula as the real gesture controller
            speed = controller.max_speed * pow(controller.min_speed / controller.max_speed, y_position)
            controller.current_speed = speed
            
            # Generate a note
            pitch, step, duration = system.predict_next_note(temperature=2.0)
            duration = max(0.1, min(2.0, duration))
            
            # Apply speed
            step_adjusted = step * speed
            duration_adjusted = duration * speed
            
            # Display with hand position indicator
            hand_indicator = "🔼" if y_position < 0.3 else ("🔽" if y_position > 0.7 else "➡️")
            note_name = system._pitch_to_name(pitch)
            
            print(f"♪ {count+1:3d}: {note_name:4s} | Hand Y: {y_position:.2f} {hand_indicator} | "
                  f"Speed: {speed:.2f}x | step={step_adjusted:.3f}s dur={duration_adjusted:.3f}s")
            
            # Play the note
            system.play_note(pitch, duration_adjusted, velocity=80)
            
            # Send to visualization
            note_data = {
                'type': 'note',
                'pitch': int(pitch),
                'step': float(step_adjusted),
                'duration': float(duration_adjusted),
                'velocity': 80,
                'note_name': note_name,
            }
            system.send_to_visualization(note_data)
            
            # Update sequence
            system.update_sequence(pitch, step, duration)
            
            # Wait
            time.sleep(step_adjusted)
            count += 1
            
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    
    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Test tempo control with simulated hand movement')
    parser.add_argument('--num-notes', type=int, default=50, help='Number of notes to generate')
    parser.add_argument('--cycle', type=float, default=10.0, help='Hand movement cycle duration in seconds')
    args = parser.parse_args()
    
    print("Loading model and setting up MIDI...")
    
    # Create system WITHOUT gesture control (we'll simulate it)
    system = IntegratedMusicGestureSystem(
        model_path='music_rnn_model.keras',
        enable_gesture=False,  # We'll control speed manually
        enable_polyphony=False
    )
    
    # Load seed sequence (required for note prediction)
    system.load_seed_sequence()
    
    # But we need a gesture controller for speed calculation
    system.gesture_controller = GestureMIDIController(system.midi_out)
    
    simulate_hand_movement(system, args.num_notes, args.cycle)
    
    # Cleanup
    system.stop_websocket_server()
    system.midi_out.close()
    print("✓ MIDI port closed")


if __name__ == "__main__":
    main()
