#!/usr/bin/env python3
"""
Fast Evaluation / Demo Script for Original RNN (train_music_rnn.py).

Trains on a tiny subset of data to visualize loss convergence.
Outputs a plot of Pitch Loss vs Step/Duration Loss.
"""

import matplotlib.pyplot as plt
import train_music_rnn as original_train
import tensorflow as tf
import numpy as np
import pathlib
import glob
import random
import pandas as pd
import os

# Demo Config
NUM_DEMO_FILES = 50   # Same size as improved demo
DEMO_EPOCHS = 10      
BATCH_SIZE = 64
SEQ_LENGTH = 50
VOCAB_SIZE = 128

def train_and_plot():
    print("="*60)
    print("Original Model Fast Evaluation Demo")
    print("="*60)
    
    # 1. Setup Data (TensorFlow extracts to maestro-v2.0.0, not maestro-v2_extracted)
    data_dir = pathlib.Path('data/maestro-v2.0.0')
    original_train.download_dataset(data_dir)
    
    filenames = glob.glob(str(data_dir / '**/*.mid*'), recursive=True)
    random.shuffle(filenames)
    demo_files = filenames[:NUM_DEMO_FILES]
    print(f"Docs: {len(filenames)} -> Selected {len(demo_files)} for demo.")
    
    # 2. Process Data (In-memory approach from original script)
    # Note: original script loads all into RAM. For 50 files it works fine.
    print("Parsing notes...")
    all_notes = []
    for f in demo_files:
        try:
            notes = original_train.midi_to_notes(f)
            all_notes.append(notes)
        except Exception:
            pass
            
    if not all_notes:
        print("No notes parsed!")
        return

    all_notes = pd.concat(all_notes)
    n_notes = len(all_notes)
    print(f"Total notes: {n_notes}")

    train_notes = np.stack([all_notes[key] for key in original_train.KEY_ORDER], axis=1)
    notes_ds = tf.data.Dataset.from_tensor_slices(train_notes)
    seq_ds = original_train.create_sequences(notes_ds, SEQ_LENGTH, VOCAB_SIZE)
    
    dataset = (seq_ds
                .shuffle(1000) # Small buffer for demo
                .batch(BATCH_SIZE, drop_remainder=True)
                .prefetch(tf.data.experimental.AUTOTUNE))
    
    # 3. Model
    model = original_train.build_model(SEQ_LENGTH, VOCAB_SIZE, original_train.LEARNING_RATE)
    
    # 4. Train
    print("\nStarting Demo Training...")
    history = model.fit(
        dataset,
        epochs=DEMO_EPOCHS,
        verbose=1
    )
    
    # 5. Plotting
    # Original has 3 losses: pitch, step, duration
    print("\nPlotting results...")
    metrics = history.history
    
    plt.figure(figsize=(15, 5))
    
    # Plot Pitch Loss
    plt.subplot(1, 3, 1)
    plt.plot(metrics['pitch_loss'], label='Pitch Loss')
    plt.title('Pitch Convergence')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    # Plot Step Loss
    plt.subplot(1, 3, 2)
    plt.plot(metrics['step_loss'], label='Step Loss')
    plt.title('Step (Time) Convergence')
    plt.xlabel('Epoch')
    plt.ylabel('Loss (Custom MSE)')
    plt.legend()
    plt.grid(True)

    # Plot Duration Loss
    plt.subplot(1, 3, 3)
    plt.plot(metrics['duration_loss'], label='Duration Loss')
    plt.title('Duration Convergence')
    plt.xlabel('Epoch')
    plt.ylabel('Loss (Custom MSE)')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    output_img = 'original_demo_loss_curve.png'
    plt.savefig(output_img)
    print(f"Loss curve saved to: {output_img}")
    print("Compare this with 'demo_loss_curve.png'!")

if __name__ == "__main__":
    train_and_plot()
