#!/bin/bash
# Test Parallel Property Scraping with 3 Small Suburbs
# Last Updated: 31/01/2026, 12:51 pm (Brisbane Time)
#
# PURPOSE: Test BOTH optimizations - dynamic suburb spawning + parallel property scraping
# USAGE: bash run_test_3_suburbs_parallel.sh

echo "================================================================================"
echo "PARALLEL PROPERTY SCRAPING TEST - 3 Suburbs"
echo "================================================================================"
echo ""
echo "Test Suburbs:"
echo "  1. Bilinga (4225) - Small suburb"
echo "  2. Tugun (4224) - Small suburb"
echo "  3. Elanora (4221) - Medium suburb"
echo ""
echo "Optimizations:"
echo "  ✓ Dynamic suburb spawning (3 suburbs in parallel)"
echo "  ✓ Parallel property scraping (3 properties at once per suburb)"
echo ""
echo "Expected Performance:"
echo "  Phase 1 (no parallel properties): ~16 minutes"
echo "  Phase 2 (with parallel properties): ~5-8 minutes (3× faster)"
echo ""
echo "This will test:"
echo "  ✓ Thread-safe MongoDB writes"
echo "  ✓ Multiple WebDriver instances"
echo "  ✓ Concurrent property scraping"
echo "  ✓ No duplicate entries (unique index protection)"
echo ""
echo "================================================================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Run parallel scraper with 3 test suburbs AND parallel properties
python3 run_parallel_suburb_scrape.py \
  --suburbs \
  "Bilinga:4225" \
  "Tugun:4224" \
  "Elanora:4221" \
  --parallel-properties 3

echo ""
echo "================================================================================"
echo "TEST COMPLETE"
echo "================================================================================"
echo ""
echo "Performance Comparison:"
echo "  Phase 1 (sequential properties): ~16 minutes"
echo "  Phase 2 (parallel properties):   [check actual time above]"
echo ""
echo "Next steps:"
echo "  1. Compare execution time (should be ~3× faster)"
echo "  2. Check MongoDB collections: bilinga, tugun, elanora"
echo "  3. Verify document counts match Phase 1 (76 total)"
echo "  4. Spot-check for duplicates (should be none)"
echo ""
echo "To check results:"
echo "  mongosh"
echo "  use Gold_Coast_Currently_For_Sale"
echo "  db.bilinga.countDocuments({})  // Should be 27"
echo "  db.tugun.countDocuments({})    // Should be 21"
echo "  db.elanora.countDocuments({})  // Should be 28"
echo "  // Check for duplicates:"
echo "  db.bilinga.aggregate([{\$group: {_id: '\$listing_url', count: {\$sum: 1}}}, {\$match: {count: {\$gt: 1}}}])"
echo ""
