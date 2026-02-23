# FOR-SALE PROPERTIES - COMPLETE UPDATE PROCESS PLAN

## 📋 Executive Summary

This plan outlines the complete implementation for tracking Domain.com.au **for-sale** properties using the new HTML-based scraping method (adapted from the Sold Properties system) and integrating it with the existing MongoDB change-tracking infrastructure.

**Key Objective:** Replace the screenshot/OCR method with the more reliable URL extraction → HTML scraping approach while maintaining full change detection and historical tracking.

---

## 🔄 System Overview

### Current Systems

1. **Old Method (07_Undetectable_method/Simple_Method/)**
   - Screenshot capture → OCR → Text parsing
   - MongoDB upload with change tracking
   - Works but unreliable OCR extraction

2. **New Method (02_Domain_Scaping/Sold_Properties/)**
   - List page scraping → URL extraction → Individual property scraping
   - HTML parsing (more reliable)
   - Currently designed for SOLD properties

3. **Database Infrastructure (automation/mongodb_client.py)**
   - `properties` collection: Current for-sale listings
   - `property_snapshots` collection: Historical data snapshots
   - `property_changes` collection: Detected changes over time

---

## 📊 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY UPDATE WORKFLOW                         │
└─────────────────────────────────────────────────────────────────┘

1. SCRAPE LIST PAGES
   ├─ Navigate to Domain.com.au for-sale list pages
   ├─ Extract HTML from each page
   └─ Parse all property listing URLs
         ↓
2. SCRAPE INDIVIDUAL PROPERTIES
   ├─ For each listing URL:
   │  ├─ Navigate to property page
   │  ├─ Extract HTML
   │  └─ Parse property details (beds, baths, price, etc.)
   └─ Save raw data to JSON
         ↓
3. UPLOAD TO MONGODB (properties collection)
   ├─ Identify NEW properties (not in DB)
   ├─ Identify EXISTING properties (still for sale)
   ├─ Identify REMOVED properties (no longer for sale)
   └─ Update `properties` collection with status & last_seen
         ↓
4. DETECT & LOG CHANGES
   ├─ For each property with existing snapshot:
   │  ├─ Compare new data vs latest snapshot
   │  ├─ Log changes to `property_changes` collection
   │  └─ Create new snapshot in `property_snapshots`
   └─ For new properties: Create initial snapshot
         ↓
5. ENRICH PROPERTIES (Optional - if needed)
   ├─ Run batch_processor.py for detailed enrichment
   └─ Update properties with additional data
         ↓
6. CLEANUP & REPORTING
   ├─ Archive old removed properties
   └─ Generate status reports
```

---

## 🎯 Implementation Plan

### Phase 1: Create For-Sale Properties Directory Structure

**Location:** `02_Domain_Scaping/For_Sale_Properties/`

**Files to Create:**

1. **`list_page_scraper_forsale.py`**
   - Adapt from `Sold_Properties/list_page_scraper.py`
   - Update URLs to for-sale listings:
     ```python
     URLS = [
         "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0",
         "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0&page=2",
         # Add more pages as needed
     ]
     ```
   - Keep same HTML extraction and URL parsing logic
   - Output: `listing_results/property_listing_urls_TIMESTAMP.json`

2. **`property_detail_scraper_forsale.py`**
   - Adapt from `Sold_Properties/property_detail_scraper.py`
   - Same scraping logic (works for both sold and for-sale)
   - Output: `property_data/property_scrape_report_TIMESTAMP.json`

3. **`mongodb_uploader_forsale.py`** ⭐ NEW
   - Use `automation/mongodb_client.py` PropertyDB class
   - Read scraped property data from JSON
   - Call `update_daily_list()` to handle new/updated/removed
   - Output: MongoDB `properties` collection updated

4. **`change_detector.py`** ⭐ NEW
   - For each property in today's scrape:
     - Get latest snapshot from `property_snapshots`
     - Compare key fields (price, description, etc.)
     - Log changes to `property_changes` collection
     - Create new snapshot in `property_snapshots`
   - Uses `PropertyDB.detect_and_log_changes()` and `store_detailed_snapshot()`

5. **`process_forsale_properties.sh`** ⭐ MASTER SCRIPT
   - Orchestrate the complete pipeline
   - Steps:
     1. Scrape list pages → extract URLs
     2. Scrape individual properties → extract data
     3. Upload to MongoDB → update properties collection
     4. Detect changes → log to property_changes
     5. Create snapshots → save to property_snapshots
     6. Generate report

---

### Phase 2: MongoDB Integration Components

#### A. `mongodb_uploader_forsale.py` - Detailed Specification

```python
#!/usr/bin/env python3
"""
MongoDB Uploader for For-Sale Properties
Uploads scraped property data and manages property lifecycle
"""

