# Development Plan: Sold Properties Scraper (Last 6 Months)

**Created:** 15 December 2025  
**Target Folder:** `02_Domain_Scaping/Sold_In_Last_6_Months/`  
**Database:** `property_data`  
**Collection:** `sold_last_6_months`  
**Reference Script:** `00_Run_Commands/01_Scraping_For_Sale_Properties_04122025.md`

---

## 📋 Executive Summary

This plan outlines the development of a scraping system to collect all properties sold in the last 6 months from domain.com.au. The system will:

1. **Scrape sold property listings** from multiple Gold Coast suburbs
2. **Extract sale dates** from each property listing
3. **Implement intelligent stop conditions** (suburb-by-suburb):
   - Stop when 3 consecutive properties have sale dates >6 months old
   - Stop when 3 consecutive properties already exist in the collection
4. **Store data** in MongoDB collection `sold_last_6_months`
5. **Process suburbs sequentially** to ensure clean stop triggers per suburb

---

## 🎯 Key Requirements

### 1. Target URLs (Sold Listings)
The scraper will process these Domain.com.au sold listing URLs:

**Robina (7 pages):**
- https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1
- https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1&page=2
- https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1&page=3
- https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1&page=4
- https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1&page=5
- https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1&page=6
- https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1&page=7

**Mudgeeraba (5 pages):**
- https://www.domain.com.au/sold-listings/mudgeeraba-qld-4213/house/?excludepricewithheld=1
- https://www.domain.com.au/sold-listings/mudgeeraba-qld-4213/house/?excludepricewithheld=1&page=2
- https://www.domain.com.au/sold-listings/mudgeeraba-qld-4213/house/?excludepricewithheld=1&page=3
- https://www.domain.com.au/sold-listings/mudgeeraba-qld-4213/house/?excludepricewithheld=1&page=4
- https://www.domain.com.au/sold-listings/mudgeeraba-qld-4213/house/?excludepricewithheld=1&page=5

**Varsity Lakes (4 pages):**
- https://www.domain.com.au/sold-listings/varsity-lakes-qld-4227/house/?excludepricewithheld=1
- https://www.domain.com.au/sold-listings/varsity-lakes-qld-4227/house/?excludepricewithheld=1&page=2
- https://www.domain.com.au/sold-listings/varsity-lakes-qld-4227/house/?excludepricewithheld=1&page=3
- https://www.domain.com.au/sold-listings/varsity-lakes-qld-4227/house/?excludepricewithheld=1&page=4

**Reedy Creek (2 pages):**
- https://www.domain.com.au/sold-listings/reedy-creek-qld-4227/house/?excludepricewithheld=1
- https://www.domain.com.au/sold-listings/reedy-creek-qld-4227/house/?excludepricewithheld=1&page=2

**Burleigh Waters (4 pages):**
- https://www.domain.com.au/sold-listings/burleigh-waters-qld-4220/house/?excludepricewithheld=1
- https://www.domain.com.au/sold-listings/burleigh-waters-qld-4220/house/?excludepricewithheld=1&page=2
- https://www.domain.com.au/sold-listings/burleigh-waters-qld-4220/house/?excludepricewithheld=1&page=3
- https://www.domain.com.au/sold-listings/burleigh-waters-qld-4220/house/?excludepricewithheld=1&page=4

**Total:** 5 suburbs, 22 pages

### 2. Stop Conditions (Per Suburb)

The scraper must implement **two independent stop conditions** that are checked **per suburb**:

#### Stop Condition A: Sale Date Check
- Extract the sale date from each property
- Track consecutive properties with sale dates >6 months from today
- **Stop scraping current suburb** when 3 consecutive properties exceed 6 months
- Reset counter when a property within 6 months is found

#### Stop Condition B: Duplicate Check
- Check if property already exists in `sold_last_6_months` collection (by address)
- Track consecutive duplicate properties
- **Stop scraping current suburb** when 3 consecutive duplicates are found
- Reset counter when a new (non-duplicate) property is found

