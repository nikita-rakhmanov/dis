#!/bin/bash
# ============================================================
# First-Time Setup Script for CS Compute Node
# Run this ONCE in an interactive job to set up the environment
# ============================================================

echo "============================================================"
echo "Cluster Node Setup Script"
echo "============================================================"
echo ""

# Check if we're on a compute node
if [ -z "$SLURM_JOB_ID" ]; then
    echo "WARNING: This script should be run inside a Slurm job"
    echo "Start an interactive job first:"
    echo "  srun --partition gpu-l4-n2 --qos gpu-l4-n2 --gpus 1 --time=02:00:00 --pty bash"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Create directories
echo "[1/4] Creating directories..."
mkdir -p ~/dis
mkdir -p ~/apptainer-cache
mkdir -p ~/apptainer-tmpdir
echo "  ✓ Created ~/dis"
echo "  ✓ Created ~/apptainer-cache"
echo "  ✓ Created ~/apptainer-tmpdir"
echo ""

# 2. Set Apptainer environment
echo "[2/4] Setting up Apptainer environment..."
export APPTAINER_CACHEDIR=$HOME/apptainer-cache
export APPTAINER_TMPDIR=$HOME/apptainer-tmpdir
echo "  ✓ APPTAINER_CACHEDIR=$APPTAINER_CACHEDIR"
echo "  ✓ APPTAINER_TMPDIR=$APPTAINER_TMPDIR"
echo ""

# 3. Pull TensorFlow container
CONTAINER="$HOME/tensorflow_ngc.sif"
echo "[3/4] Checking TensorFlow container..."

if [ -f "$CONTAINER" ]; then
    echo "  Container already exists at $CONTAINER"
    echo "  Size: $(du -h $CONTAINER | cut -f1)"
    read -p "  Re-download? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$CONTAINER"
    else
        echo "  Skipping container download"
    fi
fi

if [ ! -f "$CONTAINER" ]; then
    echo "  Pulling TensorFlow NGC container..."
    echo "  This may take 10-15 minutes for ~6GB download..."
    apptainer pull $CONTAINER docker://nvcr.io/nvidia/tensorflow:24.10-tf2-py3
    if [ $? -eq 0 ]; then
        echo "  ✓ Container downloaded successfully"
        echo "  Size: $(du -h $CONTAINER | cut -f1)"
    else
        echo "  ✗ Container download failed!"
        exit 1
    fi
fi
echo ""

# 4. Verify GPU access
echo "[4/4] Verifying GPU access..."
nvidia-smi -L
if [ $? -eq 0 ]; then
    echo "  ✓ GPU is accessible"
else
    echo "  ✗ GPU not found - make sure you requested --gpus 1"
fi
echo ""

# Summary
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Transfer your code to ~/dis on this node"
echo "     From your local machine:"
echo "     scp -r your_project/* mr298@$(hostname).cs.st-andrews.ac.uk:~/dis/"
echo ""
echo "  2. Run the evaluation:"
echo "     cd ~/dis"
echo "     sbatch cluster_scripts/run_evaluate_improved_rnn.sh"
echo ""
echo "  3. Or run interactively:"
echo "     apptainer exec --nv --bind \$(pwd):/workspace --pwd /workspace \\"
echo "       \$HOME/tensorflow_ngc.sif \\"
echo "       bash -c 'pip install pandas pretty_midi mido matplotlib && python3 evaluate_improved_rnn.py'"
echo ""

# Show disk usage
echo "Current disk usage:"
du -sh ~/*
echo ""
echo "Quota:"
quota -s 2>/dev/null || echo "(quota command not available)"
