#!/bin/bash
# Monitor Scraping Progress
# Last Updated: 31/01/2026, 1:54 pm (Brisbane Time)
#
# PURPOSE: Monitor MongoDB collection count during scraping
# USAGE: bash monitor_progress.sh

echo "================================================================================"
echo "MONITORING SCRAPING PROGRESS"
echo "================================================================================"
echo ""
echo "This will check MongoDB every 60 seconds"
echo "Press Ctrl+C to stop monitoring"
echo ""
echo "================================================================================"
echo ""

while true; do
    # Get current time
    TIMESTAMP=$(date "+%I:%M:%S %p")
    
    # Get collection count
    COUNT=$(mongosh --quiet --eval "use Gold_Coast_Currently_For_Sale; db.getCollectionNames().length" 2>/dev/null)
    
    # Get total documents across all collections
    TOTAL=$(mongosh --quiet --eval "use Gold_Coast_Currently_For_Sale; var total = 0; db.getCollectionNames().forEach(function(name) { total += db[name].countDocuments({}); }); total;" 2>/dev/null)
    
    # Display progress
    echo "[$TIMESTAMP] Collections: $COUNT/52 | Total Properties: $TOTAL"
    
    # Check if complete
    if [ "$COUNT" = "52" ]; then
        echo ""
        echo "================================================================================"
        echo "✅ ALL 52 SUBURBS COMPLETE!"
        echo "================================================================================"
        echo ""
        echo "Final Statistics:"
        echo "  Collections: $COUNT"
        echo "  Total Properties: $TOTAL"
        echo ""
        break
    fi
    
    # Wait 60 seconds
    sleep 60
done
