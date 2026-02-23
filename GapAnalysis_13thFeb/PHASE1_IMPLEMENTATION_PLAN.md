# Phase 1 Implementation Plan - 12 Months Sold Data Collection
# Last Edit: 13/02/2026, 11:38 AM (Thursday) — Brisbane Time
#
# Description: Complete implementation plan for collecting 12 months of sold property data
# for all 8 target market suburbs to address the critical data volume gap identified in the
# gap analysis report.
#
# Edit History:
# - 13/02/2026 11:38 AM: Initial creation based on gap analysis requirements

---

## Executive Summary

**Objective:** Collect 12 months of historical sold property data for all 8 target market suburbs to increase database from 275 properties to 1,000+ properties.

**Target Database:** `Gold_Coast_Recently_Sold` (Azure Cosmos DB)

**Expected Outcome:** 800-1,500 sold properties with comprehensive data fields

**Timeline:** 2-3 days

**Estimated Cost:** $5-10 (compute time, no API costs)

---

## Current State Analysis

### Existing Infrastructure ✅

We have a **production-ready** sold property scraper at:
```
/Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold_In_Last_6_Months/
```

**Key Components:**
1. ✅ `list_page_scraper_sold.py` - Extracts property URLs from listing pages
2. ✅ `property_detail_scraper_sold.py` - Scrapes individual property details
3. ✅ `html_parser_sold.py` - Parses HTML with 4 sale date extraction methods
4. ✅ `mongodb_uploader_sold.py` - Uploads to MongoDB with deduplication
5. ✅ `process_sold_properties.sh` - Orchestration script

**Current Limitations:**
- ❌ Only scrapes 5 suburbs (missing Carrara, Merrimac, Worongary)
- ❌ Limited to ~7 pages per suburb (6 months of data)
- ❌ Uploads to `sold_last_6_months` collection (not target database)

### Target Market Suburbs

Based on `/Users/projects/Documents/Cline/Rules/Target Market Subrubs.md`:

| Suburb | Annual Sales | Median Price | Current Data | Gap |
|--------|--------------|--------------|--------------|-----|
| Robina | 228 | $1,400,000 | 5 properties | 223 |
| Mudgeeraba | 144 | $1,300,000 | 6 properties | 138 |
| Varsity Lakes | 117 | $1,312,500 | 6 properties | 111 |
| Reedy Creek | 87 | $1,630,000 | 4 properties | 83 |
| Burleigh Waters | 225 | $1,775,000 | 6 properties | 219 |
| Merrimac | 59 | $1,063,250 | 5 properties | 54 |
| Worongary | 41 | $1,737,500 | 4 properties | 37 |
| Carrara | ~100 | $1,200,000 | 2 properties | 98 |

**Total Gap:** ~963 properties needed for 12 months of data

---

## Implementation Strategy

### Approach: Extend Existing Scraper

Rather than building from scratch, we'll **extend the proven 6-month scraper** to:
1. Add 3 missing suburbs (Carrara, Merrimac, Worongary)
2. Increase page depth from 7 to 15 pages per suburb (12 months)
3. Update MongoDB target to `Gold_Coast_Recently_Sold` database
4. Add intelligent stop conditions for 12-month cutoff

### Why This Approach?

✅ **Proven Infrastructure** - Existing scraper has 95%+ success rate  
✅ **Deduplication Built-in** - MongoDB uploader handles duplicates  
✅ **Sale Date Extraction** - 4 methods ensure high accuracy  
✅ **Intelligent Stop Conditions** - Stops when data gets too old  
✅ **Fast Development** - Modify existing code vs. build from scratch  

---

## Technical Implementation

### Step 1: Create Modified Scraper

**New Directory:**
```
/Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb/Phase1_12Month_Scraper/
```

**Files to Create:**
1. `list_page_scraper_12months.py` - Modified list scraper with 8 suburbs, 15 pages each
2. `property_detail_scraper_12months.py` - Copy from existing (no changes needed)
3. `html_parser_12months.py` - Copy from existing (no changes needed)
4. `mongodb_uploader_12months.py` - Modified to target `Gold_Coast_Recently_Sold`
5. `process_12month_scrape.sh` - Orchestration script
6. `requirements.txt` - Python dependencies
7. `README.md` - Usage documentation

### Step 2: Suburb URL Configuration

**Domain.com.au URL Pattern:**
```
https://www.domain.com.au/sold-listings/{suburb}-qld-{postcode}/house/?excludepricewithheld=1&page={N}
```

**New Suburb URLs to Add:**

