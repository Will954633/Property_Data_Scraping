#!/bin/bash

echo "=========================================="
echo "SOLD PROPERTIES SCRAPER - LAST 6 MONTHS"
echo "=========================================="
echo ""
echo "This script will scrape all sold properties from the last 6 months"
echo "from Domain.com.au for 5 Gold Coast suburbs."
echo ""
echo "Suburbs: Robina, Mudgeeraba, Varsity Lakes, Reedy Creek, Burleigh Waters"
echo ""
echo "Stop conditions (per suburb):"
echo "  • 3 consecutive properties with sale dates >6 months old"
echo "  • 3 consecutive properties already in database"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Stage 1: Extract property URLs (all suburbs)
echo "=========================================="
echo "STAGE 1: Extracting Property URLs"
echo "=========================================="
echo ""
python3 list_page_scraper_sold.py
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: URL extraction failed"
    exit 1
fi
echo ""

# Stage 2: Scrape property details (suburb by suburb)
echo "=========================================="
echo "STAGE 2: Scraping Property Details"
echo "=========================================="
echo ""
for suburb in robina mudgeeraba varsity-lakes reedy-creek burleigh-waters; do
    echo "→ Processing suburb: $suburb"
    python3 property_detail_scraper_sold.py --suburb $suburb
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to scrape $suburb"
        exit 1
    fi
    echo ""
done

# Stage 3: Upload to MongoDB with stop conditions
echo "=========================================="
echo "STAGE 3: Uploading to MongoDB"
echo "=========================================="
echo ""
echo "Collection: sold_last_6_months"
echo "Database: property_data"
echo ""
python3 mongodb_uploader_sold.py
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: MongoDB upload failed"
    exit 1
fi
echo ""

# Stage 4: Summary report
echo "=========================================="
echo "STAGE 4: Final Summary"
echo "=========================================="
echo ""
python3 check_mongodb_status_sold.py
echo ""

echo "=========================================="
echo "SCRAPING COMPLETE"
echo "=========================================="
echo ""
echo "✓ All stages completed successfully"
echo ""
echo "Next steps:"
echo "  • Review upload logs in current directory"
echo "  • Check MongoDB collection: sold_last_6_months"
echo "  • Run again weekly to catch new sales"
echo ""
