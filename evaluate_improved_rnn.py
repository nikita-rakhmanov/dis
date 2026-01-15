#!/usr/bin/env python3
"""
Fast Evaluation / Demo Script for Improved RNN.

Trains on a tiny subset of data to visualize loss convergence.
Outputs a plot of Pitch Loss vs Time Loss.
"""

import matplotlib.pyplot as plt
import train_improved_rnn as improved_train
import tensorflow as tf
import numpy as np
import pathlib
import glob
import random
import os

# Demo Config
NUM_DEMO_FILES = 50   # Small subset for speed
DEMO_EPOCHS = 10      # Enough to see a curve
BATCH_SIZE = 64

def train_and_plot():
    print("="*60)
    print("Fast Evaluation Demo")
    print("="*60)
    
    # 1. Setup Data
    data_dir = pathlib.Path('data/maestro-v3.0.0')
    improved_train.download_dataset_v3(data_dir)
    
    filenames = glob.glob(str(data_dir / '**/*.mid*'), recursive=True)
    if not filenames:
         filenames = glob.glob('data/maestro-v3.0.0/**/*.mid*', recursive=True)
    
    random.shuffle(filenames)
    demo_files = filenames[:NUM_DEMO_FILES]
    print(f"Docs: {len(filenames)} -> Selected {len(demo_files)} for demo.")
    
    # 2. Stats
    max_log_delta = improved_train.compute_dataset_stats(demo_files, sample_size=50)
    
    # 3. Generator
    def data_generator():
        for f in demo_files:
            yield from improved_train.process_file_to_features(f, max_log_delta)

    output_signature = (
        tf.TensorSpec(shape=(improved_train.SEQUENCE_LENGTH, 2), dtype=tf.float32),
        (
            tf.TensorSpec(shape=(), dtype=tf.int32),
            tf.TensorSpec(shape=(), dtype=tf.float32)
        )
    )
    
    dataset = tf.data.Dataset.from_generator(
        data_generator, 
        output_signature=output_signature
    ).shuffle(1000).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    
    # 4. Model
    model = improved_train.build_improved_model((improved_train.SEQUENCE_LENGTH, 2))
    
    # 5. Train & Capture History
    print("\nStarting Demo Training...")
    history = model.fit(
        dataset,
        epochs=DEMO_EPOCHS,
        verbose=1
    )
    
    # 6. Plotting
    print("\nPlotting results...")
    metrics = history.history
    
    plt.figure(figsize=(12, 5))
    
    # Plot Pitch Loss
    plt.subplot(1, 2, 1)
    plt.plot(metrics['pitch_head_loss'], label='Pitch Loss')
    plt.title('Pitch Convergence')
    plt.xlabel('Epoch')
    plt.ylabel('Loss (CrossEntropy)')
    plt.legend()
    plt.grid(True)
    
    # Plot Time Loss
    plt.subplot(1, 2, 2)
    plt.plot(metrics['time_head_loss'], label='Time Loss')
    plt.title('Time Convergence')
    plt.xlabel('Epoch')
    plt.ylabel('Loss (MSE)')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    output_img = 'demo_loss_curve.png'
    plt.savefig(output_img)
    print(f"Loss curve saved to: {output_img}")
    print("Check this image to see if the model is learning!")

if __name__ == "__main__":
    train_and_plot()
