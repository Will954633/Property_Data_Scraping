#!/bin/bash
################################################################################
# Monitor 50 Multi-Suburb Workers
# Shows real-time progress across all target suburbs
################################################################################

SCRIPT_NAME="domain_scraper_multi_suburb_mongodb.py"
LOG_DIR="multisuburb_worker_logs"
TARGET_SUBURBS=("surfers_paradise" "southport" "labrador" "palm_beach" "upper_coomera" "pimpama" "broadbeach")

# Function to get MongoDB stats
get_mongo_stats() {
    python3 << 'EOF'
from pymongo import MongoClient
import json

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']

suburbs = ['surfers_paradise', 'southport', 'labrador', 'palm_beach', 'upper_coomera', 'pimpama', 'broadbeach']

stats = {}
total_addresses = 0
total_scraped = 0

for suburb in suburbs:
    coll = db[suburb]
    total = coll.count_documents({})
    scraped = coll.count_documents({'scraped_data': {'$exists': True}})
    stats[suburb] = {'total': total, 'scraped': scraped, 'unscraped': total - scraped}
    total_addresses += total
    total_scraped += scraped

stats['_totals'] = {
    'total': total_addresses,
    'scraped': total_scraped,
    'unscraped': total_addresses - total_scraped
}

print(json.dumps(stats))
EOF
}

# Clear screen and show header
clear
echo "========================================================================"
echo "MULTI-SUBURB WORKER MONITOR - 50 Workers"
echo "========================================================================"
echo "Target: 30% of Gold Coast addresses"
echo "Press Ctrl+C to exit"
echo "========================================================================"
echo ""

# Main monitoring loop
while true; do
    # Count running workers
    RUNNING_WORKERS=$(ps aux | grep "$SCRIPT_NAME" | grep -v grep | wc -l | xargs)
    
    echo "🔄 Status Update - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "────────────────────────────────────────────────────────────────────"
    echo "Running workers: $RUNNING_WORKERS / 50"
    echo ""
    
    # Get MongoDB statistics
    if command -v python3 &> /dev/null; then
        STATS=$(get_mongo_stats 2>/dev/null)
        
        if [ $? -eq 0 ] && [ ! -z "$STATS" ]; then
            echo "MongoDB Progress by Suburb:"
            echo "────────────────────────────────────────────────────────────────────"
            
            for suburb in "${TARGET_SUBURBS[@]}"; do
                TOTAL=$(echo "$STATS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('$suburb', {}).get('total', 0))")
                SCRAPED=$(echo "$STATS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('$suburb', {}).get('scraped', 0))")
                UNSCRAPED=$(echo "$STATS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('$suburb', {}).get('unscraped', 0))")
                
                if [ "$TOTAL" -gt 0 ]; then
                    PERCENT=$(echo "scale=1; $SCRAPED * 100 / $TOTAL" | bc)
                    BAR_LENGTH=$(echo "scale=0; $SCRAPED * 40 / $TOTAL" | bc)
                    BAR=$(printf '█%.0s' $(seq 1 $BAR_LENGTH))
                    SPACES=$(printf ' %.0s' $(seq 1 $((40 - BAR_LENGTH))))
                    
                    printf "  %-20s [%s%s] %5.1f%% (%6d/%6d)\n" "$suburb" "$BAR" "$SPACES" "$PERCENT" "$SCRAPED" "$TOTAL"
                fi
            done
            
            echo "────────────────────────────────────────────────────────────────────"
            
            # Show totals
            TOTAL_ALL=$(echo "$STATS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('_totals', {}).get('total', 0))")
            SCRAPED_ALL=$(echo "$STATS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('_totals', {}).get('scraped', 0))")
            UNSCRAPED_ALL=$(echo "$STATS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('_totals', {}).get('unscraped', 0))")
            
            if [ "$TOTAL_ALL" -gt 0 ]; then
                PERCENT_ALL=$(echo "scale=1; $SCRAPED_ALL * 100 / $TOTAL_ALL" | bc)
                echo "  TOTAL:               $SCRAPED_ALL / $TOTAL_ALL ($PERCENT_ALL%)"
                echo "  Remaining:           $UNSCRAPED_ALL addresses"
                
                # Calculate ETA
                if [ "$SCRAPED_ALL" -gt 0 ] && [ "$RUNNING_WORKERS" -gt 0 ]; then
                    RATE=$(echo "scale=1; $RUNNING_WORKERS * 120" | bc)  # 120 addresses/hour per worker
                    HOURS_LEFT=$(echo "scale=1; $UNSCRAPED_ALL / $RATE" | bc)
                    echo "  Estimated rate:      $RATE addresses/hour"
                    echo "  Estimated time left: $HOURS_LEFT hours"
                fi
            fi
        else
            echo "⚠️  Could not connect to MongoDB"
        fi
    fi
    
    echo ""
    echo "────────────────────────────────────────────────────────────────────"
    
    # Check for recent errors in logs
    if [ -d "$LOG_DIR" ]; then
        RECENT_ERRORS=$(find "$LOG_DIR" -name "*.log" -mmin -5 -exec grep -l "FATAL ERROR\|✗ Error" {} \; 2>/dev/null | wc -l | xargs)
        if [ "$RECENT_ERRORS" -gt 0 ]; then
            echo "⚠️  $RECENT_ERRORS worker(s) reported errors in last 5 minutes"
        fi
    fi
    
    # Show worker activity summary
    if [ -d "$LOG_DIR" ] && [ "$RUNNING_WORKERS" -gt 0 ]; then
        echo ""
        echo "Recent worker activity (last 10 lines per worker):"
        for i in $(seq 0 4); do
            if [ -f "$LOG_DIR/worker_$i.log" ]; then
                LAST_LINE=$(tail -1 "$LOG_DIR/worker_$i.log" 2>/dev/null | grep -o '\[[0-9]*/[0-9]*\]' | head -1)
                if [ ! -z "$LAST_LINE" ]; then
                    echo "  Worker $i: $LAST_LINE"
                fi
            fi
        done
        if [ "$RUNNING_WORKERS" -gt 5 ]; then
            echo "  ... and $((RUNNING_WORKERS - 5)) more workers"
        fi
    fi
    
    echo ""
    echo "────────────────────────────────────────────────────────────────────"
    echo "Commands:"
    echo "  View worker logs:  tail -f $LOG_DIR/worker_N.log"
    echo "  Stop all workers:  pkill -f '$SCRIPT_NAME'"
    echo "  Check database:    mongosh Gold_Coast"
    echo "────────────────────────────────────────────────────────────────────"
    echo ""
    
    # Wait before next update
    sleep 30
    
    # Clear for next iteration
    clear
done
