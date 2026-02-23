#!/bin/bash

echo "================================================================="
echo "COMPREHENSIVE CLEANUP: Workers + Orphaned Chrome Processes"
echo "================================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "ISSUE IDENTIFIED:"
echo "The domain_scraper_multi_suburb_mongodb.py uses Selenium with Chrome."
echo "Even after Python workers stop, Chrome processes can remain orphaned."
echo ""
echo "================================================================="
echo ""

# Step 1: Stop Python worker processes
echo "Step 1: Stopping Python domain_scraper processes"
echo "-----------------------------------------------------------------"

PYTHON_WORKERS=$(pgrep -f "domain_scraper.*mongodb\.py" 2>/dev/null)
if [ -z "$PYTHON_WORKERS" ]; then
    echo -e "${GREEN}✓ No Python worker processes found${NC}"
else
    echo -e "${YELLOW}Found Python workers, stopping...${NC}"
    echo "$PYTHON_WORKERS" | xargs kill -9 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓ Python workers stopped${NC}"
fi

echo ""

# Step 2: Stop orphaned headless Chrome processes
echo "Step 2: Stopping orphaned headless Chrome processes"
echo "-----------------------------------------------------------------"

CHROME_COUNT=$(ps aux | grep -E "Chrome.*headless|chromedriver" | grep -v grep | wc -l | tr -d ' ')
echo "Found $CHROME_COUNT headless Chrome processes"

if [ "$CHROME_COUNT" -gt 0 ]; then
    echo ""
    echo "Orphaned Chrome processes (first 10):"
    ps aux | grep -E "Chrome.*headless" | grep -v grep | head -10 | awk '{print "  PID: " $2 " | CPU: " $3"% | " $11}'
    echo ""
    
    # Kill Chrome Helper processes
    echo "Killing Chrome Helper processes..."
    pkill -f "Chrome Helper.*headless" 2>/dev/null
    sleep 1
    
    # Kill main Chrome processes
    echo "Killing main Chrome processes..."
    pkill -f "Google Chrome.*headless" 2>/dev/null
    sleep 1
    
    # Kill chromedriver
    echo "Killing chromedriver processes..."
    pkill -f "chromedriver" 2>/dev/null
    sleep 1
    
    # Force kill any remaining
    REMAINING=$(ps aux | grep -E "Chrome.*headless|chromedriver" | grep -v grep | awk '{print $2}')
    if [ ! -z "$REMAINING" ]; then
        echo "Force killing remaining processes..."
        echo "$REMAINING" | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    echo -e "${GREEN}✓ Chrome cleanup complete${NC}"
else
    echo -e "${GREEN}✓ No orphaned Chrome processes found${NC}"
fi

echo ""

# Step 3: Verify cleanup
echo "Step 3: Verification"
echo "-----------------------------------------------------------------"

PYTHON_CHECK=$(pgrep -f "domain_scraper" 2>/dev/null | wc -l | tr -d ' ')
CHROME_CHECK=$(ps aux | grep -E "Chrome.*headless" | grep -v grep | wc -l | tr -d ' ')

echo "Python workers remaining: $PYTHON_CHECK"
echo "Chrome processes remaining: $CHROME_CHECK"

echo ""

if [ "$PYTHON_CHECK" -eq 0 ] && [ "$CHROME_CHECK" -eq 0 ]; then
    echo -e "${GREEN}✓✓✓ SUCCESS! All workers and Chrome processes stopped!${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Some processes may still be running${NC}"
    if [ "$PYTHON_CHECK" -gt 0 ]; then
        echo "  Python workers: $PYTHON_CHECK"
        pgrep -f "domain_scraper" -l
    fi
    if [ "$CHROME_CHECK" -gt 0 ]; then
        echo "  Chrome processes: $CHROME_CHECK"
        ps aux | grep -E "Chrome.*headless" | grep -v grep | head -5
    fi
fi

echo ""
echo "================================================================="
echo "Cleanup Complete"
echo "================================================================="
echo ""
echo "To verify CPU usage has dropped:"
echo "  top -l 1 | grep 'CPU usage'"
echo ""
echo "To check for any remaining processes:"
echo "  ./diagnose_cpu_usage.sh"
echo ""
