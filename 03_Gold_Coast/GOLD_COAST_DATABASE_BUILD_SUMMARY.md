# Gold Coast Database Build Summary
**Last Updated:** 30/01/2026, 6:56 pm (Brisbane Time)

## Database Overview
- **Database Name:** `Gold_Coast`
- **MongoDB URI:** `mongodb://127.0.0.1:27017/`
- **Total Records:** ~331,224 addresses across 81 suburbs
- **Organization:** One collection per suburb, one document per address

---

## Core Scripts That Built the Database

### 1. **Base Address Import** (STEP 1)
**Script:** `gold_coast_importer.py`
- **Purpose:** Imports all Gold Coast addresses from Queensland property location data
- **Source Data:** `/Users/projects/Documents/Fetcha_Addresses/QLD/DP_PROP_LOCATION_INDEX_QLD_20251103.txt`
- **What it creates:** 81 suburb collections with 24 base fields per address
- **Run Command:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 gold_coast_importer.py
```

**Base Fields Added (24 total):**
- ADDRESS_PID, PLAN, LOT, LOTPLAN_STATUS, ADDRESS_STATUS, ADDRESS_STANDARD
- UNIT_TYPE, UNIT_NUMBER, UNIT_SUFFIX, PROPERTY_NAME
- STREET_NO_1, STREET_NO_1_SUFFIX, STREET_NO_2, STREET_NO_2_SUFFIX
- STREET_NAME, STREET_TYPE, STREET_SUFFIX
- LOCALITY, LOCAL_AUTHORITY, LGA_CODE
- LATITUDE, LONGITUDE, GEOCODE_TYPE, DATUM

---

### 2. **Cadastral Data Enrichment** (STEP 2)
**Script:** `enrich_cadastral_data.py`
- **Purpose:** Adds property details from QLD Spatial GIS API
- **API:** Queensland Spatial GIS API (Land Parcel Property Framework)
- **Run Command:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 enrich_cadastral_data.py
```

**Fields Added (20 total):**
- lot, plan, lotplan, lot_area ⭐, excl_area, lot_volume
- tenure, cover_typ, parcel_typ, acc_code, surv_ind
- feat_name, alias_name, shire_name, smis_map
- API_address, API_street_full, API_floor_number, API_floor_type, API_floor_suffix
- enriched_at, enriched_source

---

### 3. **Postcode Enrichment** (STEP 3)
**Script:** `enrich_postcodes.py` or `enrich_postcodes_optimized.py`
- **Purpose:** Adds postcode data to addresses
- **Run Command:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 enrich_postcodes_optimized.py
```

**Field Added:**
- POSTCODE

---

### 4. **Domain Property Scraping** (STEP 4 - MAIN DATA ENRICHMENT)
**Script:** `domain_scraper_multi_suburb_mongodb.py`
- **Purpose:** Scrapes property data from Domain.com.au and adds to MongoDB
- **What it adds:** Property timeline, images, features, valuations, rental estimates
- **Run Command:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 domain_scraper_multi_suburb_mongodb.py
```

**Fields Added (nested under `scraped_data`):**
- **url:** Domain listing URL
- **address:** Formatted address
- **scraped_at:** Timestamp
- **features:** {bedrooms, bathrooms, car_spaces, land_size, property_type}
- **valuation:** {low, mid, high, accuracy, date}
- **rental_estimate:** {weekly_rent, yield}
- **property_timeline:** [array of timeline events] ⭐
- **images:** [array of image objects with url, index, date] ⭐
- **address_pid, suburb, worker_id**

**Timeline Event Structure:**
```javascript
{
  date: "2025-11-03",
  month_year: "Nov 2025",
  category: "listing",
  type: "For Sale",
  price: 1530000,
  days_on_market: 35,
  is_major_event: true,
  agency_name: "Gold Coast Property Sales",
  agency_url: "...",
  is_sold: false
}
```

**Image Structure:**
```javascript
{
  url: "https://bucket-api.domain.com.au/...",
  index: 0,
  date: "2025-11-03"
}
```

---

## Complete Data Pipeline Sequence

```
STEP 1: Base Import
↓
gold_coast_importer.py
→ Creates 81 suburb collections
→ Adds 24 base address fields
→ ~331,224 documents

STEP 2: Cadastral Enrichment
↓
enrich_cadastral_data.py
→ Queries QLD Spatial GIS API
→ Adds 20 property/cadastral fields
→ Includes lot_area, tenure, parcel_typ

STEP 3: Postcode Enrichment
↓
enrich_postcodes_optimized.py
→ Adds POSTCODE field

STEP 4: Domain Scraping (MAIN ENRICHMENT)
↓
domain_scraper_multi_suburb_mongodb.py
→ Scrapes Domain.com.au
→ Adds scraped_data object with:
  - property_timeline ⭐
  - images ⭐
  - features, valuation, rental_estimate
```

---

## Document Structure After All Steps

