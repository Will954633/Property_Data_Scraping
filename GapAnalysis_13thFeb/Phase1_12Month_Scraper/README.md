# Phase 1: 12-Month Sold Property Scraper
# Last Edit: 13/02/2026, 11:46 AM (Thursday) — Brisbane Time

## Overview

This scraper collects 12 months of sold property data for all 8 target market suburbs and uploads to the `Gold_Coast_Recently_Sold` database (Azure Cosmos DB).

**Goal:** Increase database from 275 properties to 1,000+ properties to support property valuation modeling.

---

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb/Phase1_12Month_Scraper && \
pip3 install --break-system-packages -r requirements.txt
```

### 2. Set Environment Variable

```bash
export COSMOS_CONNECTION_STRING="mongodb://your-cosmos-connection-string"
```

Or create a `.env` file:
```bash
echo 'COSMOS_CONNECTION_STRING="mongodb://your-cosmos-connection-string"' > .env
```

### 3. Run Complete Pipeline

```bash
# Step 1: Scrape listing pages (2-3 hours)
python3 list_page_scraper_12months.py

# Step 2: Scrape property details (4-6 hours)
python3 property_detail_scraper_sold.py --input listing_results_sold/sold_property_urls_12months_*.json

# Step 3: Upload to MongoDB (1-2 hours)
python3 mongodb_uploader_12months.py
```

---

## What's Included

### Core Scripts

1. **`list_page_scraper_12months.py`** - Extracts property URLs from Domain.com.au
   - Scrapes 8 suburbs × 15 pages = 120 pages
   - Expected output: 800-1,500 property URLs
   - Runtime: 2-3 hours

2. **`property_detail_scraper_sold.py`** - Scrapes individual property details
   - Extracts 20+ fields per property
   - Includes sale date, price, features, images, floor plans
   - Runtime: 4-6 hours

3. **`html_parser_sold.py`** - Parses HTML with 4 sale date extraction methods
   - JSON-LD structured data
   - data-testid attributes
   - Text pattern matching
   - Meta tags

4. **`mongodb_uploader_12months.py`** - Uploads to Azure Cosmos DB
   - Target database: `Gold_Coast_Recently_Sold`
   - Suburb-specific collections (e.g., Robina, Mudgeeraba)
   - Intelligent stop conditions (12-month cutoff)
   - Deduplication by address and property_url
   - Runtime: 1-2 hours

### Supporting Files

- **`requirements.txt`** - Python dependencies
- **`README.md`** - This file
- **`.env.example`** - Example environment configuration

---

## Target Suburbs

All 8 target market suburbs from `/Users/projects/Documents/Cline/Rules/Target Market Subrubs.md`:

| Suburb | Annual Sales | Median Price | Expected Properties |
|--------|--------------|--------------|---------------------|
| Robina | 228 | $1,400,000 | 150-200 |
| Mudgeeraba | 144 | $1,300,000 | 100-150 |
| Varsity Lakes | 117 | $1,312,500 | 80-120 |
| Reedy Creek | 87 | $1,630,000 | 60-90 |
| Burleigh Waters | 225 | $1,775,000 | 150-200 |
| Carrara | ~100 | $1,200,000 | 70-100 |
| Merrimac | 59 | $1,063,250 | 40-60 |
| Worongary | 41 | $1,737,500 | 30-50 |

**Total Expected:** 800-1,500 properties

---

## Database Structure

### Target Database
- **Name:** `Gold_Coast_Recently_Sold`
- **Type:** Azure Cosmos DB (MongoDB API)
- **Connection:** Via `COSMOS_CONNECTION_STRING` environment variable

### Collections
One collection per suburb:
- `Robina`
- `Mudgeeraba`
- `Varsity_Lakes`
- `Reedy_Creek`
- `Burleigh_Waters`
- `Carrara`
- `Merrimac`
- `Worongary`

### Document Structure

```json
{
  "address": "123 Main St, Robina QLD 4226",
  "property_url": "https://www.domain.com.au/...",
  "domain_id": "2018123456",
  "suburb": "Robina",
  "postcode": "4226",
  "sale_price": 1400000,
  "sale_date": "2025-06-15",
  "bedrooms": 4,
  "bathrooms": 2,
  "car_spaces": 2,
  "property_type": "House",
  "features": ["Air Conditioning", "Pool", "..."],
  "description": "Full property description...",
  "images": ["https://...", "https://..."],
  "floor_plans": ["https://..."],
  "first_seen": "2026-02-13T11:45:00",
  "last_updated": "2026-02-13T11:45:00",
  "source": "selenium_sold_scraper_12months",
  "scraper_version": "12month_v1.0"
}
```

---

## Intelligent Stop Conditions

The scraper uses two stop conditions to avoid scraping too far back:

### Stop Condition A: 12-Month Cutoff
- Stops if 5 consecutive properties sold >12 months ago
- Ensures we only collect recent data
- Saves time by not scraping old listings

### Stop Condition B: Duplicate Detection
- Stops if 5 consecutive properties already in database
- Prevents re-scraping existing data
- Enables efficient incremental updates

---

## Step-by-Step Guide

### Step 1: List Page Scraping

```bash
python3 list_page_scraper_12months.py
```

**What it does:**
- Opens Chrome browser via Selenium
- Navigates to Domain.com.au sold listings for each suburb
- Scrapes 15 pages per suburb (12 months of data)
- Extracts property URLs from each page
- Saves URLs to JSON files

**Output files:**
- `listing_results_sold/sold_property_urls_12months_TIMESTAMP.json` - All URLs
- `listing_results_sold/sold_urls_SUBURB_12months_TIMESTAMP.json` - Per-suburb URLs
- `listing_results_sold/SUBURB_page_N_raw.html` - Raw HTML for debugging

**Expected results:**
- 800-1,500 unique property URLs
- 2-3 hours runtime
- ~120 pages scraped

### Step 2: Property Detail Scraping

```bash
python3 property_detail_scraper_sold.py --input listing_results_sold/sold_property_urls_12months_*.json
```

**What it does:**
- Loads property URLs from Step 1
- Visits each property page
- Extracts 20+ data fields
- Parses sale date using 4 methods
- Downloads images and floor plans (optional)
- Saves to JSON files

**Output files:**
- `property_data/sold_scrape_SUBURB_TIMESTAMP.json` - Property data per suburb
- `property_data/PROPERTYID_raw.html` - Raw HTML for debugging

**Expected results:**
- 800-1,500 properties with complete data
- 95%+ sale date extraction success
- 4-6 hours runtime

### Step 3: MongoDB Upload

```bash
python3 mongodb_uploader_12months.py
```

**What it does:**
- Connects to Azure Cosmos DB
- Loads scraped data from Step 2
- Uploads to suburb-specific collections
- Applies 12-month cutoff logic
- Deduplicates by address and URL
- Creates indexes for performance

**Output files:**
- `upload_log_12months_TIMESTAMP.json` - Upload summary

**Expected results:**
- 800-1,500 properties uploaded
- 0 duplicates
- 1-2 hours runtime

---

## Monitoring Progress

### Real-time Monitoring

```bash
# Watch list scraper progress
tail -f logs/list_scraper.log

