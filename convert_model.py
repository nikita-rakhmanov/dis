#!/usr/bin/env python3
"""
Convert model to be compatible with different TensorFlow versions.
Run this on the GPU machine after training.
"""

import tensorflow as tf
import os

def mse_with_positive_pressure(y_true, y_pred):
    """Custom loss function needed for model loading."""
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)

# Load the model
print("Loading model...")
model = tf.keras.models.load_model(
    'music_rnn_model.keras',
    custom_objects={'mse_with_positive_pressure': mse_with_positive_pressure}
)

print("Model loaded successfully!")
print(f"Input shape: {model.input_shape}")
print(f"Output shapes: {[(name, output.shape) for name, output in model.output.items()]}")

# Save in H5 format (more compatible)
h5_path = 'music_rnn_model.h5'
print(f"\nSaving model to {h5_path}...")
model.save(h5_path, save_format='h5')

# Also save weights only
weights_path = 'music_rnn_weights.h5'
print(f"Saving weights to {weights_path}...")
model.save_weights(weights_path)

print("\n✅ Conversion complete!")
print("Files created:")
print(f"  - {h5_path} (full model in H5 format)")
print(f"  - {weights_path} (weights only)")
print("\nCopy these files to your local machine along with seed_sequence.npy")
