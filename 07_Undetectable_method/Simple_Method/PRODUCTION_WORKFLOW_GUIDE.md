# Production Workflow Guide - MongoDB Integration

Complete guide for the production-ready property scraping and enrichment pipeline with automatic data quality management.

## Overview

This system provides a fully automated pipeline for:
1. Scraping properties from realestate.com.au
2. Storing in MongoDB with deduplication
3. Auto-enriching with domain.com.au data
4. Removing off-market properties
5. Cleaning up temporary files

## Quick Start

### Prerequisites

1. **MongoDB Running**
```bash
brew services start mongodb-community
```

2. **One-Time Index Setup**
```bash
cd 07_Undetectable_method/Simple_Method
python fix_mongodb_indexes.py
```

### Run Complete Pipeline

```bash
cd 07_Undetectable_method/Simple_Method
./process_all_sessions.sh
```

That's it! The pipeline handles everything automatically.

## Pipeline Steps

### Step 0: Cleanup Previous Runs
```bash
python cleanup_temp_files.py --remove
```
**What it does:**
- Removes `screenshots_session_*/` directories
- Removes `ocr_output_session_*/` directories
- Removes `property_data_session_*.json` files
- Cleans enrichment temp files

**Why:** Prevents disk space accumulation from repeated runs

### Step 1-3: Scrape & Parse
Standard scraping workflow:
1. Capture screenshots
2. Extract text via OCR
3. Parse property data

### Step 4: MongoDB Upload
```bash
python mongodb_uploader.py
```
**What it does:**
- Loads all session JSON files
- Upserts properties to MongoDB (creates or updates)
- Triggers auto-enrichment for new properties

### Step 5: Remove Duplicates
```bash
python remove_duplicates.py --remove
```
**What it does:**
- Scans for duplicate addresses
- Keeps most recently updated version
- Removes all other duplicates
- Reports what was removed

**Why:** Ensures data integrity, prevents duplicate processing

### Step 6: Enrich Properties
```bash
cd ../00_Production_System/02_Individual_Property_Google_Search
python batch_processor.py --mongodb
```
**What it does:**
- Queries MongoDB for unenriched properties
- Navigates to domain.com.au for each
- Extracts comprehensive property data
- Updates MongoDB with enriched data

**Note:** Only processes properties once (tracked via `enriched` flag)

### Step 7: Remove Off-Market Properties
```bash
python remove_offmarket_properties.py --remove
```
**What it does:**
- Identifies properties without listing URLs
- Removes them from database
- Reports what was removed

**Why:** Properties without listing URLs are not currently for sale

### Step 8: Final Status
```bash
python check_mongodb_status.py
```
**What it does:**
- Shows total properties
- Shows enriched vs unenriched count
- Lists recent additions
- Shows properties needing enrichment
- Displays failed enrichments

## Manual Operations

### Check Current Status
```bash
python check_mongodb_status.py
```

### Clean Temp Files (Dry Run First)
```bash
# See what would be deleted
python cleanup_temp_files.py

# Actually delete
python cleanup_temp_files.py --remove
```

### Find Duplicates (Dry Run First)
```bash
# See what would be removed
python remove_duplicates.py

# Actually remove
python remove_duplicates.py --remove
```

### Find Off-Market Properties (Dry Run First)
```bash
# See what would be removed
python remove_offmarket_properties.py

# Actually remove
python remove_offmarket_properties.py --remove
```

### Manual Enrichment
```bash
cd ../00_Production_System/02_Individual_Property_Google_Search
python batch_processor.py --mongodb
```

### Test Single Address
```bash
cd ../00_Production_System/02_Individual_Property_Google_Search
python batch_processor.py --address "5 Picabeen Close, Robina, QLD 4226"
```

## MongoDB Document Structure

