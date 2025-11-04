#!/usr/bin/env python3
"""
MIDI CC Mapping Assistant for Ableton Live

This script helps you map MIDI CC parameters ONE AT A TIME in your DAW.
It sends only the CC you're currently mapping, preventing interference
from other hand movements.

Perfect for setting up MIDI Learn in Ableton without confusion!
"""

import mido
import time
import sys

class MappingAssistant:
    """Interactive MIDI CC mapping helper."""

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
        self.midi_out = mido.open_output('Gesture Control Mapper', virtual=True)
        print("✓ Virtual port 'Gesture Control Mapper' created\n")

    def send_cc(self, cc_number, value, channel=0):
        """Send MIDI CC message."""
        value = max(0, min(127, value))
        msg = mido.Message('control_change', control=cc_number, value=value, channel=channel)
        self.midi_out.send(msg)

    def sweep_cc(self, cc_number, cc_name, duration=3.0, repetitions=2):
        """Sweep a single CC from 0 to 127 and back."""
        print(f"\n{'='*70}")
        print(f"Mapping: {cc_name} (CC {cc_number})")
        print(f"{'='*70}")
        print(f"\n📍 ONLY CC {cc_number} will be sent - no interference from other CCs!")
        print(f"\nInstructions:")
        print(f"  1. In Ableton, press Cmd+M (Mac) or Ctrl+M (Win) to enter MIDI Mapping")
        print(f"  2. Click the parameter you want to map to {cc_name}")
        print(f"  3. Press Enter here to start the sweep")
        print(f"  4. Ableton will auto-detect CC {cc_number}")
        print(f"  5. Press Cmd+M / Ctrl+M again to exit MIDI Mapping mode")

        input("\n▶ Press ENTER when ready to start sweep...")

        print(f"\n🎛️  Sweeping CC {cc_number} ({cc_name})...")

        for rep in range(repetitions):
            print(f"\n  Sweep {rep + 1}/{repetitions}:")

            # Sweep up: 0 → 127
            print("    0 → 127...", end='', flush=True)
            for value in range(0, 128, 2):
                self.send_cc(cc_number, value)
                time.sleep(duration / 128)

            # Sweep down: 127 → 0
            print(" 127 → 0...", end='', flush=True)
            for value in range(127, -1, -2):
                self.send_cc(cc_number, value)
                time.sleep(duration / 128)
            print(" Done!")

        # Reset to middle
        self.send_cc(cc_number, 64)

        print(f"\n✓ CC {cc_number} mapping complete!")
        print(f"  The parameter should now show 'MIDI' indicator in Ableton")

        confirm = input("\n  Was the mapping successful? (Y/n): ").strip().lower()
        if confirm and confirm != 'y':
            print("  💡 Try again - make sure MIDI Mapping mode is active!")
            retry = input("  Retry this mapping? (Y/n): ").strip().lower()
            if not retry or retry == 'y':
                self.sweep_cc(cc_number, cc_name, duration, repetitions)

    def run_mapping_wizard(self):
        """Interactive mapping wizard for all CCs."""
        print("\n" + "="*70)
        print("🎛️  ABLETON LIVE - MIDI CC MAPPING WIZARD")
        print("="*70)
        print("\nThis wizard will help you map each CC parameter ONE AT A TIME.")
        print("No interference, no confusion - just clean MIDI mapping!")
        print("\n" + "="*70)

        input("\nPress ENTER to start the mapping wizard...")

        mappings = [
            (self.CC_FILTER_CUTOFF, "Filter Cutoff",
             "Map this to: Auto Filter → Frequency"),
            (self.CC_RESONANCE, "Filter Resonance",
             "Map this to: Auto Filter → Resonance"),
            (self.CC_REVERB, "Reverb/Delay Level",
             "Map this to: Reverb → Dry/Wet"),
            (self.CC_CHORUS, "Chorus Amount",
             "Map this to: Chorus → Dry/Wet"),
            (self.CC_MODULATION, "Modulation",
             "Map this to: Any modulation effect (optional)"),
        ]

        for i, (cc_num, cc_name, suggestion) in enumerate(mappings, 1):
            print(f"\n\n{'='*70}")
            print(f"STEP {i}/{len(mappings)}: {cc_name}")
            print(f"{'='*70}")
            print(f"\n💡 Suggestion: {suggestion}")

            choice = input(f"\nMap this parameter now? (Y/n/skip): ").strip().lower()

            if choice == 'skip' or choice == 's':
                print(f"⏭️  Skipped {cc_name}")
                continue
            elif choice == 'n':
                print(f"⏭️  Skipped {cc_name}")
                continue

            # Run the sweep for this CC
            self.sweep_cc(cc_num, cc_name)

        print("\n\n" + "="*70)
        print("✅ MAPPING WIZARD COMPLETE!")
        print("="*70)
        print("\nAll parameters should now be mapped in Ableton Live.")
        print("\nTest your mappings:")
        print("  - Run: python test_gesture_midi_sim.py")
        print("  - Press 'S' to start auto-sweep")
        print("  - Watch your effects respond in Ableton!")
        print("\nWhen ready for real gesture control:")
        print("  - Run: python test_gesture_midi.py (with webcam)")
        print("  - Or: python integrated_music_gesture_control.py (full system)")
        print("="*70)

    def manual_mode(self):
        """Manual mode - pick which CC to send."""
        print("\n" + "="*70)
        print("MANUAL MAPPING MODE")
        print("="*70)
        print("\nSelect which CC to sweep:\n")
        print("  1. CC 74 - Filter Cutoff")
        print("  2. CC 71 - Filter Resonance")
        print("  3. CC 91 - Reverb/Delay Level")
        print("  4. CC 93 - Chorus Amount")
        print("  5. CC  1 - Modulation")
        print("\n  W. Run full wizard")
        print("  Q. Quit")
        print("="*70)

        mappings = {
            '1': (self.CC_FILTER_CUTOFF, "Filter Cutoff"),
            '2': (self.CC_RESONANCE, "Filter Resonance"),
            '3': (self.CC_REVERB, "Reverb/Delay"),
            '4': (self.CC_CHORUS, "Chorus Amount"),
            '5': (self.CC_MODULATION, "Modulation"),
        }

        while True:
            choice = input("\nSelect option: ").strip().upper()

            if choice == 'Q':
                break
            elif choice == 'W':
                self.run_mapping_wizard()
                break
            elif choice in mappings:
                cc_num, cc_name = mappings[choice]
                self.sweep_cc(cc_num, cc_name)
            else:
                print("Invalid choice. Try again.")

        # Reset all CCs
        print("\nResetting all CC values to 0...")
        for cc in [self.CC_FILTER_CUTOFF, self.CC_RESONANCE,
                   self.CC_REVERB, self.CC_CHORUS, self.CC_MODULATION]:
            self.send_cc(cc, 0)

        self.midi_out.close()
        print("✓ Done!")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='MIDI CC Mapping Assistant for Ableton Live'
    )
    parser.add_argument('--port', default=None, help='MIDI port name')
    parser.add_argument('--manual', action='store_true',
                       help='Manual mode instead of wizard')
    args = parser.parse_args()

    print("\n🎛️  MIDI CC MAPPING ASSISTANT")
    print("   Perfect for Ableton Live MIDI Learn!\n")

    assistant = MappingAssistant(args.port)

    if args.manual:
        assistant.manual_mode()
    else:
        assistant.run_mapping_wizard()


if __name__ == "__main__":
    main()
