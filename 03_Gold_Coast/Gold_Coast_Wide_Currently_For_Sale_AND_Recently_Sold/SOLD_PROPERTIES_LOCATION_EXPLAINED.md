# Sold Properties Database Location - RESOLVED
**Last Updated: 03/02/2026, 7:55 pm (Brisbane Time)**

## ✅ ISSUE RESOLVED - Sold Properties ARE Being Stored!

### The Confusion
You were looking for a database called **"Gold_Coast_Recently_Sold"** but the sold properties are actually stored in:

- **Database**: `Gold_Coast_Currently_For_Sale`
- **Collection**: `Gold_Coast_Recently_Sold`

### Why This Design?
The script stores sold properties as a **collection within the same database** as the for-sale properties, not as a separate database. This is actually a better design because:

1. **Logical grouping**: All Gold Coast property data is in one database
2. **Easier queries**: Can easily compare for-sale vs sold properties
3. **Simpler management**: One database to backup/maintain

## Current Status

### ✅ Sold Properties Found: **65 properties**

**Database**: `Gold_Coast_Currently_For_Sale`  
**Collection**: `Gold_Coast_Recently_Sold`

### Recent Sold Properties (Last 10)

1. **4 17 Thelma Avenue Biggera Waters, QLD 4216**
   - Original Suburb: Biggera Waters
   - Sold Date: Sold at auction 31 Jan 2026
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:53:15

2. **5 Helena Street Biggera Waters, QLD 4216**
   - Original Suburb: Biggera Waters
   - Sold Date: Sold at auction 31 Jan 2026
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:53:05

3. **12 25 Brighton Street Biggera Waters, QLD 4216**
   - Original Suburb: Biggera Waters
   - Sold Date: Sold by private treaty 23 Jan 2026
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:52:47

4. **2 27 Cawthray Street Biggera Waters, QLD 4216**
   - Original Suburb: Biggera Waters
   - Sold Date: Sold by private treaty 27 Nov 2025
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:52:35

5. **1606 25 31 East Quay Drive Biggera Waters, QLD 4216**
   - Original Suburb: Biggera Waters
   - Sold Date: Sold by private treaty 22 Dec 2025
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:52:26

6. **2 203 Central Street, Labrador, QLD 4215**
   - Original Suburb: Labrador
   - Sold Date: Sold by private treaty 9 Dec 2025
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:51:58

7. **1 16 Botanical Drive, Labrador, QLD 4215**
   - Original Suburb: Labrador
   - Sold Date: Sold by private treaty 3 Nov 2025
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:51:48

8. **4 32 Bath Street, Labrador, QLD 4215**
   - Original Suburb: Labrador
   - Sold Date: Sold by private treaty 27 Nov 2025
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:51:39

9. **193 La Sabbia 74 86 Old Burleigh Road Surfers Paradise, QLD 4217**
   - Original Suburb: Surfers Paradise
   - Sold Date: Sold at auction 31 Jan 2026
   - Detection Method: listing_tag
   - Moved to Sold: 2026-02-03 19:48:58

10. **47 2943 Surfers Paradise Boulevard Surfers Paradise, QLD 4217**
    - Original Suburb: Surfers Paradise
    - Sold Date: Sold by private treaty 25 Jan 2026
    - Detection Method: listing_tag
    - Moved to Sold: 2026-02-03 19:48:08

## How to Access Sold Properties

### Using MongoDB Shell (mongosh)
```bash
mongosh
use Gold_Coast_Currently_For_Sale
db.Gold_Coast_Recently_Sold.find().pretty()
```

### Using Python
```python
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast_Currently_For_Sale']
sold_collection = db['Gold_Coast_Recently_Sold']

# Get all sold properties
sold_properties = list(sold_collection.find({}))
print(f"Total sold: {len(sold_properties)}")

# Get recent sold properties
recent = sold_collection.find({}).sort('sold_detection_date', -1).limit(10)
for prop in recent:
    print(f"{prop['address']} - Sold: {prop.get('sold_date_text')}")
```

### Using the Script's Report Feature
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --report
```

## What Data is Stored for Each Sold Property?

Each sold property document contains:
- **Original listing data**: address, bedrooms, bathrooms, property type, etc.
- **Sold information**: 
  - `sold_status`: 'sold'
  - `sold_detection_date`: When the script detected it was sold
  - `sold_date_text`: Raw sold date text from Domain
  - `sold_date`: Parsed sold date
  - `sale_price`: Sale price (if available)
  - `detection_method`: How it was detected (e.g., 'listing_tag')
- **Migration metadata**:
  - `moved_to_sold_date`: When moved to sold collection
  - `original_collection`: Original suburb collection name
  - `original_suburb`: Original suburb name
- **All historical data**: images, floor plans, agent info, etc.

## Database Structure Overview

```
MongoDB Server (localhost:27017)
├── Gold_Coast_Currently_For_Sale (Database)
│   ├── Gold_Coast_Recently_Sold (Collection) ← SOLD PROPERTIES HERE
│   ├── advancetown (Collection)
│   ├── arundel (Collection)
│   ├── ashmore (Collection)
│   ├── biggera_waters (Collection)
│   └── ... (52 suburb collections total)
│
└── Gold_Coast (Database) ← Master property database
    ├── advancetown (Collection)
    ├── arundel (Collection)
    └── ... (52 suburb collections)
```

## Script Behavior

When `monitor_sold_properties.py` runs:

1. **Scans** each suburb collection in `Gold_Coast_Currently_For_Sale`
2. **Detects** sold properties using 5 detection methods
3. **Moves** sold properties to `Gold_Coast_Recently_Sold` collection
4. **Updates** master property record in `Gold_Coast` database (adds to sales_history)
5. **Removes** from original suburb collection

## Verification Commands

### Check if sold properties exist:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 -c "
from pymongo import MongoClient
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast_Currently_For_Sale']
sold_coll = db['Gold_Coast_Recently_Sold']
print(f'Total sold properties: {sold_coll.count_documents({})}')
client.close()
"
```

### View recent sold properties:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --report
```

## Summary

✅ **Sold properties ARE being stored correctly**  
✅ **Location**: `Gold_Coast_Currently_For_Sale` database → `Gold_Coast_Recently_Sold` collection  
✅ **Current count**: 65 sold properties  
✅ **Script is working as designed**  

The confusion was about the naming - you expected a separate database called "Gold_Coast_Recently_Sold" but it's actually a collection within the "Gold_Coast_Currently_For_Sale" database.
