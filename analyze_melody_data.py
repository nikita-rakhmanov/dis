#!/usr/bin/env python3
"""
Analyze extracted melody data to inform vocabulary design decisions.

Generates visualizations:
1. Pitch distribution histogram
2. Pitch range per file
3. Interval distribution
4. Cumulative pitch coverage

Helps decide between:
- Full 128 vocabulary
- Clipped pitch range
- Interval-based representation
"""

import matplotlib.pyplot as plt
import numpy as np
import glob
import pathlib
from collections import Counter
import train_improved_rnn as trainer

# Config
NUM_FILES_TO_ANALYZE = 200  # Sample size
OUTPUT_DIR = "data_analysis"


def analyze_melodies():
    print("=" * 60)
    print("Melody Data Analysis")
    print("=" * 60)
    
    # Setup
    data_dir = pathlib.Path('data/maestro-v3.0.0')
    trainer.download_dataset_v3(data_dir)
    
    filenames = glob.glob(str(data_dir / '**/*.mid*'), recursive=True)
    filenames = filenames[:NUM_FILES_TO_ANALYZE]
    print(f"Analyzing {len(filenames)} files...\n")
    
    # Collect data
    all_pitches = []
    all_intervals = []
    file_ranges = []  # (min, max) per file
    
    for i, f in enumerate(filenames):
        if i % 50 == 0:
            print(f"  Processing file {i+1}/{len(filenames)}...")
        try:
            import pretty_midi
            pm = pretty_midi.PrettyMIDI(f)
            notes = trainer.onset_biased_skyline(pm)
            notes = trainer.post_process_notes(notes)
            
            if len(notes) < 10:
                continue
            
            pitches = [n['pitch'] for n in notes]
            all_pitches.extend(pitches)
            
            # Intervals
            for j in range(1, len(pitches)):
                interval = pitches[j] - pitches[j-1]
                all_intervals.append(interval)
            
            # Range per file
            file_ranges.append((min(pitches), max(pitches)))
            
        except Exception as e:
            continue
    
    print(f"\nTotal notes collected: {len(all_pitches)}")
    print(f"Total intervals: {len(all_intervals)}")
    
    # Create output directory
    pathlib.Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # ===== ANALYSIS =====
    
    # Basic stats
    print("\n" + "=" * 60)
    print("PITCH STATISTICS")
    print("=" * 60)
    print(f"Min pitch: {min(all_pitches)} ({pitch_to_name(min(all_pitches))})")
    print(f"Max pitch: {max(all_pitches)} ({pitch_to_name(max(all_pitches))})")
    print(f"Range: {max(all_pitches) - min(all_pitches)} semitones")
    print(f"Unique pitches used: {len(set(all_pitches))}")
    
    # Percentiles
    p5 = int(np.percentile(all_pitches, 5))
    p95 = int(np.percentile(all_pitches, 95))
    print(f"\n5th percentile: {p5} ({pitch_to_name(p5)})")
    print(f"95th percentile: {p95} ({pitch_to_name(p95)})")
    print(f"90% of notes are in range: {p5}-{p95} ({p95-p5+1} pitches)")
    
    # Interval stats
    print("\n" + "=" * 60)
    print("INTERVAL STATISTICS")
    print("=" * 60)
    print(f"Min interval: {min(all_intervals)} semitones")
    print(f"Max interval: {max(all_intervals)} semitones")
    print(f"Mean interval: {np.mean(np.abs(all_intervals)):.2f} semitones")
    
    i5 = int(np.percentile(all_intervals, 5))
    i95 = int(np.percentile(all_intervals, 95))
    print(f"90% of intervals are in range: {i5} to {i95}")
    print(f"Interval vocabulary size needed: {i95 - i5 + 1}")
    
    # ===== PLOTS =====
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Pitch Distribution
    ax1 = axes[0, 0]
    pitch_counts = Counter(all_pitches)
    pitches_sorted = sorted(pitch_counts.keys())
    counts = [pitch_counts[p] for p in pitches_sorted]
    ax1.bar(pitches_sorted, counts, color='steelblue', alpha=0.7)
    ax1.axvline(p5, color='red', linestyle='--', label=f'5th %ile ({p5})')
    ax1.axvline(p95, color='red', linestyle='--', label=f'95th %ile ({p95})')
    ax1.set_xlabel('MIDI Pitch')
    ax1.set_ylabel('Count')
    ax1.set_title('Pitch Distribution (with 90% range)')
    ax1.legend()
    
    # 2. Interval Distribution
    ax2 = axes[0, 1]
    interval_counts = Counter(all_intervals)
    intervals_sorted = sorted(interval_counts.keys())
    int_counts = [interval_counts[i] for i in intervals_sorted]
    ax2.bar(intervals_sorted, int_counts, color='coral', alpha=0.7)
    ax2.axvline(i5, color='green', linestyle='--', label=f'5th %ile ({i5})')
    ax2.axvline(i95, color='green', linestyle='--', label=f'95th %ile ({i95})')
    ax2.set_xlabel('Interval (semitones)')
    ax2.set_ylabel('Count')
    ax2.set_title('Interval Distribution')
    ax2.legend()
    
    # 3. Cumulative Pitch Coverage
    ax3 = axes[1, 0]
    total = len(all_pitches)
    cumsum = 0
    coverage_x = []
    coverage_y = []
    for p in sorted(set(all_pitches)):
        cumsum += pitch_counts[p]
        coverage_x.append(p)
        coverage_y.append(cumsum / total * 100)
    ax3.plot(coverage_x, coverage_y, color='purple', linewidth=2)
    ax3.axhline(90, color='red', linestyle='--', alpha=0.5, label='90% coverage')
    ax3.axhline(95, color='orange', linestyle='--', alpha=0.5, label='95% coverage')
    ax3.set_xlabel('MIDI Pitch')
    ax3.set_ylabel('Cumulative % of Notes')
    ax3.set_title('Cumulative Pitch Coverage')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. File Pitch Ranges
    ax4 = axes[1, 1]
    file_mins = [r[0] for r in file_ranges]
    file_maxs = [r[1] for r in file_ranges]
    ax4.scatter(file_mins, file_maxs, alpha=0.5, color='teal')
    ax4.plot([0, 127], [0, 127], 'k--', alpha=0.3)  # diagonal
    ax4.set_xlabel('Min Pitch in File')
    ax4.set_ylabel('Max Pitch in File')
    ax4.set_title('Pitch Range per File')
    ax4.set_xlim(20, 100)
    ax4.set_ylim(20, 100)
    
    plt.tight_layout()
    output_path = f"{OUTPUT_DIR}/melody_analysis.png"
    plt.savefig(output_path, dpi=150)
    print(f"\n✓ Saved: {output_path}")
    
    # ===== RECOMMENDATIONS =====
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    clipped_vocab = p95 - p5 + 1
    interval_vocab = i95 - i5 + 1
    
    print(f"\nOption 1: FULL VOCABULARY")
    print(f"  Vocab size: 128")
    print(f"  Notes covered: 100%")
    
    print(f"\nOption 2: CLIPPED RANGE ({p5}-{p95})")
    print(f"  Vocab size: {clipped_vocab}")
    print(f"  Notes covered: 90%")
    print(f"  Reduction: {(1 - clipped_vocab/128)*100:.1f}% fewer classes")
    
    print(f"\nOption 3: INTERVALS ({i5} to {i95})")
    print(f"  Vocab size: {interval_vocab}")
    print(f"  Coverage: 90% of transitions")
    print(f"  Reduction: {(1 - interval_vocab/128)*100:.1f}% fewer classes")
    print(f"  Note: Requires anchor pitch for generation")
    
    # Save summary
    summary_path = f"{OUTPUT_DIR}/analysis_summary.txt"
    with open(summary_path, 'w') as f:
        f.write("MELODY DATA ANALYSIS SUMMARY\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Files analyzed: {len(filenames)}\n")
        f.write(f"Total notes: {len(all_pitches)}\n\n")
        f.write(f"Pitch range: {min(all_pitches)}-{max(all_pitches)}\n")
        f.write(f"90% range: {p5}-{p95} ({clipped_vocab} pitches)\n\n")
        f.write(f"Interval range: {min(all_intervals)} to {max(all_intervals)}\n")
        f.write(f"90% interval range: {i5} to {i95} ({interval_vocab} values)\n")
    print(f"✓ Saved: {summary_path}")


def pitch_to_name(midi_pitch):
    """Convert MIDI pitch to note name."""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_pitch // 12) - 1
    note = notes[midi_pitch % 12]
    return f"{note}{octave}"


if __name__ == "__main__":
    analyze_melodies()
