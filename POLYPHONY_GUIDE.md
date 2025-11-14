# Polyphony Guide - Dual-Model 2-Voice Generation

## Overview

This project now supports **2-voice polyphonic music generation** using a cascaded dual-model architecture:
- **Model 1 (Melody)**: Your existing trained RNN generates the melody line
- **Model 2 (Harmony)**: Generates harmony notes based on the melody output

This approach allows polyphony without retraining your existing model!

---

## Quick Start

### Basic Polyphonic Generation

```bash
# Run with polyphony enabled (default: classical harmony style)
python integrated_music_gesture_control.py --polyphony

# With custom harmony style
python integrated_music_gesture_control.py --polyphony --harmony-style jazz

# With polyphony and no gesture control (faster)
python integrated_music_gesture_control.py --polyphony --no-gesture
```

### Available Harmony Styles

1. **Classical** (default)
   - Thirds and fifths
   - Traditional harmonic intervals
   - Best for: Classical, folk, traditional music

2. **Jazz**
   - Added 7ths and extended harmonies
   - Richer, more complex chords
   - Best for: Jazz, blues, sophisticated pop

3. **Modern**
   - Wider interval spacing (octaves, seconds)
   - More dissonant, experimental
   - Best for: Contemporary, experimental, ambient

---

## How It Works

### Architecture

```
Input Sequence
     ↓
[Model 1: RNN Melody Generator]
     ↓
(pitch₁, step₁, duration₁)
     ↓
[Model 2: Harmony Generator]
     ↓
(pitch₂, step₂, duration₂)
     ↓
Play Both Notes Simultaneously
```

### Current Implementation: Rule-Based Harmony

**Phase 1** (Current): Simple rule-based harmony generator
- Uses weighted probability distribution of harmonic intervals
- Context-aware (knows recent melody history)
- Fast and predictable

**Phase 2** (Future): Learned neural harmony
- Train a small neural network on melody-harmony pairs
- Learns from actual MIDI data
- More musical and context-sensitive

---

## Command-Line Options

```bash
python integrated_music_gesture_control.py \
    --polyphony                    # Enable 2-voice polyphony
    --harmony-style classical      # Harmony style: classical/jazz/modern
    --temperature 2.0              # Melody temperature
    --velocity 80                  # MIDI velocity
    --speed 1.0                    # Playback speed
    --no-gesture                   # Disable gesture control
    --no-visualization             # Disable 3D visualization
```

---

## Output Examples

### Monophonic (Original)
```
♪    1: C4   (pitch= 60) step=0.500s dur=0.400s
♪    2: D4   (pitch= 62) step=0.450s dur=0.380s
♪    3: E4   (pitch= 64) step=0.500s dur=0.420s
```

### Polyphonic (New)
```
♪    1: C4  +A3   (melody= 60, harmony= 57) step=0.500s dur=0.400s
♪    2: D4  +B3   (melody= 62, harmony= 59) step=0.450s dur=0.380s
♪    3: E4  +C4   (melody= 64, harmony= 60) step=0.500s dur=0.420s
```

---

## Technical Details

### Harmony Interval Profiles

**Classical Style:**
- Perfect 5th down (-7): 25%
- Perfect 4th down (-5): 20%
- Major 3rd down (-4): 15%
- Minor 3rd down (-3): 15%
- Minor 3rd up (+3): 10%
- Major 3rd up (+4): 5%
- Perfect 4th up (+5): 5%
- Perfect 5th up (+7): 5%

**Jazz Style:**
- More 7ths and extensions
- Richer harmonic palette

**Modern Style:**
- Wider intervals (octaves, 2nds)
- More experimental harmonies

### Timing Synchronization

- Harmony timing matches melody (synchronized playback)
- Harmony duration is 95% of melody duration (cleaner note cutoff)
- Both notes start simultaneously

### MIDI Output

- Melody: Full velocity (as specified)
- Harmony: 80% of melody velocity (slightly quieter)
- Both sent to same MIDI port/channel

---

## Next Steps: Training a Real Harmony Model

### Phase 2: Train Model 2 (Neural Harmony Generator)

The project includes infrastructure for training a learned harmony model:

1. **Extract Training Data**
   ```bash
   python train_harmony_model.py --extract-data
   ```
   - Parses MAESTRO dataset
   - Extracts melody-harmony pairs
   - Saves training dataset

2. **Train Harmony Model**
   ```bash
   python train_harmony_model.py --train
   ```
   - Trains small neural network
   - Input: melody note + context
   - Output: harmony pitch prediction

3. **Use Learned Model**
   ```bash
   python integrated_music_gesture_control.py \
       --polyphony \
       --harmony-model harmony_model.keras
   ```

**Note**: Training script to be created in Phase 2

---

## Limitations & Future Work

### Current Limitations

1. **2 voices only** - Can extend to 3+ by adding more models
2. **Rule-based harmony** - Phase 2 will add learned harmony
3. **No chord voicing** - Each timestep generates exactly 2 notes
4. **Fixed timing** - Harmony follows melody timing exactly

### Future Enhancements

1. **3-Voice Polyphony**
   - Add bass model (Model 3)
   - Melody + Harmony + Bass = fuller sound

2. **Learned Harmony**
   - Train on real melody-harmony pairs
   - More musical and context-aware

3. **Chord Generation**
   - Generate 3-6 note chords per timestep
   - Multi-hot encoding for unlimited polyphony

4. **Independent Timing**
   - Allow harmony to have different rhythms
   - More complex polyphonic textures

---

## File Structure

```
/home/user/dis/
├── dual_model_polyphony.py           # Polyphony system implementation
├── integrated_music_gesture_control.py  # Main script (updated)
├── train_music_rnn.py                # Model 1 training (unchanged)
├── music_rnn_model.keras             # Trained Model 1
└── POLYPHONY_GUIDE.md                # This guide
```

---

## Troubleshooting

### Issue: Notes sound the same
- Check MIDI routing in your DAW
- Verify both notes are being sent (check console output)
- Harmony might be unison - try different harmony style

### Issue: Harmony sounds dissonant
- Try `--harmony-style classical` for safer intervals
- Reduce temperature for more predictable melody
- Some dissonance is normal in modern/jazz styles

### Issue: Performance is slow
- Polyphony adds ~2x prediction time (minimal)
- Use `--no-gesture` and `--no-visualization` for faster performance
- Still real-time capable on most systems

---

## Examples

### Classical Piano Piece
```bash
python integrated_music_gesture_control.py \
    --polyphony \
    --harmony-style classical \
    --temperature 1.5 \
    --velocity 70 \
    --no-gesture
```

### Jazz-Style Improvisation
```bash
python integrated_music_gesture_control.py \
    --polyphony \
    --harmony-style jazz \
    --temperature 2.0 \
    --velocity 85
```

### Experimental/Ambient
```bash
python integrated_music_gesture_control.py \
    --polyphony \
    --harmony-style modern \
    --temperature 2.5 \
    --speed 2.0
```

---

## Contributing

To add new harmony styles, edit `dual_model_polyphony.py`:

```python
self.interval_profiles = {
    'your_style': {
        'intervals': [-7, -5, -4, ...],  # Semitone intervals
        'weights': [0.3, 0.2, 0.15, ...]  # Probabilities (must sum to 1.0)
    }
}
```

---

*Last Updated: 2025-11-14*
*Status: Phase 1 Complete (Rule-based harmony)*
*Next: Phase 2 (Neural harmony model)*
