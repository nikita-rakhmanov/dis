#!/usr/bin/env python3
"""
Unified Model Comparison Script.

Compares the Original RNN (pitch/step/duration) with the V2 RNN (pitch/time).
Generates samples from both and computes comparable metrics.

Usage:
    python compare_models.py --original music_rnn_model.keras --improved improved_melody_model.keras
    
Or evaluate a single model:
    python compare_models.py --model music_rnn_model.keras --type original
    python compare_models.py --model improved_melody_model.keras --type improved
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TF logging
os.environ['TF_USE_LEGACY_KERAS'] = '1'   # Use tf_keras for compatibility with cluster-trained models

import numpy as np
import tensorflow as tf
import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
import mido


def mse_with_positive_pressure(y_true, y_pred):
    """Custom loss for original model."""
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)


class OriginalModelGenerator:
    """Generator for original model (pitch, step, duration)."""
    
    def __init__(self, model_path, seed_path=None):
        print(f"Loading Original Model from {model_path}...")
        self.model = tf.keras.models.load_model(
            model_path,
            custom_objects={'mse_with_positive_pressure': mse_with_positive_pressure}
        )
        self.sequence_length = self.model.input_shape[1]
        self.vocab_size = 128
        self.model_type = "original"
        self._load_seed(seed_path)
        print(f"  Sequence length: {self.sequence_length}")
        print(f"  Output heads: pitch, step, duration\n")
    
    def _load_seed(self, seed_file):
        if seed_file and Path(seed_file).exists():
            seed = np.load(seed_file)
            self.current_notes = seed / np.array([self.vocab_size, 1, 1])
        else:
            # Default C major scale seed
            seed_notes = []
            c_major = [0, 2, 4, 5, 7, 9, 11, 12]
            for i in range(self.sequence_length):
                pitch = 60 + c_major[i % len(c_major)]
                seed_notes.append([pitch, 0.5, 0.4])
            self.current_notes = np.array(seed_notes) / np.array([self.vocab_size, 1, 1])
    
    def reset_seed(self, seed_path=None):
        self._load_seed(seed_path)
    
    def generate_sequence(self, num_notes=100, temperature=1.0):
        notes = []
        for _ in range(num_notes):
            inputs = tf.expand_dims(self.current_notes, 0)
            predictions = self.model.predict(inputs, verbose=0)
            
            pitch_logits = predictions['pitch'] / temperature
            pitch = int(tf.squeeze(tf.random.categorical(pitch_logits, num_samples=1)))
            step = float(tf.maximum(0, tf.squeeze(predictions['step'])))
            duration = float(tf.maximum(0.1, tf.squeeze(predictions['duration'])))
            
            notes.append({'pitch': pitch, 'step': step, 'duration': duration})
            
            # Update sequence
            input_note = np.array([pitch, step, duration]) / np.array([self.vocab_size, 1, 1])
            self.current_notes = np.vstack([self.current_notes[1:], input_note])
        
        return notes


class ImprovedModelGenerator:
    """Generator for improved model (pitch, normalized_log_time)."""
    
    def __init__(self, model_path, metadata_path=None, seed_path=None):
        print(f"Loading Improved Model from {model_path}...")
        self.model = tf.keras.models.load_model(model_path)
        self.sequence_length = self.model.input_shape[1]
        self.model_type = "improved"
        
        # Defaults for full vocabulary model
        self.max_log_delta = 1.0
        self.vocab_size = 128
        self.min_pitch = 0  # No offset for full vocab
        
        # Load metadata for time denormalization and vocab info
        if metadata_path and Path(metadata_path).exists():
            with open(metadata_path) as f:
                meta = json.load(f)
                self.max_log_delta = meta.get('max_log_delta', 1.0)
                self.vocab_size = meta.get('vocab_size', 128)
                self.min_pitch = meta.get('min_pitch', 0)
            print(f"  Loaded metadata: max_log_delta={self.max_log_delta:.4f}, vocab={self.vocab_size}, min_pitch={self.min_pitch}")
        
        self._load_seed(seed_path)
        print(f"  Sequence length: {self.sequence_length}")
        print(f"  Output heads: pitch, time\n")
    
    def _load_seed(self, seed_file):
        if seed_file and Path(seed_file).exists():
            self.current_notes = np.load(seed_file)
        else:
            # Default seed: normalized (pitch/128, time~0.3)
            seed_notes = []
            c_major = [0, 2, 4, 5, 7, 9, 11, 12]
            for i in range(self.sequence_length):
                pitch_norm = (60 + c_major[i % len(c_major)]) / self.vocab_size
                time_norm = 0.3  # moderate timing
                seed_notes.append([pitch_norm, time_norm])
            self.current_notes = np.array(seed_notes, dtype=np.float32)
    
    def reset_seed(self, seed_path=None):
        self._load_seed(seed_path)
    
    def _denorm_time(self, norm_time):
        """Convert normalized log-time back to seconds."""
        log_delta = norm_time * self.max_log_delta
        return np.expm1(log_delta)  # inverse of log1p
    
    def generate_sequence(self, num_notes=100, temperature=1.0):
        notes = []
        for _ in range(num_notes):
            inputs = tf.expand_dims(self.current_notes, 0)
            predictions = self.model.predict(inputs, verbose=0)
            
            # predictions[0] = pitch logits, predictions[1] = time
            pitch_logits = predictions[0] / temperature
            pitch_class = int(tf.squeeze(tf.random.categorical(pitch_logits, num_samples=1)))
            time_norm = float(tf.maximum(0, tf.squeeze(predictions[1])))
            
            # Convert class index to MIDI pitch (add min_pitch offset for clipped models)
            pitch = pitch_class + self.min_pitch
            
            # Denormalize time to get step (time between notes)
            step = self._denorm_time(time_norm)
            step = max(0.05, min(step, 2.0))  # clamp to reasonable range
            
            # Improved model doesn't predict duration - use fixed or proportional
            duration = max(0.2, step * 0.8)  # 80% of step time
            
            notes.append({'pitch': pitch, 'step': step, 'duration': duration})
            
            # Update sequence (use class index, not MIDI pitch)
            pitch_norm = pitch_class / self.vocab_size
            input_note = np.array([pitch_norm, time_norm], dtype=np.float32)
            self.current_notes = np.vstack([self.current_notes[1:], input_note])
        
        return notes


def compute_metrics(notes):
    """Compute comparable metrics for any generated sequence."""
    pitches = [n['pitch'] for n in notes]
    steps = [n['step'] for n in notes]
    durations = [n['duration'] for n in notes]
    
    metrics = {}
    
    # Pitch metrics
    unique_pitches = len(set(pitches))
    metrics['unique_pitches'] = unique_pitches
    metrics['pitch_diversity'] = unique_pitches / len(pitches)
    metrics['pitch_range'] = max(pitches) - min(pitches)
    metrics['pitch_mean'] = float(np.mean(pitches))
    metrics['pitch_std'] = float(np.std(pitches))
    
    # Interval analysis
    intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
    metrics['mean_interval'] = float(np.mean(np.abs(intervals)))
    metrics['large_jumps'] = sum(1 for i in intervals if abs(i) > 12)
    metrics['large_jump_ratio'] = metrics['large_jumps'] / len(intervals)
    
    # Rhythm metrics
    metrics['mean_step'] = float(np.mean(steps))
    metrics['std_step'] = float(np.std(steps))
    metrics['mean_duration'] = float(np.mean(durations))
    
    # Repetition/entropy
    pitch_counter = Counter(pitches)
    _, most_common_count = pitch_counter.most_common(1)[0]
    metrics['repetition_ratio'] = most_common_count / len(pitches)
    
    pitch_probs = np.array([count / len(pitches) for count in pitch_counter.values()])
    metrics['pitch_entropy'] = float(-np.sum(pitch_probs * np.log2(pitch_probs + 1e-10)))
    
    # Consecutive repetitions
    consec_reps = sum(1 for i in range(len(pitches)-1) if pitches[i] == pitches[i+1])
    metrics['consecutive_rep_ratio'] = consec_reps / (len(pitches) - 1)
    
    return metrics


def save_midi(notes, output_path):
    """Save notes as MIDI file."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=500000))
    
    for note in notes:
        step_ticks = int(note['step'] * 480)
        duration_ticks = int(note['duration'] * 480)
        track.append(mido.Message('note_on', note=note['pitch'], velocity=80, time=step_ticks))
        track.append(mido.Message('note_off', note=note['pitch'], velocity=0, time=duration_ticks))
    
    mid.save(output_path)