import json
import sys
from datetime import datetime
sys.path.append('../../automation')
from mongodb_client import PropertyDB

def load_scraped_data(report_file):
    """Load property data from scrape report"""
    with open(report_file, 'r') as f:
        data = json.load(f)
    
    # Extract successful property data
    properties = []
    for result in data.get('results', []):
        if result.get('success') and result.get('property_data'):
            properties.append(result['property_data'])
    
    return properties

def main():
    # Find most recent scrape report
    report_file = get_latest_report()
    
    # Load data
    properties = load_scraped_data(report_file)
    
    # Connect to MongoDB
    db = PropertyDB()
    
    # Update daily list (handles new, updated, removed)
    stats = db.update_daily_list(properties)
    
    print(f"MongoDB Upload Complete:")
    print(f"  New properties: {stats['new']}")
    print(f"  Updated properties: {stats['updated']}")
    print(f"  Removed properties: {stats['removed']}")
    
    db.close()

if __name__ == "__main__":
    main()
```

#### B. `change_detector.py` - Detailed Specification

```python
#!/usr/bin/env python3
"""
Property Change Detector
Compares current property data with historical snapshots
Logs changes and creates new snapshots
"""

import json
import sys
sys.path.append('../../automation')
from mongodb_client import PropertyDB

def main():
    # Load today's scraped data
    properties = load_scraped_data()
    
    # Connect to MongoDB
    db = PropertyDB()
    
    # For each property
    for prop in properties:
        address = prop['address']
        
        # Detect and log changes
        db.detect_and_log_changes(address, prop)
        
        # Create new snapshot
        db.store_detailed_snapshot(address, prop)
    
    print(f"Change detection complete for {len(properties)} properties")
    
    db.close()

if __name__ == "__main__":
    main()
```

---

### Phase 3: Master Pipeline Script

#### `process_forsale_properties.sh` - Complete Workflow

```bash
#!/bin/bash
#
# For-Sale Properties - Complete Pipeline
# Scrapes Domain.com.au for-sale listings and tracks changes
#

echo "======================================================================"
echo "DOMAIN.COM.AU FOR-SALE PROPERTIES - COMPLETE PIPELINE"
echo "======================================================================"
echo ""

# Step 1: Scrape list pages for URLs
echo "STEP 1: Scraping list pages for property URLs..."
echo "----------------------------------------------------------------------"
python3 list_page_scraper_forsale.py

if [ $? -ne 0 ]; then
    echo "✗ List page scraping failed!"
    exit 1
fi

# Step 2: Find latest URL file
URLS_FILE=$(ls -t listing_results/property_listing_urls_*.json 2>/dev/null | head -n 1)

if [ -z "$URLS_FILE" ]; then
    echo "✗ No property URLs file found!"
    exit 1
fi

URL_COUNT=$(python3 -c "import json; data=json.load(open('$URLS_FILE')); print(data.get('total_count', 0))")
echo "✓ Found $URL_COUNT property URLs to process"

# Step 3: Scrape individual properties
echo ""
echo "STEP 2: Scraping individual property listings..."
echo "----------------------------------------------------------------------"
python3 property_detail_scraper_forsale.py --input "$URLS_FILE"

if [ $? -ne 0 ]; then
    echo "✗ Property detail scraping failed!"
    exit 1
fi

# Step 4: Upload to MongoDB
echo ""
echo "STEP 3: Uploading to MongoDB..."
echo "----------------------------------------------------------------------"
python3 mongodb_uploader_forsale.py

if [ $? -ne 0 ]; then
    echo "✗ MongoDB upload failed!"
    exit 1
fi

# Step 5: Detect changes and create snapshots
echo ""
echo "STEP 4: Detecting changes and creating snapshots..."
echo "----------------------------------------------------------------------"
python3 change_detector.py

if [ $? -ne 0 ]; then
    echo "⚠ Change detection encountered errors (continuing)"
fi

# Step 6: Optional - Enrich properties with detailed data
echo ""
echo "STEP 5: Enriching properties (optional)..."
echo "----------------------------------------------------------------------"
read -p "Run property enrichment? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ../../07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search
    python3 batch_processor.py --mongodb
    cd ../../../02_Domain_Scaping/For_Sale_Properties
