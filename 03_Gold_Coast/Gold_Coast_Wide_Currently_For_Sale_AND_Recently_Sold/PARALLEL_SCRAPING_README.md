# Parallel Suburb Scraping Implementation
**Last Updated: 31/01/2026, 11:05 am (Brisbane Time)**

## Overview

This implementation enables simultaneous scraping of multiple suburbs using parallel processing. Each suburb runs in its own process with a dedicated browser instance, significantly reducing total scraping time.

## New Files Created

### 1. `clear_collections.py`
**Purpose:** Clear MongoDB collections before fresh scraping

**Features:**
- Clear specific suburb collections
- Clear all collections (with caution)
- List all available collections
- Confirmation prompts for safety
- Verification of successful deletion

**Usage:**
```bash
# Clear specific suburbs
python3 clear_collections.py --suburbs robina varsity_lakes

# List all collections
python3 clear_collections.py --list

# Clear all collections (dangerous!)
python3 clear_collections.py --all

# Skip confirmation (for automation)
python3 clear_collections.py --suburbs robina --no-confirm
```

### 2. `run_parallel_suburb_scrape.py`
**Purpose:** Process multiple suburbs simultaneously using multiprocessing

**Features:**
- Parallel processing (one process per suburb)
- Each suburb gets dedicated browser instance
- Real-time progress monitoring across all processes
- Consolidated final summary
- All existing functionality preserved:
  - Agent carousel capture (24 seconds per property)
  - First listed date extraction
  - Days on Domain calculation
  - Change tracking
  - MongoDB integration

**Usage:**
```bash
# Scrape Robina and Varsity Lakes simultaneously
python3 run_parallel_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227"

# Add more suburbs
python3 run_parallel_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227" "Burleigh Heads:4220"
```

**Architecture:**
```
Main Process
├── Progress Monitor (tracks all suburbs)
├── Process 1: Robina
│   ├── Browser Instance 1
│   ├── Discovery Phase
│   └── Scraping Phase
└── Process 2: Varsity Lakes
    ├── Browser Instance 2
    ├── Discovery Phase
    └── Scraping Phase
```

### 3. `run_robina_varsity_lakes_scrape.sh`
**Purpose:** Complete workflow automation script

**Features:**
- Step 1: Clear existing collections
- Step 2: Run parallel scraping
- Step 3: Display final results
- Error handling
- Colored output for clarity

**Usage:**
```bash
# Run complete workflow
bash run_robina_varsity_lakes_scrape.sh

# Or with explicit path
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold
bash run_robina_varsity_lakes_scrape.sh
```

## Quick Start Guide

### Option 1: Complete Automated Workflow (Recommended)
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold
bash run_robina_varsity_lakes_scrape.sh
```

This will:
1. Clear robina and varsity_lakes collections
2. Scrape both suburbs in parallel
3. Display final summary

### Option 2: Manual Step-by-Step
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold

# Step 1: Clear collections
python3 clear_collections.py --suburbs robina varsity_lakes

# Step 2: Run parallel scraping
python3 run_parallel_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227"
```

## Data Structure

### MongoDB Database
- **Database:** `Gold_Coast_Currently_For_Sale`
- **Collections:** One per suburb (e.g., `robina`, `varsity_lakes`)

### Document Schema
Each property document includes:
```javascript
{
  // Basic Info
  listing_url: "https://www.domain.com.au/...",
  address: "123 Main St, Robina, QLD 4226",
  suburb: "Robina",
  
  // Property Details
  bedrooms: 4,
  bathrooms: 2,
  parking: 2,
  property_type: "House",
  land_size: "450 sqm",
  
  // Pricing
  price: "$850,000",
  
  // Listing Information
  first_listed_date: "15 January",
  first_listed_year: 2026,
  first_listed_full: "15 January 2026",
  first_listed_timestamp: "2026-01-15T10:30:00",
  days_on_domain: 16,
  last_updated_date: "20 January",
  
  // Agent Information (captured from carousel)
  agent_names: ["John Smith", "Jane Doe"],
  agent_name: "John Smith, Jane Doe",
  agency: "Ray White Robina",
  
  // Images
  property_images: [...],
  
  // Metadata
  scrape_mode: "headless",
  extraction_method: "HTML",
  extraction_date: "2026-01-31T11:05:00",
  source: "parallel_suburb_scraper",
  first_seen: ISODate("2026-01-31T11:05:00"),
  last_updated: ISODate("2026-01-31T11:05:00"),
  
  // Change Tracking
  change_count: 0,
  history: {
    price: [{value: "$850,000", recorded_at: ISODate("...")}],
    inspection_times: [...],
    agents_description: [...]
  },
  
  // Enrichment (for future processing)
  enriched: false,
  enrichment_attempted: false,
  enrichment_retry_count: 0,
  enrichment_error: null,
  enrichment_data: null,
  last_enriched: null,
  image_analysis: []
}
```

## Performance Benefits

### Sequential vs Parallel Processing

**Sequential (Old Method):**
- Robina: ~2 hours
- Varsity Lakes: ~1.5 hours
- **Total: ~3.5 hours**