#### Processing Flow
```
For each suburb:
  consecutive_old_count = 0
  consecutive_duplicate_count = 0
  
  For each page in suburb:
    For each property on page:
      1. Extract property data including sale_date
      2. Check if sale_date > 6 months ago
         - If yes: consecutive_old_count++
         - If no: consecutive_old_count = 0
      3. Check if property exists in DB
         - If yes: consecutive_duplicate_count++
         - If no: consecutive_duplicate_count = 0
      4. If consecutive_old_count >= 3 OR consecutive_duplicate_count >= 3:
         - Log stop reason
         - Break to next suburb
      5. Otherwise: Save property to DB
  
  Move to next suburb (reset counters)
```

### 3. Data Schema

Each property document in `sold_last_6_months` collection will include:

**Core Fields (from HTML parser):**
- `address` (string, unique index) - Full property address
- `street_address` (string)
- `suburb` (string)
- `postcode` (string)
- `bedrooms` (integer)
- `bathrooms` (integer)
- `carspaces` (integer)
- `property_type` (string) - House, Townhouse, Apartment, etc.
- `land_size_sqm` (integer)
- `price` (string) - Sold price
- `description` (string)
- `agents_description` (string)
- `property_images` (array of strings) - Image URLs
- `floor_plans` (array of strings) - Floor plan URLs
- `features` (array of strings)
- `listing_url` (string)

**Sold-Specific Fields (NEW):**
- `sale_date` (ISO date string) - **CRITICAL** for stop condition
- `sale_price` (string) - Actual sold price
- `days_on_market` (integer) - If available

**Metadata Fields:**
- `extraction_method` (string) - "HTML"
- `extraction_date` (ISO datetime)
- `first_seen` (ISO datetime)
- `last_updated` (ISO datetime)
- `source` (string) - "selenium_sold_scraper"
- `suburb_scraped` (string) - Which suburb scrape found this property

---

## 🏗️ System Architecture

### Component Overview

The system will consist of 4 main Python scripts (adapted from for-sale scraper):

```
02_Domain_Scaping/Sold_In_Last_6_Months/
├── list_page_scraper_sold.py          # Stage 1: Extract property URLs
├── property_detail_scraper_sold.py    # Stage 2: Scrape property details + sale dates
├── mongodb_uploader_sold.py           # Stage 3: Upload to MongoDB with stop logic
├── process_sold_properties.sh         # Orchestration script
├── html_parser_sold.py                # HTML parser with sale date extraction
├── DEVELOPMENT_PLAN.md                # This document
├── listing_results/                   # Output: Property URLs by suburb
├── property_data/                     # Output: Scraped property data
└── logs/                              # Execution logs
```

---

## 📝 Detailed Component Specifications

### 1. `list_page_scraper_sold.py`

**Purpose:** Extract individual property listing URLs from sold listing pages

**Key Differences from For-Sale Version:**
- URLs point to `/sold-listings/` instead of `/sale/`
- Process suburbs sequentially (not all at once)
- Generate separate URL files per suburb for tracking

**Inputs:**
- Hardcoded list of sold listing URLs (grouped by suburb)

**Outputs:**
- `listing_results/sold_urls_robina_TIMESTAMP.json`
- `listing_results/sold_urls_mudgeeraba_TIMESTAMP.json`
- `listing_results/sold_urls_varsity_lakes_TIMESTAMP.json`
- `listing_results/sold_urls_reedy_creek_TIMESTAMP.json`
- `listing_results/sold_urls_burleigh_waters_TIMESTAMP.json`

**Processing Logic:**
```python
SUBURBS = {
    "robina": [
        "https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1",
        "https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1&page=2",
        # ... pages 3-7
    ],
    "mudgeeraba": [
        # ... 5 pages
    ],
    # ... other suburbs
}

for suburb_name, urls in SUBURBS.items():
    suburb_urls = []
    for url in urls:
        # Extract property URLs from page
        property_urls = extract_listing_urls(url)
        suburb_urls.extend(property_urls)
    
    # Save suburb-specific URL file
    save_urls(suburb_name, suburb_urls)
```

**Technology:**
- Selenium WebDriver (Chrome)
- BeautifulSoup for HTML parsing
- Same URL extraction regex as for-sale version

---

### 2. `html_parser_sold.py`

