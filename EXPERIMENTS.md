# RNN Model Experiments

This document summarizes the experiments conducted to improve melody generation using RNN models, comparing three different approaches.

---

## Experiment Overview

| Model | Dataset | Vocab Size | Data Processing | Training Platform |
|-------|---------|------------|-----------------|-------------------|
| **Original** | MAESTRO v2 | 128 | Raw polyphonic | Local |
| **Improved** | MAESTRO v3 | 128 | Skyline melody extraction | L4 GPU Cluster |
| **Clipped** | MAESTRO v3 | 42 | Skyline + pitch clipping | L4 GPU Cluster |

---

## Model Architectures

### Original Model (`train_music_rnn.py`)
```
Input: (batch, 50, 3) - [pitch, step, duration]
├── LSTM(256, return_sequences=True)
├── Dropout(0.3)
├── LSTM(128)
└── Output Heads:
    ├── pitch: Dense(128) - logits, SparseCategoricalCrossentropy
    ├── step: Dense(1) + custom MSE with positive pressure
    └── duration: Dense(1) + custom MSE with positive pressure
```
- **Parameters**: ~479K (same as improved)
- **Loss weights**: pitch=0.25, step=1.0, duration=1.0
- **Loss**: Custom MSE with positive pressure for step/duration

### Improved Model (`train_improved_rnn.py`)
```
Input: (batch, 50, 2) - [pitch_norm, log_delta_time_norm]
├── LSTM(256, return_sequences=True)
├── Dropout(0.3)
├── LSTM(128)
├── Dropout(0.2)
└── Output Heads:
    ├── pitch_head: Dense(128, softmax)
    └── time_head: Dense(1, linear)
```
- **Parameters**: ~479K
- **Optimizations**: Mixed precision (float16), batch size 256
- **Data**: Onset-biased skyline melody extraction

### Clipped Model (`train_clipped_rnn.py`)
- Same architecture as Improved
- **Key difference**: `VOCAB_SIZE = 42` (pitches 48-89 only)
- Based on data analysis showing 90% of melody notes fall in C3-F6 range

---

## Data Processing Pipeline

### Original Model
1. Load MIDI files directly
2. Extract all notes (polyphonic)
3. Compute (pitch, step, duration) features

### Improved & Clipped Models
1. Load MIDI files
2. **Onset-Biased Skyline Algorithm**:
   - At each time point, select the highest-pitched **active** note
   - Add 12-semitone bonus for notes that just started (onset bias)
   - This prefers melody notes over sustained accompaniment
3. **Post-processing**:
   - Merge gaps < 50ms
   - Remove notes < 50ms duration
4. Compute dataset statistics (99th percentile log-delta for normalization)
5. Create (pitch_normalized, log_time_normalized) features

### Vocabulary Clipping (Clipped Model Only)
Based on data analysis of 200 MAESTRO files:
- **5th percentile pitch**: 48 (C3)
- **95th percentile pitch**: 89 (F6)
- **90% of melody notes** fall within 42 pitches instead of 128

---

## Training Configuration

| Parameter | Original | Improved | Clipped |
|-----------|----------|----------|---------|
| Batch Size | 64 | 256 | 256 |
| Learning Rate | 0.005 | 0.002 | 0.002 |
| Epochs | 50 | 30 | 30 |
| Early Stopping | patience=5 | patience=5 | patience=5 |
| Mixed Precision | No | Yes (float16) | Yes (float16) |
| Training Files | ~1200 | 1200 | 1200 |
| GPU | Local CPU/GPU | NVIDIA L4 (24GB) | NVIDIA L4 (24GB) |

---

## Training Results

### Loss Curves (Demo Runs - 50 files, 10 epochs)

| Model | Start Pitch Loss | End Pitch Loss | Convergence |
|-------|-----------------|----------------|-------------|
| Original | 4.00 | 3.65 | Smooth |
| Improved | 3.75 | 3.20 | Very smooth |

### Full Training Results

| Model | Best Epoch | Final Pitch Loss | Notes |
|-------|------------|------------------|-------|
| Original | Unknown | ~2.8-3.0 (estimated) | Previously trained |
| Improved | 7 | 3.6 | Early stopping at epoch ~23 |
| Clipped | 19 | ~3.0 | 42-class problem (baseline: ln(42)=3.74) |

---

## Generation Evaluation

