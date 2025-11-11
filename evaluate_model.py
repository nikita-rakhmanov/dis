#!/usr/bin/env python3
"""
Model Evaluation Script for Music RNN

Generates music samples and computes quantitative metrics for model comparison.
Run this after training to evaluate model quality objectively.
"""

import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import numpy as np
import tensorflow as tf
import argparse
import json
from collections import Counter
from datetime import datetime
import mido
from pathlib import Path


def mse_with_positive_pressure(y_true, y_pred):
    """Custom loss function needed for model loading."""
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)


class ModelEvaluator:
    """Evaluate music generation model with quantitative metrics."""

    def __init__(self, model_path, seed_path=None):
        print(f"Loading model from {model_path}...")
        self.model = tf.keras.models.load_model(
            model_path,
            custom_objects={'mse_with_positive_pressure': mse_with_positive_pressure}
        )
        print("✓ Model loaded\n")

        self.sequence_length = self.model.input_shape[1]
        self.vocab_size = 128
        self._load_seed(seed_path)

    def _load_seed(self, seed_file):
        """Load seed sequence."""
        if seed_file and Path(seed_file).exists():
            seed = np.load(seed_file)
            self.current_notes = seed / np.array([self.vocab_size, 1, 1])
            print(f"✓ Loaded seed from {seed_file}\n")
        else:
            # Default C major scale
            seed_notes = []
            c_major = [0, 2, 4, 5, 7, 9, 11, 12]
            for i in range(self.sequence_length):
                pitch = 60 + c_major[i % len(c_major)]
                seed_notes.append([pitch, 0.5, 0.4])
            seed_notes = np.array(seed_notes)
            self.current_notes = seed_notes / np.array([self.vocab_size, 1, 1])
            print("✓ Using default seed\n")

    def predict_next_note(self, temperature=1.0):
        """Generate next note."""
        inputs = tf.expand_dims(self.current_notes, 0)
        predictions = self.model.predict(inputs, verbose=0)

        pitch_logits = predictions['pitch'] / temperature
        pitch = tf.random.categorical(pitch_logits, num_samples=1)
        pitch = tf.squeeze(pitch, axis=-1)
        step = tf.maximum(0, tf.squeeze(predictions['step'], axis=-1))
        duration = tf.maximum(0, tf.squeeze(predictions['duration'], axis=-1))

        return int(pitch), float(step), float(duration)

    def update_sequence(self, pitch, step, duration):
        """Update the rolling input sequence."""
        input_note = np.array([pitch, step, duration])
        self.current_notes = np.delete(self.current_notes, 0, axis=0)
        self.current_notes = np.append(
            self.current_notes,
            np.expand_dims(input_note / np.array([self.vocab_size, 1, 1]), 0),
            axis=0
        )

    def generate_sequence(self, num_notes=100, temperature=1.0):
        """Generate a sequence of notes and return as list."""
        notes = []
        for _ in range(num_notes):
            pitch, step, duration = self.predict_next_note(temperature)
            duration = max(0.1, min(2.0, duration))
            notes.append({'pitch': pitch, 'step': step, 'duration': duration})
            self.update_sequence(pitch, step, duration)
        return notes

    def compute_metrics(self, notes):
        """Compute quantitative metrics for generated sequence."""
        pitches = [n['pitch'] for n in notes]
        steps = [n['step'] for n in notes]
        durations = [n['duration'] for n in notes]

        metrics = {}

        # 1. Pitch diversity
        unique_pitches = len(set(pitches))
        metrics['unique_pitches'] = unique_pitches
        metrics['pitch_diversity_ratio'] = unique_pitches / len(pitches)

        # 2. Pitch range
        metrics['pitch_range'] = max(pitches) - min(pitches)
        metrics['pitch_mean'] = np.mean(pitches)
        metrics['pitch_std'] = np.std(pitches)

        # 3. Interval analysis (melodic jumps)
        intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
        metrics['mean_interval'] = np.mean(np.abs(intervals))
        metrics['max_interval'] = max(np.abs(intervals))
        metrics['large_jumps'] = sum(1 for i in intervals if abs(i) > 12)  # Octave+

        # 4. Rhythm/timing metrics
        metrics['mean_step'] = np.mean(steps)
        metrics['std_step'] = np.std(steps)
        metrics['mean_duration'] = np.mean(durations)
        metrics['std_duration'] = np.std(durations)

        # 5. Repetition analysis
        pitch_counter = Counter(pitches)
        most_common_pitch, most_common_count = pitch_counter.most_common(1)[0]
        metrics['most_repeated_pitch'] = most_common_pitch
        metrics['repetition_ratio'] = most_common_count / len(pitches)

        # 6. Note distribution entropy (how spread out notes are)
        pitch_probs = np.array([count / len(pitches) for count in pitch_counter.values()])
        metrics['pitch_entropy'] = -np.sum(pitch_probs * np.log2(pitch_probs + 1e-10))

        # 7. Consecutive repetitions
        consecutive_reps = 0
        for i in range(len(pitches) - 1):
            if pitches[i] == pitches[i+1]:
                consecutive_reps += 1
        metrics['consecutive_repetition_ratio'] = consecutive_reps / (len(pitches) - 1)

        return metrics

    def save_midi(self, notes, output_path):
        """Save generated notes as MIDI file."""
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        track.append(mido.MetaMessage('set_tempo', tempo=500000))  # 120 BPM

        time = 0
        for note in notes:
            # Convert step/duration to MIDI ticks (480 ticks per beat)
            step_ticks = int(note['step'] * 480)
            duration_ticks = int(note['duration'] * 480)

            # Note on
            track.append(mido.Message('note_on',
                                     note=note['pitch'],
                                     velocity=80,
                                     time=step_ticks))
            # Note off
            track.append(mido.Message('note_off',
                                     note=note['pitch'],
                                     velocity=0,
                                     time=duration_ticks))

        mid.save(output_path)
        print(f"✓ Saved MIDI to {output_path}")