**Purpose:** Parse sold property HTML to extract all data including sale date

**Key Additions to Existing Parser:**
- **Extract sale date** from JSON-LD or HTML elements
- **Extract sold price** (may differ from listing price)
- **Extract days on market** if available

**Sale Date Extraction Strategy:**

```python
def extract_sale_date(soup):
    """
    Extract sale date from sold listing page
    
    Priority order:
    1. JSON-LD structured data (most reliable)
    2. Meta tags (og:updated_time, etc.)
    3. HTML elements with data-testid
    4. Text pattern matching ("Sold on DD MMM YYYY")
    """
    
    # Method 1: JSON-LD
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        data = json.loads(script.string)
        if 'datePosted' in data or 'dateSold' in data:
            return parse_date(data.get('dateSold') or data.get('datePosted'))
    
    # Method 2: Look for "Sold on" text
    sold_text = soup.find(string=re.compile(r'Sold on \d{1,2} \w+ \d{4}', re.I))
    if sold_text:
        return parse_sold_date_text(sold_text)
    
    # Method 3: data-testid elements
    sold_date_elem = soup.find(attrs={'data-testid': 'listing-details__sold-date'})
    if sold_date_elem:
        return parse_date(sold_date_elem.get_text(strip=True))
    
    return None
```

**Date Validation:**
```python
def is_within_6_months(sale_date_str):
    """Check if sale date is within last 6 months"""
    from datetime import datetime, timedelta
    
    sale_date = datetime.fromisoformat(sale_date_str)
    six_months_ago = datetime.now() - timedelta(days=182)  # ~6 months
    
    return sale_date >= six_months_ago
```

---

### 3. `property_detail_scraper_sold.py`

**Purpose:** Scrape individual sold property pages and extract all data

**Key Differences from For-Sale Version:**
- Import `html_parser_sold.py` instead of standard parser
- Process suburbs sequentially (one at a time)
- Include sale date in output
- Track which suburb each property came from

**Inputs:**
- `listing_results/sold_urls_{suburb}_TIMESTAMP.json` (one suburb at a time)

**Outputs:**
- `property_data/sold_scrape_{suburb}_TIMESTAMP.json`

**Processing Logic:**
```python
def process_suburb(suburb_name, urls_file):
    """Process all properties for a single suburb"""
    
    urls = load_urls(urls_file)
    results = []
    
    for i, url in enumerate(urls, 1):
        # Scrape property page
        html = fetch_with_selenium(url)
        
        # Parse data including sale date
        property_data = parse_sold_listing_html(html, address)
        
        # Add suburb tracking
        property_data['suburb_scraped'] = suburb_name
        
        # Validate sale date exists
        if not property_data.get('sale_date'):
            print(f"  ⚠ No sale date found for {address}")
        
        results.append({
            'success': True,
            'property_data': property_data,
            'listing_url': url
        })
    
    return results
```

---

### 4. `mongodb_uploader_sold.py`

**Purpose:** Upload sold properties to MongoDB with intelligent stop conditions

**Key Features:**
- Upload to `sold_last_6_months` collection (not `properties_for_sale`)
- Implement both stop conditions per suburb
- Track consecutive counters
- Log stop reasons
- Create indexes on `address`, `sale_date`, `suburb_scraped`

**Stop Condition Implementation:**

