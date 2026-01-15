#!/bin/bash
#SBATCH --job-name=train_rnn
#SBATCH --partition=gpu-l4-n2
#SBATCH --qos=gpu-l4-n2
#SBATCH --gpus=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --chdir=/home/mr298/dis
#SBATCH --output=/home/mr298/slurm-%x-%j.out
#SBATCH --error=/home/mr298/slurm-%x-%j.err

# ============================================================
# Full Training Script for Improved RNN
# Runs train_improved_rnn.py on GPU using TensorFlow NGC
# ============================================================

echo "============================================================"
echo "RNN Full Training Job Started"
echo "============================================================"
echo "Job ID:      $SLURM_JOB_ID"
echo "Job Name:    $SLURM_JOB_NAME"
echo "Node:        $(hostname)"
echo "Start Time:  $(date)"
echo "Working Dir: $(pwd)"
echo ""

# Show GPU info
echo "GPU Information:"
nvidia-smi -L
nvidia-smi
echo ""

# Set container paths
CONTAINER="$HOME/tensorflow_ngc.sif"

# Check container exists
if [ ! -f "$CONTAINER" ]; then
    echo "ERROR: Container not found at $CONTAINER"
    echo "Please run setup_cluster_node.sh first"
    exit 1
fi

# Show initial disk usage
echo "Disk usage before training:"
df -h .
echo ""

# Run the full training
echo "Starting full training (30 epochs on 1200 files)..."
echo "This may take several hours..."
echo ""

apptainer exec --nv \
  --bind $(pwd):/workspace \
  --pwd /workspace \
  $CONTAINER \
  bash -c "pip install --no-cache-dir pandas pretty_midi mido matplotlib && python3 train_improved_rnn.py"

EXIT_CODE=$?

echo ""
echo "============================================================"
echo "Training Job Completed"
echo "============================================================"
echo "End Time:    $(date)"
echo "Exit Code:   $EXIT_CODE"
echo ""

# List output files
echo "Output files:"
ls -lh improved_melody_model.keras 2>/dev/null || echo "  - improved_melody_model.keras: NOT FOUND"
ls -lh model_metadata.json 2>/dev/null || echo "  - model_metadata.json: NOT FOUND"
ls -lh improved_seed_sequence.npy 2>/dev/null || echo "  - improved_seed_sequence.npy: NOT FOUND"

# Show final disk usage
echo ""
echo "Disk usage after training:"
df -h .

exit $EXIT_CODE