# Watch property scraper progress
tail -f logs/property_scraper.log

# Watch upload progress
tail -f logs/upload.log
```

### Check Database Status

```bash
python3 -c "
from mongodb_uploader_12months import SoldPropertyUploader
uploader = SoldPropertyUploader()
uploader.print_summary()
uploader.close()
"
```

---

## Troubleshooting

### Issue: ChromeDriver not found

**Solution:**
```bash
pip3 install --break-system-packages webdriver-manager
```

The scraper will auto-download the correct ChromeDriver version.

### Issue: MongoDB connection failed

**Solution:**
1. Check `COSMOS_CONNECTION_STRING` is set correctly
2. Verify connection string format: `mongodb://...`
3. Test connection:
```bash
python3 -c "
from pymongo import MongoClient
import os
client = MongoClient(os.getenv('COSMOS_CONNECTION_STRING'))
print(client.server_info())
"
```

### Issue: No properties found

**Solution:**
1. Check Domain.com.au is accessible
2. Verify suburb URLs are correct
3. Check for CAPTCHA or rate limiting
4. Try reducing scraping speed (increase delays)

### Issue: Sale date extraction failing

**Solution:**
The scraper uses 4 extraction methods. Check logs for which method is failing:
```bash
grep "sale_date" property_data/sold_scrape_*.json
```