```python
class SoldPropertyUploader:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client['property_data']
        self.collection = self.db['sold_last_6_months']
        self.ensure_indexes()
    
    def ensure_indexes(self):
        """Create necessary indexes"""
        self.collection.create_index("address", unique=True)
        self.collection.create_index("sale_date")
        self.collection.create_index("suburb_scraped")
        self.collection.create_index("first_seen")
    
    def upload_suburb_properties(self, suburb_name, properties):
        """
        Upload properties for a suburb with stop conditions
        
        Returns: (uploaded_count, stop_reason)
        """
        consecutive_old = 0
        consecutive_duplicate = 0
        uploaded_count = 0
        
        six_months_ago = datetime.now() - timedelta(days=182)
        
        for prop in properties:
            address = prop.get('address')
            sale_date_str = prop.get('sale_date')
            
            # Parse sale date
            if sale_date_str:
                sale_date = datetime.fromisoformat(sale_date_str)
            else:
                print(f"  ⚠ No sale date for {address}, skipping")
                continue
            
            # STOP CONDITION A: Check if sale date > 6 months
            if sale_date < six_months_ago:
                consecutive_old += 1
                print(f"  ⚠ Property sold >6 months ago: {address} ({sale_date_str})")
                print(f"    Consecutive old: {consecutive_old}/3")
                
                if consecutive_old >= 3:
                    return uploaded_count, "STOP: 3 consecutive properties >6 months old"
            else:
                consecutive_old = 0  # Reset counter
            
            # STOP CONDITION B: Check if already in database
            existing = self.collection.find_one({"address": address})
            
            if existing:
                consecutive_duplicate += 1
                print(f"  ⚠ Duplicate property: {address}")
                print(f"    Consecutive duplicates: {consecutive_duplicate}/3")
                
                if consecutive_duplicate >= 3:
                    return uploaded_count, "STOP: 3 consecutive duplicate properties"
                
                # Update existing record
                self.collection.update_one(
                    {"address": address},
                    {"$set": {**prop, "last_updated": datetime.now()}}
                )
            else:
                consecutive_duplicate = 0  # Reset counter
                
                # Insert new property
                insert_doc = {
                    **prop,
                    "first_seen": datetime.now(),
                    "last_updated": datetime.now(),
                    "source": "selenium_sold_scraper"
                }
                self.collection.insert_one(insert_doc)
                uploaded_count += 1
                print(f"  ✓ Inserted: {address}")
        
        return uploaded_count, "COMPLETE: All properties processed"
```

**Main Upload Flow:**

```python
def main():
    uploader = SoldPropertyUploader()
    
    suburbs = ['robina', 'mudgeeraba', 'varsity_lakes', 'reedy_creek', 'burleigh_waters']
    
    for suburb in suburbs:
        print(f"\n{'='*80}")
        print(f"Processing Suburb: {suburb.upper()}")
        print(f"{'='*80}")
        
        # Load scraped data for this suburb
        data_file = f"property_data/sold_scrape_{suburb}_*.json"
        properties = load_latest_scrape(data_file)
        
        # Upload with stop conditions
        count, stop_reason = uploader.upload_suburb_properties(suburb, properties)
        
        print(f"\n  Uploaded: {count} properties")
        print(f"  Stop reason: {stop_reason}")
        
        # Log results
        log_suburb_result(suburb, count, stop_reason)
    
    uploader.print_summary()
    uploader.close()
```

---

### 5. `process_sold_properties.sh`

**Purpose:** Orchestrate the entire scraping pipeline

**Workflow:**

```bash
#!/bin/bash

echo "=========================================="
echo "SOLD PROPERTIES SCRAPER - LAST 6 MONTHS"
echo "=========================================="
echo ""

# Stage 1: Extract property URLs (all suburbs)
echo "Stage 1: Extracting property URLs from sold listing pages..."
python3 list_page_scraper_sold.py
if [ $? -ne 0 ]; then
    echo "ERROR: URL extraction failed"
    exit 1
fi
echo ""

# Stage 2: Scrape property details (suburb by suburb)
echo "Stage 2: Scraping property details..."
for suburb in robina mudgeeraba varsity_lakes reedy_creek burleigh_waters; do
    echo "  → Processing suburb: $suburb"
    python3 property_detail_scraper_sold.py --suburb $suburb
    if [ $? -ne 0 ]; then
        echo "  ERROR: Failed to scrape $suburb"
        exit 1
    fi
done
echo ""

# Stage 3: Upload to MongoDB with stop conditions
echo "Stage 3: Uploading to MongoDB (sold_last_6_months collection)..."
python3 mongodb_uploader_sold.py
if [ $? -ne 0 ]; then
    echo "ERROR: MongoDB upload failed"
    exit 1
fi
echo ""

# Stage 4: Summary report
echo "Stage 4: Generating summary report..."
python3 check_mongodb_status_sold.py
echo ""

echo "=========================================="
echo "SCRAPING COMPLETE"
echo "=========================================="
```

---