fi

# Step 7: Generate final report
echo ""
echo "STEP 6: Generating final report..."
echo "----------------------------------------------------------------------"
python3 generate_report.py

echo ""
echo "======================================================================"
echo "🎉 PIPELINE COMPLETE!"
echo "======================================================================"
```

---

## 🗂️ MongoDB Collections Schema

### 1. `properties` Collection (Current State)

```javascript
{
  "_id": ObjectId("..."),
  "address": "123 Main Street, Robina, QLD 4226",  // UNIQUE INDEX
  "status": "for_sale",  // or "removed"  // INDEX
  "first_seen": ISODate("2025-01-15T10:00:00Z"),
  "last_seen": ISODate("2025-01-20T10:00:00Z"),  // INDEX
  "last_detailed_update": ISODate("2025-01-20T10:00:00Z"),
  
  // Basic property data
  "bedrooms": 4,
  "bathrooms": 2,
  "parking": 2,
  "land_size_sqm": 450,
  "property_type": "House",
  "price": "$850,000",
  "price_type": "Fixed Price",
  
  // Agency info
  "agency": "Ray White Robina",
  "agent": "John Smith",
  
  // Listing details
  "listing_url": "https://www.domain.com.au/...",
  "under_offer": false,
  "auction_date": null,
  "inspection": "Saturday 10:00-10:30am",
  
  // Metadata
  "extraction_date": ISODate("2025-01-20T10:00:00Z")
}
```

### 2. `property_snapshots` Collection (Historical Data)

```javascript
{
  "_id": ObjectId("..."),
  "address": "123 Main Street, Robina, QLD 4226",
  "property_id": "domain_123456789",  // INDEX
  "snapshot_date": ISODate("2025-01-20T10:00:00Z"),  // INDEX
  "source": "list_page_scraper",
  
  // Complete property data at this point in time
  "data": {
    "bedrooms": 4,
    "bathrooms": 2,
    "price": "$850,000",
    "description": "Beautiful family home...",
    "features": ["Pool", "Air Conditioning"],
    // ... all fields
  }
}
```

### 3. `property_changes` Collection (Change Log)

```javascript
{
  "_id": ObjectId("..."),
  "property_id": "domain_123456789",  // INDEX
  "address": "123 Main Street, Robina, QLD 4226",
  "change_date": ISODate("2025-01-20T10:00:00Z"),  // INDEX
  "change_type": "price",
  "old_value": "$875,000",
  "new_value": "$850,000",
  "details": "Changed from $875,000 to $850,000"
}
```

---

## 🔧 Key Implementation Details

### URL Configuration for For-Sale Properties

Update list page URLs to target **for-sale** (not sold):

```python
# For Robina, QLD - For Sale Houses
URLS = [
    "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0",
    "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0&page=2",
    "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0&page=3",
    # Add more pages as needed
]

# Or for broader search across suburbs
URLS = [
    "https://www.domain.com.au/sale/gold-coast-qld/house/?excludeunderoffer=1",
    # Add pagination
]
```

### HTML Parser Compatibility

The existing `html_parser.py` from `07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/` already works for both sold and for-sale properties:

```python
from html_parser import parse_listing_html, clean_property_data

# Use as-is - no modifications needed
property_data = parse_listing_html(html, address)
property_data = clean_property_data(property_data)
```

### Change Detection Fields

Monitor these fields for changes:
- **Price** (most important!)
- **Description**
- **Bedrooms/Bathrooms/Parking**
- **Land size**
- **Agent name**
- **Features list**
- **Inspection times**
- **Auction date**
- **Under offer status**

---

## 📁 Directory Structure

```
02_Domain_Scaping/
├── Sold_Properties/           # Existing (template)
│   ├── list_page_scraper.py
│   ├── property_detail_scraper.py
│   └── process_sold_properties.sh
│
└── For_Sale_Properties/       # NEW - To be created
    ├── list_page_scraper_forsale.py
    ├── property_detail_scraper_forsale.py
    ├── mongodb_uploader_forsale.py       ⭐ NEW
    ├── change_detector.py                ⭐ NEW
    ├── generate_report.py                ⭐ NEW
    ├── process_forsale_properties.sh     ⭐ MASTER SCRIPT
    ├── requirements.txt
    ├── README.md
    ├── listing_results/          # Output: URLs
    │   └── property_listing_urls_TIMESTAMP.json
    └── property_data/            # Output: Scraped data
        ├── html/
        └── property_scrape_report_TIMESTAMP.json
