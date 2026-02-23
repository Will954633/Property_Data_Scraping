#!/bin/bash

# Configuration
BUCKET="property-scraper-production-data-477306"
TOTAL_TARGET=331224
START_TIME_FILE="/tmp/scraper_start_time.txt"

# Save start time on first run
if [ ! -f "$START_TIME_FILE" ]; then
    date +%s > "$START_TIME_FILE"
fi

START_TIMESTAMP=$(cat "$START_TIME_FILE")
CURRENT_TIMESTAMP=$(date +%s)
ELAPSED_SECONDS=$((CURRENT_TIMESTAMP - START_TIMESTAMP))

clear
echo "=========================================="
echo "Property Scraping Progress Monitor"
echo "Time: $(date '+%I:%M %p %Z')"
echo "=========================================="
echo ""

# Get current count
echo "Fetching current count from GCS..."
CURRENT_COUNT=$(gsutil ls -r gs://$BUCKET/scraped_data/ 2>/dev/null | grep -c "\.json$" || echo "0")

# Calculate progress
PROGRESS=$(echo "scale=2; $CURRENT_COUNT * 100 / $TOTAL_TARGET" | bc)

# Calculate elapsed time
ELAPSED_HOURS=$(echo "scale=2; $ELAPSED_SECONDS / 3600" | bc)
ELAPSED_MINS=$(echo "scale=0; $ELAPSED_SECONDS / 60" | bc)

echo ""
echo "=========================================="
echo "Progress Summary:"
echo "=========================================="
printf "  Properties Scraped: %'d / %'d\n" $CURRENT_COUNT $TOTAL_TARGET
printf "  Progress: %.2f%%\n" $PROGRESS
printf "  Elapsed Time: %d minutes (%.1f hours)\n" $ELAPSED_MINS $ELAPSED_HOURS
echo ""

# Calculate rate and ETA
if [ $CURRENT_COUNT -gt 0 ] && [ $ELAPSED_SECONDS -gt 0 ]; then
    # Properties per hour
    RATE=$(echo "scale=1; $CURRENT_COUNT * 3600 / $ELAPSED_SECONDS" | bc)
    
    # Remaining properties
    REMAINING=$((TOTAL_TARGET - CURRENT_COUNT))
    
    # Time remaining in hours
    if [ $(echo "$RATE > 0" | bc) -eq 1 ]; then
        REMAINING_HOURS=$(echo "scale=1; $REMAINING / $RATE" | bc)
        REMAINING_MINS=$(echo "scale=0; $REMAINING * 60 / $RATE" | bc)
        
        # Calculate ETA
        ETA_TIMESTAMP=$((CURRENT_TIMESTAMP + (REMAINING * 3600 / ${RATE%.*})))
        ETA_DATE=$(date -r $ETA_TIMESTAMP '+%I:%M %p, %b %d')
        
        echo "=========================================="
        echo "Performance Metrics:"
        echo "=========================================="
        printf "  Scraping Rate: %.1f properties/hour\n" $RATE
        printf "  Remaining: %'d properties\n" $REMAINING
        printf "  Est. Time Remaining: %d minutes (%.1f hours)\n" $REMAINING_MINS $REMAINING_HOURS
        printf "  Estimated Completion: %s\n" "$ETA_DATE"
        echo ""
    fi
fi

# Worker status
echo "=========================================="
echo "Worker Status:"
echo "=========================================="

# Cloud workers
CLOUD_RUNNING=$(gcloud compute instances list --filter="name:property-scraper-hybrid AND status:RUNNING" --format="value(name)" 2>/dev/null | wc -l)
echo "  Cloud Workers: $CLOUD_RUNNING / 16"

# Local workers  
LOCAL_RUNNING=$(ps aux | grep -c "[d]omain_scraper_gcs.py" || echo "0")
echo "  Local Workers: $LOCAL_RUNNING / 10"
echo "  Total Workers: $((CLOUD_RUNNING + LOCAL_RUNNING)) / 26"

echo ""
echo "=========================================="
echo "Commands:"
echo "=========================================="
echo ""
echo "Re-run this monitor:"
echo "  ./monitor_progress.sh"
echo ""
echo "Watch continuously (updates every 60 seconds):"
echo "  watch -n 60 './monitor_progress.sh'"
echo ""
echo "Check local worker log:"
echo "  tail worker_logs/worker_16.log"
echo ""
echo "Download results so far:"
echo "  mkdir -p partial_results"
echo "  gsutil -m cp -r gs://$BUCKET/scraped_data/ ./partial_results/"
echo ""
echo "=========================================="
