#!/bin/bash
################################################################################
# Start 50 Local Multi-Suburb Workers on macOS
# Processes top 7 suburbs (30% of total Gold Coast addresses)
################################################################################

echo "========================================================================"
echo "STARTING 50 MULTI-SUBURB WORKERS"
echo "========================================================================"
echo ""
echo "Target: 30% of Gold Coast addresses (~98,872 addresses)"
echo "Suburbs: surfers_paradise, southport, labrador, palm_beach,"
echo "         upper_coomera, pimpama, broadbeach"
echo ""
echo "Expected completion: ~16-20 hours with 50 workers @ 120/hr each"
echo ""

# Configuration
TOTAL_WORKERS=50
SCRIPT_NAME="domain_scraper_multi_suburb_mongodb.py"
LOG_DIR="multisuburb_worker_logs"
MONGODB_URI="mongodb://127.0.0.1:27017/"

# Create log directory
mkdir -p "$LOG_DIR"

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  WARNING: MongoDB doesn't appear to be running!"
    echo "   Please start MongoDB first:"
    echo "   brew services start mongodb-community"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if scraper script exists
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "❌ Error: $SCRIPT_NAME not found!"
    exit 1
fi

# Check if suburb_analysis.json exists
if [ ! -f "suburb_analysis.json" ]; then
    echo "⚠️  WARNING: suburb_analysis.json not found"
    echo "   Running suburb analysis first..."
    python3 analyze_suburbs.py
    echo ""
fi

echo "Starting $TOTAL_WORKERS workers..."
echo "Logs will be saved to: $LOG_DIR/"
echo ""

# Start all workers
for i in $(seq 0 $((TOTAL_WORKERS - 1))); do
    LOG_FILE="$LOG_DIR/worker_$i.log"
    
    # Export environment variables and run worker in background (unbuffered output)
    WORKER_ID=$i TOTAL_WORKERS=$TOTAL_WORKERS MONGODB_URI="$MONGODB_URI" PYTHONUNBUFFERED=1 \
        python3 -u "$SCRIPT_NAME" > "$LOG_FILE" 2>&1 &
    
    WORKER_PID=$!
    echo "  Worker $i started (PID: $WORKER_PID) → $LOG_FILE"
    
    # Small delay to avoid overwhelming system
    sleep 0.5
done

echo ""
echo "========================================================================"
echo "✓ ALL $TOTAL_WORKERS WORKERS STARTED"
echo "========================================================================"
echo ""
echo "Monitor progress with:"
echo "  ./monitor_multisuburb_workers.sh"
echo ""
echo "View individual worker logs:"
echo "  tail -f $LOG_DIR/worker_0.log"
echo ""
echo "Stop all workers:"
echo "  pkill -f '$SCRIPT_NAME'"
echo ""
echo "Check status:"
echo "  ps aux | grep '$SCRIPT_NAME' | grep -v grep | wc -l"
echo ""
echo "Started at: $(date)"
echo "========================================================================"
