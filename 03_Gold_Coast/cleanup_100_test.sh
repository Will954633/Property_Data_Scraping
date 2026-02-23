#!/bin/bash

# Configuration
PROJECT_ID="property-data-scraping-477306"
ZONE="us-central1-a"
INSTANCE_BASE="property-scraper-100test"
TOTAL_WORKERS=30

echo "=========================================="
echo "Cleanup 100-Address Test Workers"
echo "=========================================="
echo ""
echo "This will delete all $TOTAL_WORKERS worker instances"
echo "Instance pattern: ${INSTANCE_BASE}-0 to ${INSTANCE_BASE}-$((TOTAL_WORKERS-1))"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Deleting workers..."

for ((i=0; i<TOTAL_WORKERS; i++)); do
    INSTANCE_NAME="${INSTANCE_BASE}-${i}"
    echo "  Deleting worker $i: $INSTANCE_NAME"
    gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet 2>/dev/null || echo "    (already deleted)"
done

echo ""
echo "=========================================="
echo "✓ Cleanup Complete"
echo "=========================================="
echo ""
echo "Note: Test data remains in GCS bucket"
echo "To delete test data: gsutil -m rm -r gs://property-scraper-test-data-477306/scraped_data/"
echo ""
