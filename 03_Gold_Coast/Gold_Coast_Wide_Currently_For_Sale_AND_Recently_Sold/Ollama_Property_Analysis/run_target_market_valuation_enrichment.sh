#!/bin/bash
# Target Market Valuation Enrichment Script
# Last Updated: 24/02/2026
#
# Runs GPT valuation-grade photo & floor plan enrichment for 8 target market suburbs.
# Writes property_valuation_data, floor_plan_analysis, and processing_status to
# Gold_Coast_Currently_For_Sale.[suburb].
#
# These fields are preserved automatically when properties sell and are migrated
# to Gold_Coast_Recently_Sold by monitor_sold_properties.py.
#
# Called by Fields Orchestrator Process 108

set -e  # Exit on error

echo "=========================================="
echo "Target Market Valuation Enrichment"
echo "Started: $(date)"
echo "=========================================="

# Base directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run enrichment for all 8 target market suburbs
python3 enrich_for_sale_batch.py

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "Target Market Valuation Enrichment Complete"
else
    echo "Target Market Valuation Enrichment FAILED (exit code $EXIT_CODE)"
fi
echo "Completed: $(date)"
echo "=========================================="

exit $EXIT_CODE
