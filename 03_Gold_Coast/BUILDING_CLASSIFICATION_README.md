# Building Classification System

## Overview

This system identifies and classifies properties in the Gold Coast database as either:
- **Standalone** - Single houses or properties
- **Building** - Multi-unit building complexes
- **Unit** - Individual units within a building complex

## Problem

In the original data, addresses like "414 MARINE PARADE" appear to be single houses, but they're actually building complexes with multiple units (U 1/414, U 2/414, U 12/414, etc.). This classification helps:

1. **Accurate scraping** - Scrape once per building, not per unit
2. **Data organization** - Understand property structure
3. **Cost optimization** - Reduce duplicate scraping

## How It Works

### Detection Logic

The `identify_buildings.py` script analyzes addresses and:

1. **Groups by base address**: Street number + street name + street type + locality
2. **Counts units**: Checks for UNIT_TYPE and UNIT_NUMBER fields
3. **Classifies**:
   - If ≥2 units at same address → **Building complex**
   - If 0 units at address → **Standalone property**

### Example

**Before Classification:**
```
- 414 MARINE PARADE, BIGGERA WATERS
- U 1/414 MARINE PARADE, BIGGERA WATERS
- U 2/414 MARINE PARADE, BIGGERA WATERS  
- U 12/414 MARINE PARADE, BIGGERA WATERS
- U 20/414 MARINE PARADE, BIGGERA WATERS
```

**After Classification:**
```
Building: "414 MARINE PARADE"
  - property_classification: "building"
  - total_units_in_building: 20
  
Units: U 1, U 2, U 12, U 20
  - property_classification: "unit"
  - building_complex: "414 MARINE PARADE"
  - building_address: "414 MARINE PARADE, BIGGERA WATERS"
  - total_units_in_building: 20
```

## Running Classification

### Step 1: Install Dependencies

```bash
# If using virtual environment
python3 -m venv venv
source venv/bin/activate
pip install pymongo

# Or system-wide (if allowed)
pip3 install pymongo --break-system-packages
```

### Step 2: Run Classification Script

```bash
cd 03_Gold_Coast
chmod +x identify_buildings.py
python3 identify_buildings.py
```

### Expected Output

```
================================================================================
Building Complex Identification
================================================================================

Connecting to MongoDB...
✓ Connected to MongoDB

Processing 63 suburb collections...

  [10/63] Processed Biggera Waters
  [20/63] Processed Gilston
  ...
  [63/63] Processed Varsity Lakes

================================================================================
Identification Complete
================================================================================
Total addresses:         325,463
Standalone houses:       245,120
Buildings identified:    3,847
Units in buildings:      77,496
Documents updated:       326,463
================================================================================

Example Buildings Found:
================================================================================

Building: 414 MARINE PARADE
  Suburb: BIGGERA WATERS
  Units: 20 units
    - U 1/414 MARINE PARADE
    - U 2/414 MARINE PARADE
    - U 12/414 MARINE PARADE
```

## New Database Fields

After running the script, each document will have:

```javascript
{
  // Existing fields...
  "ADDRESS_PID": 123456,
  "STREET_NO_1": "414",
  "STREET_NAME": "MARINE",
  "STREET_TYPE": "PARADE",
  "LOCALITY": "BIGGERA WATERS",
  "UNIT_TYPE": "U",
  "UNIT_NUMBER": "12",
  
  // New classification fields
  "property_classification": "unit",           // or "building" or "standalone"
  "building_complex": "414 MARINE PARADE",     // Building name (units only)
  "building_address": "414 MARINE PARADE, BIGGERA WATERS",  // Full building address
  "total_units_in_building": 20,               // Total units in this building
  "classification_updated": ISODate("2025-01-05T...")
}
```

## Integration with Scraper

### Option 1: Scrape Only Buildings (Recommended)

Scrape the building address once instead of each unit:

