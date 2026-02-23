# Sold Properties Scraper - Complete Workflow Explanation

**Created:** 15 December 2025  
**Purpose:** Explain the two-stage scraping process for sold properties

---

## 🎯 Overview

This scraper uses a **two-stage workflow** similar to the for-sale properties scraper:

1. **Stage 1:** Extract property URLs from listing pages
2. **Stage 2:** Visit each property URL and scrape detailed data

This approach is necessary because Domain.com.au listing pages only show summary cards, while the full property data (including sale dates, descriptions, images, etc.) is only available on individual property detail pages.

---

## 📋 Stage 1: List Page Scraping

### Script: `list_page_scraper_sold.py`

### What It Does

Visits the sold listing pages you provided (e.g., `https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1`) and extracts the URLs of individual properties.

### Input URLs (Listing Pages)

```
Robina (7 pages):
  https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1
  https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1&page=2
  ... (pages 3-7)

Mudgeeraba (5 pages):
  https://www.domain.com.au/sold-listings/mudgeeraba-qld-4213/house/?excludepricewithheld=1
  ... (pages 2-5)

Varsity Lakes (4 pages):
  https://www.domain.com.au/sold-listings/varsity-lakes-qld-4227/house/?excludepricewithheld=1
  ... (pages 2-4)

Reedy Creek (2 pages):
  https://www.domain.com.au/sold-listings/reedy-creek-qld-4227/house/?excludepricewithheld=1
  ... (page 2)

Burleigh Waters (4 pages):
  https://www.domain.com.au/sold-listings/burleigh-waters-qld-4220/house/?excludepricewithheld=1
  ... (pages 2-4)
```

### Process

1. Opens each listing page with Selenium
2. Scrolls to load lazy-loaded content
3. Extracts HTML
4. Parses HTML to find property URLs (pattern: `/property-name-12345678`)
5. Saves all URLs to JSON file

### Output

**File:** `listing_results_sold/sold_property_urls_TIMESTAMP.json`

```json
{
  "timestamp": "2025-12-15T11:30:00",
  "property_type": "SOLD",
  "target_period": "Last 6 Months",
  "total_count": 250,
  "urls": [
    "https://www.domain.com.au/15-example-street-robina-qld-4226-2019123456",
    "https://www.domain.com.au/22-another-road-robina-qld-4226-2019234567",
    ...
  ]
}
```

### Example Output

```
Robina: 85 property URLs
Mudgeeraba: 45 property URLs
Varsity Lakes: 60 property URLs
Reedy Creek: 25 property URLs
Burleigh Waters: 55 property URLs
---
Total: 270 unique property URLs
```

---

## 📋 Stage 2: Property Detail Scraping

### Script: `property_detail_scraper_sold.py`

### What It Does

Takes the URLs from Stage 1 and visits **each individual property page** to extract complete data including:
- Sale date (CRITICAL)
- Sale price
- Bedrooms, bathrooms, parking
- Property description
- All images and floor plans
- Agent information
- Property features

### Input

The JSON file from Stage 1 containing property URLs.

### Process (Per Suburb)

```
For each suburb (Robina, Mudgeeraba, etc.):
  Initialize counters:
    consecutive_old_sales = 0
    consecutive_duplicates = 0
  
  For each property URL in this suburb:
    1. Visit property detail page with Selenium
    2. Extract HTML
    3. Parse HTML to extract ALL property data
    4. Extract sale_date (CRITICAL)
    
    5. Check Stop Condition A (Sale Date):
       If sale_date > 6 months ago:
         consecutive_old_sales++
         If consecutive_old_sales >= 3:
           STOP this suburb, move to next
       Else:
         consecutive_old_sales = 0
    
    6. Check Stop Condition B (Duplicate):
       If property already in database:
         consecutive_duplicates++
         If consecutive_duplicates >= 3:
           STOP this suburb, move to next
       Else:
         consecutive_duplicates = 0
    
    7. Save property data to JSON file
  
  Move to next suburb (reset counters)
```

### Output

**Directory:** `property_data/`

Individual JSON files for each property:
```
property_data/
├── robina_property_1_2019123456.json
├── robina_property_2_2019234567.json
├── mudgeeraba_property_1_2019345678.json
└── ...
```

**Each file contains:**
```json
{
  "address": "15 Example Street, Robina QLD 4226",
  "sale_date": "2024-11-20",
  "sale_price": "$875,000",
  "bedrooms": 4,
  "bathrooms": 2,
  "carspaces": 2,
  "property_type": "House",
  "land_size_sqm": 450,
  "description": "Beautiful family home...",
  "property_images": [
    "https://bucket-api.domain.com.au/v1/bucket/image/...",
    ...
  ],
  "floor_plans": [
    "https://bucket-api.domain.com.au/v1/bucket/image/..."
  ],
  "features": ["Pool", "Air conditioning", ...],
  "listing_url": "https://www.domain.com.au/15-example-street-robina-qld-4226-2019123456",
  "extraction_date": "2025-12-15T12:00:00",
  "suburb_scraped": "robina"
}
```

---

## 📋 Stage 3: MongoDB Upload

### Script: `mongodb_uploader_sold.py`

### What It Does

Reads all the JSON files from Stage 2 and uploads them to MongoDB collection `sold_last_6_months`.

### Process

