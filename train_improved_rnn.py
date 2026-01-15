#!/usr/bin/env python3
"""
Train an Improved Melody RNN (Experiment).

Features:
1. Dataset: MAESTRO v3.0.0.
2. Melody Extraction: Onset-Biased Skyline Algorithm.
   - Prefers new attacks over sustaining high notes.
3. Preprocessing:
   - Drop short notes (< 50ms).
   - Merge gaps (< 50ms).
4. Representation: (Pitch, Log-Delta-Time).
   - Pitch: Normalized 0-1.
   - Time: Log1p scaled and Normalized by dataset max.
5. Pipeline: tf.data Generator (Memory Efficient).
6. GPU Optimization: Mixed precision for L4/Tensor Cores.
"""

import collections
import glob
import pathlib
import numpy as np
import tensorflow as tf
import pretty_midi
import random
import os
import json

# Enable mixed precision for faster training on L4 GPU (uses Tensor Cores)
from tensorflow.keras import mixed_precision
mixed_precision.set_global_policy('mixed_float16')
print("Mixed precision enabled: float16 compute, float32 variables")

# Constants
SEED = 42
SEQUENCE_LENGTH = 50
VOCAB_SIZE = 128
BATCH_SIZE = 256  # Increased for L4 GPU (24GB VRAM)
EPOCHS = 30
LEARNING_RATE = 0.002
NUM_TRAINING_FILES = 1200
ONSET_BIAS = 12  # Semitones bonus for onset (e.g. 1 octave)

# Preprocessing Thresholds
MIN_NOTE_DURATION = 0.05
MERGE_GAP_THRESHOLD = 0.05

tf.random.set_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)


def download_dataset_v3(data_dir: pathlib.Path):
    """Download MAESTRO v3.0.0 if needed."""
    if not data_dir.exists():
        print("Downloading MAESTRO v3.0.0 dataset...")
        tf.keras.utils.get_file(
            'maestro-v3.0.0-midi.zip',
            origin='https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0-midi.zip',
            extract=True,
            cache_dir='.',
            cache_subdir='data',
        )
        print("Dataset downloaded!")
    else:
        print(f"Dataset found at {data_dir}")


def onset_biased_skyline(pm):
    """
    Extract melody using Onset-Biased Skyline.
    Algo: EffectivePitch = RealPitch + (Bias if is_onset else 0)
    At any time t, Melody = Note with max EffectivePitch.
    """
    all_notes = []
    for instrument in pm.instruments:
        if not instrument.is_drum:
            all_notes.extend(instrument.notes)
    
    if not all_notes:
        return []

    # Events: (time, type, pitch, id)
    # Types: 0=End, 1=Start (Start processed AFTER End if times equal, to handle legato)
    # wait, if legato (end==start), we want start to register. 
    # Sorting: Time asc. If time equal: End before Start? 
    # If end happens at T and start happens at T. 
    # If we process End first: note acts removed. Then Start adds new note.
    # This seems correct for monophonic extraction.
    
    events = []
    for i, note in enumerate(all_notes):
        events.append((note.start, 1, note.pitch, i))  # 1 = Start
        events.append((note.end, 0, note.pitch, i))    # 0 = End
    
    # Sort: Time Ascending, then Type Ascending (End=0 before Start=1)
    events.sort(key=lambda x: (x[0], x[1]))
    
    melody_notes = []
    active_notes = {}  # id -> {pitch, start_time}
    
    # Track current melody state
    current_melody_note = None # {start, pitch, end}
    
    # Skyline Bias Window
    # We apply bias for a short duration after onset
    bias_duration = 0.05 # 50ms (or just apply to the "latest" note?)
    # Alternative strategy: "The note that started most recently" gets a bonus?
    # Common Skyline algo: Pitch + V(t). V(t) decays?
    
    # Simple Onset Bias:
    # We just track "active notes". The most recent onset gets a virtual pitch boost.
    # But for how long? 
    # Let's stick to a simpler interpretation: "Latest Onset wins if pitch is close enough"
    # Or: "score = pitch + 12 if (time - note.start < 0.1) else pitch"
    
    def get_effective_pitch(note_info, current_time):
        is_onset = (current_time - note_info['start']) < 0.1 # 100ms window
        return note_info['pitch'] + (ONSET_BIAS if is_onset else 0)

    for i in range(len(events) - 1):
        time, type, pitch, idx = events[i]
        next_time = events[i+1][0]
        
        if type == 1: # Start
            active_notes[idx] = {'pitch': pitch, 'start': time}
        else: # End
            if idx in active_notes:
                del active_notes[idx]
        
        # Determine melody for [time, next_time]
        if not active_notes:
            winner_pitch = None
        else:
            # Find note with max effective pitch
            winner_pitch = -1
            max_score = -999
            
            for nid, info in active_notes.items():
                score = get_effective_pitch(info, time)
                if score > max_score:
                    max_score = score
                    winner_pitch = info['pitch']
                    
        # Update melody sequence
        if next_time > time:
            if winner_pitch is not None:
                if current_melody_note is None:
                    current_melody_note = {'start': time, 'pitch': winner_pitch, 'end': next_time}
                    melody_notes.append(current_melody_note)
                elif current_melody_note['pitch'] != winner_pitch:
                    current_melody_note['end'] = time
                    current_melody_note = {'start': time, 'pitch': winner_pitch, 'end': next_time}
                    melody_notes.append(current_melody_note)
                else:
                    current_melody_note['end'] = next_time
            else:
                if current_melody_note is not None:
                    current_melody_note['end'] = time
                    current_melody_note = None
                    
    return melody_notes


