#!/bin/bash
set -e

echo "=========================================="
echo "Stopping All Google Cloud Workers"
echo "=========================================="

# Configuration
PROJECT_ID="property-data-scraping-477306"

echo ""
echo "Setting GCP project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

echo ""
echo "Finding all running instances..."
INSTANCES=$(gcloud compute instances list --format="value(name,zone)" --filter="name~'property-scraper-.*' AND status=RUNNING")

if [ -z "$INSTANCES" ]; then
    echo "✓ No running workers found"
    exit 0
fi

echo ""
echo "Found running instances:"
echo "$INSTANCES"
echo ""

# Count instances
INSTANCE_COUNT=$(echo "$INSTANCES" | wc -l | tr -d ' ')
echo "Total instances to stop: $INSTANCE_COUNT"
echo ""

read -p "Stop all $INSTANCE_COUNT instances? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

echo ""
echo "Stopping instances..."

while IFS=$'\t' read -r INSTANCE_NAME ZONE; do
    if [ ! -z "$INSTANCE_NAME" ]; then
        echo "  Stopping: $INSTANCE_NAME in $ZONE"
        gcloud compute instances delete "$INSTANCE_NAME" \
            --zone="$ZONE" \
            --quiet &
    fi
done <<< "$INSTANCES"

wait

echo ""
echo "=========================================="
echo "✓ All Google Cloud Workers Stopped"
echo "=========================================="
echo ""
echo "Next step: Download GCS data to MongoDB"
echo "  ./download_gcs_to_mongodb.sh"
echo ""
