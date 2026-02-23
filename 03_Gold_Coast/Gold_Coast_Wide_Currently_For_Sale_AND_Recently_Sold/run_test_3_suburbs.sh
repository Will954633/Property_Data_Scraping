#!/bin/bash
# Test Dynamic Scraping with 3 Small Suburbs
# Last Updated: 31/01/2026, 12:17 pm (Brisbane Time)
#
# PURPOSE: Test dynamic suburb spawning with 3 small suburbs before full run
# USAGE: bash run_test_3_suburbs.sh

echo "================================================================================"
echo "DYNAMIC SUBURB SCRAPING - TEST RUN (3 Suburbs)"
echo "================================================================================"
echo ""
echo "Test Suburbs:"
echo "  1. Bilinga (4225) - Small suburb"
echo "  2. Tugun (4224) - Small suburb"
echo "  3. Elanora (4221) - Medium suburb"
echo ""
echo "This will test:"
echo "  ✓ Dynamic suburb spawning"
echo "  ✓ MongoDB safety with concurrent writes"
echo "  ✓ Process completion detection"
echo "  ✓ Error handling"
echo ""
echo "================================================================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Run parallel scraper with 3 test suburbs
python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Bilinga:4225" \
  "Tugun:4224" \
  "Elanora:4221"

echo ""
echo "================================================================================"
echo "TEST COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Check MongoDB collections: bilinga, tugun, elanora"
echo "  2. Verify document counts match expected"
echo "  3. If successful, proceed to full 52-suburb run"
echo ""
echo "To check results:"
echo "  mongosh"
echo "  use Gold_Coast_Currently_For_Sale"
echo "  db.bilinga.countDocuments({})"
echo "  db.tugun.countDocuments({})"
echo "  db.elanora.countDocuments({})"
echo ""
