# GPU Training Guide - PC9 Lab Machines

**Target Hardware**: PC9-001 to PC9-010 (RTX 3060 GPUs)
**Environment**: Linux with Podman (rootless containers)

---

## ⚠️ Important Notes

1. **Home directories are cleared on reboot** - Save your models externally!
2. **Use Podman, not Docker** - Docker command is aliased to Podman
3. **GPU access**: Use `--device nvidia.com/gpu=all` flag
4. **Mount volumes**: Use `:z` annotation (e.g., `-v $(pwd):/workspace:z`)

---

## Quick Start - Run Training on GPU

### 1. On PC9 Lab Machine (C0.35)

First, verify GPU is available:
```bash
podman run --rm --device nvidia.com/gpu=all ubuntu nvidia-smi -L
```

Expected output: `GPU 0: NVIDIA GeForce RTX 3060 (UUID: ...)`

---

### 2. Clone Your Repository

```bash
cd ~/
git clone https://github.com/nikita-rakhmanov/dis.git
cd dis
git checkout claude/optimize-rnn-model-011CV2Hmb3tQG8U7jhSDyr1X
```

Or if already cloned:
```bash
cd ~/dis
git pull origin claude/optimize-rnn-model-011CV2Hmb3tQG8U7jhSDyr1X
```

---

### 3. Run Training in TensorFlow GPU Container

**Option A: Using TensorFlow Official Image (Recommended)**

```bash
podman run --rm \
  --device nvidia.com/gpu=all \
  --volume $(pwd):/workspace:z \
  --workdir /workspace \
  --shm-size=2g \
  docker.io/tensorflow/tensorflow:latest-gpu \
  python3 train_music_rnn.py
```

**Option B: Using NVIDIA NGC TensorFlow Image (More Optimized)**

```bash
podman run --rm \
  --device nvidia.com/gpu=all \
  --volume $(pwd):/workspace:z \
  --workdir /workspace \
  --shm-size=2g \
  nvcr.io/nvidia/tensorflow:24.10-tf2-py3 \
  python3 train_music_rnn.py
```

**What this does**:
- `--device nvidia.com/gpu=all`: Gives container access to all GPUs
- `--volume $(pwd):/workspace:z`: Mounts current directory to /workspace (with SELinux label)
- `--workdir /workspace`: Sets working directory in container
- `--shm-size=2g`: Increases shared memory (helps with large batches)
- `--rm`: Auto-removes container when done

---

### 4. Monitor Training Progress

The training script will output:
- Epoch progress (1/50, 2/50, etc.)
- Loss values for pitch, step, duration
- Checkpoints saved every epoch

Example output:
```
Epoch 1/50
1234/1234 [==============================] - 45s 36ms/step - loss: 1.2345 - pitch_loss: 2.345 - step_loss: 0.234 - duration_loss: 0.156
...
```

---

## 🔧 Troubleshooting

### GPU Not Detected

If you see "GPU will not be used" error:
```bash
# Test GPU access first
podman run --rm --device nvidia.com/gpu=all ubuntu nvidia-smi

# Should show GPU info, not errors
```

### Out of Memory (OOM) Errors

If training crashes with OOM:
1. **Reduce batch size**: Edit `train_music_rnn.py` before running:
   ```python
   BATCH_SIZE = 32  # Or 16
   ```

2. **Use smaller sequence**:
   ```python
   SEQUENCE_LENGTH = 40  # Instead of 50
   ```

3. **Reduce training files**:
   ```python
   NUM_TRAINING_FILES = 500  # Instead of 1000
   ```

### Container Can't Find Files

Make sure you're in the `dis` directory when running podman:
```bash
cd ~/dis
pwd  # Should show /home/USERNAME/dis
ls   # Should show train_music_rnn.py
```

### Permission Denied Errors

Use `:z` flag on volume mount (already in commands above):
```bash
--volume $(pwd):/workspace:z
```

---

## 💾 Saving Your Trained Model

**CRITICAL**: Home directories are wiped on reboot!

### Option 1: Copy to External Storage

After training completes:
```bash
# Copy model and checkpoints to USB drive or network location
cp music_rnn_model.keras /path/to/external/storage/
cp seed_sequence.npy /path/to/external/storage/
cp -r training_checkpoints/ /path/to/external/storage/
```

### Option 2: Push to Git LFS (If Available)

```bash
git lfs track "*.keras"
git add music_rnn_model.keras seed_sequence.npy
git commit -m "Add trained model with optimizations"
git push
```

