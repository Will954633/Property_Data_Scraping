#!/bin/bash

echo "=========================================="
echo "Comprehensive Worker Process Cleanup"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to count processes
count_processes() {
    pgrep -f "$1" 2>/dev/null | wc -l | tr -d ' '
}

# Function to kill processes
kill_processes() {
    local pattern="$1"
    local description="$2"
    
    echo -e "${YELLOW}Searching for: ${description}${NC}"
    
    # First try to find processes
    PIDS=$(pgrep -f "$pattern" 2>/dev/null)
    
    if [ -z "$PIDS" ]; then
        echo -e "  ${GREEN}✓ No processes found${NC}"
        return 0
    fi
    
    # Count processes
    COUNT=$(echo "$PIDS" | wc -l | tr -d ' ')
    echo -e "  ${RED}Found $COUNT process(es)${NC}"
    
    # Display process details
    echo "  Process details:"
    ps -p $PIDS -o pid,ppid,etime,cmd 2>/dev/null | head -10
    
    # Kill processes gracefully first (SIGTERM)
    echo "  Attempting graceful shutdown (SIGTERM)..."
    echo "$PIDS" | xargs kill 2>/dev/null
    
    # Wait a moment
    sleep 2
    
    # Check if any are still running
    REMAINING=$(pgrep -f "$pattern" 2>/dev/null)
    
    if [ ! -z "$REMAINING" ]; then
        echo "  ${YELLOW}Some processes still running, forcing shutdown (SIGKILL)...${NC}"
        echo "$REMAINING" | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    # Final check
    FINAL_CHECK=$(pgrep -f "$pattern" 2>/dev/null)
    if [ -z "$FINAL_CHECK" ]; then
        echo -e "  ${GREEN}✓ All processes stopped successfully${NC}"
        return 0
    else
        echo -e "  ${RED}✗ Some processes could not be stopped${NC}"
        return 1
    fi
}

echo "Step 1: Checking for all domain_scraper related processes"
echo "-----------------------------------------------------------"

# Check for different types of scraper processes
PATTERNS=(
    "domain_scraper_multi_suburb_mongodb.py"
    "domain_scraper_robina_mongodb.py"
    "domain_scraper_gcs.py"
    "domain_scraper_gcs_json.py"
    "domain_scraper.py"
)

TOTAL_INITIAL=0
for pattern in "${PATTERNS[@]}"; do
    COUNT=$(count_processes "$pattern")
    if [ "$COUNT" -gt 0 ]; then
        echo "  - $pattern: $COUNT process(es)"
        TOTAL_INITIAL=$((TOTAL_INITIAL + COUNT))
    fi
done

if [ "$TOTAL_INITIAL" -eq 0 ]; then
    echo -e "${GREEN}✓ No worker processes currently running${NC}"
    echo ""
    echo "Additional checks:"
    echo "-------------------"
else
    echo ""
    echo "Total processes found: $TOTAL_INITIAL"
    echo ""
    
    echo "Step 2: Stopping all worker processes"
    echo "-----------------------------------------------------------"
    
    for pattern in "${PATTERNS[@]}"; do
        kill_processes "$pattern" "$pattern"
        echo ""
    done
fi

# Check for any remaining python processes that might be related
echo "Step 3: Checking for any other potentially related processes"
echo "-----------------------------------------------------------"

# Look for any python processes with 'scraper' in the name
OTHER_SCRAPERS=$(pgrep -f "python.*scraper" 2>/dev/null)
if [ ! -z "$OTHER_SCRAPERS" ]; then
    echo -e "${YELLOW}Found other scraper-related processes:${NC}"
    ps -p $OTHER_SCRAPERS -o pid,cmd 2>/dev/null
    echo ""
    read -p "Do you want to stop these as well? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill_processes "python.*scraper" "Other scraper processes"
    fi
else
    echo -e "${GREEN}✓ No other scraper processes found${NC}"
fi

echo ""
echo "Step 4: Final verification"
echo "-----------------------------------------------------------"

# Final comprehensive check
ALL_PYTHON=$(pgrep -f "python.*domain" 2>/dev/null)
if [ -z "$ALL_PYTHON" ]; then
    echo -e "${GREEN}✓ All domain_scraper processes have been stopped${NC}"
else
    echo -e "${YELLOW}Warning: Some Python processes with 'domain' still running:${NC}"
    ps -p $ALL_PYTHON -o pid,cmd 2>/dev/null
fi

echo ""
echo "Step 5: Checking background jobs in current shell"
echo "-----------------------------------------------------------"

# Check for background jobs
JOBS_COUNT=$(jobs -r 2>/dev/null | wc -l | tr -d ' ')
if [ "$JOBS_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Found $JOBS_COUNT background job(s) in current shell:${NC}"
    jobs -l
    echo ""
    echo "To stop these, run: kill %1 %2 ... or use 'killall' command"
else
    echo -e "${GREEN}✓ No background jobs in current shell${NC}"
fi

echo ""
echo "=========================================="
echo "Cleanup Summary"
echo "=========================================="
echo ""

# Show summary of all process types
echo "Current process status:"
for pattern in "${PATTERNS[@]}"; do
    COUNT=$(count_processes "$pattern")
    if [ "$COUNT" -gt 0 ]; then
        echo -e "  ${RED}✗ $pattern: $COUNT still running${NC}"
    else
        echo -e "  ${GREEN}✓ $pattern: 0 running${NC}"
    fi
done

echo ""
echo "=========================================="
echo ""

if [ "$TOTAL_INITIAL" -eq 0 ]; then
    echo -e "${GREEN}No processes needed to be stopped. System is clean.${NC}"
else
    echo "If processes are still running after this script:"
    echo "  1. Check if they're running in other terminal sessions"
    echo "  2. Try manual kill: kill -9 <PID>"
    echo "  3. Check for processes in other directories"
    echo "  4. Restart your terminal/computer if necessary"
fi

echo ""
