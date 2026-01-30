#!/usr/bin/env python3
"""
Convert harmony model to be compatible with tf_keras (legacy keras).
Run this WITHOUT TF_USE_LEGACY_KERAS to load the Keras 3.x model,
then save as H5 for compatibility.
"""

import os
# Make sure we're NOT using legacy keras for loading
if 'TF_USE_LEGACY_KERAS' in os.environ:
    del os.environ['TF_USE_LEGACY_KERAS']

import tensorflow as tf
import numpy as np

# Load the harmony model (Keras 3.x format)
print("Loading harmony_model.keras...")
model = tf.keras.models.load_model('harmony_model.keras')

print("Model loaded successfully!")
print(f"Input shape: {model.input_shape}")
print(f"Output shape: {model.output_shape}")

# Save weights to numpy file (most portable)
weights = model.get_weights()
print(f"\nExtracting {len(weights)} weight arrays...")
np.savez('harmony_model_weights.npz', *weights)

# Also try .weights.h5 format
weights_path = 'harmony_model_converted.weights.h5'
print(f"Saving weights to {weights_path}...")
model.save_weights(weights_path)

print("\n✓ Conversion complete!")
print("Files created:")
print(f"  - harmony_model_weights.npz (numpy format)")
print(f"  - {weights_path} (Keras weights format)")
