# Model Evaluation Guide

**Purpose**: Systematically evaluate and compare music generation models with quantitative metrics and listening tests.

---

## 🎯 Evaluation Framework

### Two Types of Evaluation

1. **Quantitative Metrics** (Automated)
   - Objective measurements of generated music
   - Reproducible and comparable across models
   - Use `evaluate_model.py`

2. **Qualitative Assessment** (Listening)
   - Subjective quality evaluation
   - Use structured criteria for consistency
   - Listen to generated MIDI files

---

## 📊 Quantitative Metrics Explained

### 1. **Pitch Diversity Metrics**

**unique_pitches**: Number of distinct notes used
- Higher = more variety
- Range: 1-128 (MIDI range)
- Good: 20-40 for melodic music

**pitch_diversity_ratio**: unique_pitches / total_notes
- Measures how repetitive the melody is
- Range: 0-1
- Good: 0.3-0.6

**pitch_entropy**: Information entropy of note distribution
- Measures how evenly notes are distributed
- Higher = more unpredictable
- Range: 0-7 bits
- Good: 3-5 for music

### 2. **Melodic Contour Metrics**

**pitch_range**: Highest note - lowest note
- Measures melodic span
- Good: 12-36 semitones (1-3 octaves)

**mean_interval**: Average absolute distance between consecutive notes
- Measures melodic smoothness
- Good: 2-4 semitones (stepwise motion)

**max_interval**: Largest melodic jump
- Good: <12 semitones (within octave)

**large_jumps**: Number of intervals > 1 octave
- Too many = awkward melodies
- Good: <5% of total

### 3. **Repetition Metrics**

**repetition_ratio**: Most common note / total notes
- Measures over-reliance on single note
- Good: <0.15 (less than 15%)

**consecutive_repetition_ratio**: Same note repeated back-to-back
- Measures note stuttering
- Good: <0.20 (less than 20%)

### 4. **Rhythm Metrics**

**mean_step**: Average time between notes
- Measures tempo consistency

**std_step**: Variation in timing
- Higher = more rhythmic variety

**mean_duration**: Average note length

**std_duration**: Variation in note length

---

## 🚀 How to Use

### Step 1: Evaluate a Model

After training, run evaluation:

```bash
cd ~/Desktop/dis

# Basic evaluation (5 samples at 4 temperatures)
python evaluate_model.py \
  --model music_rnn_model.keras \
  --seed seed_sequence.npy \
  --output evaluation_v2

# Custom evaluation
python evaluate_model.py \
  --model music_rnn_model.keras \
  --num-samples 10 \
  --num-notes 200 \
  --temperatures 0.8 1.0 1.2 1.5 2.0 \
  --output evaluation_v2
```

**Output**:
- `evaluation_v2/evaluation_results.json` - Metrics data
- `evaluation_v2/temp0.8_sample1.mid` - MIDI files for listening
- `evaluation_v2/temp1.0_sample1.mid` - etc.

---

### Step 2: Compare Two Models

After evaluating both models:

```bash
# Evaluate version 1
python evaluate_model.py \
  --model music_rnn_model_v1.keras \
  --output evaluation_v1

# Evaluate version 2
python evaluate_model.py \
  --model music_rnn_model_v2.keras \
  --output evaluation_v2

# Compare them
python evaluate_model.py \
  --model music_rnn_model_v2.keras \
  --output evaluation_v2 \
  --compare evaluation_v1/evaluation_results.json
```

**Output shows**:
```
Temperature: 1.0
----------------------------------------
  unique_pitches          :  18.40 →  24.60 ( +6.20, +33.7%) ✓
  pitch_range             :  24.20 →  31.40 ( +7.20, +29.8%) ✓
  mean_interval           :   2.34 →   2.89 ( +0.55, +23.5%) ✓
  pitch_entropy           :   3.45 →   4.12 ( +0.67, +19.4%) ✓
  repetition_ratio        :   0.14 →   0.09 ( -0.05, -35.7%) ✓
```

**✓** = >5% change (significant)
**~** = <5% change (minor)

---

### Step 3: Listen and Rate

Open the generated MIDI files in your DAW or MIDI player:

```bash
# On Mac
open evaluation_v2/temp1.0_sample1.mid

# Or use your DAW (Ableton, Logic, etc.)
```

**Use this rating sheet**:

```
Model: ___________  Temperature: ___  Sample: ___

Melodic Quality         [1-5]: ___
- Are note choices musical?
- Do melodies make sense?

Coherence              [1-5]: ___
- Do phrases flow logically?
- Long-term structure?

Variety                [1-5]: ___
- Enough variation?
- Not too repetitive?

Rhythm Quality         [1-5]: ___
- Good timing?
- Rhythmic interest?

Overall Quality        [1-5]: ___
- Would you listen to this?

Notes: _________________________________
```

**Rating Scale**:
- 1 = Poor (random/broken)
- 2 = Below average (some issues)
- 3 = Average (acceptable)
- 4 = Good (enjoyable)
- 5 = Excellent (impressive)

---

## 📈 Interpreting Results

### What Makes Good Music?

