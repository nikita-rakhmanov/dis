#!/bin/bash

TEMPERATURE=0.8
SPEED=16.0
HARMONY_STYLE="classical"

echo "========================================"
echo "  AI Music Generation Launcher"
echo "========================================"
echo ""
echo "Select harmony mode:"
echo "  [1] Simple (rule-based) - default"
echo "  [2] Learned (neural network)"
echo "  [3] No polyphony (melody only)"
echo ""
read -p "Enter choice (1/2/3): " choice

case $choice in
    2)
        echo ""
        echo "Starting with LEARNED harmony mode..."
        python integrated_music_gesture_control.py \
            --polyphony \
            --harmony-mode learned \
            --harmony-model harmony_model_converted.h5 \
            --harmony-style $HARMONY_STYLE \
            --temperature $TEMPERATURE \
            --speed $SPEED
        ;;
    3)
        echo ""
        echo "Starting MELODY ONLY (no polyphony)..."
        python integrated_music_gesture_control.py \
            --temperature $TEMPERATURE \
            --speed $SPEED
        ;;
    *)
        echo ""
        echo "Starting with SIMPLE harmony mode..."
        python integrated_music_gesture_control.py \
            --polyphony \
            --harmony-style $HARMONY_STYLE \
            --temperature $TEMPERATURE \
            --speed $SPEED
        ;;
esac
