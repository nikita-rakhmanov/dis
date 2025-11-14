#!/usr/bin/env python3
"""
Dual-Model Polyphony System

Implements cascaded two-model architecture for polyphonic music generation:
- Model 1 (Melody): Your existing trained RNN
- Model 2 (Harmony): Generates harmony based on melody output

This allows polyphonic (2-voice) music generation without retraining the main model.
"""

import numpy as np
import tensorflow as tf
from typing import Tuple, Optional
import random


class SimpleHarmonyGenerator:
    """
    Rule-based harmony generator for quick prototyping.
    This serves as Model 2 before training a real neural network.
    """

    def __init__(self, style='classical'):
        """
        Initialize harmony generator.

        Args:
            style: Harmony style ('classical', 'jazz', 'modern')
        """
        self.style = style
        self.interval_profiles = {
            'classical': {
                'intervals': [-7, -5, -4, -3, 3, 4, 5, 7],  # Fifths, thirds
                'weights': [0.25, 0.20, 0.15, 0.15, 0.10, 0.05, 0.05, 0.05]
            },
            'jazz': {
                'intervals': [-7, -5, -4, -3, 3, 4, 7, 10],  # Add 7ths
                'weights': [0.20, 0.15, 0.15, 0.15, 0.10, 0.10, 0.10, 0.05]
            },
            'modern': {
                'intervals': [-12, -7, -5, -2, 2, 5, 7, 12],  # Wider intervals
                'weights': [0.15, 0.20, 0.15, 0.10, 0.10, 0.10, 0.10, 0.10]
            }
        }

    def generate_harmony(self, melody_pitch: int, melody_context: Optional[list] = None) -> int:
        """
        Generate harmony note for given melody pitch.

        Args:
            melody_pitch: MIDI pitch of melody note (0-127)
            melody_context: Optional list of recent melody pitches for context

        Returns:
            harmony_pitch: MIDI pitch of harmony note (0-127)
        """
        profile = self.interval_profiles[self.style]

        # Choose interval based on weighted probabilities
        interval = random.choices(
            profile['intervals'],
            weights=profile['weights'],
            k=1
        )[0]

        harmony_pitch = melody_pitch + interval

        # Ensure harmony is in valid MIDI range
        harmony_pitch = max(0, min(127, harmony_pitch))

        # Avoid unison (same note as melody)
        if harmony_pitch == melody_pitch:
            # Try adjacent interval
            alternative = interval + (1 if interval > 0 else -1)
            harmony_pitch = max(0, min(127, melody_pitch + alternative))

        return harmony_pitch


class LearnedHarmonyModel:
    """
    Neural network-based harmony generator (Model 2).
    Will be trained on melody-harmony pairs from MIDI data.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize learned harmony model.

        Args:
            model_path: Path to trained harmony model (optional)
        """
        self.model = None
        self.context_length = 10

        if model_path:
            self.load_model(model_path)

    def build_model(self, input_dim: int = 33, vocab_size: int = 128):
        """
        Build harmony prediction model.

        Input features:
        - Current melody note: [pitch, step, duration] (3)
        - Recent melody context: last 10 notes (30)

        Output:
        - Harmony pitch (128 classes)
        """
        inputs = tf.keras.Input(shape=(input_dim,), name='harmony_input')

        # Smaller model than main RNN - harmony is simpler task
        x = tf.keras.layers.Dense(128, activation='relu')(inputs)
        x = tf.keras.layers.Dropout(0.3)(x)
        x = tf.keras.layers.Dense(64, activation='relu')(x)
        x = tf.keras.layers.Dropout(0.2)(x)

        # Output: pitch prediction
        pitch_output = tf.keras.layers.Dense(
            vocab_size,
            activation='softmax',
            name='harmony_pitch'
        )(x)

        self.model = tf.keras.Model(inputs=inputs, outputs=pitch_output)

        self.model.compile(
            loss='sparse_categorical_crossentropy',
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            metrics=['accuracy']
        )

        return self.model

    def generate_harmony(self, melody_pitch: int, melody_step: float,
                        melody_duration: float, melody_context: list,
                        temperature: float = 1.0) -> int:
        """
        Generate harmony using trained model.

        Args:
            melody_pitch: Current melody pitch
            melody_step: Current melody step
            melody_duration: Current melody duration
            melody_context: Recent melody notes [(pitch, step, dur), ...]
            temperature: Sampling temperature

        Returns:
            harmony_pitch: Predicted harmony pitch
        """
        if self.model is None:
            raise ValueError("Model not built or loaded")

        # Prepare input features
        current_note = np.array([melody_pitch / 128.0, melody_step, melody_duration])

        # Flatten recent context (last 10 notes)
        context_flat = np.array(melody_context[-self.context_length:]).flatten()

        # Pad if not enough context
        if len(context_flat) < self.context_length * 3:
            padding = np.zeros(self.context_length * 3 - len(context_flat))
            context_flat = np.concatenate([padding, context_flat])

        # Combine current note + context
        input_features = np.concatenate([current_note, context_flat])
        input_features = np.expand_dims(input_features, 0)

        # Predict
        predictions = self.model.predict(input_features, verbose=0)

        # Sample with temperature
        predictions = np.log(predictions + 1e-7) / temperature
        predictions = np.exp(predictions) / np.sum(np.exp(predictions))

        harmony_pitch = np.random.choice(128, p=predictions[0])

        return int(harmony_pitch)

    def load_model(self, model_path: str):
        """Load pre-trained harmony model."""
        self.model = tf.keras.models.load_model(model_path)

    def save_model(self, model_path: str):
        """Save trained harmony model."""
        if self.model:
            self.model.save(model_path)


