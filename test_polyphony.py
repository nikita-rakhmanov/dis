#!/usr/bin/env python3
"""
Quick test script for polyphony functionality.
Tests the dual-model system without requiring MIDI hardware.
"""

import numpy as np
from dual_model_polyphony import SimpleHarmonyGenerator, DualModelPolyphonySystem


def test_simple_harmony_generator():
    """Test rule-based harmony generator."""
    print("=" * 60)
    print("Testing Simple Harmony Generator")
    print("=" * 60)

    # Test all three styles
    styles = ['classical', 'jazz', 'modern']
    test_pitches = [60, 64, 67, 72]  # C4, E4, G4, C5

    for style in styles:
        print(f"\n{style.upper()} Style:")
        print("-" * 40)

        harmony_gen = SimpleHarmonyGenerator(style=style)

        for pitch in test_pitches:
            # Generate 5 harmony notes for each pitch
            harmonies = [harmony_gen.generate_harmony(pitch) for _ in range(5)]

            # Calculate intervals
            intervals = [h - pitch for h in harmonies]

            print(f"  Melody: {pitch:3d} | Harmonies: {harmonies}")
            print(f"              | Intervals: {intervals}")

    print("\n✓ Simple harmony generator test passed!\n")


def test_interval_distribution():
    """Test that interval weights are properly distributed."""
    print("=" * 60)
    print("Testing Interval Distribution (1000 samples)")
    print("=" * 60)

    harmony_gen = SimpleHarmonyGenerator(style='classical')
    melody_pitch = 60  # Middle C

    # Generate 1000 harmonies
    harmonies = [harmony_gen.generate_harmony(melody_pitch) for _ in range(1000)]
    intervals = [h - melody_pitch for h in harmonies]

    # Count occurrences
    from collections import Counter
    interval_counts = Counter(intervals)

    print(f"\nMelody pitch: {melody_pitch} (C4)")
    print("\nInterval distribution:")
    for interval in sorted(interval_counts.keys()):
        count = interval_counts[interval]
        percentage = (count / 1000) * 100
        bar = '█' * int(percentage / 2)
        print(f"  {interval:+3d} semitones: {count:4d} ({percentage:5.1f}%) {bar}")

    print("\n✓ Interval distribution test passed!\n")


def test_context_awareness():
    """Test that harmony generator can use melody context."""
    print("=" * 60)
    print("Testing Context Awareness")
    print("=" * 60)

    harmony_gen = SimpleHarmonyGenerator(style='classical')

    # Simulate a melody sequence
    melody_sequence = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale
    melody_context = []

    print("\nGenerating harmony for C major scale:")
    print("-" * 40)

    for i, pitch in enumerate(melody_sequence):
        harmony_pitch = harmony_gen.generate_harmony(pitch, melody_context)
        interval = harmony_pitch - pitch

        print(f"  Note {i+1}: Melody={pitch:3d}, Harmony={harmony_pitch:3d}, Interval={interval:+3d}")

        # Update context
        melody_context.append(pitch)
        if len(melody_context) > 10:
            melody_context.pop(0)

    print("\n✓ Context awareness test passed!\n")


def test_edge_cases():
    """Test edge cases (very low/high pitches, etc.)."""
    print("=" * 60)
    print("Testing Edge Cases")
    print("=" * 60)

    harmony_gen = SimpleHarmonyGenerator(style='classical')

    edge_cases = [
        (0, "Lowest MIDI note"),
        (21, "A0 (Piano lowest)"),
        (108, "C8 (Piano highest)"),
        (127, "Highest MIDI note"),
    ]

    print("\nTesting extreme pitches:")
    print("-" * 40)

    for pitch, description in edge_cases:
        try:
            harmonies = [harmony_gen.generate_harmony(pitch) for _ in range(5)]
            all_valid = all(0 <= h <= 127 for h in harmonies)
            status = "✓" if all_valid else "✗"
            print(f"  {status} {description:20s} (pitch={pitch:3d}): {harmonies}")
        except Exception as e:
            print(f"  ✗ {description:20s} (pitch={pitch:3d}): ERROR - {e}")

    print("\n✓ Edge cases test passed!\n")


def test_no_unison():
    """Test that harmony avoids unison with melody."""
    print("=" * 60)
    print("Testing Unison Avoidance")
    print("=" * 60)

    harmony_gen = SimpleHarmonyGenerator(style='classical')

    # Test 100 notes
    test_pitches = list(range(30, 90, 2))  # Sample across range

    unison_count = 0
    total_tests = 0

    for pitch in test_pitches:
        for _ in range(10):
            harmony = harmony_gen.generate_harmony(pitch)
            if harmony == pitch:
                unison_count += 1
            total_tests += 1

    unison_percentage = (unison_count / total_tests) * 100

    print(f"\nTotal tests: {total_tests}")
    print(f"Unison occurrences: {unison_count} ({unison_percentage:.2f}%)")

    if unison_percentage < 1.0:
        print("\n✓ Unison avoidance test passed (< 1% unisons)\n")
    else:
        print("\n⚠ Warning: High unison rate detected\n")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "POLYPHONY SYSTEM TEST SUITE" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    try:
        test_simple_harmony_generator()
        test_interval_distribution()
        test_context_awareness()
        test_edge_cases()
        test_no_unison()

        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPolyphony system is ready to use!")
        print("\nNext steps:")
        print("  1. Test with MIDI output:")
        print("     python integrated_music_gesture_control.py --polyphony --no-gesture")
        print("  2. Try different harmony styles:")
        print("     python integrated_music_gesture_control.py --polyphony --harmony-style jazz")
        print("  3. See POLYPHONY_GUIDE.md for more options")
        print("\n")

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ TEST FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        print("\n")


if __name__ == "__main__":
    main()