### Methodology
- Generated 100 notes at temperatures 0.8, 1.0, 1.5
- 5 samples per temperature
- Metrics: pitch diversity, entropy, intervals, repetition

### Key Metrics Comparison (Temperature 1.0)

| Metric | Original | Improved | Clipped | Best |
|--------|----------|----------|---------|------|
| **Pitch Range** | 49 semitones | 126 semitones | 41 semitones | Clipped ✓ |
| **Large Jumps (>12)** | **30%** | 81% | 56% | Original ✓ |
| **Stepwise (≤2)** | **15%** | 1% | 10% | Original ✓ |
| **Mean Interval** | **10** | 41 | 15 | Original ✓ |
| **Unique Pitches** | 35 | **70** | 38 | Improved ✓ |
| **Pitch Entropy** | 4.81 | **5.99** | 5.05 | Improved ✓ |
| **Repetition Ratio** | 9.6% | **3.6%** | 6.8% | Improved ✓ |

### MIDI Sample Analysis

#### Original Model (Temp 0.8)
```
First notes: E4 → A4 → A3 → C4 → A4 → D5 → G4 → E4 → F#4
Intervals:   +5   -12   +3   +9   +5   -7   -3   +2
✓ Melodic motion, reasonable jumps
```

#### Improved Model (Temp 0.8)
```
First notes: B4 → C9 → B4 → F0 → F-1 → A#7 → D7 → A8
Intervals:   +49  -49  -54  -12  +101 +8   +19
✗ Chaotic, full keyboard range, no melodic structure
```

#### Clipped Model (Temp 0.8)
```
First notes: B4 → D4 → A#4 → F#3 → D6 → G5 → D#6 → A3
Intervals:   -9   +8   -16  +32   -7   +8   -30
~ Constrained range (C3-F6), but still jumpy
```

---

## Key Findings

### 1. Melody Extraction Worked
- Skyline algorithm successfully extracts monophonic melody lines
- Data analysis confirmed 90% of notes fall in C3-F6 range
- Time loss converged quickly, indicating well-distributed timing data

### 2. Vocabulary Reduction Helped
- Clipped model produces outputs strictly in C3-F6 range (as designed)
- No more extreme outliers like C-1 or G9
- 67% fewer classification classes

### 3. Sequential Learning Remains Challenging
Despite improvements:
- **Original model learned melodic transitions** (stepwise motion, reasonable intervals)
- **Improved models learned note distributions** (which pitches are common)
- **Neither improved model learned sequential patterns** as effectively

### 4. Possible Causes
1. **Early stopping saved too early** (epoch 7 for improved, epoch 19 for clipped)
2. **Learning rate may be too high** for learning subtle sequential patterns
3. **RNN architecture limitation** — LSTMs may need more depth or attention mechanisms

---

## Recommendations

### Short-term (Generation Constraints)
Add post-hoc constraints to generation:
- Maximum interval of 12 semitones
- Prefer stepwise motion when probabilities are similar

### Medium-term (Training Improvements)
1. Lower learning rate (0.0005 instead of 0.002)
2. Increase patience (10 epochs)
3. Use learning rate scheduling
4. Train for more epochs (50-100)

### Long-term (Architecture Changes)
1. **Interval-based representation**: Predict relative pitch changes instead of absolute pitches
2. **Attention mechanism**: Add attention layer before output heads
3. **Transformer architecture**: Replace LSTM with Transformer for better long-range dependencies

---

## Files Generated

| File | Description |
|------|-------------|
| `improved_melody_model.keras` | Trained improved model (128 vocab) |
| `clipped_melody_model.keras` | Trained clipped model (42 vocab) |
| `model_metadata.json` | Normalization parameters for improved model |
| `clipped_model_metadata.json` | Normalization parameters for clipped model |
| `*_seed_sequence.npy` | Seed sequences for generation |
| `model_comparison/` | Generated MIDI files and evaluation results |
| `data_analysis/` | Melody data analysis plots and statistics |

---

## Conclusion

The vocabulary-clipped model represents an improvement in output range constraint but does not solve the fundamental challenge of learning melodic sequential patterns. The original model, despite using messier polyphonic data, produces more musical output due to its longer training and potentially more suitable hyperparameters.

Future work should focus on:
1. Training regime improvements (lower LR, longer training)
2. Generation-time constraints for immediate improvement
3. Architecture exploration (attention, transformers) for structural improvement