class DualModelPolyphonySystem:
    """
    Orchestrates two models for polyphonic generation:
    - Model 1: Melody generator (existing RNN)
    - Model 2: Harmony generator (simple or learned)
    """

    def __init__(self, melody_generator, harmony_mode='simple',
                 harmony_model_path: Optional[str] = None, harmony_style='classical'):
        """
        Initialize dual-model system.

        Args:
            melody_generator: Existing IntegratedMusicGestureSystem instance
            harmony_mode: 'simple' (rule-based) or 'learned' (neural network)
            harmony_model_path: Path to trained harmony model (if learned mode)
            harmony_style: Style for simple harmony ('classical', 'jazz', 'modern')
        """
        self.melody_generator = melody_generator
        self.harmony_mode = harmony_mode

        # Initialize harmony generator
        if harmony_mode == 'simple':
            self.harmony_gen = SimpleHarmonyGenerator(style=harmony_style)
        elif harmony_mode == 'learned':
            self.harmony_gen = LearnedHarmonyModel(model_path=harmony_model_path)
        else:
            raise ValueError(f"Unknown harmony_mode: {harmony_mode}")

        # Track melody history for context
        self.melody_history = []
        self.max_history = 50

    def predict_next_notes(self, temperature: float = 1.0) -> Tuple[Tuple[int, float, float], Tuple[int, float, float]]:
        """
        Generate next melody and harmony notes.

        Args:
            temperature: Sampling temperature for melody generation

        Returns:
            (melody_note, harmony_note) where each is (pitch, step, duration)
        """
        # Model 1: Generate melody (existing model)
        melody_pitch, melody_step, melody_duration = self.melody_generator.predict_next_note(temperature)

        # Model 2: Generate harmony based on melody
        if self.harmony_mode == 'simple':
            harmony_pitch = self.harmony_gen.generate_harmony(
                melody_pitch,
                melody_context=self.melody_history
            )
        else:  # learned mode
            harmony_pitch = self.harmony_gen.generate_harmony(
                melody_pitch,
                melody_step,
                melody_duration,
                melody_context=self.melody_history,
                temperature=temperature
            )

        # Harmony timing: match melody (could be varied later)
        harmony_step = melody_step
        harmony_duration = melody_duration * 0.95  # Slightly shorter for cleaner cutoff

        # Update melody history for context
        self.melody_history.append([melody_pitch / 128.0, melody_step, melody_duration])
        if len(self.melody_history) > self.max_history:
            self.melody_history.pop(0)

        melody_note = (melody_pitch, melody_step, melody_duration)
        harmony_note = (harmony_pitch, harmony_step, harmony_duration)

        return melody_note, harmony_note

    def play_notes(self, melody_note: Tuple[int, float, float],
                   harmony_note: Tuple[int, float, float], velocity: int = 80):
        """
        Play melody and harmony notes simultaneously via MIDI.

        Args:
            melody_note: (pitch, step, duration) for melody
            harmony_note: (pitch, step, duration) for harmony
            velocity: MIDI velocity (0-127)
        """
        import mido
        import time
        import threading

        melody_pitch, melody_step, melody_duration = melody_note
        harmony_pitch, harmony_step, harmony_duration = harmony_note

        # Ensure valid MIDI values
        melody_pitch = max(0, min(127, melody_pitch))
        harmony_pitch = max(0, min(127, harmony_pitch))
        velocity = max(0, min(127, velocity))

        midi_out = self.melody_generator.midi_out
        midi_lock = self.melody_generator.gesture_controller.midi_lock if self.melody_generator.gesture_controller else threading.Lock()

        # Send both note_on messages
        with midi_lock:
            midi_out.send(mido.Message('note_on', note=melody_pitch, velocity=velocity))
            midi_out.send(mido.Message('note_on', note=harmony_pitch, velocity=int(velocity * 0.8)))  # Harmony slightly quieter

        # Wait for duration
        max_duration = max(melody_duration, harmony_duration)
        time.sleep(max_duration)

        # Send both note_off messages
        with midi_lock:
            midi_out.send(mido.Message('note_off', note=melody_pitch, velocity=0))
            midi_out.send(mido.Message('note_off', note=harmony_pitch, velocity=0))
