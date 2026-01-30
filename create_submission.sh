#!/bin/bash

OUTPUT_FILE="submission.zip"
OUTPUT_DIR=$(pwd)

echo "=== Creating Submission Package ==="
echo ""

# Remove old submission zip if exists
if [ -f "$OUTPUT_FILE" ]; then
    echo "Removing old $OUTPUT_FILE..."
    rm "$OUTPUT_FILE"
fi

# Create the zip file
echo "Creating $OUTPUT_FILE..."
zip -r "$OUTPUT_FILE" \
    *.py \
    *.md \
    *.txt \
    *.html \
    *.js \
    *.css \
    *.json \
    *.keras \
    *.npy \
    docs/ \
    gesture_control/ \
    model_comparison/ \
    data_analysis/ \
    -x "*.pyc" \
    -x "*__pycache__*" \
    -x "*.DS_Store" \
    -x "create_submission.sh"

echo ""
echo "=== Submission Package Created ==="
echo ""

# Show the size
SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo "File: $OUTPUT_FILE"
echo "Size: $SIZE"
echo ""

# Check if under 600MB limit
SIZE_BYTES=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
LIMIT_BYTES=$((600 * 1024 * 1024))

if [ "$SIZE_BYTES" -lt "$LIMIT_BYTES" ]; then
    echo "✓ Under 600MB limit - ready for submission!"
else
    echo "✗ WARNING: File exceeds 600MB limit!"
fi

echo ""
echo "=== Contents Summary ==="
unzip -l "$OUTPUT_FILE" | tail -1

echo ""
echo "=== Excluded (as required) ==="
echo "- venv/ (third party libraries)"
echo "- data/ (third party dataset - MAESTRO)"
echo "- .git/ (version control - use repo link instead)"
echo "- training_checkpoints/ (regenerable)"
echo "- cluster_scripts/"
echo "- figures/"
echo ""
echo "Repository link: https://github.com/nikita-rakhmanov/dis"
