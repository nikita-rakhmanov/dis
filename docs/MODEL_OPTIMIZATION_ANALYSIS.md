# RNN Music Model - Optimization Analysis & Progress Tracker

**Date Started**: 2025-11-11
**Current Model**: Single LSTM(128) with 3-head output
**Training Data**: MAESTRO v2.0.0 (1000 files)

---

## Current Model Architecture

```
Input: (25, 3) [pitch, step, duration]
    ↓
LSTM(128 units)
    ↓
├─→ Dense(128) → Pitch prediction
├─→ Dense(1) → Step prediction
└─→ Dense(1) → Duration prediction
```

**Parameters**:
- Sequence Length: 25 notes
- Vocab Size: 128 (MIDI notes)
- Batch Size: 64
- Epochs: 50
- Learning Rate: 0.005 (Adam)
- Loss Weights: `{pitch: 0.05, step: 1.0, duration: 1.0}`

---

## Performance Baseline

### Current Model Characteristics
- **Total Parameters**: ~199K (estimated)
- **Single LSTM Layer**: 128 units
- **Training Time**: ~50 epochs with early stopping
- **Generation Quality**:
  - Timing: Good (heavily weighted)
  - Melodic coherence: Weak (pitch under-weighted at 0.05)
  - Long-term structure: Limited (short 25-note context)

### Known Issues
1. ❌ Pitch loss weight too low (0.05 vs 1.0 for timing)
2. ❌ Very short sequence length (25 notes)
3. ❌ Shallow architecture (1 layer)
4. ❌ No regularization (dropout)
5. ❌ No validation set
6. ❌ Only uses first instrument (no polyphony)

---

## Optimization Priority Tiers

### 🔴 HIGH PRIORITY (Start Here)

#### 1. Loss Weight Rebalancing
**Current**: `{pitch: 0.05, step: 1.0, duration: 1.0}`
**Target**: `{pitch: 0.5, step: 1.0, duration: 1.0}`

**Rationale**: Pitch is 20x under-weighted, causing poor melodic structure

**Expected Impact**: ⭐⭐⭐⭐⭐
- Better note selection
- More musical coherence
- Improved melodic patterns

**Implementation Difficulty**: 🟢 Trivial (1-line change)

---

#### 2. Increase Sequence Length
**Current**: 25 notes
**Target**: 50-100 notes

**Rationale**: 25 notes ≈ 10-15 seconds of music; too short for musical phrases

**Expected Impact**: ⭐⭐⭐⭐
- Better long-term structure
- Captures musical motifs
- More coherent compositions

**Implementation Difficulty**: 🟢 Easy (change constant, retrain)

**Trade-offs**:
- ✅ Better musical memory
- ⚠️ 2-4x more GPU memory
- ⚠️ Slower training (~20-30%)

---

#### 3. Deeper Architecture
**Current**: Single LSTM(128)
**Proposed Options**: See detailed architecture analysis below

**Expected Impact**: ⭐⭐⭐⭐⭐
- Captures complex patterns
- Better generalization
- Richer musical representations

**Implementation Difficulty**: 🟡 Moderate (architecture redesign)

---

### 🟡 MEDIUM PRIORITY

#### 4. Add Dropout Regularization
**Target**: 0.2-0.3 dropout rate

**Expected Impact**: ⭐⭐⭐
- Reduces overfitting
- Better generalization
- More diverse outputs

---

#### 5. Train/Validation Split
**Target**: 90/10 split

**Expected Impact**: ⭐⭐⭐
- Monitor overfitting
- Better hyperparameter tuning
- Early stopping on validation loss

---

#### 6. Learning Rate Scheduling
**Options**:
- ExponentialDecay
- ReduceLROnPlateau

**Expected Impact**: ⭐⭐⭐
- Faster convergence
- Better final performance
- Escape local minima

---

### 🟢 LOW PRIORITY (Future Work)

7. Data augmentation (transposition, time stretching)
8. Polyphony support (chord generation)
9. Add velocity as 4th feature
10. Attention mechanisms
11. Transformer architecture
12. Conditional generation (style/genre control)

---

## Architecture Comparison Matrix

See detailed analysis in **ARCHITECTURE_OPTIONS** section below.

| Architecture | Params | Training Speed | Quality | Memory | Complexity |
|--------------|--------|----------------|---------|--------|------------|
| **Current (Baseline)** | 199K | ⚡⚡⚡ Fast | ⭐⭐ | Low | Simple |
| **Option A: Stacked LSTM** | 528K | ⚡⚡ Moderate | ⭐⭐⭐⭐⭐ | Medium | Moderate |
| **Option B: Bidirectional** | 398K | ⚡⚡ Moderate | ⭐⭐⭐⭐ | Medium | Moderate |
| **Option C: LSTM+Dense** | 223K | ⚡⚡⚡ Fast | ⭐⭐⭐ | Low | Simple |
| **Option D: Hybrid (A+C)** | 552K | ⚡ Slower | ⭐⭐⭐⭐⭐ | High | Complex |

