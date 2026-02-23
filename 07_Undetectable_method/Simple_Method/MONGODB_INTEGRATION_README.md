# MongoDB Integration - Complete Workflow

This document describes the complete MongoDB-integrated property scraping and enrichment pipeline.

## Overview

The system now integrates MongoDB to store property data and automatically enrich properties with detailed information from domain.com.au. The workflow is fully automated:

1. **Scrape** properties from realestate.com.au (Robina)
2. **Store** in MongoDB collection `properties_for_sale`
3. **Enrich** new properties automatically with detailed data
4. **Track** enrichment status for all properties

## MongoDB Configuration

- **URI**: `mongodb://127.0.0.1:27017/`
- **Database**: `property_data`
- **Collection**: `properties_for_sale`

## Prerequisites

### 1. Start MongoDB

```bash
# Start MongoDB (if not already running)
brew services start mongodb-community

# Verify MongoDB is running
mongosh --eval "db.version()"
```

### 2. Install Python Dependencies

```bash
pip install pymongo
```

## Complete Workflow

### One-Command Execution

Run the entire pipeline with a single command:

```bash
cd 07_Undetectable_method/Simple_Method
./process_all_sessions.sh
```

This will:
1. ✓ Capture screenshots from realestate.com.au
2. ✓ Extract text using OCR
3. ✓ Parse property data
4. ✓ Upload to MongoDB
5. ✓ **Automatically enrich new properties**

### Step-by-Step Breakdown

#### Step 1: Scrape Properties
```bash
python multi_session_runner.py
python ocr_extractor_multi.py --session 1
python data_parser_multi.py --input ocr_output_session_1/raw_text_all.txt --output property_data_session_1.json
```

#### Step 2: Upload to MongoDB
```bash
python mongodb_uploader.py
```

This script:
- Loads all `property_data_session_*.json` files
- Upserts properties to MongoDB (creates or updates)
- Marks new properties as `enriched: false`
- **Automatically triggers enrichment** for new properties

#### Step 3: Enrichment (Automatic)

The enrichment runs automatically via `batch_processor.py`:
- Queries MongoDB for unenriched properties
- Navigates to domain.com.au for each property
- Extracts comprehensive property data
- Updates MongoDB with enriched data

## MongoDB Document Schema

```javascript
{
  "_id": ObjectId("..."),
  "address": "5 Picabeen Close, Robina",
  
  // Basic data from scraping
  "bedrooms": 4,
  "bathrooms": 2,
  "parking": 3,
  "land_size_sqm": 459,
  "property_type": "House",
  "price": "$1,239,000",
  "agency": "Harcourts",
  "agent": "John Smith",
  
  // Enrichment tracking
  "enriched": false,                    // Has enrichment completed?
  "enrichment_attempted": false,        // Has enrichment been tried?
  "enrichment_retry_count": 0,          // Number of retry attempts
  "enrichment_error": null,             // Error message if failed
  
  // Timestamps
  "first_seen": ISODate("2025-11-14..."),
  "last_updated": ISODate("2025-11-14..."),
  "last_enriched": null,
  
  // Source tracking
  "source": "process_all_sessions",
  
  // Enriched data (populated after enrichment)
  "enrichment_data": {
    "domain_url": "https://www.domain.com.au/...",
    "html_file": "batch_results/html/property_1_20251114_123820.html",
    "property_data": {
      // Comprehensive property details from domain.com.au
    }
  }
}
```

## Manual Operations

### Check MongoDB Status

```bash
python check_mongodb_status.py
```

Shows:
- Total properties in database
- How many are enriched vs unenriched
- Recent additions
- Properties needing enrichment
- Failed enrichments with error details

### Manual Enrichment

To manually enrich properties without running the full scrape:

```bash
cd ../00_Production_System/02_Individual_Property_Google_Search
python batch_processor.py --mongodb
```

### Enrich Single Address (Testing)

```bash
cd ../00_Production_System/02_Individual_Property_Google_Search
python batch_processor.py --address "5 Picabeen Close, Robina, QLD 4226"
```

## Workflow Features

### ✅ Automatic Detection
- New properties are automatically detected
- Enrichment triggers only for new/unenriched properties
- No duplicate enrichment attempts

### ✅ Error Handling
- Failed enrichments are tracked
- Retry count maintained
- Error messages stored for debugging

### ✅ Idempotent Operations
- Safe to run `process_all_sessions.sh` multiple times
- Existing properties are updated (not duplicated)
- Only new properties trigger enrichment

### ✅ Progress Tracking
- Enrichment status per property
- Timestamps for all operations
- Completion rate statistics

## MongoDB Indexes

The following indexes are automatically created:
- `address` (unique) - Fast lookups by address
- `enriched` - Quick filtering of enriched/unenriched
- `first_seen` - Temporal queries
- `last_updated` - Recent changes

## Troubleshooting

### MongoDB Connection Error

```bash
# Check if MongoDB is running
brew services list | grep mongodb

# Start MongoDB
brew services start mongodb-community

# Test connection
mongosh
```

### No Properties Enriched

Check the enrichment logs:
```bash
python check_mongodb_status.py
```

Look for failed enrichments and error messages.

### Re-enrich Failed Properties

To retry failed enrichments, reset the `enrichment_attempted` flag:

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

## Files Created/Modified

### New Files
- `mongodb_uploader.py` - Uploads properties and triggers enrichment
- `check_mongodb_status.py` - Status checker utility
- `MONGODB_INTEGRATION_README.md` - This file

### Modified Files
- `process_all_sessions.sh` - Added MongoDB upload step
- `batch_processor.py` - Added `--mongodb` mode

## Data Flow Diagram

```
┌─────────────────────────────────────────────────┐
│  1. realestate.com.au (Scraping)                │
│     • Screenshot capture                         │
│     • OCR extraction                             │
│     • Data parsing                               │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         property_data_session_*.json
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  2. MongoDB Upload (mongodb_uploader.py)        │
│     • Load session JSON files                    │
│     • Upsert to MongoDB                          │
│     • Detect new properties                      │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼ (If new properties detected)
┌─────────────────────────────────────────────────┐
│  3. Auto Enrichment (batch_processor.py)        │
│     • Query unenriched properties                │
│     • Navigate to domain.com.au                  │
│     • Extract detailed data                      │
│     • Update MongoDB                             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         MongoDB: properties_for_sale
         (All properties enriched with full data)
```

## Next Steps

### Automation
Consider scheduling the scraper to run daily:
```bash
# Run daily at 8 AM
0 8 * * * cd /path/to/07_Undetectable_method/Simple_Method && ./process_all_sessions.sh
```

### Monitoring
Set up alerts for:
- Failed enrichments
- Low enrichment completion rate
- MongoDB connection issues

### Scaling
- Increase session count for more properties
- Implement parallel enrichment
- Add multiple suburbs

## Support

For issues or questions:
1. Check `check_mongodb_status.py` for current state
2. Review error messages in MongoDB
3. Check batch_processor logs for enrichment details