### Option 3: Upload to Cloud Storage

```bash
# Example with scp to remote server
scp music_rnn_model.keras user@yourserver:~/models/
```

---

## 📊 Expected Training Time

**Hardware**: RTX 3060 (12GB)
**Configuration**: SEQUENCE_LENGTH=50, BATCH_SIZE=64, 1000 files

**Estimated Time**:
- Per epoch: ~2-4 minutes (depends on data preprocessing)
- Total (50 epochs): ~2-3 hours
- With early stopping: ~1.5-2 hours (may stop at epoch 30-40)

**Performance Check**:
- If < 1 minute/epoch: ✅ GPU is working well
- If > 10 minutes/epoch: ⚠️ Something's wrong (likely using CPU)

---

## 🧪 Testing the Model After Training

### Inside the Container (Quick Test)

```bash
podman run --rm -it \
  --device nvidia.com/gpu=all \
  --volume $(pwd):/workspace:z \
  --workdir /workspace \
  docker.io/tensorflow/tensorflow:latest-gpu \
  python3 -c "
import tensorflow as tf
model = tf.keras.models.load_model('music_rnn_model.keras',
    custom_objects={'mse_with_positive_pressure': lambda y_true, y_pred: tf.reduce_mean((y_true - y_pred)**2 + 10*tf.maximum(-y_pred, 0.0))})
print('✅ Model loaded successfully!')
print(f'Model expects input shape: {model.input_shape}')
"
```

### On Your Local Machine (For MIDI Generation)

Copy the model back to your dev machine:
```bash
# On PC9 machine
scp music_rnn_model.keras seed_sequence.npy your-dev-machine:~/dis/

# On your dev machine
cd ~/dis
python realtime_midi_generator.py --temperature 1.5
```

---

## 📝 Training Checklist

- [ ] SSH/login to PC9 lab machine (PC9-001 to PC9-010)
- [ ] Clone/update repository
- [ ] Verify GPU access: `podman run --rm --device nvidia.com/gpu=all ubuntu nvidia-smi`
- [ ] Run training command (see Option A or B above)
- [ ] Monitor training progress (losses decreasing?)
- [ ] Wait for completion (~2-3 hours)
- [ ] Copy trained model to external storage (don't lose it on reboot!)
- [ ] Test model loading
- [ ] Transfer model to dev machine for generation

---

## 🎵 After Training

Once you have the trained model:

1. **Listen to generated music**:
   ```bash
   python realtime_midi_generator.py --temperature 1.0
   python realtime_midi_generator.py --temperature 1.5
   python realtime_midi_generator.py --temperature 2.0
   ```

2. **Compare to old model**:
   - Better melodies? (Thanks to pitch weight fix)
   - Longer coherence? (Thanks to sequence length increase)

3. **Come back for next optimization**:
   - Implement Stacked LSTM architecture
   - Further quality improvements

---

## 🐛 Common Issues & Solutions

### "CUDA out of memory"
→ Reduce `BATCH_SIZE` to 32 or 16

### "No space left on device"
→ Dataset might be too large, reduce `NUM_TRAINING_FILES` to 500

### Training very slow (>10 min/epoch)
→ GPU not being used, check `--device nvidia.com/gpu=all` flag

### "Cannot find train_music_rnn.py"
→ Make sure you're in the `dis` directory: `cd ~/dis`

### Model lost after reboot
→ Remember: Home directories are ephemeral! Always backup immediately

---

## 📚 Additional Resources

- **NGC TensorFlow Containers**: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tensorflow
- **Podman Documentation**: https://docs.podman.io/
- **TensorFlow GPU Guide**: https://www.tensorflow.org/install/gpu

---

## 💡 Pro Tips

1. **Start with smaller test run**:
   ```python
   NUM_TRAINING_FILES = 100  # Quick test (10-15 min)
   EPOCHS = 10
   ```
   Then do full training once verified it works.

2. **Use `tmux` or `screen`** to keep training running if SSH disconnects:
   ```bash
   tmux new -s training
   # Run your podman command
   # Press Ctrl+B, then D to detach
   # Later: tmux attach -t training
   ```

3. **Monitor GPU usage** while training:
   ```bash
   # In another terminal
   watch -n 1 nvidia-smi
   ```

4. **Save checkpoints frequently** - They're in `training_checkpoints/`

---

*Good luck with your GPU training! 🚀*
