#!/bin/bash

echo "=========================================="
echo "Hybrid Deployment - 10 Local Workers"
echo "Part 2 of 2: Local Workers (IDs 16-25)"
echo "=========================================="

# Configuration
BUCKET_NAME="property-scraper-production-data-477306"
TOTAL_WORKERS=26  # 16 cloud + 10 local
LOCAL_START_ID=16
LOCAL_END_ID=25
MONGODB_URI="mongodb://127.0.0.1:27017/"

echo ""
echo "Configuration:"
echo "  Total Workers: $TOTAL_WORKERS (16 cloud + 10 local)"
echo "  Local Worker IDs: $LOCAL_START_ID-$LOCAL_END_ID"
echo "  MongoDB: Local (direct access)"
echo "  GCS Bucket: $BUCKET_NAME"
echo ""

# Check dependencies
echo "Checking local dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "  ✗ python3 not found"
    exit 1
fi

if ! python3 -c "import selenium" 2>/dev/null; then
    echo "  Installing selenium..."
    pip3 install selenium google-cloud-storage pymongo
fi

echo "  ✓ Python dependencies OK"

# Check ChromeDriver
if ! command -v chromedriver &> /dev/null; then
    echo "  ⚠ ChromeDriver not found in PATH"
    echo "  Attempting to use system ChromeDriver..."
fi

echo ""
echo "=========================================="
echo "Starting 10 Local Workers"
echo "=========================================="
echo ""

# Create log directory
mkdir -p worker_logs

# Start workers in background
for ((WORKER_ID=LOCAL_START_ID; WORKER_ID<=LOCAL_END_ID; WORKER_ID++)); do
    echo "Starting local worker $WORKER_ID..."
    
    # Export environment variables and run in background
    (
        export WORKER_ID=$WORKER_ID
        export TOTAL_WORKERS=$TOTAL_WORKERS
        export GCS_BUCKET=$BUCKET_NAME
        export MONGODB_URI=$MONGODB_URI
        
        python3 domain_scraper_gcs.py > worker_logs/worker_${WORKER_ID}.log 2>&1
    ) &
    
    WORKER_PID=$!
    echo "  Started worker $WORKER_ID (PID: $WORKER_PID)"
    
    # Small delay between worker starts
    sleep 2
done

echo ""
echo "=========================================="
echo "✓ All 10 Local Workers Started!"
echo "=========================================="
echo ""
echo "Local Workers:"
echo "  Worker IDs: 16-25"
echo "  Total: 10 workers"
echo "  Running in background"
echo "  Logs: worker_logs/worker_*.log"
echo ""
echo "Combined Deployment:"
echo "  Cloud Workers: 16 (IDs 0-15)"
echo "  Local Workers: 10 (IDs 16-25)"
echo "  Total: 26 workers"
echo "  Processing: 331,224 addresses"
echo "  Est. Time: ~13 hours"
echo ""
echo "Monitor all workers:"
echo "  ./monitor_hybrid.sh"
echo ""
echo "Watch local worker logs:"
echo "  tail -f worker_logs/worker_16.log"
echo ""
echo "Check running processes:"
echo "  ps aux | grep domain_scraper_gcs.py"
echo ""
echo "Stop local workers:"
echo "  pkill -f domain_scraper_gcs.py"
echo ""
echo "=========================================="
echo ""
echo "⏳ Workers are now processing..."
echo "Check progress with: ./monitor_hybrid.sh"
echo ""
