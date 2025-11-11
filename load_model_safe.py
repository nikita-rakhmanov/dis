#!/usr/bin/env python3
"""
Safe model loading that handles version mismatches.
"""

import tensorflow as tf
import os
import sys

def mse_with_positive_pressure(y_true, y_pred):
    """Custom loss function needed for model loading."""
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)

def load_model_safe(model_path='music_rnn_model.keras'):
    """
    Try multiple methods to load the model.
    Returns: loaded model or None
    """
    custom_objects = {'mse_with_positive_pressure': mse_with_positive_pressure}

    # Method 1: Try loading .keras file directly
    if os.path.exists(model_path):
        print(f"Attempting to load {model_path}...")
        try:
            model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
            print("✅ Model loaded successfully!")
            return model
        except Exception as e:
            print(f"⚠️  Failed to load .keras file: {e}")

    # Method 2: Try loading .h5 file if available
    h5_path = model_path.replace('.keras', '.h5')
    if os.path.exists(h5_path):
        print(f"Attempting to load {h5_path}...")
        try:
            model = tf.keras.models.load_model(h5_path, custom_objects=custom_objects)
            print("✅ Model loaded successfully from H5 format!")
            return model
        except Exception as e:
            print(f"⚠️  Failed to load .h5 file: {e}")

    # Method 3: Rebuild model and load weights
    weights_path = model_path.replace('.keras', '_weights.h5')
    if os.path.exists(weights_path):
        print(f"Attempting to rebuild model and load weights from {weights_path}...")
        try:
            from train_music_rnn import build_model, SEQUENCE_LENGTH, VOCAB_SIZE, LEARNING_RATE
            model = build_model(SEQUENCE_LENGTH, VOCAB_SIZE, LEARNING_RATE)
            model.load_weights(weights_path)
            print("✅ Model rebuilt and weights loaded successfully!")
            return model
        except Exception as e:
            print(f"⚠️  Failed to rebuild and load weights: {e}")

    print("\n❌ All model loading methods failed!")
    print("\nTroubleshooting:")
    print("1. Make sure you have the same TensorFlow version as training")
    print("2. Try: TF_USE_LEGACY_KERAS=1 python your_script.py")
    print("3. Convert model on GPU machine using convert_model.py")
    print(f"4. Check TensorFlow version: {tf.__version__}")

    return None

if __name__ == "__main__":
    # Test the loader
    model = load_model_safe()
    if model:
        print(f"\nModel details:")
        print(f"Input shape: {model.input_shape}")
        model.summary()