```python
SUBURB_URLS = {
    # Existing 5 suburbs (extend to 15 pages)
    "robina": [
        "https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1",
        # ... pages 2-15
    ],
    "mudgeeraba": [
        "https://www.domain.com.au/sold-listings/mudgeeraba-qld-4213/house/?excludepricewithheld=1",
        # ... pages 2-15
    ],
    "varsity-lakes": [
        "https://www.domain.com.au/sold-listings/varsity-lakes-qld-4227/house/?excludepricewithheld=1",
        # ... pages 2-15
    ],
    "reedy-creek": [
        "https://www.domain.com.au/sold-listings/reedy-creek-qld-4227/house/?excludepricewithheld=1",
        # ... pages 2-15
    ],
    "burleigh-waters": [
        "https://www.domain.com.au/sold-listings/burleigh-waters-qld-4220/house/?excludepricewithheld=1",
        # ... pages 2-15
    ],
    
    # NEW SUBURBS (15 pages each)
    "carrara": [
        "https://www.domain.com.au/sold-listings/carrara-qld-4211/house/?excludepricewithheld=1",
        # ... pages 2-15
    ],
    "merrimac": [
        "https://www.domain.com.au/sold-listings/merrimac-qld-4226/house/?excludepricewithheld=1",
        # ... pages 2-15
    ],
    "worongary": [
        "https://www.domain.com.au/sold-listings/worongary-qld-4213/house/?excludepricewithheld=1",
        # ... pages 2-15
    ]
}
```

### Step 3: MongoDB Configuration

**Target Database:** `Gold_Coast_Recently_Sold` (Azure Cosmos DB)

**Collection Strategy:**
- **Option A:** One collection per suburb (e.g., `Robina`, `Mudgeeraba`, etc.)
- **Option B:** Single collection `sold_properties_12months` with suburb field
- **Recommendation:** Option A (matches existing database structure)

**Connection String:**
```python
# From environment variable or .env file
COSMOS_CONNECTION_STRING = os.getenv("COSMOS_CONNECTION_STRING")
DATABASE_NAME = "Gold_Coast_Recently_Sold"
```

**Deduplication Strategy:**
```python
# Use property URL as unique identifier
unique_key = {"property_url": property_url}
collection.update_one(
    unique_key,
    {"$set": property_data},
    upsert=True
)
```

### Step 4: Intelligent Stop Conditions

**12-Month Cutoff Logic:**

```python
from datetime import datetime, timedelta

TWELVE_MONTHS_AGO = datetime.now() - timedelta(days=365)

def should_stop_scraping(consecutive_old_properties, consecutive_duplicates):
    """
    Stop scraping if:
    - 5 consecutive properties sold >12 months ago, OR
    - 5 consecutive properties already in database
    """
    if consecutive_old_properties >= 5:
        return True, "Reached 12-month cutoff"
    
    if consecutive_duplicates >= 5:
        return True, "All recent properties already in database"
    
    return False, None
```

### Step 5: Data Fields to Capture

**Required Fields (from gap analysis):**

```python
property_data = {
    # Core identifiers
    "property_url": str,
    "domain_id": str,
    "address": str,
    "suburb": str,
    "postcode": str,
    
    # Sale information
    "sale_price": int,
    "sale_date": datetime,
    "sale_method": str,  # "Auction" or "Private Treaty"
    
    # Property characteristics
    "bedrooms": int,
    "bathrooms": int,
    "car_spaces": int,
    "property_type": str,  # "House"
    
    # Structural data (CRITICAL GAPS)
    "lot_size": int,  # m² (extract from description/features)
    "floor_area": int,  # m² (extract from description/features)
    "building_age": int,  # years (extract from description/features)
    
    # Features
    "features": list,  # All listed features
    "description": str,  # Full property description
    
    # Media
    "images": list,  # All image URLs
    "floor_plans": list,  # Floor plan image URLs
    
    # Calculated fields
    "days_on_market": int,  # Calculate from first_listed_date and sale_date
    "first_listed_date": datetime,  # Extract if available
    
    # Metadata
    "scraped_at": datetime,
    "data_source": "domain.com.au",
    "scraper_version": "12month_v1.0"
}
```

---

## Execution Plan

### Phase 1A: Setup (30 minutes)

1. **Create project directory:**
   ```bash
   cd /Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb
   mkdir Phase1_12Month_Scraper
   cd Phase1_12Month_Scraper
   ```

2. **Copy existing scraper files:**
   ```bash
   cp ../../02_Domain_Scaping/Sold_In_Last_6_Months/*.py .
   cp ../../02_Domain_Scaping/Sold_In_Last_6_Months/requirements.txt .
   ```

3. **Create .env file:**
   ```bash
   echo "COSMOS_CONNECTION_STRING=mongodb://..." > .env
   ```

