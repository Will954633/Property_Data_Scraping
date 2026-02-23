#!/bin/bash

echo "=========================================="
echo "Local Workers Monitor"
echo "=========================================="

LOG_DIR="./local_worker_logs"

if [ ! -d "$LOG_DIR" ]; then
    echo "✗ Log directory not found: $LOG_DIR"
    echo "Workers may not be running."
    exit 1
fi

# Count running workers
RUNNING_WORKERS=$(pgrep -f "python3.*domain_scraper_multi_suburb_mongodb.py" | wc -l | tr -d ' ')

echo ""
echo "Status: $RUNNING_WORKERS workers running"
echo ""

# MongoDB stats
echo "MongoDB Statistics:"
python3 << 'PYTHON_SCRIPT'
from pymongo import MongoClient
import os

mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
db = client['Gold_Coast']

collections = [c for c in db.list_collection_names() if c != 'system.indexes']

total_docs = 0
total_scraped = 0

for coll_name in collections:
    count = db[coll_name].count_documents({})
    scraped = db[coll_name].count_documents({'scraped_data': {'$exists': True}})
    total_docs += count
    total_scraped += scraped

print(f"  Total addresses:    {total_docs:,}")
print(f"  Scraped:            {total_scraped:,} ({total_scraped/total_docs*100:.1f}%)")
print(f"  Remaining:          {total_docs - total_scraped:,} ({(total_docs - total_scraped)/total_docs*100:.1f}%)")
print(f"  Collections:        {len(collections)}")

client.close()
PYTHON_SCRIPT

echo ""
echo "Recent Worker Activity (last 10 lines from each worker):"
echo "─────────────────────────────────────────────────────────"

for i in {0..9}; do
    LOG_FILE="$LOG_DIR/worker_${i}.log"
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "Worker $i:"
        tail -n 3 "$LOG_FILE" 2>/dev/null | grep -E "(Processing|Progress|Worker.*COMPLETE)" || echo "  (no recent activity)"
    fi
done

echo ""
echo "─────────────────────────────────────────────────────────"
echo ""
echo "Commands:"
echo "  View worker 0 log:    tail -f $LOG_DIR/worker_0.log"
echo "  Stop all workers:     pkill -f 'python3.*domain_scraper_multi_suburb_mongodb.py'"
echo "  Re-run monitor:       ./monitor_local_workers.sh"
echo "  Analyze status:       python3 analyze_completion_status.py"
echo ""
