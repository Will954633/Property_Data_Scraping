# Refresh For-Sale Data with Correct Floor Plans

## Problem Summary

The current data in MongoDB collections was scraped **before** the `__NEXT_DATA__` floor plan parser fix was implemented. This means:

- ❌ **Current data**: Has incorrect floor plans (random property photos labeled as floor plans due to `_3_` filename heuristic)
- ✅ **New scraper**: Uses Domain's explicit `mediaType: "floorplan"` labels from `__NEXT_DATA__` JSON

## Current Data Analysis

### Collections in Use

Based on code analysis, there is **ONLY ONE collection** for for-sale properties:

- **`properties_for_sale`** - Main collection (used by `mongodb_uploader.py`)
- ⚠️ **`properties_for_sale_enriched`** - This collection **DOES NOT EXIST** in the for-sale pipeline

The script comments confirm: *"Enrichment is designed for sold properties only"*

### Data Structure

Each document contains:
```json
{
  "address": "927 Medinah Avenue, Robina, QLD 4226",
  "bedrooms": 5,
  "bathrooms": 5,
  "property_images": [...],  // ← All scraped from Domain
  "floor_plans": [...],       // ← Currently WRONG (has random photos)
  "enriched": false,
  "enrichment_attempted": true,
  "enrichment_error": "Direct URL failed",
  "first_seen": "2025-12-04T12:24:16.949000",
  "last_updated": "2025-12-09T13:11:35.098000",
  "source": "selenium_forsale_scraper"
}
```

### What Would Be Lost if We Drop the Collection?

**NOTHING IMPORTANT** - Here's why:

1. **All data comes from Domain scraping** - No manual additions
2. **Enrichment doesn't work for for-sale properties** - The `enrichment_attempted: true` with `enrichment_error: "Direct URL failed"` shows enrichment fails
3. **Metadata fields are auto-generated**:
   - `first_seen` - Will be regenerated on re-scrape
   - `last_updated` - Will be current timestamp
   - `enriched: false` - Already false, enrichment doesn't work anyway
4. **Source of truth is Domain.com.au** - Re-scraping will get the latest data

## Recommended Refresh Strategy

### Option 1: Drop & Re-scrape (RECOMMENDED) ✅

**Advantages:**
- Clean slate with correct floor plans
- Removes any stale/off-market properties
- Gets latest data from Domain
- Simple and foolproof

**Steps:**

```bash
# 1. Backup current data (optional - for safety)
cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/Simple_Method

mongodump --db property_data --collection properties_for_sale --out backup_$(date +%Y%m%d_%H%M%S)

# 2. Drop the collection
mongosh property_data --eval "db.properties_for_sale.drop()"

# 3. Run the scraper fresh
./process_forsale_properties.sh
```

**What you'll get:**
- ✅ Correct floor plans using `__NEXT_DATA__` parser
- ✅ Latest property data from Domain
- ✅ Only currently listed properties (natural cleanup)
- ✅ Fresh timestamps

### Option 2: Selective Re-scrape (More Complex)

If you want to preserve `first_seen` timestamps:

```bash
# 1. Export addresses to re-scrape
mongosh property_data --eval "db.properties_for_sale.find({}, {address: 1, _id: 0}).forEach(doc => print(doc.address))" > addresses_to_rescrape.txt

# 2. Drop collection
mongosh property_data --eval "db.properties_for_sale.drop()"

# 3. Run scraper
./process_forsale_properties.sh

# 4. Manually restore first_seen dates (complex Python script needed)
```

**Not recommended** - The complexity isn't worth it since `first_seen` dates can be regenerated.

## What About properties_for_sale_enriched?

**This collection doesn't exist in the for-sale pipeline.**

Evidence:
1. `mongodb_uploader.py` only uses `COLLECTION_NAME = "properties_for_sale"`
2. `process_forsale_properties.sh` explicitly skips enrichment: *"SKIPPED for for-sale properties"*
3. `check_mongodb_status.py` only checks `properties_for_sale`
4. Search for `properties_for_sale_enriched` in codebase returns 0 results

The enrichment system is **only for sold properties** (different pipeline).

## Verification After Re-scrape

After running `process_forsale_properties.sh`, verify the fix:

```bash
# Check a property's floor plans
mongosh property_data --eval '
  db.properties_for_sale.findOne(
    {"address": /Medinah Avenue/},
    {"address": 1, "floor_plans": 1, "_id": 0}
  )
'
```

**Expected result:**
```json
{
  "address": "927 Medinah Avenue, Robina, QLD 4226",
  "floor_plans": [
    "https://rimh2.domainstatic.com.au/.../2020454939_34_3_251127_042459-w2000-h1414"
  ]
}
```

The floor plan URL should:
- ✅ Be labeled as `mediaType: "floorplan"` in Domain's `__NEXT_DATA__`
- ✅ Actually be a floor plan (not a kitchen/exterior photo)
- ✅ Typically have higher image numbers (e.g., `_34_3_` not `_3_1_`)

## Final Recommendation

**Just drop and re-scrape.** 

You're not losing any valuable data:
- ❌ No manual enrichment data (enrichment doesn't work for for-sale)
- ❌ No custom fields added by other processes
- ❌ No historical tracking needed (for-sale properties change frequently)
- ✅ Source of truth is Domain.com.au
- ✅ Re-scraping gets latest + correct floor plans

## Quick Command

```bash
cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/Simple_Method

# Drop and refresh
mongosh property_data --eval "db.properties_for_sale.drop()" && \
./process_forsale_properties.sh
```

Done! 🎉