## 🔧 Implementation Steps

### Phase 1: Setup & Infrastructure (Day 1)
- [x] Create folder structure: `02_Domain_Scaping/Sold_In_Last_6_Months/`
- [ ] Create subdirectories: `listing_results/`, `property_data/`, `logs/`
- [ ] Copy and adapt `html_parser.py` → `html_parser_sold.py`
- [ ] Add sale date extraction functions to parser
- [ ] Test sale date extraction on sample sold listing HTML

### Phase 2: URL Extraction (Day 1-2)
- [ ] Create `list_page_scraper_sold.py` based on for-sale version
- [ ] Update URLs to sold-listings format
- [ ] Implement suburb-grouped URL extraction
- [ ] Test on 1-2 suburbs first
- [ ] Verify URL extraction accuracy

### Phase 3: Property Detail Scraping (Day 2-3)
- [ ] Create `property_detail_scraper_sold.py`
- [ ] Integrate `html_parser_sold.py`
- [ ] Add suburb tracking to output
- [ ] Test on small sample (5-10 properties)
- [ ] Verify sale date extraction works
- [ ] Validate all data fields populated correctly

### Phase 4: MongoDB Integration (Day 3-4)
- [ ] Create `mongodb_uploader_sold.py`
- [ ] Implement stop condition A (sale date check)
- [ ] Implement stop condition B (duplicate check)
- [ ] Create indexes on new collection
- [ ] Test stop conditions with mock data
- [ ] Test with real data from 1 suburb

### Phase 5: Orchestration & Testing (Day 4-5)
- [ ] Create `process_sold_properties.sh`
- [ ] Test full pipeline on 1 suburb
- [ ] Verify stop conditions trigger correctly
- [ ] Test all 5 suburbs sequentially
- [ ] Monitor for edge cases

### Phase 6: Production Deployment (Day 5)
- [ ] Create `check_mongodb_status_sold.py` for monitoring
- [ ] Add logging and error handling
- [ ] Create usage documentation
- [ ] Run full production scrape
- [ ] Validate data quality in MongoDB

---

## 📊 Expected Outcomes

### Data Volume Estimates
- **Robina:** ~50-100 properties (7 pages)
- **Mudgeeraba:** ~30-60 properties (5 pages)
- **Varsity Lakes:** ~40-80 properties (4 pages)
- **Reedy Creek:** ~15-30 properties (2 pages)
- **Burleigh Waters:** ~40-80 properties (4 pages)

**Total Expected:** 175-350 properties (depending on stop conditions)

### Stop Condition Scenarios

**Scenario 1: Fresh Database**
- All properties are new
- Stop when 3 consecutive properties >6 months old
- Expected: Maximum data collection

**Scenario 2: Subsequent Runs**
- Many properties already in database
- Stop when 3 consecutive duplicates found
- Expected: Only new sales added (incremental updates)

**Scenario 3: Mixed**
- Some new, some duplicates, some old
- Whichever stop condition triggers first
- Expected: Efficient incremental updates

---

## 🚨 Edge Cases & Error Handling