```

---

## ⚙️ Configuration & Environment

### Requirements

```txt
beautifulsoup4>=4.12.0
pymongo>=4.6.0
requests>=2.31.0
lxml>=5.0.0
```

### MongoDB Setup

```bash
# Ensure MongoDB is running
brew services start mongodb-community

# Or using existing connection
# mongodb://127.0.0.1:27017/property_data
```

---

## 🚀 Execution Steps

### Daily Run Schedule

```bash
# Navigate to directory
cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/For_Sale_Properties

# Run complete pipeline
./process_forsale_properties.sh

# Or run steps individually:
# 1. Scrape list pages
python3 list_page_scraper_forsale.py

# 2. Scrape properties
python3 property_detail_scraper_forsale.py --input listing_results/property_listing_urls_*.json

# 3. Upload to MongoDB
python3 mongodb_uploader_forsale.py

# 4. Detect changes
python3 change_detector.py

# 5. Generate report
python3 generate_report.py
```

---

## 📊 Reporting & Monitoring

### Daily Report Contents

1. **Scraping Summary**
   - Total properties found
   - Successfully scraped
   - Failed scrapes

2. **Database Updates**
   - New properties added
   - Existing properties updated
   - Properties removed (off market)

3. **Change Detection**
   - Price changes detected
   - Description updates
   - Other field changes

4. **Alerts**
   - Significant price drops
   - New properties in target area
   - Properties removed from market

---

## 🔄 Migration from Old System

### Transition Plan

1. **Week 1: Build & Test**
   - Create For_Sale_Properties directory
   - Adapt scrapers for for-sale listings
   - Build MongoDB integration scripts
   - Test on small dataset

2. **Week 2: Parallel Run**
   - Run both old (OCR) and new (HTML) systems
   - Compare results
   - Validate accuracy

3. **Week 3: Full Migration**
   - Switch to new system as primary
   - Retire old OCR-based system
   - Archive old scripts

### Data Migration

```python
# migrate_existing_data.py
# Migrate existing properties from old system to new schema
# Ensure continuity of change tracking
```

---

## ✅ Success Criteria

- [ ] Successfully scrape 100% of for-sale listings from target pages
- [ ] Accurately parse property details (95%+ accuracy)
- [ ] Correctly identify new/updated/removed properties
- [ ] Successfully detect and log price changes
- [ ] Create historical snapshots for all properties
- [ ] Generate comprehensive daily reports
- [ ] Run reliably as scheduled task

---

## 🎯 Next Steps

1. **Create directory structure** for `For_Sale_Properties`
2. **Adapt list_page_scraper.py** for for-sale URLs
3. **Adapt property_detail_scraper.py** (minimal changes)
4. **Build mongodb_uploader_forsale.py** (use PropertyDB)
5. **Build change_detector.py** (use PropertyDB methods)
6. **Create master script** `process_forsale_properties.sh`
7. **Test on small dataset** (5-10 properties)
8. **Run full pipeline** on complete dataset
9. **Schedule daily execution** (cron/automation)
10. **Monitor and refine**

---

## 📝 Notes & Considerations

### Anti-Detection

- Use delays between requests (2-5 seconds)
- Rotate user agents (already implemented)
- Use Chrome automation (already implemented)
- Avoid overwhelming the server

### Error Handling

- Retry failed scrapes (3 attempts)
- Log all errors to MongoDB errors collection
- Continue pipeline even if individual properties fail
- Alert on >10% failure rate

### Performance

- Sequential scraping (avoid parallelization for now)
- Average 5-10 seconds per property
- 100 properties = ~10 minutes runtime
- Schedule during off-peak hours

### Data Retention

- Keep `properties` collection indefinitely (current state)
- Keep `property_snapshots` for 2 years (historical)
- Keep `property_changes` for 2 years (audit trail)
- Archive old data to separate database

---

## 🔗 Related Documentation

- `02_Domain_Scaping/Sold_Properties/CURRENT_STATUS.md` - Sold properties system
- `automation/mongodb_client.py` - Database client implementation
- `07_Undetectable_method/Simple_Method/process_all_sessions.sh` - Old OCR-based system
- `07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/batch_processor.py` - Enrichment system

---

**Last Updated:** 2025-12-04
**Status:** Planning Phase - Ready for Implementation
**Owner:** Property Data Scraping Team
