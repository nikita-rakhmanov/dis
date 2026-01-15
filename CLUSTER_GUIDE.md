# CS Compute Service - GPU Cluster Guide

This guide explains how to run RNN training/evaluation on the St Andrews CS Compute Service using Nvidia L4 GPUs.

## Quick Reference

| Item | Value |
|------|-------|
| **Login Node** | `compute1.cs.st-andrews.ac.uk` |
| **Username** | `mr298` |
| **Partition** | `gpu-l4-n2` |
| **QoS** | `gpu-l4-n2` |
| **GPU** | Nvidia L4 (24GB VRAM) |
| **Max Resources** | 1 GPU, 16 cores, 96GB RAM |

---

## 1. Connect to the Cluster

### SSH to Login Node

```bash
ssh mr298@compute1.cs.st-andrews.ac.uk
```

> [!NOTE]
> The cluster uses CS SSH certificate or password authentication only. SSH keys (authorized_keys) are **not** supported.

### Use tmux for Long Sessions

Always use `tmux` to prevent losing work if your SSH connection drops:

```bash
# Start a new session
tmux new -s rnn

# Detach: Ctrl+B, then D
# Reattach later:
tmux attach -t rnn
```

---

## 2. First-Time Setup (Run Once)

### Start an Interactive Job

```bash
srun --partition gpu-l4-n2 --qos gpu-l4-n2 --gpus 1 --cpus-per-task 4 --mem 16G --time=02:00:00 --pty bash
```

### Verify GPU Access

```bash
nvidia-smi -L
```

Expected output:
```
GPU 0: NVIDIA L4 (UUID: GPU-...)
```

### Pull TensorFlow Container

```bash
# Set up cache directories (important!)
export APPTAINER_CACHEDIR=$HOME/apptainer-cache
export APPTAINER_TMPDIR=$HOME/apptainer-tmpdir
mkdir -p $APPTAINER_CACHEDIR $APPTAINER_TMPDIR

# Pull the TensorFlow NGC container
apptainer pull $HOME/tensorflow_ngc.sif docker://nvcr.io/nvidia/tensorflow:24.10-tf2-py3
```

> [!TIP]
> This container is ~6GB and includes TensorFlow, CUDA, cuDNN pre-configured for the L4 GPU.

### Create Project Directory and Transfer Files

On the **compute node** (while in the interactive job):

```bash
mkdir -p ~/dis
```

From your **local machine** (separate terminal):

```bash
# Copy your project to the compute node
scp -r /Users/nikita/Desktop/dissertation/dis/* mr298@gpu-l4-n2.cs.st-andrews.ac.uk:~/dis/
```

> [!IMPORTANT]
> You can only SCP directly to a compute node while you have an active job running on it.

### Alternative: Transfer via Login Node

If direct transfer fails, use the login node as intermediate:

```bash
# From local machine to login node
scp -r /Users/nikita/Desktop/dissertation/dis/* mr298@compute1.cs.st-andrews.ac.uk:~/dis_transfer/

# Then from login node, SCP to compute node (within interactive job)
scp -r ~/dis_transfer/* mr298@gpu-l4-n2.cs.st-andrews.ac.uk:~/dis/
```

---

## 3. Running Jobs

### Option A: Interactive Execution (Recommended for Testing)

Start an interactive session and run directly:

```bash
# Start interactive job
srun --partition gpu-l4-n2 --qos gpu-l4-n2 --gpus 1 --cpus-per-task 8 --mem 48G --time=04:00:00 --pty bash

# Navigate to project
cd ~/dis

# Run evaluation with GPU support
apptainer exec --nv \
  --bind $(pwd):/workspace \
  --pwd /workspace \
  $HOME/tensorflow_ngc.sif \
  bash -c "pip install --no-cache-dir pandas pretty_midi mido matplotlib && python3 evaluate_improved_rnn.py"
```

### Option B: Batch Job (Recommended for Long Training)

Submit a job script:

```bash
cd ~/dis
sbatch cluster_scripts/run_evaluate_improved_rnn.sh
```