---

## Experiment Tracking

### Experiment 1: Baseline (Current Model)
**Status**: ✅ Completed
**Date**: [Original training date]

**Configuration**:
- Architecture: Single LSTM(128)
- Sequence Length: 25
- Loss Weights: `{pitch: 0.05, step: 1.0, duration: 1.0}`
- Learning Rate: 0.005

**Results**:
- Final Loss: [TBD - check training logs]
- Pitch Accuracy: [TBD]
- Step MAE: [TBD]
- Duration MAE: [TBD]

**Observations**:
- Good timing generation
- Weak melodic structure
- Limited long-term coherence

---

### Experiment 2: [NEXT] Loss Weight Rebalancing
**Status**: ⏳ Pending

**Configuration**:
- Architecture: Single LSTM(128)
- Sequence Length: 25
- Loss Weights: `{pitch: 0.5, step: 1.0, duration: 1.0}` ⬅️ CHANGED
- Learning Rate: 0.005

**Hypothesis**: 10x increase in pitch weight will improve melodic quality without sacrificing timing

**Expected Results**:
- ✅ Better pitch selection
- ✅ More musical melodies
- ⚠️ Slightly worse timing (acceptable trade-off)

**Results**: [Run and record]

---

### Experiment 3: [FUTURE] Increased Sequence Length
**Status**: ⏳ Pending

**Configuration**:
- Architecture: Single LSTM(128)
- Sequence Length: 50 ⬅️ CHANGED
- Loss Weights: `{pitch: 0.5, step: 1.0, duration: 1.0}`
- Learning Rate: 0.005

---

### Experiment 4: [FUTURE] New Architecture
**Status**: ⏳ Pending

**Configuration**: [TBD based on architecture decision]

---

## Implementation Checklist

### Phase 1: High Priority (This Week)
- [ ] **Fix Loss Weights**
  - [ ] Change pitch weight from 0.05 → 0.5
  - [ ] Retrain model
  - [ ] Compare generated music quality
  - [ ] Document results in Experiment 2

- [ ] **Increase Sequence Length**
  - [ ] Change SEQUENCE_LENGTH from 25 → 50
  - [ ] Update seed sequence generation
  - [ ] Retrain model
  - [ ] Monitor memory usage
  - [ ] Document results in Experiment 3

- [ ] **Choose & Implement New Architecture**
  - [ ] Review architecture options (see below)
  - [ ] Implement chosen architecture
  - [ ] Add dropout layers
  - [ ] Retrain model
  - [ ] Compare all metrics
  - [ ] Document results in Experiment 4

### Phase 2: Medium Priority (Next Week)
- [ ] Add train/validation split
- [ ] Implement validation metrics
- [ ] Add learning rate scheduling
- [ ] Add ReduceLROnPlateau callback

### Phase 3: Low Priority (Future)
- [ ] Data augmentation
- [ ] Polyphony support
- [ ] Velocity modeling

---

## Notes & Observations

### Training Tips
- Monitor both loss AND generated music quality (subjective listening tests)
- Save checkpoints every 5 epochs for rollback
- Use TensorBoard for visualization
- Test generation at multiple temperature values (0.8, 1.0, 1.5, 2.0)

### Common Issues
- If loss doesn't decrease: Learning rate too high or too low
- If overfitting: Add dropout or reduce model size
- If output too repetitive: Increase temperature or sequence length
- If output too random: Decrease temperature or increase training epochs

---

## Resources
- Training script: `train_music_rnn.py`
- Generation script: `realtime_midi_generator.py`
- Model file: `music_rnn_model.keras`
- Dataset: MAESTRO v2.0.0 (1000 files)
- Checkpoints: `training_checkpoints/ckpt_*.weights.h5`

---

## Quick Reference: Code Locations

**Loss Weights**: `train_music_rnn.py:128-132`
```python
loss_weights={
    'pitch': 0.05,  # ⬅️ CHANGE THIS
    'step': 1.0,
    'duration': 1.0,
}
```

**Sequence Length**: `train_music_rnn.py:18`
```python
SEQUENCE_LENGTH = 25  # ⬅️ CHANGE THIS
```

**Model Architecture**: `train_music_rnn.py:105-136`
```python
def build_model(seq_length: int, vocab_size: int, learning_rate: float):
    # ⬅️ MODIFY THIS FUNCTION
```

---

*Last Updated: 2025-11-11*
