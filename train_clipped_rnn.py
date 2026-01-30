#!/usr/bin/env python3
"""
Train a Clipped-Vocabulary Melody RNN.
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

# Enable mixed precision for faster training on L4 GPU
from tensorflow.keras import mixed_precision
mixed_precision.set_global_policy('mixed_float16')
print("Mixed precision enabled: float16 compute, float32 variables")

# Constants
SEED = 42
SEQUENCE_LENGTH = 50

# CLIPPED VOCABULARY - based on data analysis
MIN_PITCH = 48  # C3
MAX_PITCH = 89  # F6
VOCAB_SIZE = MAX_PITCH - MIN_PITCH + 1  # 42 classes

BATCH_SIZE = 256
EPOCHS = 30
LEARNING_RATE = 0.002
NUM_TRAINING_FILES = 1200
ONSET_BIAS = 12

# Preprocessing Thresholds
MIN_NOTE_DURATION = 0.05
MERGE_GAP_THRESHOLD = 0.05

# Output files
MODEL_OUTPUT = 'clipped_melody_model.keras'
METADATA_OUTPUT = 'clipped_model_metadata.json'
SEED_OUTPUT = 'clipped_seed_sequence.npy'

tf.random.set_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

print(f"Clipped Vocabulary: {MIN_PITCH}-{MAX_PITCH} ({VOCAB_SIZE} classes)")


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
    """Extract melody using Onset-Biased Skyline."""
    all_notes = []
    for instrument in pm.instruments:
        if not instrument.is_drum:
            all_notes.extend(instrument.notes)
    
    if not all_notes:
        return []

    events = []
    for i, note in enumerate(all_notes):
        events.append((note.start, 1, note.pitch, i))
        events.append((note.end, 0, note.pitch, i))
    
    events.sort(key=lambda x: (x[0], x[1]))
    
    melody_notes = []
    active_notes = {}
    current_melody_note = None
    
    def get_effective_pitch(note_info, current_time):
        is_onset = (current_time - note_info['start']) < 0.1
        return note_info['pitch'] + (ONSET_BIAS if is_onset else 0)

    for i in range(len(events) - 1):
        time, type, pitch, idx = events[i]
        next_time = events[i+1][0]
        
        if type == 1:
            active_notes[idx] = {'pitch': pitch, 'start': time}
        else:
            if idx in active_notes:
                del active_notes[idx]
        
        if not active_notes:
            winner_pitch = None
        else:
            winner_pitch = -1
            max_score = -999
            for nid, info in active_notes.items():
                score = get_effective_pitch(info, time)
                if score > max_score:
                    max_score = score
                    winner_pitch = info['pitch']
                    
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


def clip_pitch(pitch):
    """Clip pitch to vocabulary range and convert to class index."""
    clipped = max(MIN_PITCH, min(MAX_PITCH, pitch))
    return clipped - MIN_PITCH  # 0-indexed class


def compute_dataset_stats(filenames, sample_size=200):
    """Scan subset for normalization constants."""
    print(f"Scanning {sample_size} files for stats...")
    deltas = []
    clipped_count = 0
    total_notes = 0
    
    files_to_scan = filenames[:sample_size] if len(filenames) > sample_size else filenames
    
    for f in files_to_scan:
        try:
            pm = pretty_midi.PrettyMIDI(f)
            notes = onset_biased_skyline(pm)
            notes = post_process_notes(notes)
            
            prev_start = 0.0
            for n in notes:
                total_notes += 1
                # Track clipping
                if n['pitch'] < MIN_PITCH or n['pitch'] > MAX_PITCH:
                    clipped_count += 1
                
                d = n['start'] - prev_start
                if d < 0: d = 0
                deltas.append(d)
                prev_start = n['start']
        except:
            continue
            
    if not deltas:
        return 1.0
    
    clip_pct = clipped_count / total_notes * 100 if total_notes > 0 else 0
    print(f"Notes clipped to range: {clipped_count}/{total_notes} ({clip_pct:.1f}%)")
        
    log_deltas = np.log1p(deltas)
    max_val = np.percentile(log_deltas, 99)
    print(f"Stats: 99th percentile LogDelta = {max_val:.4f}")
    return float(max_val)


def process_file_to_features(filename, max_log_delta):
    """Yield windowed features with clipped pitch."""
    try:
        pm = pretty_midi.PrettyMIDI(filename)
        notes = onset_biased_skyline(pm)
        notes = post_process_notes(notes)
        
        if len(notes) <= SEQUENCE_LENGTH:
            return
            
        feats = []
        prev_start = 0.0
        for n in notes:
            d = n['start'] - prev_start
            prev_start = n['start']
            if d < 0: d = 0
            
            ld = np.log1p(d)
            ld_norm = ld / max_log_delta
            
            # CLIPPED PITCH (0 to VOCAB_SIZE-1)
            pitch_class = clip_pitch(n['pitch'])
            feats.append([pitch_class, ld_norm])
            
        feats = np.array(feats, dtype=np.float32)
        
        num_windows = len(feats) - SEQUENCE_LENGTH
        
        for i in range(num_windows):
            window = feats[i:i+SEQUENCE_LENGTH]
            target = feats[i+SEQUENCE_LENGTH]
            
            inp = np.copy(window)
            inp[:, 0] /= float(VOCAB_SIZE)  # Normalize to 0-1
            
            t_pitch = int(target[0])  # Class index (0 to 41)
            t_time = target[1]
            
            yield inp, (t_pitch, t_time)
            
    except Exception as e:
        pass


def build_clipped_model(input_shape):
    """Build model with clipped vocabulary output."""
    inputs = tf.keras.Input(shape=input_shape)
    
    x = tf.keras.layers.LSTM(256, return_sequences=True)(inputs)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.LSTM(128)(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    
    # Output: VOCAB_SIZE classes (42 instead of 128)
    pitch_out = tf.keras.layers.Dense(VOCAB_SIZE, activation='softmax', name='pitch_head')(x)
    time_out = tf.keras.layers.Dense(1, activation='linear', name='time_head')(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=[pitch_out, time_out])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss={'pitch_head': 'sparse_categorical_crossentropy', 'time_head': 'mse'},
        loss_weights={'pitch_head': 1.0, 'time_head': 10.0},
        metrics={'pitch_head': 'accuracy'}
    )
    return model


def main():
    print("=" * 60)
    print("Clipped Vocabulary Melody Training")
    print(f"Vocabulary: {MIN_PITCH}-{MAX_PITCH} ({VOCAB_SIZE} classes)")
    print("=" * 60)
    
    data_dir = pathlib.Path('data/maestro-v3.0.0')
    download_dataset_v3(data_dir)
    
    filenames = glob.glob(str(data_dir / '**/*.mid*'), recursive=True)
    if not filenames:
        filenames = glob.glob('data/maestro-v3.0.0/**/*.mid*', recursive=True)
    
    random.shuffle(filenames)
    train_files = filenames[:NUM_TRAINING_FILES]
    print(f"Selected {len(train_files)} files for training.")
    
    max_log_delta = compute_dataset_stats(train_files)
    
    # Save metadata
    metadata = {
        'max_log_delta': max_log_delta,
        'vocab_size': VOCAB_SIZE,
        'min_pitch': MIN_PITCH,
        'max_pitch': MAX_PITCH,
        'sequence_length': SEQUENCE_LENGTH
    }
    with open(METADATA_OUTPUT, 'w') as f:
        json.dump(metadata, f)
    print(f"Saved {METADATA_OUTPUT}")
    
    # Train/val split
    val_split_idx = int(len(train_files) * 0.9)
    val_files = train_files[val_split_idx:]
    train_files_final = train_files[:val_split_idx]
    
    def train_gen():
        for f in train_files_final:
            yield from process_file_to_features(f, max_log_delta)
            
    def val_gen():
        for f in val_files:
            yield from process_file_to_features(f, max_log_delta)

    output_signature = (
        tf.TensorSpec(shape=(SEQUENCE_LENGTH, 2), dtype=tf.float32),
        (
            tf.TensorSpec(shape=(), dtype=tf.int32),
            tf.TensorSpec(shape=(), dtype=tf.float32)
        )
    )
    
    train_ds = tf.data.Dataset.from_generator(train_gen, output_signature=output_signature)\
        .shuffle(10000).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
        
    val_ds = tf.data.Dataset.from_generator(val_gen, output_signature=output_signature)\
        .batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

    print("\nBuilding Model...")
    model = build_clipped_model((SEQUENCE_LENGTH, 2))
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
        tf.keras.callbacks.ModelCheckpoint(MODEL_OUTPUT, save_best_only=True, verbose=1),
        checkpoint_logger
    ]
    
    print("\nStarting Training...")
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks
    )
    
    # Save seed
    for batch_x, _ in train_ds.take(1):
        seed_seq = batch_x[0].numpy()
        np.save(SEED_OUTPUT, seed_seq)
        print(f"Saved {SEED_OUTPUT}")
        break
        
    print(f"\nDone! Model saved to {MODEL_OUTPUT}")


if __name__ == "__main__":
    main()
