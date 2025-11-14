# Quick Ableton Setup Guide

## The Problem You're Having

When using MIDI Learn in Ableton, moving your hand sends **multiple CC messages at once**:
- Moving LEFT/RIGHT sends CC 74 (Filter)
- But also sends CC 91 (Reverb) if hand moves up/down slightly
- And CC 71 (Resonance) changes too

This confuses Ableton's MIDI Learn - it doesn't know which CC to map!

## The Solution: Mapping Assistant

Use `map_midi_cc.py` to map **ONE CC at a time** with NO interference!

## Step-by-Step Setup

### Step 1: Setup Your Ableton Tracks (2 minutes)

1. **Create Track 1 (MIDI)**: "Generator Notes"
   - MIDI From: "RNN Music Generator" (or your MIDI port)
   - Monitor: In
   - Add instrument: Analog, Wavetable, Piano, etc.
   - Audio To: "3-Audio Output"

2. **Create Track 2 (MIDI)**: "Gesture Control"
   - MIDI From: "RNN Music Generator"
   - Monitor: In
   - NO instrument needed
   - MIDI To: "1-Generator Notes"

3. **Create Track 3 (Audio)**: "Audio Output"
   - Audio From: "1-Generator Notes" (Post FX)
   - Monitor: In
   - Add effects:
     - Auto Filter
     - Reverb
     - Chorus

### Step 2: Run the Mapping Assistant (3 minutes)

```bash
python map_midi_cc.py
```

**The wizard will guide you through mapping each CC:**

#### Mapping 1/5: Filter Cutoff (CC 74)

```
1. In Ableton: Press Cmd+M (Mac) or Ctrl+M (Windows)
2. Click: Auto Filter → Frequency knob
3. In terminal: Press ENTER
4. The knob will auto-detect CC 74
5. In Ableton: Press Cmd+M to exit MIDI Mapping
```

Filter Cutoff is now mapped.

#### Mapping 2/5: Filter Resonance (CC 71)

```
1. In Ableton: Press Cmd+M
2. Click: Auto Filter → Resonance knob
3. In terminal: Press ENTER
4. Auto-detects CC 71
5. In Ableton: Press Cmd+M to exit
```

Resonance is now mapped.

#### Mapping 3/5: Reverb Level (CC 91)

```
1. In Ableton: Press Cmd+M
2. Click: Reverb → Dry/Wet knob
3. In terminal: Press ENTER
4. Auto-detects CC 91
5. In Ableton: Press Cmd+M to exit
```

Reverb is now mapped.

#### Mapping 4/5: Chorus Amount (CC 93)

```
1. In Ableton: Press Cmd+M
2. Click: Chorus → Dry/Wet knob
3. In terminal: Press ENTER
4. Auto-detects CC 93
5. In Ableton: Press Cmd+M to exit
```

Chorus is now mapped.

#### Mapping 5/5: Modulation (CC 1) - Optional

```
Skip this one for now (type 'skip')
You can add it later to any modulation effect
```

### Step 3: Test Your Mappings

```bash
python test_gesture_midi_sim.py
```

Type `S` to start auto-sweep. You should see:
- Filter sweeping
- Reverb fading in/out
- Chorus modulating

### Step 4: Try With Webcam

```bash
python test_gesture_midi.py
```

Move your hand:
- LEFT/RIGHT = Filter opens/closes
- UP/DOWN = More/less reverb
- PINCH = Resonance changes

### Step 5: Full System!

```bash
python integrated_music_gesture_control.py
```

Now you have:
- Music generation from RNN
- Gesture control of effects
- Both running simultaneously

## Troubleshooting

### "I mapped it but the parameter doesn't respond"

**Solution:** Make sure Track 2 (Gesture Control) is:
- Monitor: In
- MIDI To: Track 1

### "The sweep happens but nothing gets mapped"

**Solution:** You forgot to enter MIDI Mapping mode!
- Press **Cmd+M** (Mac) or **Ctrl+M** (Windows) BEFORE pressing Enter

### "I want to re-map a parameter"

**Solution:** Run manual mode:
```bash
python map_midi_cc.py --manual
```

Then select which CC to sweep again.

### "Can I map multiple parameters to the same CC?"

**Yes!** In MIDI Mapping mode, you can:
1. Click parameter 1 → Sweep CC
2. Click parameter 2 → Sweep same CC
3. Both parameters now respond to that CC

## Quick Reference

| CC# | Parameter | Ableton Effect | Control |
|-----|-----------|----------------|---------|
| 74 | Filter Cutoff | Auto Filter → Frequency | Hand X |
| 71 | Resonance | Auto Filter → Resonance | Pinch |
| 91 | Reverb | Reverb → Dry/Wet | Hand Y |
| 93 | Chorus | Chorus → Dry/Wet | Gestures |
| 1 | Modulation | Any mod effect | Gestures |

## Additional Tips

### Tip 1: Adjust CC Ranges
After mapping, you can fine-tune ranges:
1. Enter MIDI Mapping mode (Cmd+M)
2. Click mapped parameter
3. At bottom of screen: set Min/Max
4. Example: Reverb Min=10%, Max=60% (not 0-100%)

### Tip 2: Save as Default
Once mapped:
- File → "Save Live Set as Default Set"
- Every new project starts with gesture control!

### Tip 3: Test Before Full System
Always test mappings with the simulator first:
```bash
python test_gesture_midi_sim.py
```

This is faster than using the webcam for testing.

### Tip 4: One CC at a Time
If you ever need to re-map:
```bash
python map_midi_cc.py --manual
```

Pick just the CC you want to fix.

## Complete Workflow

```
1. Setup Ableton tracks (3 tracks)           [2 min]
2. Run mapping assistant                     [3 min]
3. Test with simulator                       [1 min]
4. Test with webcam                          [1 min]
5. Run full integrated system                [Done!]
```

**Total time: Approximately 7 minutes** from zero to gesture-controlled music.

---

**Next:** See [ABLETON_MAPPING_GUIDE.md](ABLETON_MAPPING_GUIDE.md) for advanced setups and effect chain recommendations.