```python
# In domain_scraper_gcs.py, modify get_my_addresses():

def get_my_addresses(self):
    addresses = []
    for collection_name in collections:
        collection = self.db[collection_name]
        
        # Get only buildings and standalone properties (not individual units)
        docs = list(collection.find({
            'property_classification': {'$in': ['building', 'standalone']}
        }))
        
        for doc in docs:
            address = self.build_address_from_components(doc)
            if address:
                addresses.append({
                    'address_pid': doc.get('ADDRESS_PID'),
                    'address': address,
                    'suburb': doc.get('LOCALITY'),
                    'doc_id': str(doc.get('_id')),
                    'collection': collection_name,
                    'classification': doc.get('property_classification'),
                    'units_in_building': doc.get('total_units_in_building', 1)
                })
    
    return addresses
```

**Benefits:**
- Reduces scraping from 325k to ~250k addresses
- Avoids duplicate data for units in same building
- Saves ~$3-5 in cloud costs
- Faster completion (12-15 hours instead of 15-20)

### Option 2: Scrape All (Units + Buildings)

Keep scraping all addresses but add classification metadata:

```python
# Add classification info to scraped data
property_data.update({
    'property_classification': addr_info['classification'],
    'building_complex': addr_info.get('building_complex'),
    'units_in_building': addr_info.get('units_in_building')
})
```

## Querying Classified Data

### MongoDB Queries

```javascript
// Count by classification
db.biggera_waters.aggregate([
  { $group: { 
      _id: "$property_classification", 
      count: { $sum: 1 } 
  }}
])

// Find all buildings with 10+ units
db.biggera_waters.find({
  property_classification: "building",
  total_units_in_building: { $gte: 10 }
})

// Find units in specific building
db.biggera_waters.find({
  property_classification: "unit",
  building_complex: "414 MARINE PARADE"
})

// Count standalone houses
db.biggera_waters.countDocuments({
  property_classification: "standalone"
})
```

### Statistics

After classification, view stats with:

```bash
mongosh Gold_Coast --eval "
  db.biggera_waters.aggregate([
    { \$group: { 
        _id: '\$property_classification', 
        count: { \$sum: 1 } 
    }},
    { \$sort: { count: -1 }}
  ])
"
```

## Re-running Classification

The script is safe to re-run. It will:
- Overwrite existing classifications
- Update the `classification_updated` timestamp
- Recalculate building unit counts

```bash
python3 identify_buildings.py
```

## Cost Impact on Scraping

**Before Classification:**
- Total addresses: 325,463
- Scraping all: ~$15-20 (200 workers × 15-20 hours)

**After Classification (Buildings + Standalone Only):**
- Buildings: ~3,847
- Standalone: ~245,120
- Total to scrape: ~249,000
- Cost: ~$12-15 (200 workers × 12-15 hours)
- **Savings: ~$3-5 and 3-5 hours**

## Verification

Check classification worked correctly:

```bash
# View a sample building
mongosh Gold_Coast --eval "
  db.biggera_waters.findOne({ 
    property_classification: 'building' 
  })
"

# Count classifications
mongosh Gold_Coast --eval "
  db.biggera_waters.countDocuments({ 
    property_classification: 'building' 
  })
"
```

## Notes

- Classification is based on UNIT_TYPE and UNIT_NUMBER fields
- Buildings must have ≥2 units to be classified as "building"
- Single units (e.g., only U 1/414) are treated as standalone
- Classification is suburb-specific (runs on each collection)
- The base building address (without unit number) is marked as "building"
- Individual units are marked as "unit" with building reference

## Troubleshooting

### No Buildings Found

If no buildings identified:
- Check UNIT_TYPE and UNIT_NUMBER fields exist
- Verify data was imported correctly
- Run sample query: `db.biggera_waters.findOne({UNIT_TYPE: {$ne: null}})`

### Classification Not Updating

- Ensure MongoDB is running
- Check connection string in script
- Verify write permissions on database
- Review error messages in output

### Wrong Classifications

Re-run the script - it will overwrite existing classifications with fresh analysis.

## Future Enhancements

Potential improvements:
1. **Confidence scores** - Mark uncertain classifications
2. **Building names** - Extract actual building names from property data
3. **Cross-reference** - Validate against Domain.com.au data
4. **Historical tracking** - Track when units are added/removed

---

**Last Updated:** 2025-01-05
