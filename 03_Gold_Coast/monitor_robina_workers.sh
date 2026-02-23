#!/bin/bash

# Monitor Robina Workers Script
# Displays real-time progress of 20 local workers processing Robina addresses

MONGODB_URI="mongodb://127.0.0.1:27017/"

clear
echo "========================================================================"
echo "ROBINA PRIORITY WORKERS - MONITORING DASHBOARD"
echo "========================================================================"
echo ""

# Function to get scraped count from MongoDB
get_scraped_count() {
    python3 -c "
from pymongo import MongoClient
client = MongoClient('$MONGODB_URI')
db = client['Gold_Coast']
collection = db['robina']
count = collection.count_documents({'scraped_data': {'\$exists': True}})
print(count)
" 2>/dev/null
}

# Function to get total count
get_total_count() {
    python3 -c "
from pymongo import MongoClient
client = MongoClient('$MONGODB_URI')
db = client['Gold_Coast']
collection = db['robina']
count = collection.count_documents({})
print(count)
" 2>/dev/null
}

# Check if MongoDB is accessible
if ! python3 -c "from pymongo import MongoClient; MongoClient('$MONGODB_URI', serverSelectionTimeoutMS=2000).admin.command('ping')" 2>/dev/null; then
    echo "✗ MongoDB connection failed"
    echo "  Please ensure MongoDB is running on localhost:27017"
    exit 1
fi

# Get counts
TOTAL=$(get_total_count)
SCRAPED=$(get_scraped_count)
REMAINING=$((TOTAL - SCRAPED))
PERCENT=$(python3 -c "print(f'{($SCRAPED/$TOTAL*100):.2f}' if $TOTAL > 0 else '0.00')")

echo "Database Status:"
echo "  Database: Gold_Coast"
echo "  Collection: robina"
echo ""
echo "Progress:"
echo "  Total addresses: $TOTAL"
echo "  Scraped:         $SCRAPED ($PERCENT%)"
echo "  Remaining:       $REMAINING"
echo ""

# Check running workers
WORKER_COUNT=$(ps aux | grep -c "[d]omain_scraper_robina_mongodb.py")
echo "Workers:"
echo "  Running workers: $WORKER_COUNT / 20"
echo ""

# Show recent worker activity
if [ -d "robina_worker_logs" ]; then
    echo "========================================================================"
    echo "Recent Worker Activity (last 5 lines per worker):"
    echo "========================================================================"
    echo ""
    
    for i in {0..19}; do
        LOG_FILE="robina_worker_logs/worker_${i}.log"
        if [ -f "$LOG_FILE" ]; then
            echo "--- Worker $i ---"
            tail -n 5 "$LOG_FILE" 2>/dev/null | grep -v "^$" || echo "  (No recent activity)"
            echo ""
        fi
    done
else
    echo "⚠ Log directory 'robina_worker_logs' not found"
fi

echo "========================================================================"
echo "Commands:"
echo "========================================================================"
echo ""
echo "Watch live updates (this script):"
echo "  ./monitor_robina_workers.sh"
echo ""
echo "Watch all worker logs in real-time:"
echo "  tail -f robina_worker_logs/worker_*.log"
echo ""
echo "Watch specific worker:"
echo "  tail -f robina_worker_logs/worker_0.log"
echo ""
echo "Check MongoDB directly:"
echo "  mongosh --eval \"db.getSiblingDB('Gold_Coast').robina.countDocuments({scraped_data: {\\\$exists: true}})\""
echo ""
echo "Stop all workers:"
echo "  pkill -f domain_scraper_robina_mongodb.py"
echo ""
echo "Restart workers:"
echo "  ./start_20_robina_workers.sh"
echo ""
echo "========================================================================"
