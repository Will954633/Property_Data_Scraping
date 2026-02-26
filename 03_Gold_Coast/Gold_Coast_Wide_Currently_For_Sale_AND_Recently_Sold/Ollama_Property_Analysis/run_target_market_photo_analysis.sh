#!/bin/bash
# Target Market Photo Analysis Script
# Last Updated: 04/02/2026, 7:18 AM (Tuesday) - Brisbane
#
# Runs Ollama photo analysis for 8 target market suburbs
# Called by Fields Orchestrator Process 105

set -e  # Exit on error

echo "=========================================="
echo "Target Market Photo Analysis"
echo "Started: $(date)"
echo "=========================================="

# Base directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Target market suburbs (collection names in lowercase with underscores)
TARGET_SUBURBS=(
    "robina"
    "varsity_lakes"
    "burleigh_waters"
)

# Process each suburb
for suburb in "${TARGET_SUBURBS[@]}"; do
    echo ""
    echo "=========================================="
    echo "Processing: $suburb"
    echo "=========================================="

    # Run photo analysis with 4 workers
    python3 run_production.py --collection "$suburb" --workers 4

    if [ $? -eq 0 ]; then
        echo "✅ $suburb photo analysis completed successfully"
    else
        echo "❌ $suburb photo analysis failed"
        exit 1
    fi

    # Run photo reorder (creates photo_tour_order from ollama_image_analysis)
    echo ""
    echo "Running photo reorder for: $suburb"
    python3 run_photo_reorder.py --collection "$suburb"

    if [ $? -eq 0 ]; then
        echo "✅ $suburb photo reorder completed successfully"
    else
        echo "❌ $suburb photo reorder failed"
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "Target Market Photo Analysis Complete"
echo "Completed: $(date)"
echo "=========================================="
