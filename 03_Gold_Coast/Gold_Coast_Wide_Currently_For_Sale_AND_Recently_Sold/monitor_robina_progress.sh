#!/bin/bash
# Monitor Robina scraping progress
# Last Updated: 31/01/2026, 9:31 am (Brisbane Time)

echo "Monitoring Robina Scraping Progress..."
echo "========================================"
echo ""

while true; do
    clear
    echo "Robina Scraping Progress Monitor"
    echo "================================="
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Count documents in MongoDB
    COUNT=$(mongosh mongodb://127.0.0.1:27017/Gold_Coast_Currently_For_Sale --quiet --eval "db.robina.countDocuments({})")
    
    echo "Properties scraped: $COUNT / 47"
    echo "Progress: $(echo "scale=1; $COUNT * 100 / 47" | bc)%"
    echo ""
    
    # Check if complete
    if [ "$COUNT" -eq 47 ]; then
        echo "✅ COMPLETE! All 47 properties scraped."
        break
    fi
    
    echo "Refreshing in 10 seconds... (Ctrl+C to stop monitoring)"
    sleep 10
done
