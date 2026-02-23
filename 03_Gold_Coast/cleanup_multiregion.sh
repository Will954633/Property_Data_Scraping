#!/bin/bash

# Configuration
PROJECT_ID="property-data-scraping-477306"
INSTANCE_PATTERN="property-scraper-prod"

echo "=========================================="
echo "Cleanup Multi-Region Deployment"
echo "=========================================="
echo ""

# List all workers
INSTANCES=$(gcloud compute instances list --filter="name:$INSTANCE_PATTERN" --format="value(name,zone)" | wc -l)

echo "Found $INSTANCES workers across all regions"
echo ""
echo "This will delete ALL production workers"
echo ""
read -p "Continue with cleanup? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Deleting workers..."
echo ""

# Get list of all instances and their zones
gcloud compute instances list \
    --filter="name:$INSTANCE_PATTERN" \
    --format="value(name,zone)" | \
while IFS=$'\t' read -r NAME ZONE; do
    echo "  Deleting $NAME in $ZONE"
    gcloud compute instances delete "$NAME" --zone="$ZONE" --quiet 2>/dev/null || echo "    (already deleted or error)"
done

echo ""
echo "=========================================="
echo "✓ Cleanup Complete"
echo "=========================================="
echo ""
echo "Note: Scraped data remains in GCS bucket"
echo "To delete scraped data:"
echo "  gsutil -m rm -r gs://property-scraper-production-data-477306/scraped_data/"
echo ""
echo "To delete the entire bucket:"
echo "  gsutil -m rm -r gs://property-scraper-production-data-477306/"
echo ""
