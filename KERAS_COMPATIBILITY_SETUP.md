# TensorFlow/Keras Compatibility Setup

## One-Time Setup Required

If you haven't already, install the `tf_keras` package for compatibility with models trained in TensorFlow 2.16+ containers:

```bash
pip install tf_keras
```

This is needed because:
- GPU training container uses TensorFlow 2.16+ (with `tf_keras` internally)
- Your local environment has Keras 3.x (standalone)
- The compatibility layer bridges the gap

## What Was Fixed

All music generation scripts now include this compatibility fix at the top:

```python
import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'
```

**Fixed scripts**:
- `realtime_midi_generator.py`
- `integrated_music_gesture_control.py`
- `evaluate_model.py`

## Usage (Same as Before!)

After the one-time setup, use your scripts normally:

```bash
# Real-time generation
python realtime_midi_generator.py --temperature 1.5

# With gesture control
python integrated_music_gesture_control.py

# Evaluation
python evaluate_model.py --model music_rnn_model.keras --output evaluation_v2
```

No need for `generate_music.py` - your original scripts work with the new models!

---

*This setup bridges the gap between GPU training (TensorFlow 2.16+) and local inference (Keras 3.x) environments.*
