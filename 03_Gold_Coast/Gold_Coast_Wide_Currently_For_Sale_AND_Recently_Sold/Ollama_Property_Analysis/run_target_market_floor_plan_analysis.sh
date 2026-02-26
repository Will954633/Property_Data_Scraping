#!/bin/bash
# Target Market Floor Plan Analysis Script
# Last Updated: 06/02/2026, 10:18 AM (Thursday) - Brisbane
#
# Runs OpenAI GPT floor plan analysis for 8 target market suburbs
# UPDATED: Now uses 3 parallel workers for faster processing with OpenAI API
# Called by Fields Orchestrator Process 106

set -e  # Exit on error

echo "=========================================="
echo "Target Market Floor Plan Analysis"
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

# Process each suburb with 3 parallel workers (optimized for OpenAI API)
for suburb in "${TARGET_SUBURBS[@]}"; do
    echo ""
    echo "=========================================="
    echo "Processing: $suburb (3 parallel workers)"
    echo "=========================================="
    
    # Run floor plan analysis with 3 workers for OpenAI API
    python3 ollama_floor_plan_analysis.py --collection "$suburb" --workers 3
    
    if [ $? -eq 0 ]; then
        echo "✅ $suburb completed successfully"
    else
        echo "❌ $suburb failed"
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "Target Market Floor Plan Analysis Complete"
echo "Completed: $(date)"
echo "=========================================="
