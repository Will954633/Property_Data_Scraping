#!/bin/bash
# Check Test Progress
# Last Edit: 13/02/2026, 11:56 AM (Thursday) — Brisbane Time

echo "================================"
echo "TEST RUN PROGRESS CHECK"
echo "================================"
echo ""

# Check if test_output directory has files
echo "📁 Output Files:"
if [ -d "test_output" ]; then
    ls -lh test_output/ 2>/dev/null || echo "  No files yet"
else
    echo "  test_output/ directory not created yet"
fi

echo ""
echo "📁 Listing Results:"
if [ -d "listing_results_sold" ]; then
    ls -lh listing_results_sold/*.html 2>/dev/null | wc -l | xargs echo "  HTML files:"
    ls -lh listing_results_sold/*.json 2>/dev/null | wc -l | xargs echo "  JSON files:"
else
    echo "  listing_results_sold/ directory not created yet"
fi

echo ""
echo "🔍 Process Status:"
ps aux | grep "test_run_small.py" | grep -v grep || echo "  Process not running (may have completed)"

echo ""
echo "📊 Latest Log Output:"
if [ -f "/var/folders/t6/rnm9m1ds6qxg8t7224_j12j80000gn/T/cline/background-1770947777937-27010hc.log" ]; then
    tail -10 /var/folders/t6/rnm9m1ds6qxg8t7224_j12j80000gn/T/cline/background-1770947777937-27010hc.log
else
    echo "  Log file not found"
fi

echo ""
echo "================================"
