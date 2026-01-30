#!/usr/bin/env python3
"""
Train a Harmony Generation Model (Model 2).

This script:
1. Loads MIDI files from the MAESTRO dataset.
2. Extracts melody-harmony pairs:
   - "Melody": Highest pitch note at a given time.
   - "Harmony": Other simultaneous notes.
3. Creates a dataset of (Melody Context + Current Melody) -> Harmony Note.
4. Trains the neural network defined in dual_model_polyphony.py.
"""

import collections
import glob
import pathlib
import numpy as np
import tensorflow as tf
import pretty_midi
import random
import os
from dual_model_polyphony import LearnedHarmonyModel

# Constants
SEED = 42
CONTEXT_LENGTH = 10
VOCAB_SIZE = 128
BATCH_SIZE = 64
EPOCHS = 20
LEARNING_RATE = 0.001
NUM_FILES_TO_PROCESS = 1282  # Adjust based on available compute/time

tf.random.set_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)


def download_dataset(data_dir: pathlib.Path):
    """Download the MAESTRO dataset if not present (reused from train_music_rnn.py)."""
    if not data_dir.exists():
        print("Downloading MAESTRO dataset...")
        tf.keras.utils.get_file(
            'maestro-v2.0.0-midi.zip',
            origin='https://storage.googleapis.com/magentadata/datasets/maestro/v2.0.0/maestro-v2.0.0-midi.zip',
            extract=True,
            cache_dir='.',
            cache_subdir='data',
        )
        print("Dataset downloaded!")
    else:
        print(f"Dataset found at {data_dir}")


def extract_melody_harmony_pairs(midi_file):
    """
    Extract training pairs from a MIDI file.
    Output format: List of (inputs, target)
    inputs: [current_melody_norm, ...context_flat...]
    target: harmony_pitch
    """
    try:
        pm = pretty_midi.PrettyMIDI(str(midi_file))
    except Exception as e:
        print(f"Warning: Could not parse {midi_file}: {e}")
        return [], []

    # Combine all notes from all instruments
    all_notes = []
    for instrument in pm.instruments:
        all_notes.extend(instrument.notes)
    
    # Sort by start time
    all_notes.sort(key=lambda x: x.start)

    if not all_notes:
        return [], []

    # Group notes by start time (quantized roughly)
    # flexible quantization to catch chords played slightly asynchronously
    chord_groups = collections.defaultdict(list)
    quantize_step = 0.05  # 50ms window
    
    for note in all_notes:
        quantized_start = round(note.start / quantize_step) * quantize_step
        chord_groups[quantized_start].append(note)

    inputs = []
    targets = []
    
    # Sliding window of melody history
    melody_history = []  # List of [pitch_norm, step, duration]
    
    sorted_times = sorted(chord_groups.keys())
    prev_time = sorted_times[0]

    for t in sorted_times:
        notes = chord_groups[t]
        if not notes:
            continue
            
        # Identify Melody (High Note) vs Harmony (others)
        # Sort notes in chord by pitch descending
        notes.sort(key=lambda x: x.pitch, reverse=True)
        
        melody_note = notes[0]
        harmony_notes = notes[1:]
        
        # Calculate step (time since last distinct melody note)
        step = t - prev_time
        duration = melody_note.end - melody_note.start
        
        melody_data = [
            melody_note.pitch / 128.0,  # Normalized pitch
            step,
            duration
        ]
        
        if harmony_notes:
            # Prepare context
            context_flat = np.array(melody_history[-CONTEXT_LENGTH:]).flatten()
            
            # Pad if needed
            required_len = CONTEXT_LENGTH * 3
            if len(context_flat) < required_len:
                padding = np.zeros(required_len - len(context_flat))
                context_flat = np.concatenate([padding, context_flat])
            
            # Construct full input vector: [current_note (3)] + [context (30)]
            full_input = np.concatenate([melody_data, context_flat])
            
            # For each harmony note, create a pair
            for h_note in harmony_notes:
                inputs.append(full_input)
                targets.append(h_note.pitch)

        # Update history
        melody_history.append(melody_data)
        prev_time = t

    return inputs, targets


def main():
    print("=" * 60)
    print("Harmony Model Training Script")
    print("=" * 60)

    # 1. Setup Data
    data_dir = pathlib.Path('data/maestro-v2_extracted')
    download_dataset(data_dir)
    
    filenames = glob.glob(str(data_dir / '**/*.mid*'), recursive=True)
    print(f"\nFound {len(filenames)} MIDI files")
    
    if len(filenames) == 0:
        print("No MIDI files found. Please check data directory.")
        return

    random.shuffle(filenames)
    filenames = filenames[:NUM_FILES_TO_PROCESS]
    
    print(f"Processing {len(filenames)} files to extract harmony pairs...")
    
    all_inputs = []
    all_targets = []
    
    for i, f in enumerate(filenames):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(filenames)} files...")
            
        inputs, targets = extract_melody_harmony_pairs(f)
        all_inputs.extend(inputs)
        all_targets.extend(targets)
        
    print(f"\nExtracted {len(all_inputs)} training pairs.")
    
    if len(all_inputs) == 0:
        print("No training data generated. Exiting.")
        return

    # Convert to numpy arrays
    X = np.array(all_inputs, dtype=np.float32)
    y = np.array(all_targets, dtype=np.int32)
    
    print(f"Input shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    
    # 2. Build Model
    print("\nBuilding model...")
    harmony_system = LearnedHarmonyModel()
    model = harmony_system.build_model(input_dim=X.shape[1], vocab_size=VOCAB_SIZE)
    model.summary()
    
    # 3. Train
    print(f"\nTraining for {EPOCHS} epochs...")
    
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint('harmony_model.keras', save_best_only=True)
    ]
    
    history = model.fit(
        X, y,
        validation_split=0.2,
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks
    )
    
    print("\nTraining complete!")
    print("Model saved to 'harmony_model.keras'")


if __name__ == "__main__":
    main()
