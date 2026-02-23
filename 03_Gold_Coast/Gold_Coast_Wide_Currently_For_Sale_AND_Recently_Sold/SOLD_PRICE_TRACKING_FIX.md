# Sold Property Price Tracking Fix
**Last Updated:** 03/02/2026, 8:15 pm (Brisbane Time)

## Problem Summary

The sold property monitoring system had critical issues with price data tracking:

### Issue 1: Price Field Replacement
- **Problem:** When properties were moved to the sold database, the original `price` field (listing price) was being overwritten with "SOLD - $X,XXX,XXX"
- **Example:** Main Beach property showed `price: "SOLD - $1,100,000"` instead of the original listing price
- **Impact:** Lost the original listing price data, making it impossible to calculate price changes or days on market value

### Issue 2: Missing Sale Price Extraction
- **Problem:** The `sale_price` field was often `null` even though the sold price was visible on the website
- **Example:** Biggera Waters property showed `price: "Auction"` and `sale_price: null`, but website displayed "SOLD - $1,700,000"
- **Impact:** No record of the actual sale price for sold properties

### Issue 3: Inadequate HTML Parsing
- **Problem:** The sold price extraction logic wasn't comprehensive enough to find prices in all HTML structures
- **Impact:** Many sold prices were not being captured from the Domain.com.au sold listing pages

## Solution Implemented

### 1. Updated `monitor_sold_properties.py`

#### A. Improved Sale Price Extraction
Added comprehensive `_extract_sale_price()` method with 4 detection methods:

```python
def _extract_sale_price(self, soup: BeautifulSoup, html: str) -> Optional[str]:
    # METHOD 1: Look for "SOLD - $X,XXX,XXX" in summary title
    # Targets: <div data-testid="listing-details__summary-title">
    
    # METHOD 2: Look for price in any element with "SOLD" text
    # Searches all price-related elements
    
    # METHOD 3: Check meta tags
    # Looks for og:price:amount meta property
    
    # METHOD 4: Look in page text for price patterns near "SOLD"
    # Regex pattern: SOLD[^$]{0,50}\$[\d,]+
```

#### B. Preserved Original Listing Price
Modified `monitor_property()` to preserve the original price:

```python
# PRESERVE ORIGINAL LISTING PRICE
original_listing_price = property_doc.get('price')

# Add sold information
property_doc['sale_price'] = sale_price  # Sold price goes here
property_doc['listing_price'] = original_listing_price  # Original price preserved
```

#### C. Updated move_to_sold_collection()
Ensures listing price is preserved when moving to sold database:

```python
# PRESERVE ORIGINAL LISTING PRICE
original_price = property_doc.get('price')
if original_price:
    property_doc['listing_price'] = original_price
```

### 2. Created `fix_sold_property_prices.py`

A retroactive fix script to correct existing sold properties in the database.

#### Features:
- **Scans** all sold properties in `Gold_Coast_Recently_Sold` database
- **Identifies** properties with missing or incorrect price data
- **Re-scrapes** the sold listing page to extract the correct sold price
- **Updates** documents with proper price fields

#### Usage:
```bash
# Generate report of what needs fixing
python3 fix_sold_property_prices.py --report

# Fix specific suburbs
python3 fix_sold_property_prices.py --suburbs "main_beach" "biggera_waters"

# Fix all suburbs
python3 fix_sold_property_prices.py --all

# Test mode (first 5 properties only)
python3 fix_sold_property_prices.py --test
```

## Data Structure Changes

### Before Fix:
```json
{
  "price": "SOLD - $1,100,000",  // ❌ Original listing price lost
  "sale_price": null,             // ❌ No sold price recorded
  "sold_date": "2025-09-17"
}
```

### After Fix:
```json
{
  "price": "Offers Over $950,000",  // ✓ Original listing price preserved
  "listing_price": "Offers Over $950,000",  // ✓ Explicit listing price field
  "sale_price": "$1,100,000",       // ✓ Actual sold price extracted
  "sold_date": "2025-09-17",
  "price_fix_date": "2026-02-03T20:15:00",  // ✓ Timestamp of fix
  "price_fix_applied": true         // ✓ Flag indicating fix was applied
}
```

## Impact Analysis

### Properties Affected:
- **Total Sold Properties:** 130
- **Need Price Fixing:** 130 (100%)
- **Suburbs Affected:** 16 suburbs

### Top Affected Suburbs:
1. sold_properties: 65/65
2. broadbeach: 6/6
3. mermaid_waters: 6/6
4. biggera_waters: 5/5
5. broadbeach_waters: 5/5
6. burleigh_heads: 5/5
7. burleigh_waters: 5/5

## Benefits

### 1. Complete Price History
- Original listing price preserved
- All price changes tracked
- Sold price accurately recorded

### 2. Better Analytics
- Can calculate price change percentage
- Can analyze days on market vs price change
- Can identify properties that sold above/below listing price

### 3. Data Integrity
- Separate fields for listing vs sold prices
- No data loss during sold property migration
- Audit trail with fix timestamps

## Testing

### Test Cases:
1. **Main Beach Property** (ObjectId: 697d8e739850c7130fb3641b)
   - Before: `price: "SOLD - $1,100,000"`, `sale_price: null`
   - After: `listing_price: [original]`, `sale_price: "$1,100,000"`

2. **Biggera Waters Property** (ObjectId: 697d9aa7ea712bfaacf2d212)
   - Before: `price: "Auction"`, `sale_price: null`
   - After: `listing_price: "Auction"`, `sale_price: "$1,700,000"`

## Future Monitoring

Going forward, all newly detected sold properties will:
1. Preserve the original listing price in `listing_price` field
2. Extract and store the sold price in `sale_price` field
3. Maintain complete price history
4. Enable accurate price change analysis

## Commands Reference

### Check Current Status:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold

# Generate report
python3 fix_sold_property_prices.py --report
```

### Fix Existing Data:
```bash
# Fix all suburbs (recommended)
python3 fix_sold_property_prices.py --all

# Fix specific suburbs
python3 fix_sold_property_prices.py --suburbs "main_beach" "biggera_waters"
```

### Verify Fixes:
```bash
# Check a specific property
python3 -c "
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast_Recently_Sold']

doc = db.main_beach.find_one({'_id': ObjectId('697d8e739850c7130fb3641b')})
print(f'Listing Price: {doc.get(\"listing_price\")}')
print(f'Sale Price: {doc.get(\"sale_price\")}')
print(f'Fix Applied: {doc.get(\"price_fix_applied\")}')
"
```

## Notes

- The fix script uses headless Chrome to re-scrape sold listing pages
- Processing time: ~5-7 seconds per property (includes page load wait)
- The script is safe to run multiple times (idempotent)
- Properties already fixed will be skipped
- Original `price` field is preserved for backward compatibility

## Related Files

- `monitor_sold_properties.py` - Main sold property monitoring script (updated)
- `fix_sold_property_prices.py` - Retroactive price fix script (new)
- `SOLD_MONITORING_EXPLANATION.md` - Overall sold monitoring documentation