```javascript
{
  "_id": ObjectId("..."),
  "address": "5 Picabeen Close, Robina",
  
  // Basic scraped data
  "bedrooms": 4,
  "bathrooms": 2,
  "parking": 3,
  "land_size_sqm": 459,
  "property_type": "House",
  "price": "$1,239,000",
  "agency": "Harcourts",
  "agent": "John Smith",
  
  // Enrichment tracking
  "enriched": false,
  "enrichment_attempted": false,
  "enrichment_retry_count": 0,
  "enrichment_error": null,
  
  // Timestamps
  "first_seen": ISODate("2025-11-14..."),
  "last_updated": ISODate("2025-11-14..."),
  "last_enriched": null,
  
  // Source
  "source": "process_all_sessions",
  
  // Enriched data (after enrichment)
  "enrichment_data": {
    "listing_url": "https://www.domain.com.au/...",
    "html_file": "batch_results/html/...",
    "property_data": {
      // Full property details
    }
  }
}
```

## Key Features

### ✅ Automatic Duplicate Prevention
- Unique index on `address` field
- Smart duplicate removal keeps latest version
- Runs before enrichment to avoid wasted processing

### ✅ Off-Market Detection
- Properties without listing URLs are not for sale
- Automatically removed from database
- Prevents enrichment of unavailable properties

### ✅ Temporary File Cleanup
- Automatic cleanup at pipeline start
- Prevents disk space accumulation
- Configurable (can modify cleanup targets)

### ✅ Idempotent Operations
- Safe to run pipeline multiple times
- Existing properties updated, not duplicated
- Only new properties trigger enrichment

### ✅ Error Handling
- Failed enrichments tracked with error messages
- Retry count maintained
- Can re-run enrichment for failed properties

## Troubleshooting

### MongoDB Not Running
```bash
# Check status
brew services list | grep mongodb

# Start
brew services start mongodb-community

# Test connection
mongosh
```

### Index Errors
```bash
# Fix indexes (removes old, creates new)
python fix_mongodb_indexes.py
```

### Re-enrich Failed Properties
```javascript
// In mongosh
use property_data
db.properties_for_sale.updateMany(
  { "enrichment_error": { $ne: null } },
  { $set: { "enrichment_attempted": false } }
)
```

Then run:
```bash
cd ../00_Production_System/02_Individual_Property_Google_Search
python batch_processor.py --mongodb
```

### Clear All Data (Start Fresh)
```javascript
// In mongosh
use property_data
db.properties_for_sale.deleteMany({})
```

## Automation

### Daily Scheduled Run
```bash
# Add to crontab (run daily at 8 AM)
0 8 * * * cd /path/to/07_Undetectable_method/Simple_Method && ./process_all_sessions.sh
```

### Monitor with Alerts
Set up monitoring for:
- Failed enrichments
- High duplicate count
- Low enrichment completion rate
- MongoDB connection issues

## Performance Notes

- **Scraping**: ~2-3 minutes for 3 sessions (~60 properties)
- **Enrichment**: ~30-60 seconds per property
- **Deduplication**: <1 second for <1000 properties
- **Cleanup**: <1 second

## Files Reference

### Core Scripts
- `process_all_sessions.sh` - Main pipeline orchestrator
- `mongodb_uploader.py` - Upload & trigger enrichment
- `batch_processor.py` - Property enrichment engine

### Utility Scripts
- `remove_duplicates.py` - Duplicate management
- `cleanup_temp_files.py` - Temporary file cleanup
- `remove_offmarket_properties.py` - Off-market removal
- `check_mongodb_status.py` - Status checker
- `fix_mongodb_indexes.py` - Index management

### Documentation
- `MONGODB_INTEGRATION_README.md` - MongoDB integration overview
- `PRODUCTION_WORKFLOW_GUIDE.md` - This file

## Data Quality Guarantees

1. **No Duplicates**: Removed before enrichment
2. **Only Active Listings**: Off-market properties removed
3. **One-Time Enrichment**: Each property enriched only once
4. **Clean State**: Temp files removed each run
5. **Error Tracking**: Failed enrichments logged for retry

## Best Practices

1. **Always run fix_mongodb_indexes.py first** (one-time setup)
2. **Check status before/after runs** with `check_mongodb_status.py`
3. **Use dry-run mode first** for manual operations
4. **Monitor enrichment failures** and retry as needed
5. **Schedule regular runs** for up-to-date data

## Support

For issues:
1. Check `check_mongodb_status.py` output
2. Review MongoDB error messages
3. Check enrichment logs in batch_processor
4. Verify MongoDB connection
5. Run fix_mongodb_indexes.py if needed
