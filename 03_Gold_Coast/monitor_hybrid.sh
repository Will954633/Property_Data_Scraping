#!/bin/bash

# Configuration
BUCKET_NAME="property-scraper-production-data-477306"
INSTANCE_PATTERN="property-scraper-hybrid"

clear
echo "=========================================="
echo "Hybrid Deployment Monitor"
echo "Time: $(date)"
echo "=========================================="
echo ""

# Cloud Workers Status
echo "Cloud Workers (IDs 0-15):"
echo "----------------------------------------"

CLOUD_RUNNING=$(gcloud compute instances list --filter="name:$INSTANCE_PATTERN AND status:RUNNING" --format="value(name)" 2>/dev/null | wc -l)
CLOUD_TERMINATED=$(gcloud compute instances list --filter="name:$INSTANCE_PATTERN AND status:TERMINATED" --format="value(name)" 2>/dev/null | wc -l)

echo "  Running: $CLOUD_RUNNING / 16"
echo "  Terminated: $CLOUD_TERMINATED"

# Local Workers Status
echo ""
echo "Local Workers (IDs 16-25):"
echo "----------------------------------------"

LOCAL_RUNNING=$(ps aux | grep -c "[d]omain_scraper_gcs.py" || echo "0")
echo "  Running: $LOCAL_RUNNING / 10"

# GCS Results
echo ""
echo "=========================================="
echo "Scraping Progress:"
echo "=========================================="

FILE_COUNT=$(gsutil ls -r gs://$BUCKET_NAME/scraped_data/ 2>/dev/null | grep -c "\.json$" || echo "0")
PROGRESS=$(echo "scale=2; $FILE_COUNT / 331224 * 100" | bc 2>/dev/null || echo "0")

echo "  Properties scraped: $FILE_COUNT / 331,224"
echo "  Progress: $PROGRESS%"

# Estimate if we have data
if [ $FILE_COUNT -gt 100 ]; then
    # Rough rate calculation
    echo ""
    echo "  📊 Scraping is progressing..."
fi

# Worker breakdown
echo ""
echo "Results by Worker:"
echo "----------------------------------------"

# Count files per worker (showing first 10 workers)
for ((w=0; w<10; w++)); do
    WORKER_FILES=$(gsutil ls -r gs://$BUCKET_NAME/scraped_data/worker_$(printf "%03d" $w)/ 2>/dev/null | grep -c "\.json$" || echo "0")
    if [ $WORKER_FILES -gt 0 ]; then
        printf "  Worker %2d: %5d files\n" $w $WORKER_FILES
    fi
done

echo "  ..."
echo "  (showing first 10 workers for brevity)"

echo ""
echo "=========================================="
echo "Commands:"
echo "=========================================="
echo ""
echo "Re-run monitor:"
echo "  ./monitor_hybrid.sh"
echo ""
echo "Continuous monitoring (every 30s):"
echo "  watch -n 30 './monitor_hybrid.sh'"
echo ""
echo "Check local worker log:"
echo "  tail -f worker_logs/worker_16.log"
echo ""
echo "Check cloud worker log:"
echo "  gcloud compute instances get-serial-port-output property-scraper-hybrid-0 --zone=us-central1-a 2>/dev/null | tail -50"
echo ""
echo "Stop local workers:"
echo "  pkill -f domain_scraper_gcs.py"
echo ""
echo "Cleanup cloud workers:"
echo "  ./cleanup_cloud_16.sh"
echo ""
echo "=========================================="
