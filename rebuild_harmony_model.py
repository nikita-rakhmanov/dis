#!/usr/bin/env python3
"""
Rebuild harmony model compatible with tf_keras (legacy keras).
This creates a fresh model with the same architecture and transfers weights.
"""

import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import numpy as np
import tensorflow as tf

print("Building harmony model with tf_keras...")

# Build the same architecture as in dual_model_polyphony.py
input_dim = 33
vocab_size = 128

inputs = tf.keras.Input(shape=(input_dim,), name='harmony_input')
x = tf.keras.layers.Dense(128, activation='relu')(inputs)
x = tf.keras.layers.Dropout(0.3)(x)
x = tf.keras.layers.Dense(64, activation='relu')(x)
x = tf.keras.layers.Dropout(0.2)(x)
pitch_output = tf.keras.layers.Dense(
    vocab_size,
    activation='softmax',
    name='harmony_pitch'
)(x)

model = tf.keras.Model(inputs=inputs, outputs=pitch_output)
model.compile(
    loss='sparse_categorical_crossentropy',
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    metrics=['accuracy']
)

print("Model architecture:")
model.summary()

# Try to load weights from the old model
try:
    # First, load the old model without legacy keras to extract weights
    print("\nExtracting weights from original model...")
    
    # We need to do this in a subprocess without TF_USE_LEGACY_KERAS
    import subprocess
    import sys
    
    extract_script = '''
import os
if 'TF_USE_LEGACY_KERAS' in os.environ:
    del os.environ['TF_USE_LEGACY_KERAS']
import tensorflow as tf
import numpy as np

model = tf.keras.models.load_model('harmony_model.keras')
weights = model.get_weights()
np.savez('harmony_weights_temp.npz', *weights)
print("Weights extracted successfully")
'''
    
    result = subprocess.run([sys.executable, '-c', extract_script], 
                          capture_output=True, text=True, 
                          env={k: v for k, v in os.environ.items() if k != 'TF_USE_LEGACY_KERAS'})
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Load the weights
    print("Loading extracted weights...")
    weights_data = np.load('harmony_weights_temp.npz')
    weights = [weights_data[f'arr_{i}'] for i in range(len(weights_data.files))]
    
    # Set weights in the new model
    model.set_weights(weights)
    print("✓ Weights transferred successfully!")
    
    # Clean up temp file
    os.remove('harmony_weights_temp.npz')
    
except Exception as e:
    print(f"⚠ Could not transfer weights: {e}")
    print("Creating new untrained model...")

# Save the compatible model
output_path = 'harmony_model_compatible.keras'
print(f"\nSaving compatible model to {output_path}...")
model.save(output_path)
print(f"✓ Done! Use --harmony-model {output_path}")
