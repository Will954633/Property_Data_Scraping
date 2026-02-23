#!/bin/bash

cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast

# Stop any existing workers
pkill -f domain_scraper_robina_mongodb.py 2>/dev/null
sleep 2

# Create log directory
mkdir -p robina_worker_logs

echo "Launching 20 Robina workers..."

# Launch workers using conda's python
for i in {0..19}; do
    export WORKER_ID=$i
    export TOTAL_WORKERS=20
    export MONGODB_URI="mongodb://127.0.0.1:27017/"
    
    python domain_scraper_robina_mongodb.py > robina_worker_logs/worker_${i}.log 2>&1 &
    PID=$!
    echo "Started worker $i (PID: $PID)"
    sleep 0.5
done

echo ""
echo "All 20 workers launched!"
echo ""
echo "Check progress:"
echo "  ./monitor_robina_workers.sh"
echo ""
echo "View logs:"
echo "  tail -f robina_worker_logs/worker_0.log"