### 1. Missing Sale Date
**Problem:** Property page doesn't contain sale date  
**Solution:** 
- Log warning
- Skip property (don't add to database)
- Continue to next property
- Don't count toward stop conditions

### 2. Invalid Sale Date Format
**Problem:** Sale date in unexpected format  
**Solution:**
- Try multiple parsing strategies
- If all fail, log error and skip
- Don't count toward stop conditions

### 3. Network Errors
**Problem:** Page fails to load  
**Solution:**
- Retry up to 3 times with exponential backoff
- If still fails, log error and continue
- Don't count toward stop conditions

### 4. Duplicate Addresses with Different Sale Dates
**Problem:** Same property sold multiple times  
**Solution:**
- Use address as unique key
- Update with most recent sale date
- Keep history in `last_updated` field

### 5. Stop Condition False Positives
**Problem:** Stop condition triggers too early  
**Solution:**
- Require 3 consecutive (not just 3 total)
- Reset counters when valid property found
- Log all stop condition checks for debugging

---

## 🔍 Testing Strategy

### Unit Tests
```python
# test_sale_date_extraction.py
def test_extract_sale_date_from_json_ld():
    html = load_sample_html('sold_property_1.html')
    sale_date = extract_sale_date(html)
    assert sale_date == '2024-11-15'

def test_is_within_6_months():
    recent_date = '2024-12-01'
    old_date = '2024-01-01'
    assert is_within_6_months(recent_date) == True
    assert is_within_6_months(old_date) == False

def test_stop_condition_sale_date():
    # Mock 3 consecutive old properties
    properties = [
        {'sale_date': '2024-01-01'},
        {'sale_date': '2024-02-01'},
        {'sale_date': '2024-03-01'},
    ]
    uploader = SoldPropertyUploader()
    count, reason = uploader.upload_suburb_properties('test', properties)
    assert 'STOP: 3 consecutive' in reason
```

### Integration Tests
1. **Single Suburb Test:** Run full pipeline on Reedy Creek (smallest)
2. **Stop Condition Test:** Manually verify stop triggers work
3. **Duplicate Test:** Run twice, verify second run stops early
4. **Full Pipeline Test:** Run all 5 suburbs, verify data quality

---

## 📈 Monitoring & Maintenance

### Daily Monitoring
- Check `sold_last_6_months` collection count
- Review logs for errors
- Verify no properties with missing sale dates

### Weekly Maintenance
- Run scraper to catch new sales
- Review stop condition logs
- Clean up old temporary files

### Monthly Review
- Analyze data quality
- Update suburb URLs if needed
- Review and optimize stop condition thresholds

---

## 🎓 Key Learnings from For-Sale Scraper

### What Worked Well
✅ Selenium for reliable JavaScript execution  
✅ BeautifulSoup for HTML parsing  
✅ JSON-LD extraction for structured data  
✅ Modular pipeline (URLs → Details → Upload)  
✅ MongoDB with unique address index  

### Adaptations for Sold Scraper
🔄 Add sale date extraction (critical new field)  
🔄 Implement stop conditions (new logic)  
🔄 Process suburbs sequentially (not parallel)  
🔄 Separate collection (`sold_last_6_months`)  
🔄 Track suburb source for each property  

---

## 📚 Documentation Deliverables

1. **DEVELOPMENT_PLAN.md** (this document)
2. **USAGE_GUIDE.md** - How to run the scraper
3. **DATA_SCHEMA.md** - MongoDB collection schema
4. **STOP_CONDITIONS.md** - Detailed stop logic explanation
5. **TROUBLESHOOTING.md** - Common issues and solutions

---

## ✅ Success Criteria

The sold properties scraper will be considered successful when:

1. ✅ All 5 suburbs can be scraped without errors
2. ✅ Sale dates are extracted for >95% of properties
3. ✅ Stop condition A (6 months) triggers correctly
4. ✅ Stop condition B (duplicates) triggers correctly
5. ✅ Data is stored in `sold_last_6_months` collection
6. ✅ Subsequent runs only add new properties (incremental)
7. ✅ Full pipeline completes in <30 minutes
8. ✅ No duplicate addresses in database
9. ✅ All required fields populated for each property
10. ✅ System can run unattended (cron job ready)

---

## 🚀 Future Enhancements

### Phase 2 Features (Post-MVP)
- [ ] Email notifications when scraper completes
- [ ] Slack/Discord integration for alerts
- [ ] Price trend analysis (compare sold vs listed price)
- [ ] Days on market statistics
- [ ] Suburb comparison reports
- [ ] Export to CSV/Excel for analysis
- [ ] Web dashboard for viewing sold properties
- [ ] Automated weekly scraping via cron

### Advanced Features
- [ ] Machine learning price prediction
- [ ] Market trend analysis
- [ ] Suburb heat maps
- [ ] Integration with for-sale data for transition tracking
- [ ] Historical price tracking over time

---

## 📞 Support & Contact

**Developer:** Property Data Scraping Team  
**Documentation:** `/02_Domain_Scaping/Sold_In_Last_6_Months/`  
**Reference:** `/00_Run_Commands/01_Scraping_For_Sale_Properties_04122025.md`

---

**END OF DEVELOPMENT PLAN**