**Parallel (New Method):**
- Both suburbs run simultaneously
- **Total: ~2 hours** (time of longest suburb)
- **Time Saved: ~1.5 hours (43% faster)**

### Timing Per Property
- Discovery: ~5 seconds per page
- Property scraping: ~40 seconds per property
  - Page load: 5 seconds
  - Agent carousel capture: 24 seconds (3 snapshots × 12 seconds)
  - HTML parsing: ~1 second
  - MongoDB save: <1 second
  - Delay between properties: 2 seconds

## Monitoring Progress

### Real-Time Output
The parallel scraper provides real-time updates:
```
[Robina] Process started (PID: 12345)
[Varsity Lakes] Process started (PID: 12346)

MONITORING PROGRESS
================================================================================

[Robina] Discovery: 156 URLs found
[Varsity Lakes] Discovery: 98 URLs found
[Robina] Progress: 5/156 (5 successful)
[Varsity Lakes] Progress: 5/98 (5 successful)
[Robina] Progress: 10/156 (10 successful)
...
[Varsity Lakes] ✅ COMPLETE
[Robina] ✅ COMPLETE
```

### MongoDB Verification
```bash
# Connect to MongoDB
mongosh

# Switch to database
use Gold_Coast_Currently_For_Sale

# Check document counts
db.robina.countDocuments({})
db.varsity_lakes.countDocuments({})

# View sample document
db.robina.findOne()

# Check for properties with listing dates
db.robina.find({first_listed_date: {$exists: true}}).count()

# Check for properties with multiple agents
db.robina.find({agent_names: {$size: 2}}).count()
```

## New Functionality Captured

Since the last scrape, these features have been added:

1. **First Listed Date Extraction**
   - Extracts "First listed on DD Month" from property pages
   - Captures from `dateListed` JSON field (most reliable)
   - Calculates days on Domain
   - Stores multiple date formats for flexibility

2. **Enhanced Agent Capture**
   - Waits 24 seconds to capture agent carousel rotation
   - Takes 3 snapshots (0s, 12s, 24s)
   - Captures all agents listed on property
   - Stores as array and comma-separated string

3. **Last Updated Date**
   - Captures "last updated on DD Month" if available
   - Useful for tracking listing modifications

## Troubleshooting

### Issue: Collections not clearing
```bash
# Check MongoDB connection
mongosh
use Gold_Coast_Currently_For_Sale
show collections

# Manually clear if needed
db.robina.deleteMany({})
db.varsity_lakes.deleteMany({})
```

### Issue: Parallel processes hanging
```bash
# Check running processes
ps aux | grep python3

# Kill if needed
pkill -f "run_parallel_suburb_scrape.py"
```

### Issue: ChromeDriver errors
```bash
# Update ChromeDriver
pip3 install --upgrade webdriver-manager

# Or manually install
brew install chromedriver
```

### Issue: MongoDB connection timeout
```bash
# Check MongoDB is running
brew services list | grep mongodb

# Start MongoDB if needed
brew services start mongodb-community
```

## Extending to More Suburbs

### Add More Suburbs to Parallel Processing
```bash
# Edit run_robina_varsity_lakes_scrape.sh
# Change the suburbs line to:
python3 run_parallel_suburb_scrape.py --suburbs \
  "Robina:4226" \
  "Varsity Lakes:4227" \
  "Burleigh Heads:4220" \
  "Mermaid Beach:4218"
```

### Process Limits
- **Recommended:** 2-4 suburbs simultaneously
- **Maximum:** Limited by system resources (CPU, RAM, network)
- Each process uses:
  - ~500MB RAM (Chrome browser)
  - 1 CPU core
  - Network bandwidth for requests

## Integration with Existing Systems

### Floor Plan Enrichment
After scraping, run enrichment:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/01.1_Floor_Plan_Data
python3 run_production.py
```

### Change Monitoring
The scraper tracks changes in:
- Price
- Inspection times
- Agent descriptions

Re-run scraping periodically to capture changes:
```bash
# Weekly update (keeps existing data, updates changes)
bash run_robina_varsity_lakes_scrape.sh
```

## Files Modified

No existing files were modified. All changes are in new files:
- `clear_collections.py` (new)
- `run_parallel_suburb_scrape.py` (new)
- `run_robina_varsity_lakes_scrape.sh` (new)
- `PARALLEL_SCRAPING_README.md` (new)

## Backward Compatibility

The original scripts remain unchanged and functional:
- `run_complete_suburb_scrape.py` - Single suburb scraping
- `headless_forsale_mongodb_scraper.py` - Original scraper

Use these if you need to:
- Process a single suburb
- Debug issues
- Test new functionality

## Summary

✅ **Created:**
- Collection clearing utility
- Parallel suburb scraper
- Automated workflow script
- Comprehensive documentation

✅ **Benefits:**
- 43% faster scraping (parallel processing)
- Fresh data with new functionality
- Easy to extend to more suburbs
- Safe collection clearing with confirmation

✅ **Ready to Use:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold
bash run_robina_varsity_lakes_scrape.sh
```
