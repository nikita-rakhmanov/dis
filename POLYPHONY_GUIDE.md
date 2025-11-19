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

2. **Jazz**
   - Added 7ths and extended harmonies
   - Richer, more complex chords

3. **Modern**
   - Wider interval spacing (octaves, seconds)
   - More dissonant, experimental

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

---

## Command-Line Options

```bash
python integrated_music_gesture_control.py \
    --polyphony                    # Enable 2-voice polyphony
    --harmony-style classical      # Harmony style: classical/jazz/modern
    --temperature 2.0              # Melody temperature
    --velocity 80                  # MIDI velocity
    --speed 16.0                    # Playback speed
    --no-gesture                   # Disable gesture control
    --no-visualization             # Disable 3D visualization
```

