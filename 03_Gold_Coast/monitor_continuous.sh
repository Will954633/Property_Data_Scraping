#!/bin/bash

# Continuous monitoring script for macOS (no 'watch' command needed)

echo "Starting continuous progress monitor..."
echo "Press Ctrl+C to stop"
echo ""
sleep 2

while true; do
    cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast
    ./monitor_progress.sh
    echo ""
    echo "Refreshing in 60 seconds... (Press Ctrl+C to stop)"
    sleep 60
done
