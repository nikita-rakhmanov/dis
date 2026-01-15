#!/bin/bash
#SBATCH --job-name=eval_rnn
#SBATCH --partition=gpu-l4-n2
#SBATCH --qos=gpu-l4-n2
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --chdir=/home/mr298/dis
#SBATCH --output=/home/mr298/slurm-%x-%j.out
#SBATCH --error=/home/mr298/slurm-%x-%j.err

# ============================================================
# Evaluation Script for Improved RNN
# Runs evaluate_improved_rnn.py on GPU using TensorFlow NGC
# ============================================================

echo "============================================================"
echo "RNN Evaluation Job Started"
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
echo ""

# Set container paths
CONTAINER="$HOME/tensorflow_ngc.sif"

# Check container exists
if [ ! -f "$CONTAINER" ]; then
    echo "ERROR: Container not found at $CONTAINER"
    echo "Please run setup_cluster_node.sh first"
    exit 1
fi

# Run the evaluation
echo "Starting evaluation..."
apptainer exec --nv \
  --bind $(pwd):/workspace \
  --pwd /workspace \
  $CONTAINER \
  bash -c "pip install --no-cache-dir pandas pretty_midi mido matplotlib && python3 evaluate_improved_rnn.py"

EXIT_CODE=$?

echo ""
echo "============================================================"
echo "Job Completed"
echo "============================================================"
echo "End Time:    $(date)"
echo "Exit Code:   $EXIT_CODE"

# List output files
if [ -f "demo_loss_curve.png" ]; then
    echo "Output: demo_loss_curve.png created successfully"
else
    echo "WARNING: demo_loss_curve.png not found"
fi

exit $EXIT_CODE
