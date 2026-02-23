#!/bin/bash
set -e

echo "=========================================="
echo "Starting 50 Local MongoDB Workers"
echo "=========================================="

# Configuration
TOTAL_WORKERS=50
MONGODB_URI=${MONGODB_URI:-"mongodb://127.0.0.1:27017/"}
SCRIPT="domain_scraper_multi_suburb_mongodb.py"

# Create timestamped log directory
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="./local_worker_logs_${TIMESTAMP}"

echo ""
echo "Configuration:"
echo "  Total Workers:   $TOTAL_WORKERS"
echo "  MongoDB URI:     ${MONGODB_URI:0:40}..."
echo "  Script:          $SCRIPT"
echo "  Log Directory:   $LOG_DIR"
echo ""

# Check if script exists
if [ ! -f "$SCRIPT" ]; then
    echo "✗ Error: Script not found: $SCRIPT"
    exit 1
fi

# Check MongoDB connection
echo "Testing MongoDB connection..."
python3 -c "
from pymongo import MongoClient
try:
    client = MongoClient('$MONGODB_URI', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ MongoDB connection OK')
except Exception as e:
    print(f'✗ MongoDB connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Create log directory
mkdir -p "$LOG_DIR"

echo ""
echo "Starting $TOTAL_WORKERS workers..."
echo ""

# Start workers in background
for ((WORKER_ID=0; WORKER_ID<TOTAL_WORKERS; WORKER_ID++)); do
    LOG_FILE="$LOG_DIR/worker_${WORKER_ID}.log"
    
    # Export environment variables and run worker in background with UNBUFFERED output
    WORKER_ID=$WORKER_ID TOTAL_WORKERS=$TOTAL_WORKERS MONGODB_URI="$MONGODB_URI" \
        python3 -u "$SCRIPT" > "$LOG_FILE" 2>&1 &
    
    WORKER_PID=$!
    echo "  Worker $WORKER_ID started (PID: $WORKER_PID) -> $LOG_FILE"
    
    # Small delay to avoid overwhelming system
    sleep 0.5
done

echo ""
echo "=========================================="
echo "✓ All 50 Workers Started"
echo "=========================================="
echo ""
echo "Monitor progress:"
echo "  ./monitor_local_workers.sh"
echo ""
echo "View specific worker log:"
echo "  tail -f $LOG_DIR/worker_0.log"
echo ""
echo "Stop all workers:"
echo "  pkill -f 'python3.*domain_scraper_multi_suburb_mongodb.py'"
echo ""
