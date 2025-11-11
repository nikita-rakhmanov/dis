#!/usr/bin/env python3
"""
Train an RNN to generate music from MIDI files.
Based on TensorFlow's music generation tutorial.
"""

import collections
import glob
import pathlib
import numpy as np
import pandas as pd
import tensorflow as tf
import pretty_midi
from typing import Optional

# Configuration
SEED = 42
SEQUENCE_LENGTH = 25  # Increased from 25 to capture longer musical phrases
VOCAB_SIZE = 128
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 0.002  # Reduced from 0.005 for more stable training
NUM_TRAINING_FILES = 1000  # Start small, increase later

# Set random seeds
tf.random.set_seed(SEED)
np.random.seed(SEED)

KEY_ORDER = ['pitch', 'step', 'duration']


def download_dataset(data_dir: pathlib.Path):
    """Download the MAESTRO dataset if not present."""
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


def midi_to_notes(midi_file: str) -> pd.DataFrame:
    """Extract notes from a MIDI file."""
    pm = pretty_midi.PrettyMIDI(midi_file)
    instrument = pm.instruments[0]
    notes = collections.defaultdict(list)

    # Sort notes by start time
    sorted_notes = sorted(instrument.notes, key=lambda note: note.start)
    prev_start = sorted_notes[0].start

    for note in sorted_notes:
        start = note.start
        end = note.end
        notes['pitch'].append(note.pitch)
        notes['start'].append(start)
        notes['end'].append(end)
        notes['step'].append(start - prev_start)
        notes['duration'].append(end - start)
        prev_start = start

    return pd.DataFrame({name: np.array(value) for name, value in notes.items()})


def create_sequences(
    dataset: tf.data.Dataset,
    seq_length: int,
    vocab_size: int = 128,
) -> tf.data.Dataset:
    """Create sequences for training."""
    seq_length = seq_length + 1

    # Create windows
    windows = dataset.window(seq_length, shift=1, stride=1, drop_remainder=True)
    flatten = lambda x: x.batch(seq_length, drop_remainder=True)
    sequences = windows.flat_map(flatten)

    # Normalize and split labels
    def scale_pitch(x):
        x = x / [vocab_size, 1.0, 1.0]
        return x

    def split_labels(sequences):
        inputs = sequences[:-1]
        labels_dense = sequences[-1]
        labels = {key: labels_dense[i] for i, key in enumerate(KEY_ORDER)}
        return scale_pitch(inputs), labels

    return sequences.map(split_labels, num_parallel_calls=tf.data.AUTOTUNE)


def mse_with_positive_pressure(y_true: tf.Tensor, y_pred: tf.Tensor):
    """Custom loss function for step and duration."""
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)


def build_model(seq_length: int, vocab_size: int, learning_rate: float):
    """Build and compile the RNN model with Stacked LSTM architecture."""
    input_shape = (seq_length, 3)

    inputs = tf.keras.Input(input_shape)

    # Stacked LSTM architecture for better temporal modeling
    x = tf.keras.layers.LSTM(256, return_sequences=True)(inputs)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.LSTM(128)(x)

    outputs = {
        'pitch': tf.keras.layers.Dense(vocab_size, name='pitch')(x),
        'step': tf.keras.layers.Dense(1, name='step')(x),
        'duration': tf.keras.layers.Dense(1, name='duration')(x),
    }

    model = tf.keras.Model(inputs, outputs)

    loss = {
        'pitch': tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        'step': mse_with_positive_pressure,
        'duration': mse_with_positive_pressure,
    }

    model.compile(
        loss=loss,
        loss_weights={
            'pitch': 0.25,  # Increased from 0.05 to improve melodic quality
            'step': 1.0,
            'duration': 1.0,
        },
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
    )

    return model


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("Music RNN Training Script")
    print("=" * 60)
    
    # Setup data directory
    data_dir = pathlib.Path('data/maestro-v2_extracted')
    download_dataset(data_dir)
    
    # Find MIDI files
    filenames = glob.glob(str(data_dir / '**/*.mid*'), recursive=True)
    print(f"\nFound {len(filenames)} MIDI files")
    
    if len(filenames) == 0:
        print("ERROR: No MIDI files found!")
        print(f"Please check that data exists at: {data_dir}")
        return
    
    # Parse notes from MIDI files
    print(f"\nParsing notes from {NUM_TRAINING_FILES} files...")
    all_notes = []
    for i, f in enumerate(filenames[:NUM_TRAINING_FILES]):
        print(f"  [{i+1}/{NUM_TRAINING_FILES}] {pathlib.Path(f).name}")
        try:
            notes = midi_to_notes(f)
            all_notes.append(notes)
        except Exception as e:
            print(f"    Warning: Could not parse file: {e}")
    
    if not all_notes:
        print("ERROR: No notes could be parsed!")
        return
    
    all_notes = pd.concat(all_notes)
    n_notes = len(all_notes)
    print(f"\nTotal notes parsed: {n_notes}")
    
    # Create dataset
    print("\nCreating training dataset...")
    train_notes = np.stack([all_notes[key] for key in KEY_ORDER], axis=1)
    notes_ds = tf.data.Dataset.from_tensor_slices(train_notes)
    seq_ds = create_sequences(notes_ds, SEQUENCE_LENGTH, VOCAB_SIZE)
    
    buffer_size = n_notes - SEQUENCE_LENGTH
    train_ds = (seq_ds
                .shuffle(buffer_size)
                .batch(BATCH_SIZE, drop_remainder=True)
                .cache()
                .prefetch(tf.data.experimental.AUTOTUNE))
    
    # Build model
    print("\nBuilding model...")
    model = build_model(SEQUENCE_LENGTH, VOCAB_SIZE, LEARNING_RATE)
    model.summary()
    
    # Setup callbacks
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath='./training_checkpoints/ckpt_{epoch}.weights.h5',
            save_weights_only=True),
        tf.keras.callbacks.EarlyStopping(
            monitor='loss',
            patience=5,
            verbose=1,
            restore_best_weights=True),
    ]
    
    # Train
    print(f"\nTraining for {EPOCHS} epochs...")
    print("=" * 60)
    history = model.fit(
        train_ds,
        epochs=EPOCHS,
        callbacks=callbacks,
    )
    
    # Save the full model
    model_path = 'music_rnn_model.keras'
    print(f"\nSaving model to {model_path}...")
    model.save(model_path)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: {model_path}")
    print("=" * 60)
    
    # Save a sample starting sequence for generation
    sample_notes = np.stack([all_notes[key] for key in KEY_ORDER], axis=1)
    seed_sequence = sample_notes[:SEQUENCE_LENGTH]
    np.save('seed_sequence.npy', seed_sequence)
    print(f"Seed sequence saved to: seed_sequence.npy")


if __name__ == "__main__":
    main()