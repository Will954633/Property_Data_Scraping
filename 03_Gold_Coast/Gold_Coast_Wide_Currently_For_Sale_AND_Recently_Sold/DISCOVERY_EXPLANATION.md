# Property Discovery Explanation
**Last Updated:** 31/01/2026, 9:33 am (Brisbane Time)

## How the 47 Robina Properties Were Identified

### Source: Existing Database

The 47 properties came from your **existing** `property_data.properties_for_sale` collection:

```bash
mongosh mongodb://127.0.0.1:27017/property_data --eval \
  "db.properties_for_sale.find({suburb: 'Robina'}, {listing_url: 1}).toArray()"
```

**Result:** 47 Robina property URLs that were previously scraped by your old (visible browser) system.

## Current Test Setup

### What's Happening Now:

```
┌─────────────────────────────────────────────────────────────┐
│ CURRENT TEST (Validation Only)                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Existing DB          Headless Scraper        New DB        │
│  ┌──────────┐        ┌──────────────┐      ┌──────────┐   │
│  │ property │        │   Headless   │      │  Gold    │   │
│  │  _data   │───────>│   Chrome     │─────>│  Coast   │   │
│  │          │ 47 URLs│   Scraper    │      │Currently │   │
│  │properties│        │              │      │For_Sale  │   │
│  │_for_sale │        │  + MongoDB   │      │          │   │
│  └──────────┘        └──────────────┘      └──────────┘   │
│                                                              │
│  Purpose: Validate headless scraper matches existing data   │
└─────────────────────────────────────────────────────────────┘
```

### What's NOT Happening:

❌ **Property Discovery** - Not discovering new listings from Domain.com.au
❌ **Search Page Scraping** - Not scraping search results pages
❌ **URL Extraction** - Not extracting URLs from search pages

## Complete Pipeline (What We Need to Build)

### Full End-to-End Process:

```
┌─────────────────────────────────────────────────────────────────────┐
│ COMPLETE HEADLESS PIPELINE (To Be Built)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: DISCOVER          Step 2: SCRAPE         Step 3: STORE    │
│  ┌──────────────┐         ┌──────────────┐      ┌──────────┐      │
│  │ Domain.com.au│         │   Headless   │      │  Gold    │      │
│  │ Search Pages │────────>│   Chrome     │─────>│  Coast   │      │
│  │              │ Extract │   Scraper    │      │Currently │      │
│  │ /sale/robina │  URLs   │              │      │For_Sale  │      │
│  │ /sale/varsity│         │  + MongoDB   │      │          │      │
│  │ /sale/...    │         │  + Change    │      │ .robina  │      │
│  └──────────────┘         │    Tracking  │      │ .varsity │      │
│                           └──────────────┘      │ ...      │      │
│  Headless List Scraper    Detail Scraper        └──────────┘      │
│  (TO BE CREATED)          (✅ WORKING)                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Existing Discovery Component

Your codebase already has a discovery component:

**File:** `07_Undetectable_method/Simple_Method/list_page_scraper_forsale.py`

**What it does:**
1. Loads Domain.com.au search pages (e.g., `/sale/robina-qld-4226/house/`)
2. Extracts all listing URLs from the page
3. Saves to JSON file

**Current limitation:** Runs in **visible browser mode** (not headless)

**URLs it scrapes:**
```python
URLS = [
    "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0",
    "https://www.domain.com.au/sale/mudgeeraba-qld-4213/house/?excludeunderoffer=1&ssubs=0",
    "https://www.domain.com.au/sale/varsity-lakes-qld-4227/house/?excludeunderoffer=1&ssubs=0",
    # ... etc
]
```

## What Needs to Be Added

### Option 1: Convert Existing List Scraper to Headless

**Modify:** `list_page_scraper_forsale.py`
- Change to headless mode (5 minutes)
- Keep same URL extraction logic
- Output: JSON file with all current for-sale URLs

### Option 2: Create New Headless Discovery Script

**New file:** `headless_list_page_scraper.py`
- Headless Chrome
- Scrapes Domain.com.au search pages
- Extracts listing URLs
- Feeds directly to detail scraper

### Option 3: Integrated Discovery + Scraping

**New file:** `headless_forsale_complete_pipeline.py`
- Discovers properties from search pages (headless)
- Scrapes each property (headless)
- Writes to MongoDB
- All in one script

## Current Test Purpose

**Why we're using existing URLs:**

1. **Validation** - Compare headless scraper output with known good data
2. **Baseline** - Ensure headless scraper matches existing system
3. **Testing** - Verify MongoDB integration works correctly

**Once validated, we'll add discovery to make it autonomous.**

## Summary

**47 Properties Source:** Your existing `property_data.properties_for_sale` collection (Robina suburb)

**Current Test:** Validation test - re-scraping known properties in headless mode

**Missing Component:** Headless discovery (scraping search pages to find new listings)

**Next Step After Validation:** Add headless discovery component for complete autonomous pipeline

---

**The current test is running to prove the headless scraper works correctly. Once complete, we'll add the discovery component to make it fully autonomous.**