Monitor job status:

```bash
# See your jobs
squeue -u mr298

# Cancel a job
scancel <JOB_ID>

# View job output (while running or after)
tail -f slurm-*.out
```

---

## 4. Job Scripts

### Evaluation Script

Use `cluster_scripts/run_evaluate_improved_rnn.sh`:

```bash
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

echo "Starting RNN Evaluation on $(hostname)"
echo "GPU Info:"
nvidia-smi -L

apptainer exec --nv \
  --bind $(pwd):/workspace \
  --pwd /workspace \
  $HOME/tensorflow_ngc.sif \
  bash -c "pip install --no-cache-dir pandas pretty_midi mido matplotlib && python3 evaluate_improved_rnn.py"

echo "Job completed at $(date)"
```

### Full Training Script

Use `cluster_scripts/run_train_improved_rnn.sh`:

```bash
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

echo "Starting RNN Training on $(hostname)"
nvidia-smi -L

apptainer exec --nv \
  --bind $(pwd):/workspace \
  --pwd /workspace \
  $HOME/tensorflow_ngc.sif \
  bash -c "pip install --no-cache-dir pandas pretty_midi mido matplotlib && python3 train_improved_rnn.py"

echo "Training completed at $(date)"
```

---

## 5. Retrieving Results

### Copy Output Files

While you have an active job on the node:

```bash
# From local machine
scp mr298@gpu-l4-n2.cs.st-andrews.ac.uk:~/dis/demo_loss_curve.png ./
scp mr298@gpu-l4-n2.cs.st-andrews.ac.uk:~/dis/improved_melody_model.keras ./
scp mr298@gpu-l4-n2.cs.st-andrews.ac.uk:~/dis/model_metadata.json ./
```

### View Output Logs

```bash
cat ~/slurm-eval_rnn-<JOB_ID>.out
cat ~/slurm-eval_rnn-<JOB_ID>.err
```

---

## 6. Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"

The NGC container doesn't include all dependencies. Install them within the container:

```bash
apptainer exec --nv $HOME/tensorflow_ngc.sif pip install pandas pretty_midi mido matplotlib
```

### GPU Not Found

Check if GPU was allocated:

```bash
nvidia-smi
```

If it shows nothing, ensure you requested `--gpus 1` in your job.

### "Permission denied" on SCP

You can only SCP to a compute node while you have an active job. Start an interactive job first.

### Job Pending Forever

Check available resources:

```bash
sinfo -p gpu-l4-n2
squeue -p gpu-l4-n2
```

### Container Pull Fails

Check disk quota:

```bash
quota -s
du -sh ~/*
```

Free space by removing old files if needed.

---

## 7. Useful Commands

| Command | Description |
|---------|-------------|
| `squeue -u mr298` | View your jobs |
| `scancel <ID>` | Cancel a job |
| `sinfo` | View cluster status |
| `scontrol show job <ID>` | Job details |
| `sacct -j <ID>` | Job accounting info |
| `quota -s` | Check disk quota |

---

## 8. Example Workflow

```bash
# 1. Connect
ssh mr298@compute1.cs.st-andrews.ac.uk
tmux new -s work

# 2. Start interactive job
srun --partition gpu-l4-n2 --qos gpu-l4-n2 --gpus 1 --time=06:00:00 --pty bash

# 3. First time only: pull container
export APPTAINER_CACHEDIR=$HOME/apptainer-cache
mkdir -p $APPTAINER_CACHEDIR
apptainer pull $HOME/tensorflow_ngc.sif docker://nvcr.io/nvidia/tensorflow:24.10-tf2-py3

# 4. Run evaluation
cd ~/dis
apptainer exec --nv \
  --bind $(pwd):/workspace \
  --pwd /workspace \
  $HOME/tensorflow_ngc.sif \
  bash -c "pip install --no-cache-dir pandas pretty_midi mido matplotlib && python3 evaluate_improved_rnn.py"

# 5. Check results
ls -la demo_loss_curve.png
```

---

## Contact

For cluster issues, email: **cs-support@st-andrews.ac.uk**
