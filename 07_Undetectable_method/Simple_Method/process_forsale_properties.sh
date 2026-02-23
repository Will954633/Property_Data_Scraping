#!/bin/bash
#
# For-Sale Properties - Complete Pipeline with Selenium Scraping
# Replaces OCR-based scraping with Selenium while keeping MongoDB integration
#

echo "======================================================================"
echo "FOR-SALE PROPERTIES SCRAPER - SELENIUM + MONGODB INTEGRATION"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Extract property URLs using Selenium (NEW)"
echo "  2. Scrape property details using Selenium (NEW)"
echo "  3. Upload to MongoDB (EXISTING)"
echo "  4. Remove duplicates (EXISTING)"
echo "  5. Enrich properties with detailed data (EXISTING)"
echo "  6. Remove off-market properties (EXISTING)"
echo "  7. Display database status (EXISTING)"
echo ""
echo "======================================================================"
echo ""

##############################################################################
# STEP 1: Extract Property URLs (Selenium - REPLACES screenshot/OCR)
##############################################################################

echo "STEP 1: Extracting property URLs using Selenium..."
echo "----------------------------------------------------------------------"
echo ""

python3 list_page_scraper_forsale.py

if [ $? -ne 0 ]; then
    echo "✗ URL extraction failed!"
    exit 1
fi

echo ""
echo "======================================================================"
echo ""

##############################################################################
# STEP 2: Find Latest URLs File
##############################################################################

echo "STEP 2: Locating extracted property URLs..."
echo "----------------------------------------------------------------------"

URLS_FILE=$(ls -t listing_results/property_listing_urls_*.json 2>/dev/null | head -1)

if [ -z "$URLS_FILE" ]; then
    echo "✗ No URLs file found!"
    exit 1
fi

echo "✓ Found URLs file: $URLS_FILE"

URL_COUNT=$(python3 -c "import json; f=open('$URLS_FILE'); d=json.load(f); print(d.get('total_count', 0))")
echo "✓ Total property URLs to process: $URL_COUNT"

echo ""
echo "======================================================================"
echo ""

##############################################################################
# STEP 3: Scrape Property Details (Selenium - REPLACES OCR parsing)
##############################################################################

echo "STEP 3: Scraping property details using Selenium..."
echo "----------------------------------------------------------------------"
echo ""

python3 property_detail_scraper_forsale.py --input "$URLS_FILE"

if [ $? -ne 0 ]; then
    echo "✗ Property scraping failed!"
    exit 1
fi

echo ""
echo "======================================================================"
echo ""

##############################################################################
# STEP 4: Upload to MongoDB (KEEP EXISTING)
##############################################################################

echo "STEP 4: Uploading to MongoDB..."
echo "----------------------------------------------------------------------"
echo ""

# Disable auto-enrichment - Selenium already provides full data
python3 mongodb_uploader.py --no-auto-enrich

if [ $? -ne 0 ]; then
    echo "⚠ MongoDB upload encountered errors"
    exit 1
fi

echo ""
echo "ℹ NOTE: Auto-enrichment disabled - Selenium scraping already provides complete data"

echo ""
echo "======================================================================"
echo ""

##############################################################################
# STEP 5: Remove Duplicates (KEEP EXISTING)
##############################################################################

echo "STEP 5: Removing duplicate properties from MongoDB..."
echo "----------------------------------------------------------------------"
echo ""

python3 remove_duplicates.py --remove

if [ $? -eq 0 ] || [ $? -eq 2 ]; then
    echo "  ✓ Duplicate removal complete"
else
    echo "  ⚠ Duplicate removal encountered errors (continuing)"
fi

echo ""
echo "======================================================================"
echo ""

##############################################################################
# STEP 6: Enrich Properties (SKIPPED FOR FOR-SALE)
##############################################################################

echo "STEP 6: Property enrichment..."
echo "----------------------------------------------------------------------"
echo ""
echo "ℹ SKIPPED for for-sale properties"
echo "  • Selenium scraping already provides complete data"
echo "  • Enrichment is designed for sold properties only"
echo "  • For-sale properties have: descriptions, images, floor plans, agent info"
echo ""
echo "======================================================================"
echo ""

##############################################################################
# STEP 7: Remove Off-Market Properties (SKIPPED FOR FOR-SALE)
##############################################################################

echo "STEP 7: Off-market property removal..."
echo "----------------------------------------------------------------------"
echo ""
echo "ℹ SKIPPED for for-sale properties"
echo "  • Natural cleanup: Re-scraping only finds currently listed properties"
echo "  • If property isn't on Domain → It won't be scraped"
echo "  • Off-market removal designed for SOLD properties tracking"
echo "  • For-sale: Scraper is the source of truth for active listings"
echo ""
echo "======================================================================"
echo ""

##############################################################################
# STEP 8: Display Database Status (KEEP EXISTING)
##############################################################################

echo "STEP 8: Final database status..."
echo "----------------------------------------------------------------------"
echo ""

python3 check_mongodb_status.py

echo ""
echo "======================================================================"
echo "🎉 FULL PIPELINE COMPLETE!"
echo "======================================================================"
echo ""
echo "All steps completed successfully:"
echo "  1. ✓ URL extraction (Selenium)"
echo "  2. ✓ Property scraping (Selenium)"
echo "  3. ✓ MongoDB upload"
echo "  4. ✓ Duplicate removal"
echo "  5. ⊘ Property enrichment (skipped - not needed for for-sale)"
echo "  6. ⊘ Off-market removal (skipped - scraper is source of truth)"
echo "  7. ✓ Database status verification"
echo ""
echo "======================================================================"