def post_process_notes(raw_notes):
    """Merge short gaps and drop short notes."""
    if not raw_notes: return []
    merged = []
    if raw_notes:
        current = raw_notes[0]
        for next_note in raw_notes[1:]:
            gap = next_note['start'] - current['end']
            if next_note['pitch'] == current['pitch'] and gap < MERGE_GAP_THRESHOLD:
                current['end'] = next_note['end']
            else:
                merged.append(current)
                current = next_note
        merged.append(current)
    return [n for n in merged if (n['end'] - n['start']) >= MIN_NOTE_DURATION]


def compute_dataset_stats(filenames, sample_size=200):
    """
    Scan a subset of files to determine normalization constants.
    Returns: max_log_delta
    """
    print(f"Scanning {sample_size} files for stats...")
    deltas = []
    
    # Shuffle and pick subset
    files_to_scan = filenames[:sample_size] if len(filenames) > sample_size else filenames
    
    for f in files_to_scan:
        try:
            pm = pretty_midi.PrettyMIDI(f)
            notes = onset_biased_skyline(pm)
            notes = post_process_notes(notes)
            
            prev_start = 0.0
            for n in notes:
                d = n['start'] - prev_start
                if d < 0: d = 0
                deltas.append(d)
                prev_start = n['start']
        except:
            continue
            
    if not deltas:
        return 1.0
        
    # Log1p scale
    log_deltas = np.log1p(deltas)
    
    # 99th percentile to filter outliers
    max_val = np.percentile(log_deltas, 99)
    print(f"Stats: 99th percentile LogDelta = {max_val:.4f}")
    return float(max_val)


def process_file_to_features(filename, max_log_delta):
    """Yield windowed features and targets from a single file."""
    try:
        pm = pretty_midi.PrettyMIDI(filename)
        notes = onset_biased_skyline(pm)
        notes = post_process_notes(notes)
        
        if len(notes) <= SEQUENCE_LENGTH:
            return
            
        # Convert to features
        feats = []
        prev_start = 0.0
        for n in notes:
            d = n['start'] - prev_start
            prev_start = n['start']
            if d < 0: d = 0
            
            # 1. Log1p
            ld = np.log1p(d)
            # 2. Normalize
            ld_norm = ld / max_log_delta
            
            feats.append([n['pitch'], ld_norm])
            
        feats = np.array(feats, dtype=np.float32)
        
        # Create Sliding Windows
        num_windows = len(feats) - SEQUENCE_LENGTH
        
        for i in range(num_windows):
            window = feats[i:i+SEQUENCE_LENGTH]
            target = feats[i+SEQUENCE_LENGTH]
            
            # Prepare Input
            inp = np.copy(window)
            inp[:, 0] /= float(VOCAB_SIZE) # Norm Pitch Input
            
            # Targets
            t_pitch = int(target[0])
            t_time = target[1] # Already normalized log delta
            
            yield inp, (t_pitch, t_time)
            
    except Exception as e:
        # print(f"Skipping {filename}: {e}")
        pass