### Phase 1B: Modify Scripts (2 hours)

1. **Update `list_page_scraper_12months.py`:**
   - Add 3 new suburbs (Carrara, Merrimac, Worongary)
   - Extend all suburbs to 15 pages
   - Update output file naming

2. **Update `mongodb_uploader_12months.py`:**
   - Change database to `Gold_Coast_Recently_Sold`
   - Update collection naming (suburb-specific)
   - Add 12-month cutoff logic
   - Enhance deduplication

3. **Create `process_12month_scrape.sh`:**
   - Orchestrate full pipeline
   - Add progress logging
   - Handle errors gracefully

### Phase 1C: Test Run (1 hour)

1. **Test single suburb (Carrara):**
   ```bash
   python3 list_page_scraper_12months.py --suburb carrara --pages 2
   python3 property_detail_scraper_12months.py --input listing_results_sold/sold_urls_carrara_*.json
   python3 mongodb_uploader_12months.py --input property_data/carrara_*.json
   ```

2. **Verify results:**
   ```bash
   python3 check_mongodb_status.py --database Gold_Coast_Recently_Sold --collection Carrara
   ```

3. **Expected output:**
   - 20-40 properties scraped
   - All fields populated
   - No duplicates
   - Sale dates within 12 months

### Phase 1D: Full Production Run (8-12 hours)

1. **Run complete scraper:**
   ```bash
   ./process_12month_scrape.sh
   ```

2. **Monitor progress:**
   ```bash
   tail -f logs/scrape_progress.log
   ```

3. **Expected timeline:**
   - List page scraping: 2-3 hours (8 suburbs × 15 pages × 30 sec/page)
   - Property detail scraping: 4-6 hours (1,000 properties × 15 sec/property)
   - MongoDB upload: 1-2 hours (1,000 properties × 5 sec/property)

### Phase 1E: Verification (30 minutes)

1. **Check database counts:**
   ```bash
   python3 check_mongodb_status.py --database Gold_Coast_Recently_Sold
   ```

2. **Verify data quality:**
   ```bash
   python3 verify_data_quality.py
   ```

3. **Expected results:**
   - 800-1,500 total properties
   - 95%+ have sale_price and sale_date
   - 60%+ have lot_size (from features)
   - 40%+ have floor_area (from features)
   - 0 duplicates

---

## Risk Mitigation

### Risk 1: Domain.com.au Rate Limiting

**Mitigation:**
- Add 3-5 second delays between requests
- Use rotating user agents
- Implement exponential backoff on errors
- Run during off-peak hours (2am-6am AEST)

### Risk 2: Incomplete Data Extraction

**Mitigation:**
- Use 4 sale date extraction methods (existing)
- Parse lot_size from multiple sources (features, description)
- Log all extraction failures for manual review
- Accept 60-70% coverage for structural data (Phase 2 will improve)

### Risk 3: MongoDB Connection Issues

**Mitigation:**
- Implement connection retry logic (3 attempts)
- Save scraped data to JSON files as backup
- Use batch uploads (50 properties at a time)
- Monitor connection health

### Risk 4: Scraper Detection/Blocking

**Mitigation:**
- Use Selenium with realistic browser behavior
- Randomize scroll patterns and timing
- Rotate user agents
- Add CAPTCHA detection and manual intervention

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
- ✅ 30%+ have building_age
- ✅ All properties within 12 months

---

## Next Steps After Phase 1

Once Phase 1 is complete, proceed to:

**Phase 2: Structural Data Enhancement (Week 1-2)**
- Extract lot_size, floor_area, building_age from descriptions
- Use QLD Spatial API for lot_size validation
- Achieve 95%+ coverage

**Phase 3: Calculated Fields (Week 2)**
- Calculate days_on_market
- Parse sale_method from descriptions
- Add price per sqm metrics

**Phase 4: Location Intelligence (Week 2-3)**
- Add proximity to amenities (Google Places API)
- Add school zone data
- Add beach distance

**Phase 5: AI Enhancement (Week 3-4)**
- Extend Ollama photo analysis to sold properties
- Extract building condition
- Score outdoor entertainment areas

---

## File Structure