---

## Performance Optimization

### Speed Up Scraping

1. **Reduce delays** (risk: rate limiting)
   - Edit `list_page_scraper_12months.py`
   - Change `time.sleep(3)` to `time.sleep(1)`

2. **Skip image downloads** (saves bandwidth)
   - Edit `property_detail_scraper_sold.py`
   - Set `download_images=False`

3. **Parallel scraping** (advanced)
   - Run multiple scrapers for different suburbs
   - Requires separate Chrome instances

### Reduce Database Load

1. **Batch uploads** (already implemented)
   - Uploads 50 properties at a time
   - Reduces connection overhead

2. **Index optimization** (already implemented)
   - Indexes on address, property_url, sale_date
   - Speeds up deduplication queries

---

## Expected Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1A | List page scraping | 2-3 hours |
| 1B | Property detail scraping | 4-6 hours |
| 1C | MongoDB upload | 1-2 hours |
| **Total** | **Complete pipeline** | **8-12 hours** |

**Recommendation:** Run overnight or during off-peak hours.

---

## Success Criteria

### Minimum Viable Success (MVP)
- ✅ 800+ properties collected
- ✅ All 8 suburbs represented
- ✅ 90%+ have sale_price and sale_date
- ✅ 50%+ have lot_size or floor_area
- ✅ 0 duplicates in database

### Ideal Success
- ✅ 1,200+ properties collected
- ✅ 95%+ have sale_price and sale_date
- ✅ 70%+ have lot_size
- ✅ 50%+ have floor_area
- ✅ All properties within 12 months

---

## Next Steps After Phase 1

Once Phase 1 is complete, proceed to:

1. **Phase 2: Structural Data Enhancement** (Week 1-2)
   - Extract lot_size, floor_area, building_age from descriptions
   - Use QLD Spatial API for lot_size validation
   - Achieve 95%+ coverage

2. **Phase 3: Calculated Fields** (Week 2)
   - Calculate days_on_market
   - Parse sale_method from descriptions
   - Add price per sqm metrics

3. **Phase 4: Location Intelligence** (Week 2-3)
   - Add proximity to amenities (Google Places API)
   - Add school zone data
   - Add beach distance

4. **Phase 5: AI Enhancement** (Week 3-4)
   - Extend Ollama photo analysis to sold properties
   - Extract building condition
   - Score outdoor entertainment areas

---

## Related Documentation

- **Implementation Plan:** `../PHASE1_IMPLEMENTATION_PLAN.md`
- **Gap Analysis Report:** `../GAP_ANALYSIS_REPORT.md`
- **Target Market Suburbs:** `/Users/projects/Documents/Cline/Rules/Target Market Subrubs.md`
- **Existing 6-Month Scraper:** `../../02_Domain_Scaping/Sold_In_Last_6_Months/`

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs in `logs/` directory
3. Check error files in `property_data/errors/`
4. Refer to implementation plan for detailed guidance

---

*Created: 13/02/2026, 11:46 AM Brisbane Time*  
*Part of Gap Analysis Phase 1 Implementation*