```javascript
{
  // BASE FIELDS (24) - from gold_coast_importer.py
  "ADDRESS_PID": 123456,
  "LOT": "12",
  "PLAN": "SP123456",
  "STREET_NO_1": "12",
  "STREET_NAME": "CARNOUSTIE",
  "STREET_TYPE": "COURT",
  "LOCALITY": "ROBINA",
  "LATITUDE": -28.0710063,
  "LONGITUDE": 153.4033753,
  // ... other base fields
  
  // POSTCODE ENRICHMENT (1) - from enrich_postcodes.py
  "POSTCODE": "4226",
  
  // CADASTRAL ENRICHMENT (20) - from enrich_cadastral_data.py
  "lot_area": 819,
  "tenure": "Freehold",
  "cover_typ": "Base",
  "parcel_typ": "Lot Type Parcel",
  "enriched_at": "2025-01-15T10:30:00",
  "enriched_source": "QLD_Spatial_GIS_API",
  // ... other cadastral fields
  
  // DOMAIN SCRAPING DATA - from domain_scraper_multi_suburb_mongodb.py
  "scraped_data": {
    "url": "https://www.domain.com.au/property-profile/...",
    "address": "12 Carnoustie Court Robina QLD 4226",
    "scraped_at": "2025-11-03T17:10:00",
    
    "features": {
      "bedrooms": 4,
      "bathrooms": 2,
      "car_spaces": 2,
      "land_size": 819,
      "property_type": "House"
    },
    
    "valuation": {
      "low": 1400000,
      "mid": 1530000,
      "high": 1650000,
      "accuracy": "high",
      "date": "2025-11-03"
    },
    
    "rental_estimate": {
      "weekly_rent": 850,
      "yield": 2.9
    },
    
    "property_timeline": [
      {
        "date": "2025-11-03",
        "month_year": "Nov 2025",
        "category": "listing",
        "type": "For Sale",
        "price": 1530000,
        "days_on_market": 35,
        "is_major_event": true,
        "agency_name": "Gold Coast Property Sales",
        "is_sold": false
      }
      // ... more timeline events
    ],
    
    "images": [
      {
        "url": "https://bucket-api.domain.com.au/v1/bucket/image/...",
        "index": 0,
        "date": "2025-11-03"
      }
      // ... more images
    ]
  },
  
  "scraped_at": "2025-11-03T17:10:00"
}
```

---

## Update Strategy Recommendations

### YOUR REQUIREMENTS:
1. **Update database periodically with fresh data**
2. **Replace `property_timeline` field** (timeline changes over time)
3. **Replace `images` field** (images may change)
4. **Preserve historical `rental_estimate`** (track changes over time)
5. **Preserve historical `valuation`** (track changes over time)

### RECOMMENDED APPROACH:

#### Option A: **Incremental Update Script** (RECOMMENDED)
Create a new script: `update_gold_coast_database.py`

**What it does:**
1. Re-runs Domain scraper for all properties
2. **Replaces** `property_timeline` and `images` with fresh data
3. **Appends** new `rental_estimate` and `valuation` to history arrays
4. Preserves all other fields

**New Document Structure:**
```javascript
{
  // ... all existing fields ...
  
  "scraped_data": {
    // ... other fields ...
    
    // REPLACED FIELDS (always current)
    "property_timeline": [ /* fresh timeline */ ],
    "images": [ /* fresh images */ ],
    
    // HISTORICAL FIELDS (append-only)
    "rental_estimate_history": [
      {
        "weekly_rent": 800,
        "yield": 2.7,
        "date": "2025-01-15T10:00:00"
      },
      {
        "weekly_rent": 850,
        "yield": 2.9,
        "date": "2025-11-03T17:10:00"
      }
    ],
    
    "valuation_history": [
      {
        "low": 1350000,
        "mid": 1450000,
        "high": 1550000,
        "accuracy": "high",
        "date": "2025-01-15T10:00:00"
      },
      {
        "low": 1400000,
        "mid": 1530000,
        "high": 1650000,
        "accuracy": "high",
        "date": "2025-11-03T17:10:00"
      }
    ]
  }
}
```

#### Option B: **Complete Rebuild** (SIMPLER BUT LOSES HISTORY)
- Drop database
- Re-run all 4 steps
- **Pros:** Clean, simple
- **Cons:** Loses all historical valuation/rental data

---

## Recommended Update Script Pseudocode

```python
# update_gold_coast_database.py

for each suburb_collection in database:
    for each property in suburb_collection:
        # 1. Scrape fresh data from Domain
        fresh_data = scrape_domain(property.address)
        
        # 2. Replace timeline and images
        property.scraped_data.property_timeline = fresh_data.property_timeline
        property.scraped_data.images = fresh_data.images
        
        # 3. Append rental_estimate to history
        if fresh_data.rental_estimate != property.scraped_data.rental_estimate:
            property.scraped_data.rental_estimate_history.append({
                **fresh_data.rental_estimate,
                "date": datetime.now()
            })
            property.scraped_data.rental_estimate = fresh_data.rental_estimate
        
        # 4. Append valuation to history
        if fresh_data.valuation != property.scraped_data.valuation:
            property.scraped_data.valuation_history.append({
                **fresh_data.valuation,
                "date": datetime.now()
            })
            property.scraped_data.valuation = fresh_data.valuation
        
        # 5. Update scraped_at timestamp
        property.scraped_at = datetime.now()
        
        # 6. Save to MongoDB
        save_to_mongodb(property)
```

---

## Summary

**Core Scripts (in order):**
1. `gold_coast_importer.py` - Base addresses (24 fields)
2. `enrich_cadastral_data.py` - Cadastral data (20 fields)
3. `enrich_postcodes_optimized.py` - Postcodes (1 field)
4. `domain_scraper_multi_suburb_mongodb.py` - Domain data (timeline, images, features, valuations)

**To Update Database:**
- Create `update_gold_coast_database.py` that:
  - Replaces: `property_timeline`, `images`
  - Preserves history: `rental_estimate_history`, `valuation_history`
  - Re-runs Domain scraper for all properties
  - Updates timestamps

**Frequency:** Run monthly or quarterly to keep data fresh
