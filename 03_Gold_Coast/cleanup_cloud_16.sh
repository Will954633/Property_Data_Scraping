#!/bin/bash

echo "=========================================="
echo "Cleanup 16 Cloud Workers"
echo "=========================================="
echo ""

INSTANCES=$(gcloud compute instances list --filter="name:property-scraper-hybrid" --format="value(name)" 2>/dev/null | wc -l)

echo "Found $INSTANCES cloud workers"
echo ""
read -p "Delete all cloud workers? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Deleting cloud workers..."

gcloud compute instances list \
    --filter="name:property-scraper-hybrid" \
    --format="value(name,zone)" 2>/dev/null | \
while IFS=$'\t' read -r NAME ZONE; do
    echo "  Deleting $NAME in $ZONE"
    gcloud compute instances delete "$NAME" --zone="$ZONE" --quiet 2>/dev/null || echo "    (already deleted)"
done

echo ""
echo "=========================================="
echo "✓ Cloud Workers Cleaned Up"
echo "=========================================="
echo ""
echo "Note: Local workers may still be running"
echo "To stop local workers:"
echo "  pkill -f domain_scraper_gcs.py"
echo ""