```
GapAnalysis_13thFeb/
├── README.md                           # Gap analysis overview
├── GAP_ANALYSIS_REPORT.md              # Detailed 50+ page report
├── PHASE1_IMPLEMENTATION_PLAN.md       # This document
├── analyze_database.py                 # Database analysis script
├── database_analysis.json              # Analysis results
├── Requirements                        # Original requirements
│
└── Phase1_12Month_Scraper/             # NEW - Phase 1 implementation
    ├── README.md                       # Usage guide
    ├── requirements.txt                # Python dependencies
    ├── .env                            # MongoDB connection string
    ├── .env.example                    # Example environment file
    │
    ├── list_page_scraper_12months.py   # Modified list scraper (8 suburbs, 15 pages)
    ├── property_detail_scraper_12months.py  # Property detail scraper
    ├── html_parser_12months.py         # HTML parser with sale date extraction
    ├── mongodb_uploader_12months.py    # MongoDB uploader (Gold_Coast_Recently_Sold)
    ├── check_mongodb_status.py         # Database status checker
    ├── verify_data_quality.py          # Data quality verification
    │
    ├── process_12month_scrape.sh       # Main orchestration script
    ├── test_single_suburb.sh           # Test script for single suburb
    │
    ├── listing_results_sold/           # List scraper output
    ├── property_data/                  # Property detail scraper output
    └── logs/                           # Scraping logs
```

---

## Cost Estimate

**Compute Time:**
- Local machine: 8-12 hours (FREE)
- OR Cloud VM: $5-10 (if running on GCP/AWS)

**API Costs:**
- Domain.com.au: FREE (public website scraping)
- MongoDB Atlas: FREE (existing Azure Cosmos DB)

**Total Estimated Cost:** $0-10

---

## Timeline

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 1A | Setup project directory | 30 min | None |
| 1B | Modify scraper scripts | 2 hours | 1A complete |
| 1C | Test single suburb | 1 hour | 1B complete |
| 1D | Full production run | 8-12 hours | 1C successful |
| 1E | Verification | 30 min | 1D complete |

**Total Timeline:** 12-16 hours (1.5-2 days)

---

## Monitoring and Logging

### Progress Logging

```bash
# Real-time progress monitoring
tail -f logs/scrape_progress.log

# Expected output:
# [2026-02-13 11:45:00] Starting list page scraping...
# [2026-02-13 11:45:30] Robina page 1: 20 properties found
# [2026-02-13 11:46:00] Robina page 2: 20 properties found
# ...
# [2026-02-13 14:30:00] List scraping complete: 1,200 URLs collected
# [2026-02-13 14:30:30] Starting property detail scraping...
# [2026-02-13 14:31:00] Property 1/1200: Success
# ...
```

### Error Handling

```python
# Log all errors to separate file
error_log = {
    "timestamp": datetime.now().isoformat(),
    "error_type": "extraction_failed",
    "property_url": url,
    "error_message": str(e),
    "html_saved": f"errors/{property_id}.html"
}

with open("logs/errors.json", "a") as f:
    f.write(json.dumps(error_log) + "\n")
```

---

## Questions and Answers

### Q: Why not use the existing 6-month scraper as-is?

**A:** The existing scraper has 3 limitations:
1. Only covers 5 of 8 target suburbs
2. Limited to ~7 pages (6 months of data)
3. Uploads to wrong database (`sold_last_6_months` vs. `Gold_Coast_Recently_Sold`)

### Q: Can we scrape more than 12 months?

**A:** Yes, but diminishing returns:
- 12 months = 1,000+ properties (sufficient for modeling)
- 24 months = 2,000+ properties (better, but 2x scraping time)
- Recommendation: Start with 12 months, expand later if needed

### Q: What if Domain.com.au blocks us?

**A:** Multiple fallback options:
1. Switch to headless browser with stealth mode
2. Use residential proxy service ($20-50)
3. Slow down scraping (1 property/minute)
4. Manual data entry for critical gaps

### Q: How do we handle missing lot_size/floor_area?

**A:** Phase 1 focuses on data volume. Phase 2 will:
1. Use QLD Spatial API for lot_size (95%+ coverage)
2. Parse floor_area from descriptions with regex
3. Use ML to estimate from photos (Phase 5)

---

## Approval Checklist

Before proceeding with implementation:

- [ ] Review gap analysis report (`GAP_ANALYSIS_REPORT.md`)
- [ ] Confirm target database (`Gold_Coast_Recently_Sold`)
- [ ] Verify MongoDB connection string available
- [ ] Approve 8-12 hour scraping runtime
- [ ] Confirm all 8 suburbs are correct
- [ ] Review success criteria (800+ properties minimum)
- [ ] Approve proceeding to Phase 1B (script modification)

---

## Related Documentation

- **Gap Analysis Report:** `GAP_ANALYSIS_REPORT.md`
- **Existing Scraper:** `02_Domain_Scaping/Sold_In_Last_6_Months/`
- **Target Market Suburbs:** `/Users/projects/Documents/Cline/Rules/Target Market Subrubs.md`
- **Database Analysis:** `database_analysis.json`

---

*Document created: 13/02/2026, 11:38 AM Brisbane Time*  
*Ready for implementation approval*
