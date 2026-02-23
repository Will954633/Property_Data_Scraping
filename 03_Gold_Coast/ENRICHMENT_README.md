# Gold Coast Cadastral Data Enrichment

This directory contains scripts to enrich the Gold Coast MongoDB database with cadastral data from the Queensland Spatial GIS API.

## What Gets Added

The enrichment process adds **20 new fields** to each property record:

### From Cadastral Parcels Layer (15 fields):
1. **lot** - Lot number (from API)
2. **plan** - Plan number (from API)
3. **lotplan** - Combined lot/plan identifier
4. **lot_area** ⭐ - Property area in square meters (m²)
5. **excl_area** - Excluded area in m² (roads, easements)
6. **lot_volume** - Lot volume for volumetric parcels
7. **tenure** - Tenure type (Freehold, Leasehold, etc.)
8. **cover_typ** - Coverage type (Base, Strata, Volumetric, Easement)
9. **parcel_typ** - Parcel type (Lot Type Parcel, Road, Easement)
10. **acc_code** - Positional accuracy code
11. **surv_ind** - Surveyed indicator (Y/N)
12. **feat_name** - Feature name
13. **alias_name** - Alias names
14. **shire_name** - Local authority name
15. **smis_map** - SmartMap link URL

### From Addresses Layer (5 fields):
16. **API_address** - Formatted full address
17. **API_street_full** - Full street name
18. **API_floor_number** - Floor number (for apartments)
19. **API_floor_type** - Floor type
20. **API_floor_suffix** - Floor suffix

### Metadata (2 fields):
21. **enriched_at** - Timestamp of enrichment
22. **enriched_source** - Source of enrichment (QLD_Spatial_GIS_API)

## Scripts

### 1. `test_enrichment.py` - Test Script
Tests the API connectivity and enrichment process on a small sample (5 properties from Mudgeeraba).

**Usage:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast
python3 test_enrichment.py
```

**What it does:**
- Connects to MongoDB
- Queries API for 5 sample properties
- Shows results and success rate
- Confirms API is working before full enrichment

### 2. `enrich_cadastral_data.py` - Main Enrichment Script
Enriches all Gold Coast properties with cadastral data from the QLD Spatial GIS API.

**Usage:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast
python3 enrich_cadastral_data.py
```

**Features:**
- Processes all 81 Gold Coast suburbs
- Skips already enriched properties
- Batches API requests (100 at a time)
- Respectful API delay (0.1s between calls)
- Progress tracking and error handling
- Resumable (can restart if interrupted)

**Estimated time:** ~45-60 minutes for full database (depends on property count and API speed)

## Step-by-Step Process

### Step 1: Test the Process
```bash
python3 test_enrichment.py
```

Expected output:
```
✓ API connection working well!
✓ Ready to run full enrichment
```

### Step 2: Run Full Enrichment
```bash
python3 enrich_cadastral_data.py
```

The script will:
1. Connect to MongoDB
2. Process each suburb sequentially
3. Query API for each property
4. Add new fields to MongoDB documents
5. Show progress and statistics

### Step 3: Verify Results
```bash
python3 verify_database.py
```

Or check manually:
```python
from pymongo import MongoClient
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']

# Check a sample property
prop = db['mudgeeraba'].find_one({'lot_area': {'$exists': True}})
print(f"Lot area: {prop.get('lot_area')} m²")
print(f"Tenure: {prop.get('tenure')}")
print(f"Parcel type: {prop.get('parcel_typ')}")
```

## Configuration

Edit the scripts to customize:

**`enrich_cadastral_data.py`:**
```python
BATCH_SIZE = 100      # Properties per bulk update
API_DELAY = 0.1       # Seconds between API calls
```

**`test_enrichment.py`:**
```python
TEST_SUBURB = "mudgeeraba"  # Suburb to test
TEST_LIMIT = 5              # Number of properties to test
```

## Data Quality Notes

1. **Coverage:** Not all properties may have cadastral data in the API
   - Typical success rate: 85-95%
   - Properties without lot/plan will be skipped
   - Some newer properties may not be in the API yet

2. **Field Values:**
   - `lot_area` may be null for some property types (easements, roads)
   - `excl_area` may be null if no excluded areas
   - `tenure` shows legal ownership type

3. **API Limits:**
   - API has no explicit rate limit
   - Script uses 0.1s delay to be respectful
   - Max 4000 records per API query

## Troubleshooting

### "No results found" for properties
- Check if LOT and PLAN fields exist in MongoDB
- Verify lot/plan format matches API expectations
- Some properties may genuinely not be in the API

### API connection errors
- Check internet connectivity
- Verify API URL is accessible
- May need to adjust timeout or retry logic

### MongoDB connection errors
- Ensure MongoDB is running: `brew services start mongodb-community`
- Check connection string: `mongodb://127.0.0.1:27017/`

### Script interrupted
- Script is resumable - just run again
- Already enriched properties are skipped
- No data loss from interruption

## API Documentation

Full API documentation available at:
`QLD_Spatial_GIS_API_Summary.md`

API endpoint:
`https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer`

## Example Queries After Enrichment

### Find properties over 1000 m²
```python
large_props = db['surfers_paradise'].find({'lot_area': {'$gt': 1000}})
```

### Find freehold properties
```python
freehold = db['broadbeach'].find({'tenure': 'Freehold'})
```

### Find strata properties (apartments)
```python
strata = db['southport'].find({'cover_typ': 'Strata'})
```

### Get average lot size by suburb
```python
pipeline = [
    {'$match': {'lot_area': {'$exists': True, '$ne': None}}},
    {'$group': {
        '_id': '$LOCALITY',
        'avg_area': {'$avg': '$lot_area'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'avg_area': -1}}
]
result = db['mudgeeraba'].aggregate(pipeline)
```

## Maintenance

### Re-run Enrichment
To update data (e.g., after new properties are added):
1. The script automatically skips already enriched properties
2. To force re-enrichment, first drop the enriched fields or delete/reimport database

### Update Specific Suburbs
To enrich only specific suburbs, modify the script:
```python
# In enrich_cadastral_data.py, after line "collections = sorted(db.list_collection_names())"
collections = [c for c in collections if c in ['mudgeeraba', 'southport']]
```

## Support

For issues or questions:
1. Check `Missing_Data_Analysis.md` for field descriptions
2. Review `QLD_Spatial_GIS_API_Summary.md` for API details
3. Test with `test_enrichment.py` first to isolate issues
