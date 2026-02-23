#!/bin/bash

# Configuration
PROJECT_ID="property-data-scraping-477306"
BUCKET_NAME="property-scraper-test-data-477306"
ZONE="us-central1-a"
INSTANCE_BASE="property-scraper-100test"
TOTAL_WORKERS=30

echo "=========================================="
echo "100-Address Test Monitor"
echo "=========================================="
echo ""

# Check worker status
echo "Worker Status:"
echo "----------------------------------------"
for ((i=0; i<TOTAL_WORKERS; i++)); do
    INSTANCE_NAME="${INSTANCE_BASE}-${i}"
    STATUS=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="value(status)" 2>/dev/null || echo "NOT_FOUND")
    printf "  Worker %2d (%s): %s\n" $i $INSTANCE_NAME $STATUS
done

echo ""
echo "=========================================="
echo "Results in GCS Bucket:"
echo "=========================================="

# Count files in bucket
FILE_COUNT=$(gsutil ls -r gs://$BUCKET_NAME/scraped_data/ 2>/dev/null | grep -c "\.json$" || echo "0")
echo "  JSON files created: $FILE_COUNT / 100"

echo ""
echo "=========================================="
echo "Recent files:"
gsutil ls -lh gs://$BUCKET_NAME/scraped_data/worker_*/  2>/dev/null | tail -10 || echo "  No files yet"

echo ""
echo "=========================================="
echo "Commands:"
echo "  Re-run this monitor: ./monitor_100_test.sh"
echo "  Check worker 0 logs: gcloud compute instances get-serial-port-output ${INSTANCE_BASE}-0 --zone=$ZONE"
echo "  Download results: mkdir -p test_results_100 && gsutil -m cp -r gs://$BUCKET_NAME/scraped_data/ ./test_results_100/"
echo "  Cleanup workers: ./cleanup_100_test.sh"
echo "=========================================="
