#!/bin/bash
# Complete Workflow: Clear Collections and Scrape Robina + Varsity Lakes
# Last Updated: 31/01/2026, 11:05 am (Brisbane Time)
#
# PURPOSE:
# 1. Clear existing MongoDB collections for Robina and Varsity Lakes
# 2. Run parallel scraping for both suburbs simultaneously
# 3. Display final results
#
# USAGE:
# bash run_robina_varsity_lakes_scrape.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "================================================================================"
echo "ROBINA + VARSITY LAKES COMPLETE SCRAPING WORKFLOW"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Clear existing MongoDB collections (robina, varsity_lakes)"
echo "  2. Run parallel scraping for both suburbs"
echo "  3. Display final results"
echo ""
echo "Database: Gold_Coast_Currently_For_Sale"
echo "Collections: robina, varsity_lakes"
echo ""
echo "================================================================================"
echo ""

# Step 1: Clear collections
echo -e "${BLUE}STEP 1: Clearing MongoDB Collections${NC}"
echo "================================================================================"
echo ""

cd "$SCRIPT_DIR" && python3 clear_collections.py --suburbs robina varsity_lakes --no-confirm

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to clear collections${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Collections cleared successfully${NC}"
echo ""

# Wait a moment
sleep 2

# Step 2: Run parallel scraping
echo ""
echo -e "${BLUE}STEP 2: Running Parallel Scraping${NC}"
echo "================================================================================"
echo ""
echo "Starting parallel scraping processes..."
echo "  - Robina (4226)"
echo "  - Varsity Lakes (4227)"
echo ""
echo "This will take some time. Progress will be displayed below."
echo ""

cd "$SCRIPT_DIR" && python3 run_parallel_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Scraping failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Scraping completed successfully${NC}"
echo ""

# Step 3: Final summary
echo ""
echo "================================================================================"
echo -e "${GREEN}WORKFLOW COMPLETE${NC}"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Verify data in MongoDB:"
echo "     mongosh"
echo "     use Gold_Coast_Currently_For_Sale"
echo "     db.robina.countDocuments({})"
echo "     db.varsity_lakes.countDocuments({})"
echo ""
echo "  2. Check a sample document:"
echo "     db.robina.findOne()"
echo ""
echo "  3. Run enrichment (if needed):"
echo "     cd ../../01.1_Floor_Plan_Data"
echo "     python3 run_production.py"
echo ""
echo "================================================================================"
echo ""
