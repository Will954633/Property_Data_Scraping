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
# TESTING MODE: Only Robina for rapid feedback
# To re-enable all suburbs, uncomment the other lines
TARGET_SUBURBS=(
    "robina"
    # TESTING: Temporarily disabled - uncomment after testing
    # "mudgeeraba"
    # "varsity_lakes"
    # "reedy_creek"
    # "burleigh_waters"
    # "merrimac"
    # "worongary"
    # "carrara"
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
        echo "✅ $suburb completed successfully"
    else
        echo "❌ $suburb failed"
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "Target Market Photo Analysis Complete"
echo "Completed: $(date)"
echo "=========================================="