def evaluate_model(model_path, seed_path, output_dir, num_samples=5, num_notes=100, temperatures=[0.8, 1.0, 1.5, 2.0]):
    """
    Full evaluation: generate samples at different temperatures and compute metrics.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    evaluator = ModelEvaluator(model_path, seed_path)

    all_results = {
        'model_path': model_path,
        'timestamp': datetime.now().isoformat(),
        'num_samples': num_samples,
        'num_notes': num_notes,
        'temperatures': temperatures,
        'results': {}
    }

    print("=" * 60)
    print(f"Evaluating Model: {model_path}")
    print("=" * 60)

    for temp in temperatures:
        print(f"\nTemperature: {temp}")
        print("-" * 40)

        temp_results = []

        for i in range(num_samples):
            print(f"  Generating sample {i+1}/{num_samples}...")

            # Reset seed for each sample
            evaluator._load_seed(seed_path)

            # Generate
            notes = evaluator.generate_sequence(num_notes, temperature=temp)

            # Compute metrics
            metrics = evaluator.compute_metrics(notes)
            temp_results.append(metrics)

            # Save MIDI
            midi_path = output_dir / f"temp{temp}_sample{i+1}.mid"
            evaluator.save_midi(notes, midi_path)

        # Aggregate metrics across samples
        aggregated = {}
        for key in temp_results[0].keys():
            values = [r[key] for r in temp_results]
            aggregated[key] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values))
            }

        all_results['results'][f'temp_{temp}'] = aggregated

        # Print summary
        print(f"\n  Summary (avg over {num_samples} samples):")
        print(f"    Unique pitches: {aggregated['unique_pitches']['mean']:.1f}")
        print(f"    Pitch range: {aggregated['pitch_range']['mean']:.1f}")
        print(f"    Mean interval: {aggregated['mean_interval']['mean']:.2f}")
        print(f"    Pitch entropy: {aggregated['pitch_entropy']['mean']:.2f}")
        print(f"    Repetition ratio: {aggregated['repetition_ratio']['mean']:.3f}")

    # Save results to JSON
    results_path = output_dir / "evaluation_results.json"
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Evaluation complete!")
    print(f"✓ Results saved to: {results_path}")
    print(f"✓ MIDI files saved to: {output_dir}")
    print("=" * 60)

    return all_results


def compare_models(results1_path, results2_path):
    """Compare evaluation results between two models."""
    with open(results1_path) as f:
        results1 = json.load(f)
    with open(results2_path) as f:
        results2 = json.load(f)

    print("\n" + "=" * 60)
    print("Model Comparison")
    print("=" * 60)

    print(f"\nModel 1: {results1['model_path']}")
    print(f"Model 2: {results2['model_path']}")

    for temp in results1['temperatures']:
        key = f'temp_{temp}'
        if key not in results1['results'] or key not in results2['results']:
            continue

        print(f"\nTemperature: {temp}")
        print("-" * 40)

        r1 = results1['results'][key]
        r2 = results2['results'][key]

        metrics = ['unique_pitches', 'pitch_range', 'mean_interval', 'pitch_entropy', 'repetition_ratio']

        for metric in metrics:
            v1 = r1[metric]['mean']
            v2 = r2[metric]['mean']
            diff = v2 - v1
            pct = (diff / v1 * 100) if v1 != 0 else 0

            symbol = "✓" if abs(pct) > 5 else "~"
            print(f"  {metric:25s}: {v1:6.2f} → {v2:6.2f} ({diff:+6.2f}, {pct:+5.1f}%) {symbol}")


def main():
    parser = argparse.ArgumentParser(description='Evaluate music generation model')
    parser.add_argument('--model', required=True, help='Path to model')
    parser.add_argument('--seed', default='seed_sequence.npy', help='Seed sequence')
    parser.add_argument('--output', default='evaluation_results', help='Output directory')
    parser.add_argument('--num-samples', type=int, default=5, help='Samples per temperature')
    parser.add_argument('--num-notes', type=int, default=100, help='Notes per sample')
    parser.add_argument('--temperatures', type=float, nargs='+', default=[0.8, 1.0, 1.5, 2.0],
                       help='Temperatures to test')
    parser.add_argument('--compare', help='Compare with another results JSON')

    args = parser.parse_args()

    if args.compare:
        # Just do comparison
        compare_models(args.output + '/evaluation_results.json', args.compare)
    else:
        # Run evaluation
        evaluate_model(
            args.model,
            args.seed,
            args.output,
            num_samples=args.num_samples,
            num_notes=args.num_notes,
            temperatures=args.temperatures
        )


if __name__ == "__main__":
    main()
