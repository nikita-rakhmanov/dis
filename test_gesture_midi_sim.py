#!/usr/bin/env python3
"""
Simulated Gesture Control MIDI CC Test
No webcam required - uses keyboard/mouse input to simulate hand movements.
Perfect for testing MIDI routing and DAW setup.
"""

import mido
import time
import sys
import threading
import random

class SimulatedMIDITest:
    """Simulate gesture control without a camera."""

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

    def send_cc(self, cc_number, value, channel=0):
        """Send MIDI CC message."""
        value = max(0, min(127, value))
        msg = mido.Message('control_change', control=cc_number, value=value, channel=channel)
        self.midi_out.send(msg)
        return value

    def print_controls(self):
        """Print control instructions."""
        print("=" * 70)
        print("SIMULATED GESTURE CONTROL - KEYBOARD MODE")
        print("=" * 70)
        print("\nNo webcam required! Use keyboard to simulate gestures:\n")
        print("CONTINUOUS CONTROL:")
        print("  1-9  : Set Filter Cutoff (CC 74) - 1=low, 9=high")
        print("  Q-P  : Set Reverb Level (CC 91) - Q=low, P=high")
        print("  A-L  : Set Resonance (CC 71) - A=low, L=high")
        print()
        print("GESTURES:")
        print("  O    : Open Palm → Chorus MAX (CC 93 = 127)")
        print("  F    : Closed Fist → Chorus OFF (CC 93 = 0)")
        print("  R    : Rock On → Modulation MAX (CC 1 = 127)")
        print("  P    : Peace Sign → Modulation MID (CC 1 = 64)")
        print()
        print("AUTOMATION:")
        print("  S    : Start auto-sweep (all parameters)")
        print("  X    : Stop auto-sweep")
        print("  T    : Test all CC values (0-127 sweep)")
        print()
        print("  C    : Clear all CC (reset to 0)")
        print("  H    : Show this help")
        print("  Ctrl+C : Quit")
        print("=" * 70)
        print()

    def test_interactive(self):
        """Interactive keyboard mode."""
        self.print_controls()

        print("Ready! Type commands (or 'H' for help):\n")

        current_values = {
            self.CC_FILTER_CUTOFF: 64,
            self.CC_REVERB: 32,
            self.CC_RESONANCE: 32,
            self.CC_CHORUS: 0,
            self.CC_MODULATION: 0
        }

        sweeping = False
        sweep_thread = None

        def auto_sweep():
            """Auto-sweep all parameters."""
            nonlocal sweeping
            step = 0
            while sweeping:
                # Create smooth sine wave movements
                t = step / 20.0

                # Filter: slow sweep
                cutoff = int(64 + 63 * (0.5 + 0.5 * (t % 1.0)))
                self.send_cc(self.CC_FILTER_CUTOFF, cutoff)

                # Reverb: medium sweep
                reverb = int(64 + 63 * (0.5 + 0.5 * ((t * 1.5) % 1.0)))
                self.send_cc(self.CC_REVERB, reverb)

                # Resonance: fast sweep
                res = int(32 + 32 * (0.5 + 0.5 * ((t * 2.0) % 1.0)))
                self.send_cc(self.CC_RESONANCE, res)

                print(f"\r[AUTO] Filter:{cutoff:3d} Reverb:{reverb:3d} Res:{res:3d}", end='', flush=True)

                step += 1
                time.sleep(0.05)

        def display_values():
            """Show current CC values."""
            print(f"[CC] Filter:{current_values[self.CC_FILTER_CUTOFF]:3d} "
                  f"Reverb:{current_values[self.CC_REVERB]:3d} "
                  f"Res:{current_values[self.CC_RESONANCE]:3d} "
                  f"Chorus:{current_values[self.CC_CHORUS]:3d} "
                  f"Mod:{current_values[self.CC_MODULATION]:3d}")

        try:
            # Non-blocking input simulation with commands
            while True:
                try:
                    cmd = input("> ").strip().upper()

                    if not cmd:
                        continue

                    # Number keys 1-9: Filter Cutoff
                    if cmd in '123456789':
                        val = int(cmd) * 14  # Map 1-9 to 14-126
                        current_values[self.CC_FILTER_CUTOFF] = self.send_cc(self.CC_FILTER_CUTOFF, val)
                        print(f"✓ Filter Cutoff (CC 74) = {val}")
                        display_values()

                    # Q-P keys: Reverb (10 levels)
                    elif cmd in 'QWERTYUIOP':
                        qwerty = 'QWERTYUIOP'
                        val = qwerty.index(cmd) * 12  # Map to 0-120
                        current_values[self.CC_REVERB] = self.send_cc(self.CC_REVERB, val)
                        print(f"✓ Reverb (CC 91) = {val}")
                        display_values()

                    # A-L keys: Resonance (12 levels)
                    elif cmd in 'ASDFGHJKL':
                        asdf = 'ASDFGHJKL'
                        val = asdf.index(cmd) * 14  # Map to 0-126
                        current_values[self.CC_RESONANCE] = self.send_cc(self.CC_RESONANCE, val)
                        print(f"✓ Resonance (CC 71) = {val}")
                        display_values()

                    # Gestures
                    elif cmd == 'O':  # Open Palm
                        current_values[self.CC_CHORUS] = self.send_cc(self.CC_CHORUS, 127)
                        print(f"✓ OPEN PALM → Chorus MAX (CC 93 = 127)")
                        display_values()

                    elif cmd == 'F':  # Fist
                        current_values[self.CC_CHORUS] = self.send_cc(self.CC_CHORUS, 0)
                        current_values[self.CC_MODULATION] = self.send_cc(self.CC_MODULATION, 0)
                        print(f"✓ CLOSED FIST → Effects OFF")
                        display_values()

                    elif cmd == 'R':  # Rock On
                        current_values[self.CC_MODULATION] = self.send_cc(self.CC_MODULATION, 127)
                        print(f"✓ ROCK ON → Modulation MAX (CC 1 = 127)")
                        display_values()

                    elif cmd == 'P':  # Peace
                        current_values[self.CC_MODULATION] = self.send_cc(self.CC_MODULATION, 64)
                        print(f"✓ PEACE SIGN → Modulation MID (CC 1 = 64)")
                        display_values()

                    # Auto-sweep
                    elif cmd == 'S':
                        if not sweeping:
                            sweeping = True
                            sweep_thread = threading.Thread(target=auto_sweep, daemon=True)
                            sweep_thread.start()
                            print("✓ Auto-sweep STARTED (press X to stop)")

                    elif cmd == 'X':
                        if sweeping:
                            sweeping = False
                            if sweep_thread:
                                sweep_thread.join(timeout=1.0)
                            print("\n✓ Auto-sweep STOPPED")
                            display_values()

                    # Test sweep
                    elif cmd == 'T':
                        print("Testing all CC values (0-127 sweep)...")
                        for cc_num in [self.CC_FILTER_CUTOFF, self.CC_REVERB,
                                      self.CC_RESONANCE, self.CC_CHORUS]:
                            cc_name = {
                                74: "Filter", 91: "Reverb",
                                71: "Resonance", 93: "Chorus"
                            }[cc_num]

                            print(f"  Sweeping {cc_name} (CC {cc_num})...", end='', flush=True)
                            for val in range(0, 128, 4):
                                self.send_cc(cc_num, val)
                                time.sleep(0.02)
                            print(" Done!")
                        print("✓ Test complete")
                        display_values()

                    # Clear all
                    elif cmd == 'C':
                        for cc in [self.CC_FILTER_CUTOFF, self.CC_REVERB,
                                  self.CC_RESONANCE, self.CC_CHORUS, self.CC_MODULATION]:
                            current_values[cc] = self.send_cc(cc, 0)
                        print("✓ All CC values reset to 0")
                        display_values()

                    # Help
                    elif cmd == 'H':
                        self.print_controls()

                    else:
                        print(f"Unknown command: {cmd} (press H for help)")

                except EOFError:
                    break

        except KeyboardInterrupt:
            print("\n\nStopping...")

        finally:
            sweeping = False

            # Reset all CCs
            print("\nResetting MIDI CC values...")
            for cc in [self.CC_FILTER_CUTOFF, self.CC_RESONANCE,
                      self.CC_REVERB, self.CC_CHORUS, self.CC_MODULATION]:
                self.send_cc(cc, 0)

            self.midi_out.close()
            print("✓ Test completed")
            print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Simulated gesture control (no webcam required)'
    )
    parser.add_argument('--port', default=None, help='MIDI port name')
    args = parser.parse_args()

    print("\n🎛️  GESTURE CONTROL SIMULATOR (No webcam required)\n")

    tester = SimulatedMIDITest(args.port)
    tester.test_interactive()


if __name__ == "__main__":
    main()