def build_improved_model(input_shape):
    inputs = tf.keras.Input(shape=input_shape)
    
    x = tf.keras.layers.LSTM(256, return_sequences=True)(inputs)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.LSTM(128)(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    
    pitch_out = tf.keras.layers.Dense(VOCAB_SIZE, activation='softmax', name='pitch_head')(x)
    time_out = tf.keras.layers.Dense(1, activation='linear', name='time_head')(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=[pitch_out, time_out])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss={'pitch_head': 'sparse_categorical_crossentropy', 'time_head': 'mse'},
        loss_weights={'pitch_head': 1.0, 'time_head': 10.0}, # Boost time weight as normalized values are small
        metrics={'pitch_head': 'accuracy'}
    )
    return model


def main():
    print("="*60)
    print("Improved Melody Training (Expert Refactor)")
    print("="*60)
    
    data_dir = pathlib.Path('data/maestro-v3.0.0')
    download_dataset_v3(data_dir)
    
    filenames = glob.glob(str(data_dir / '**/*.mid*'), recursive=True)
    if not filenames:
         filenames = glob.glob('data/maestro-v3.0.0/**/*.mid*', recursive=True)
    
    random.shuffle(filenames)
    train_files = filenames[:NUM_TRAINING_FILES]
    print(f"Selected {len(train_files)} files for training.")
    
    # 1. Compute Stats
    max_log_delta = compute_dataset_stats(train_files)
    
    # 2. Save Metadata
    metadata = {
        'max_log_delta': max_log_delta,
        'vocab_size': VOCAB_SIZE,
        'sequence_length': SEQUENCE_LENGTH
    }
    with open('model_metadata.json', 'w') as f:
        json.dump(metadata, f)
    print("Saved model_metadata.json")
    
    # 3. Create Generator Dataset
    def data_generator():
        for f in train_files:
            yield from process_file_to_features(f, max_log_delta)

    output_signature = (
        tf.TensorSpec(shape=(SEQUENCE_LENGTH, 2), dtype=tf.float32),
        (
            tf.TensorSpec(shape=(), dtype=tf.int32),   # Pitch target
            tf.TensorSpec(shape=(), dtype=tf.float32)  # Time target
        )
    )
    
    dataset = tf.data.Dataset.from_generator(
        data_generator, 
        output_signature=output_signature
    )
    
    # Shuffle and Batch
    dataset = dataset.shuffle(buffer_size=10000)
    dataset = dataset.batch(BATCH_SIZE)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)
    
    # Validation split approach (approximate)
    # Since we stream, simpler to just train on all or split filenames manually.
    # We'll split filenames for robustness.
    val_split_idx = int(len(train_files) * 0.9)
    val_files = train_files[val_split_idx:]
    train_files_final = train_files[:val_split_idx]
    
    def train_gen():
        for f in train_files_final:
            yield from process_file_to_features(f, max_log_delta)
            
    def val_gen():
        for f in val_files:
            yield from process_file_to_features(f, max_log_delta)
            
    train_ds = tf.data.Dataset.from_generator(train_gen, output_signature=output_signature)\
        .shuffle(10000).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
        
    val_ds = tf.data.Dataset.from_generator(val_gen, output_signature=output_signature)\
        .batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

    # 4. Build and Train
    print("\nBuilding Model...")
    model = build_improved_model((SEQUENCE_LENGTH, 2))
    model.summary()
    
    # Custom callback to log checkpoint saves
    class CheckpointLogger(tf.keras.callbacks.Callback):
        def __init__(self):
            super().__init__()
            self.best_val_loss = float('inf')
            self.best_epoch = 0
            
        def on_epoch_end(self, epoch, logs=None):
            val_loss = logs.get('val_loss', float('inf'))
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.best_epoch = epoch + 1
                print(f"\n✓ New best model saved at epoch {self.best_epoch} (val_loss: {val_loss:.4f})")
    
    checkpoint_logger = CheckpointLogger()
    
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', 
            patience=5, 
            restore_best_weights=True,
            verbose=1  # Will print when early stopping triggers
        ),
        tf.keras.callbacks.ModelCheckpoint('improved_melody_model.keras', save_best_only=True, verbose=1),
        checkpoint_logger
    ]
    
    print("\nStarting Training...")
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks
    )
    
    # 5. Save Seed
    # Need to fetch one batch
    for batch_x, _ in train_ds.take(1):
        seed_seq = batch_x[0].numpy()
        np.save('improved_seed_sequence.npy', seed_seq)
        print("Saved improved_seed_sequence.npy")
        break
        
    print("Done.")

if __name__ == "__main__":
    main()
