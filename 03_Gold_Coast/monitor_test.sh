#!/bin/bash

echo "==========================================" 
echo "Monitoring Test VM Progress"
echo "=========================================="
echo ""

BUCKET="gs://property-scraper-test-data-477306/test_data/"
MAX_WAIT=300  # 5 minutes
ELAPSED=0

echo "Waiting for scraper to complete..."
echo "(This may take 3-5 minutes)"
echo ""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Check if files exist in GCS
    FILE_COUNT=$(gsutil ls -r $BUCKET 2>/dev/null | grep ".json$" | wc -l)
    
    if [ $FILE_COUNT -gt 0 ]; then
        echo "✓ Found $FILE_COUNT JSON files in GCS!"
        echo ""
        echo "Listing files:"
        gsutil ls -r $BUCKET
        echo ""
        echo "=========================================="
        echo "SUCCESS! Scraper completed."
        echo "=========================================="
        exit 0
    fi
    
    echo "  Waiting... ($ELAPSED seconds elapsed, $FILE_COUNT files found)"
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

echo ""
echo "⚠ Timeout reached. Checking VM logs..."
echo ""
gcloud compute instances get-serial-port-output property-scraper-test --zone=us-central1-a | tail -100
