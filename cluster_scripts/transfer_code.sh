#!/bin/bash
# ============================================================
# Transfer Script - Sends only essential code to the cluster
# Excludes: datasets, models, venv, cache, git history
# ============================================================

# Configuration
REMOTE_USER="mr298"
REMOTE_HOST="gpu-l4-n2.cs.st-andrews.ac.uk"
REMOTE_PATH="~/dis"
LOCAL_PATH="/Users/nikita/Desktop/dissertation/dis"

echo "============================================================"
echo "Transferring code to cluster (excluding large files)"
echo "============================================================"
echo ""
echo "From: $LOCAL_PATH"
echo "To:   $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"
echo ""

# Check if rsync is available
if command -v rsync &> /dev/null; then
    echo "Using rsync for efficient transfer..."
    echo ""
    
    rsync -avz --progress \
        --exclude 'data/' \
        --exclude 'venv/' \
        --exclude '__pycache__/' \
        --exclude '.git/' \
        --exclude '*.keras' \
        --exclude '*.h5' \
        --exclude '*.npy' \
        --exclude '*.sif' \
        --exclude '*.zip' \
        --exclude '.DS_Store' \
        --exclude 'training_checkpoints/' \
        --exclude 'drafts/' \
        --exclude 'docs/' \
        --exclude '*.pyc' \
        --exclude '.gitignore' \
        "$LOCAL_PATH/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
else
    echo "rsync not found, using scp..."
    echo "Note: scp is less efficient - consider installing rsync"
    echo ""
    
    # Create a temp directory with only needed files
    TEMP_DIR=$(mktemp -d)
    echo "Creating filtered copy in $TEMP_DIR..."
    
    # Copy only essential files
    cp "$LOCAL_PATH"/*.py "$TEMP_DIR/" 2>/dev/null
    cp "$LOCAL_PATH"/*.txt "$TEMP_DIR/" 2>/dev/null
    cp "$LOCAL_PATH"/*.md "$TEMP_DIR/" 2>/dev/null
    cp -r "$LOCAL_PATH/cluster_scripts" "$TEMP_DIR/" 2>/dev/null
    cp -r "$LOCAL_PATH/gesture_control" "$TEMP_DIR/" 2>/dev/null
    
    scp -r "$TEMP_DIR"/* "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    
    rm -rf "$TEMP_DIR"
fi

echo ""
echo "============================================================"
echo "Transfer complete!"
echo "============================================================"
echo ""
echo "Next: SSH to the cluster and run your job"
echo "  ssh $REMOTE_USER@compute1.cs.st-andrews.ac.uk"
