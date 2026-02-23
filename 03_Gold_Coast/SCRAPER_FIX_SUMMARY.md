# Domain Scraper Data Extraction Fix

## Problem
The Domain.com.au scraper was successfully deployed to Google Cloud and tested with 5 addresses, but was missing critical data fields:
- **Rental estimates**: weekly_rent and yield were null (should be $950/week, 3.73%)
- **Property timeline**: empty array (should show "Sold Apr 2024 $1.15m, Rented Jul 2024")
- **Property type**: null (should be "House")
- **Land size**: null

## Root Cause
The scraper was only checking limited locations in the Apollo GraphQL state for these fields. Domain.com.au stores data in `__NEXT_DATA__` JSON with a complex Apollo GraphQL cache structure where:
1. Some data requires resolving **GraphQL references** (objects with `__ref: "Type:ID"`)
2. Field names vary across different object types
3. Rental data may be in separate `RentalEstimate` objects
4. Property timeline requires resolving listing references from the cache

## Solution Implemented

### 1. Enhanced Property Type & Land Size Extraction
**File**: `test_scraper_gcs.py`, `domain_scraper_gcs.py`

```python
# Check multiple field names and locations
prop_type = (features.get('propertyType') or features.get('type') or 
            property_obj.get('propertyType') or property_obj.get('type'))

land_size = (features.get('landSize') or features.get('land_size') or 
            features.get('landArea') or features.get('sizeInSquareMetres'))

# Search entire Apollo state if still null
if not prop_type or not land_size:
    for key, value in apollo_state.items():
        if isinstance(value, dict):
            if not land_size and ('landSize' in value or 'landArea' in value):
                land_size = value.get('landSize') or value.get('landArea')
            if not prop_type and ('propertyType' in value or 'type' in value):
                if value.get('__typename') in ['Property', 'Address']:
                    prop_type = value.get('propertyType') or value.get('type')
```

### 2. Rental Estimates Extraction
**File**: `test_scraper_gcs.py`, `domain_scraper_gcs.py`

```python
# Check valuation object first
weekly_rent = valuation.get('rentPerWeek') or valuation.get('weeklyRent')
rent_yield = valuation.get('rentYield') or valuation.get('yield')

# Search for RentalEstimate objects in Apollo state
if not weekly_rent or not rent_yield:
    for key, value in apollo_state.items():
        if isinstance(value, dict):
            # Check for RentalEstimate objects
            if value.get('__typename') == 'RentalEstimate':
                if not weekly_rent:
                    weekly_rent = value.get('price') or value.get('weeklyRent')
                if not rent_yield:
                    rent_yield = value.get('yield') or value.get('rentYield')
```

### 3. Property Timeline with Reference Resolution
**File**: `test_scraper_gcs.py`, `domain_scraper_gcs.py`

```python
# Resolve listing references from Apollo cache
for listing_ref in listings:
    listing = None
    
    # If it's a GraphQL reference like {"__ref": "Listing:123"}
    if isinstance(listing_ref, dict) and '__ref' in listing_ref:
        ref_key = listing_ref['__ref']
        listing = apollo_state.get(ref_key, {})
    elif isinstance(listing_ref, dict):
        listing = listing_ref
    
    if listing and isinstance(listing, dict):
        # Extract listing details
        listing_date = listing.get('listingDate') or listing.get('date')
        listing_type = listing.get('listingType') or listing.get('type')
        price = listing.get('price') or listing.get('displayPrice')
        sale_method = listing.get('saleMethod') or listing.get('method')
        
        # Resolve agency reference if needed
        agency_name = None
        agency_ref = listing.get('agency')
        if isinstance(agency_ref, dict) and '__ref' in agency_ref:
            agency = apollo_state.get(agency_ref['__ref'], {})
            agency_name = agency.get('name')
        
        # Only add if we have meaningful data
        if any(v is not None for v in [listing_date, listing_type, price]):
            property_data['property_timeline'].append(event)
```

## Files Updated
1. **`03_Gold_Coast/test_scraper_gcs.py`** - Test scraper (5 addresses)
2. **`03_Gold_Coast/domain_scraper_gcs.py`** - Production scraper (200 workers)

## Testing Required
To verify the fix works:

```bash
# On GCP VM, run test scrap to verify data extraction
cd /home/projects/Property_Data_Scraping/03_Gold_Coast
export GCS_BUCKET="your-bucket-name"
python3 test_scraper_gcs.py
```

Expected results for **11 Matina Street, Biggera Waters**:
```json
{
  "features": {
    "bedrooms": 4,
    "bathrooms": 2,
    "car_spaces": 3,
    "land_size": <should have value>,
    "property_type": "House"
  },
  "rental_estimate": {
    "weekly_rent": 950,
    "yield": 3.73
  },
  "property_timeline": [
    {
      "date": "2024-07-XX",
      "type": "Rent",
      "price": 950
    },
    {
      "date": "2024-04-XX",
      "type": "Sold",
      "price": 1150000
    }
  ]
}
```

## Benefits
- **More complete data**: Captures rental estimates, property history, type, and land size
- **Better Apollo state parsing**: Resolves GraphQL references properly
- **Robust field names**: Checks multiple variations of field names
- **No breaking changes**: Existing successful extractions (bedrooms, bathrooms, valuation) unchanged

## Next Steps
1. Deploy updated scrapers to GCP
2. Run test with 5 addresses to verify improvements
3. If successful, deploy to all 200 workers for full scraping job
4. Monitor results to ensure data quality improved

## Technical Notes
- Apollo GraphQL uses a normalized cache with references (`__ref`) to avoid data duplication
- Domain.com.au's property timeline uses this reference pattern for listings and agencies
- The `__typename` field helps identify object types in the Apollo cache
- Multiple field name variations exist based on GraphQL query structure