**Pitch Metrics - Good Values**:
- Unique pitches: 20-40
- Pitch diversity: 0.3-0.6
- Pitch range: 12-36 semitones
- Mean interval: 2-4 semitones
- Pitch entropy: 3-5 bits

**Red Flags**:
- ❌ Too few unique pitches (<15) = repetitive
- ❌ Too many unique pitches (>50) = random
- ❌ Very high intervals (>7 mean) = jumpy/unmusical
- ❌ High repetition ratio (>0.20) = boring
- ❌ Low entropy (<2.5) = predictable
- ❌ High entropy (>6) = too random

### Temperature Effects

**Lower Temperature (0.8-1.0)**:
- More predictable
- Safer note choices
- Lower entropy
- More repetitive
- Better for coherent melodies

**Higher Temperature (1.5-2.0)**:
- More random
- Adventurous note choices
- Higher entropy
- More variety
- Can sound chaotic

**Sweet Spot**: Usually 1.0-1.5 depending on model

---

## 🎵 Example Evaluation Workflow

### After Training Version 2

1. **Generate evaluation data**:
```bash
python evaluate_model.py \
  --model music_rnn_model.keras \
  --output evaluation_v2 \
  --num-samples 5 \
  --num-notes 100
```

2. **Check metrics** in `evaluation_v2/evaluation_results.json`

3. **Listen to MIDI files**:
   - temp1.0_sample1.mid
   - temp1.0_sample2.mid
   - etc.

4. **Compare with v1** (if you have it):
```bash
python evaluate_model.py \
  --model music_rnn_model.keras \
  --output evaluation_v2 \
  --compare evaluation_v1/evaluation_results.json
```

5. **Document findings** in CHANGES_SUMMARY.md:
```
### Experiment 3: Stacked LSTM + Stability
- Final epoch: 42
- Final loss: 1.52
- **Metrics**:
  - Unique pitches: 24.6 (+33% vs v1)
  - Pitch entropy: 4.12 (+19% vs v1)
  - Repetition: 0.09 (-36% vs v1)
- **Listening**: Much better melodies, more musical coherence
- **Best temperature**: 1.2
```

---

## 🔍 Advanced Analysis

### Custom Metrics

Add your own metrics by editing `evaluate_model.py`:

```python
# In compute_metrics() function, add:

# Chromatic vs diatonic analysis
chromatic_notes = sum(1 for p in pitches if (p % 12) in [1, 3, 6, 8, 10])
metrics['chromatic_ratio'] = chromatic_notes / len(pitches)

# Ascending vs descending tendency
ascending = sum(1 for i in intervals if i > 0)
metrics['ascending_ratio'] = ascending / len(intervals)
```

### Batch Comparison

Compare multiple models at once:

```bash
# Evaluate all models
for model in model_v1.keras model_v2.keras model_v3.keras; do
  python evaluate_model.py --model $model --output eval_${model%.keras}
done

# Compare each to baseline
python evaluate_model.py --model model_v2.keras --output eval_v2 \
  --compare eval_v1/evaluation_results.json
python evaluate_model.py --model model_v3.keras --output eval_v3 \
  --compare eval_v1/evaluation_results.json
```

---

## 📝 Evaluation Checklist

Before moving to next optimization:

- [ ] Run quantitative evaluation
- [ ] Generate MIDI files at multiple temperatures
- [ ] Listen to at least 5 samples per temperature
- [ ] Fill out subjective rating sheet
- [ ] Compare metrics to previous version
- [ ] Identify temperature sweet spot
- [ ] Document findings in experiment log
- [ ] Save best samples for reference

---

## 🎯 Decision Matrix

**Should I keep this model or iterate?**

| Metric Change vs Previous | Action |
|---------------------------|--------|
| ✅ All metrics improved 5%+ | Keep it! Great improvement |
| ✅ Key metrics improved 10%+ | Keep it! Focus on other aspects |
| 🟡 Mixed results | Listen test is tie-breaker |
| 🟡 Metrics improved but sounds worse | Trust your ears, iterate |
| ❌ Most metrics degraded | Revert, try different approach |

**Key metrics** (most important):
1. pitch_entropy (variety)
2. repetition_ratio (not boring)
3. mean_interval (melodic smoothness)
4. Listening test overall score

---

## 💡 Tips

1. **Always use same seed** for fair comparison
2. **Evaluate multiple samples** (variance is high)
3. **Listen at multiple temperatures** to find sweet spot
4. **Save MIDI files** for later reference
5. **Trust your ears** - metrics don't capture everything
6. **Test with your DAW** - add instruments/effects
7. **Share samples** - get feedback from others

---

## 🚨 Common Issues

**Problem**: Metrics look good but sounds bad
- **Solution**: Metrics don't capture musicality perfectly, trust listening test

**Problem**: High variance between samples
- **Solution**: Generate more samples (10-20) for stable averages

**Problem**: Can't decide which temperature is best
- **Solution**: Try fractional temps (1.1, 1.3, 1.4) to narrow down

**Problem**: Model worse despite better architecture
- **Solution**: May need more training epochs or LR tuning

---

*Use this guide to systematically evaluate each model version!*
