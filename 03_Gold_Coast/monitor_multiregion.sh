#!/bin/bash

# Configuration
PROJECT_ID="property-data-scraping-477306"
BUCKET_NAME="property-scraper-production-data-477306"
INSTANCE_PATTERN="property-scraper-prod"

echo "=========================================="
echo "Multi-Region Production Monitor"
echo "Time: $(date)"
echo "=========================================="
echo ""

# Count workers by status across all regions
echo "Worker Status Across All Regions:"
echo "----------------------------------------"

RUNNING=$(gcloud compute instances list --filter="name:$INSTANCE_PATTERN AND status:RUNNING" --format="value(name)" | wc -l)
TERMINATED=$(gcloud compute instances list --filter="name:$INSTANCE_PATTERN AND status:TERMINATED" --format="value(name)" | wc -l)
TOTAL=$(gcloud compute instances list --filter="name:$INSTANCE_PATTERN" --format="value(name)" | wc -l)

echo "  Running:    $RUNNING"
echo "  Terminated: $TERMINATED"
echo "  Total:      $TOTAL"

echo ""
echo "=========================================="
echo "Results in GCS Bucket:"
echo "=========================================="

# Count files in bucket
FILE_COUNT=$(gsutil ls -r gs://$BUCKET_NAME/scraped_data/ 2>/dev/null | grep -c "\.json$" || echo "0")
PROGRESS=$(echo "scale=2; $FILE_COUNT / 331224 * 100" | bc)

echo "  Properties scraped: $FILE_COUNT / 331,224"
echo "  Progress: $PROGRESS%"

# Estimate completion time
if [ $FILE_COUNT -gt 0 ] && [ $RUNNING -gt 0 ]; then
    # Calculate rate (very rough estimate)
    echo ""
    echo "  Estimated rate: ~$(echo "scale=0; $FILE_COUNT / 1" | bc) addresses so far"
    echo "  (Check again in 30 minutes for better rate estimate)"
fi

echo ""
echo "=========================================="
echo "Workers by Region:"
echo "=========================================="

gcloud compute instances list \
    --filter="name:$INSTANCE_PATTERN" \
    --format="table(name,zone,status)" \
    --sort-by="zone" | head -20

if [ $TOTAL -gt 20 ]; then
    echo "  ... (showing first 20 of $TOTAL workers)"
fi

echo ""
echo "=========================================="
echo "Commands:"
echo "=========================================="
echo ""
echo "Re-run this monitor:"
echo "  ./monitor_multiregion.sh"
echo ""
echo "Continuous monitoring (updates every 30 seconds):"
echo "  watch -n 30 './monitor_multiregion.sh'"
echo ""
echo "Check specific worker logs:"
echo "  gcloud compute instances get-serial-port-output property-scraper-prod-0 --zone=us-central1-a"
echo ""
echo "Download results (after completion):"
echo "  mkdir -p production_results"
echo "  gsutil -m cp -r gs://$BUCKET_NAME/scraped_data/ ./production_results/"
echo ""
echo "Cleanup all workers:"
echo "  ./cleanup_multiregion.sh"
echo ""
echo "=========================================="