def evaluate_generator(generator, output_dir, num_samples=5, num_notes=100, temperatures=[0.8, 1.0, 1.5]):
    """Evaluate a model generator."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    results = {'model_type': generator.model_type, 'results': {}}
    
    for temp in temperatures:
        print(f"  Temperature {temp}...")
        temp_metrics = []
        
        for i in range(num_samples):
            generator.reset_seed()
            notes = generator.generate_sequence(num_notes, temperature=temp)
            metrics = compute_metrics(notes)
            temp_metrics.append(metrics)
            
            # Save one MIDI per temperature
            if i == 0:
                midi_path = output_dir / f"{generator.model_type}_temp{temp}.mid"
                save_midi(notes, midi_path)
        
        # Aggregate
        aggregated = {}
        for key in temp_metrics[0].keys():
            values = [m[key] for m in temp_metrics]
            aggregated[key] = {'mean': float(np.mean(values)), 'std': float(np.std(values))}
        
        results['results'][f'temp_{temp}'] = aggregated
    
    return results


def print_comparison(original_results, improved_results):
    """Print side-by-side comparison."""
    print("\n" + "=" * 70)
    print("MODEL COMPARISON REPORT")
    print("=" * 70)
    
    temps = ['temp_0.8', 'temp_1.0', 'temp_1.5']
    
    key_metrics = [
        ('unique_pitches', 'Unique Pitches', '↑ better'),
        ('pitch_diversity', 'Pitch Diversity', '↑ better'),
        ('pitch_range', 'Pitch Range', '~'),
        ('mean_interval', 'Mean Interval', '~'),
        ('large_jump_ratio', 'Large Jump %', '↓ better'),
        ('pitch_entropy', 'Pitch Entropy', '↑ better'),
        ('repetition_ratio', 'Repetition %', '↓ better'),
        ('consecutive_rep_ratio', 'Consec. Rep %', '↓ better'),
        ('mean_step', 'Mean Step (s)', '~'),
    ]
    
    for temp in temps:
        if temp not in original_results['results'] or temp not in improved_results['results']:
            continue
        
        print(f"\n{'─' * 70}")
        print(f"Temperature: {temp.replace('temp_', '')}")
        print(f"{'─' * 70}")
        print(f"{'Metric':<22} {'Original':>12} {'Improved':>12} {'Diff':>10} {'Winner':>10}")
        print(f"{'─' * 70}")
        
        orig = original_results['results'][temp]
        impr = improved_results['results'][temp]
        
        for key, label, prefer in key_metrics:
            o_val = orig[key]['mean']
            i_val = impr[key]['mean']
            diff = i_val - o_val
            diff_pct = (diff / o_val * 100) if o_val != 0 else 0
            
            if prefer == '↑ better':
                winner = 'Improved' if diff > 0 else 'Original' if diff < 0 else 'Tie'
            elif prefer == '↓ better':
                winner = 'Improved' if diff < 0 else 'Original' if diff > 0 else 'Tie'
            else:
                winner = '~'
            
            print(f"{label:<22} {o_val:>12.3f} {i_val:>12.3f} {diff:>+10.3f} {winner:>10}")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Compare Original and Improved RNN models')
    parser.add_argument('--original', help='Path to original model (.keras)')
    parser.add_argument('--improved', help='Path to improved model (.keras)')
    parser.add_argument('--model', help='Single model path (use with --type)')
    parser.add_argument('--type', choices=['original', 'improved'], help='Model type for single evaluation')
    parser.add_argument('--metadata', default='model_metadata.json', help='Metadata for improved model')
    parser.add_argument('--original-seed', default='seed_sequence.npy', help='Seed for original model')
    parser.add_argument('--improved-seed', default='improved_seed_sequence.npy', help='Seed for improved model')
    parser.add_argument('--output', default='model_comparison', help='Output directory')
    parser.add_argument('--num-samples', type=int, default=5, help='Samples per temperature')
    parser.add_argument('--num-notes', type=int, default=100, help='Notes per sample')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    results = {}
    
    # Single model evaluation
    if args.model and args.type:
        print(f"\nEvaluating {args.type} model...")
        if args.type == 'original':
            gen = OriginalModelGenerator(args.model, args.original_seed)
        else:
            gen = ImprovedModelGenerator(args.model, args.metadata, args.improved_seed)
        
        results[args.type] = evaluate_generator(
            gen, output_dir / args.type,
            num_samples=args.num_samples, num_notes=args.num_notes
        )
        
        # Save results
        with open(output_dir / f'{args.type}_results.json', 'w') as f:
            json.dump(results[args.type], f, indent=2)
        
        print(f"\n✓ Results saved to {output_dir}")
        return
    
    # Compare both models
    if args.original and args.improved:
        print("\n" + "=" * 70)
        print("EVALUATING ORIGINAL MODEL")
        print("=" * 70)
        orig_gen = OriginalModelGenerator(args.original, args.original_seed)
        results['original'] = evaluate_generator(
            orig_gen, output_dir / 'original',
            num_samples=args.num_samples, num_notes=args.num_notes
        )
        
        print("\n" + "=" * 70)
        print("EVALUATING IMPROVED MODEL")
        print("=" * 70)
        impr_gen = ImprovedModelGenerator(args.improved, args.metadata, args.improved_seed)
        results['improved'] = evaluate_generator(
            impr_gen, output_dir / 'improved',
            num_samples=args.num_samples, num_notes=args.num_notes
        )
        
        # Print comparison
        print_comparison(results['original'], results['improved'])
        
        # Save results
        with open(output_dir / 'comparison_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results and MIDI files saved to {output_dir}/")
        print(f"✓ Listen to the generated MIDI files to compare musically!")
    else:
        parser.print_help()
        print("\n\nExamples:")
        print("  Compare both models:")
        print("    python compare_models.py --original music_rnn_model.keras --improved improved_melody_model.keras")
        print("\n  Evaluate single model:")
        print("    python compare_models.py --model music_rnn_model.keras --type original")


if __name__ == "__main__":
    main()