1. Reads all JSON files from `property_data/`
2. For each property:
   - Checks if already exists (by address)
   - If new: Insert
   - If exists: Update with latest data
3. Adds metadata fields:
   - `first_seen`
   - `last_updated`
   - `source`

### Output

MongoDB collection `sold_last_6_months` with all property documents.

---

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: List Page Scraping                                │
│ (list_page_scraper_sold.py)                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: Listing page URLs                                  │
│  ├─ https://domain.com.au/sold-listings/robina/...         │
│  ├─ https://domain.com.au/sold-listings/mudgeeraba/...     │
│  └─ ... (22 pages total)                                   │
│                                                             │
│  Process:                                                   │
│  ├─ Open each listing page with Selenium                   │
│  ├─ Scroll to load all content                             │
│  ├─ Extract HTML                                            │
│  └─ Parse to find property URLs                            │
│                                                             │
│  Output: sold_property_urls_TIMESTAMP.json                 │
│  └─ Contains ~250-300 individual property URLs             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: Property Detail Scraping                          │
│ (property_detail_scraper_sold.py)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: Property URLs from Stage 1                         │
│                                                             │
│  Process (per suburb):                                     │
│  ├─ For each property URL:                                 │
│  │   ├─ Visit property detail page                         │
│  │   ├─ Extract complete HTML                              │
│  │   ├─ Parse ALL data (sale_date, price, beds, etc.)     │
│  │   ├─ Check stop conditions:                             │
│  │   │   ├─ 3 consecutive sales >6 months? → STOP         │
│  │   │   └─ 3 consecutive duplicates? → STOP              │
│  │   └─ Save to JSON file                                  │
│  └─ Move to next suburb                                    │
│                                                             │
│  Output: property_data/ directory                          │
│  └─ ~150-250 JSON files (one per property)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: MongoDB Upload                                    │
│ (mongodb_uploader_sold.py)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: JSON files from Stage 2                            │
│                                                             │
│  Process:                                                   │
│  ├─ Read all JSON files                                    │
│  ├─ For each property:                                     │
│  │   ├─ Check if exists in DB                              │
│  │   ├─ Insert new or update existing                      │
│  │   └─ Add metadata                                       │
│  └─ Generate upload report                                 │
│                                                             │
│  Output: MongoDB collection "sold_last_6_months"           │
│  └─ ~150-250 property documents                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Why Two Stages?

### Listing Pages Show Limited Data

The listing pages (e.g., `https://www.domain.com.au/sold-listings/robina-qld-4226/house/`) only display:
- Property address
- Price (sometimes)
- Bed/bath count
- Small thumbnail image

### Property Detail Pages Have Everything

Individual property pages (e.g., `https://www.domain.com.au/15-example-street-robina-qld-4226-2019123456`) contain:
- **Sale date** (CRITICAL - only on detail page)
- Full description
- All images (10-30 photos)
- Floor plans
- Complete features list
- Agent information
- Exact sale price
- Property history

**Therefore:** We must visit each individual property page to get the sale date and complete data.

---

## 🛑 Stop Conditions in Detail

### Why Stop Conditions?

Without stop conditions, the scraper would process ALL properties on ALL pages, including:
- Properties sold 1-2 years ago (not relevant)
- Properties already in database (wasting time)

### How They Work

**Per Suburb Processing:**
- Each suburb is processed independently
- Counters reset when moving to next suburb
- This ensures clean stop triggers

**Stop Condition A: Old Sales**
```
Property 1: Sold 2024-12-01 (within 6 months) → consecutive_old = 0
Property 2: Sold 2024-11-15 (within 6 months) → consecutive_old = 0
Property 3: Sold 2024-05-10 (>6 months) → consecutive_old = 1
Property 4: Sold 2024-04-20 (>6 months) → consecutive_old = 2
Property 5: Sold 2024-03-15 (>6 months) → consecutive_old = 3
🛑 STOP - Move to next suburb
```

**Stop Condition B: Duplicates**
```
Property 1: New → Insert → consecutive_dup = 0
Property 2: New → Insert → consecutive_dup = 0
Property 3: Exists → Update → consecutive_dup = 1
Property 4: Exists → Update → consecutive_dup = 2
Property 5: Exists → Update → consecutive_dup = 3
🛑 STOP - Move to next suburb
```

---

## 📊 Expected Timeline

### First Run (Empty Database)
- **Stage 1:** 5-10 minutes (scrape all listing pages)
- **Stage 2:** 15-25 minutes (scrape ~200-300 property details)
- **Stage 3:** 1-2 minutes (upload to MongoDB)
- **Total:** ~25-35 minutes

### Subsequent Runs (Weekly Updates)
- **Stage 1:** 5-10 minutes (same)
- **Stage 2:** 5-10 minutes (stop conditions trigger early)
- **Stage 3:** 1 minute
- **Total:** ~10-15 minutes

---

## ✅ Summary

1. **List scraper** extracts property URLs from listing pages
2. **Detail scraper** visits each property URL to get complete data
3. **Uploader** saves everything to MongoDB
4. **Stop conditions** ensure efficiency and avoid old/duplicate data
5. **Suburb-by-suburb** processing provides clean stop triggers

This two-stage approach is the same as the for-sale properties scraper and is necessary because Domain.com.au only shows complete property data (including sale dates) on individual property detail pages.

---

**END OF WORKFLOW EXPLANATION**
