# Next Steps - Property Georeference Implementation

## Status: Ready to Begin Implementation

Based on the comprehensive implementation plan, here are the immediate next steps to get started.

---

## Step 1: Review & Approve Plan ✓

**Action**: Review the implementation plan
- **File**: `GEOREFERENCE_IMPLEMENTATION_PLAN.md`
- **Decision**: Choose between Approach A (per-property) or Approach B (POI database)
- **Recommendation**: Use **Approach B** - saves ~$500 and is more flexible

**Budget to Approve**:
- **Minimum**: $10-50 (POI database + straight-line distances only)
- **Recommended**: $110-150 (includes selective drive distances for schools)
- **Maximum**: $530 (includes full drive distances for all POI categories)

---

## Step 2: Google Cloud API Setup (Required)

### 2A. Access Google Cloud Console >> NOTE: This has been done.

1. Go to https://console.cloud.google.com/
2. Select your existing project: **`fields-estate`**
3. Verify Places API (New) is enabled:
   - Navigate to: **APIs & Services** → **Enabled APIs & services**
   - Confirm "Places API (New)" is in the list ✓  

### 2B. Enable Distance Matrix API (If Using Drive Distances) >> NOTE: This has been done.

1. In Google Cloud Console
2. Navigate to: **APIs & Services** → **Library**
3. Search for: "Routes API" or "Distance Matrix API"
4. Click **Enable**

### 2C. Create API Key

1. Navigate to: **APIs & Services** → **Credentials** API Key is here: AIzaSyAm4jRBakPQ0raG7QKapIUFTLI56eDl9b0
2. Click: **Create Credentials** → **API Key**
3. **Important**: Restrict the API key:
   - Click on the newly created key to edit
   - Under "API restrictions":
     - Select "Restrict key"
     - Check: ☑ Places API (New)
     - Check: ☑ Routes API (if using drive distances)
   - Under "Application restrictions" (optional but recommended):
     - Select "IP addresses"
     - Add your server's IP address
4. **Copy the API key** - you'll need it for the `.env` file

### 2D. Set Up Billing Alert >> DONE, ive done this. 

1. In Google Cloud Console
2. Navigate to: **Billing** → **Budgets & alerts**
3. Click: **Create Budget**
4. Set budget amount: $200 (covers your entire project)
5. Set alert thresholds:
   - 50% ($100)
   - 75% ($150)
   - 90% ($180)
6. Add your email for notifications

**Estimated Time**: 15-20 minutes

---

## Step 3: Set Up Project Structure

### 3A. Create Directory Structure

```bash
cd /Users/projects/Documents/Property_Data_Scraping/06_Property_Georeference

# Create directories
mkdir -p src
mkdir -p scripts
mkdir -p tests
mkdir -p logs

# Create placeholder files
touch src/__init__.py
touch src/api_client.py
touch src/distance_calculator.py
touch src/mongodb_handler.py
touch scripts/build_poi_database.py
touch scripts/process_properties_local.py
touch .env
touch requirements.txt
```

### 3B. Create `.env` File

Create `06_Property_Georeference/.env`:

```bash
# Google Places API
GOOGLE_PLACES_API_KEY=your_api_key_here

# MongoDB
MONGODB_URI=mongodb://127.0.0.1:27017/
MONGODB_DATABASE=Gold_Coast

# Processing Configuration
BATCH_SIZE=100
NUM_WORKERS=10
MAX_API_REQUESTS_PER_SECOND=100

# Cost Control
DAILY_BUDGET_USD=50
ALERT_THRESHOLD_PERCENT=75

# Search Parameters
DEFAULT_SEARCH_RADIUS_METERS=5000
MAX_SEARCH_RADIUS_METERS=10000
```

**Replace** `your_api_key_here` with the API key from Step 2C.

### 3C. Create `.gitignore`

Add to `.gitignore`:
```
.env
logs/
*.pyc
__pycache__/
```

### 3D. Create `requirements.txt`

```
pymongo>=4.5.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### 3E. Install Dependencies

```bash
cd /Users/projects/Documents/Property_Data_Scraping/06_Property_Georeference
pip install -r requirements.txt
```

**Estimated Time**: 10 minutes

---

## Step 4: Implement Core Components

### 4A. Copy Distance Calculator Code

The implementation plan includes complete code for `distance_calculator.py` in Section 18.1.

**Action**:
1. Open `GEOREFERENCE_IMPLEMENTATION_PLAN.md`
2. Find Section 18.1
3. Copy the entire `DistanceCalculator` class
4. Paste into `src/distance_calculator.py`

### 4B. Copy API Client Code

The implementation plan includes complete code for `api_client.py` in Section 18.2.

**Action**:
1. Find Section 18.2 in the plan
2. Copy the entire `GooglePlacesClient` class
3. Paste into `src/api_client.py`

### 4C. Copy Build POI Database Script

The implementation plan includes complete code in Section 5A.6.

**Action**:
1. Find Section 5A.6 - Script 1
2. Copy the entire `build_poi_database.py` script
3. Paste into `scripts/build_poi_database.py`

### 4D. Copy Process Properties Script

**Action**:
1. Find Section 5A.6 - Script 2
2. Copy the entire `process_properties_local.py` script
3. Paste into `scripts/process_properties_local.py`

**Estimated Time**: 15 minutes

---

## Step 5: Validate Setup

### 5A. Test MongoDB Connection

```bash
cd /Users/projects/Documents/Property_Data_Scraping/06_Property_Georeference

# Test MongoDB connection
python3 -c "
from pymongo import MongoClient
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']
collections = db.list_collection_names()
print(f'Connected! Found {len(collections)} collections')
print(f'Sample collections: {collections[:5]}')
"
```

Expected output:
```
Connected! Found XX collections
Sample collections: ['Robina', 'Burleigh', ...]
```

### 5B. Test API Key

```bash
# Test Google Places API
python3 -c "
import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv('GOOGLE_PLACES_API_KEY')

url = 'https://places.googleapis.com/v1/places:searchNearby'
headers = {
    'X-Goog-Api-Key': api_key,
    'X-Goog-FieldMask': 'places.displayName'
}
payload = {
    'includedTypes': ['school'],
    'maxResultCount': 1,
    'locationRestriction': {
        'circle': {
            'center': {'latitude': -28.110, 'longitude': 153.407},
            'radius': 5000
        }
    }
}

response = requests.post(url, json=payload, headers=headers)
if response.status_code == 200:
    print('✓ API Key Valid!')
    print(f'Response: {response.json()}')
else:
    print(f'✗ API Error: {response.status_code}')
    print(f'Response: {response.text}')
"
```

Expected output:
```
✓ API Key Valid!
Response: {'places': [{'displayName': {'text': '...'}}]}
```

**Estimated Time**: 5 minutes

---

## Step 6: Build POI Database (Phase 1)

### 6A. Run POI Database Builder

```bash
cd /Users/projects/Documents/Property_Data_Scraping/06_Property_Georeference

# Make script executable
chmod +x scripts/build_poi_database.py

# Run the script
python3 scripts/build_poi_database.py
```

This will:
- Generate ~45 grid points covering Gold Coast
- Make ~135 API calls
- Collect all POIs in the region
- Store in MongoDB collection `gold_coast_pois`
- **Cost**: ~$4-10
- **Time**: ~30-45 minutes

### 6B. Monitor Progress

The script will output:
```
================================================================================
BUILDING GOLD COAST POI DATABASE
================================================================================

Creating indexes...
Generated 45 grid points
Expected API calls: ~135 (with category grouping)

[1/45] Processing grid point...
Collecting POIs for grid_0_0 (-27.7500, 153.2500)
  → Collected 15 new POIs

...

================================================================================
POI DATABASE BUILD COMPLETE
================================================================================
primary_school      :   234 POIs
secondary_school    :    89 POIs
childcare          :   156 POIs
supermarket        :   178 POIs
...

Total POIs in database: 1,456
API calls made: 135
Total cost: $4.32
================================================================================
```

### 6C. Verify POI Database

```bash
# Check POI database
python3 -c "
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']
poi_collection = db['gold_coast_pois']

total = poi_collection.count_documents({})
print(f'Total POIs in database: {total:,}')

# Count by category
pipeline = [
    {'$group': {'_id': '$poi_type', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
for result in poi_collection.aggregate(pipeline):
    print(f'{result[\"_id\"]:20s}: {result[\"count\"]:5,} POIs')
"
```

**Estimated Time**: 30-45 minutes

---

## Step 7: Process Properties (Phase 2)

### 7A. Test with Single Property First

Before processing all 6,950 properties, test with one:

```bash
cd /Users/projects/Documents/Property_Data_Scraping/06_Property_Georeference

# Modify process_properties_local.py temporarily
# Change the query to limit to 1 property for testing
python3 scripts/process_properties_local.py
```

Verify the output structure in MongoDB:
```bash
python3 -c "
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']

# Find a property with georeference_data
for collection_name in ['Robina', 'Burleigh']:  # Adjust as needed
    collection = db[collection_name]
    property = collection.find_one({'georeference_data': {'$exists': True}})
    if property:
        print(f'Found test property in {collection_name}')
        print(f'Address: {property.get(\"complete_address\")}')
        print(f'Georeference data keys: {list(property[\"georeference_data\"].keys())}')
        print(f'Primary schools found: {len(property[\"georeference_data\"][\"distances\"][\"primary_schools\"])}')
        break
"
```

### 7B. Process All Properties

Once verified, process all 6,950 properties:

```bash
# Run full processing
python3 scripts/process_properties_local.py
```

This will:
- Process all 6,950 qualifying properties
- Query local POI database (no API calls)
- Calculate straight-line distances
- **Cost**: $0
- **Time**: ~10-15 minutes

**Estimated Time**: 20 minutes (including testing)

---

## Step 8: Optional - Add Drive Distances (Phase 3)

**Only do this if you need actual driving distances for valuation models.**

### Option A: Skip This Step (Recommended for Now)
- Straight-line distances are sufficient for most analyses
- Can add drive distances later if needed
- Saves ~$100-500

### Option B: Calculate Drive Distances for Schools Only
**Cost**: ~$104

Create script `scripts/add_drive_distances.py`:
- Loop through properties
- For each property, get top 3 closest schools from `georeference_data`
- Batch 25 properties at a time
- Call Distance Matrix API
- Update properties with drive time/distance

### Option C: Calculate Drive Distances for All High-Priority POIs
**Cost**: ~$521

Same as Option B but include:
- Schools (primary + secondary)
- Childcare centers
- Shopping centers
- Hospitals

**Estimated Time**: 1-2 hours (if implementing)

---

## Step 9: Validation & Quality Check

### 9A. Check Processing Completion

```bash
python3 -c "
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']

total_with_geo = 0
collections = [col for col in db.list_collection_names() if not col.startswith('system')]

for col_name in collections:
    collection = db[col_name]
    count = collection.count_documents({'georeference_data': {'$exists': True}})
    if count > 0:
        print(f'{col_name:30s}: {count:5,} properties with georeference data')
        total_with_geo += count

print(f'\n{'Total':30s}: {total_with_geo:5,} properties processed')
"
```

### 9B. Run Sample Queries

Test that the data is useful:

```bash
python3 -c "
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']

# Find houses within 1km of primary school and 5km of beach
for col_name in ['Robina', 'Burleigh']:
    collection = db[col_name]
    
    properties = collection.find({
        'georeference_data.summary_stats.closest_primary_school_km': {'$lte': 1},
        'georeference_data.summary_stats.closest_beach_km': {'$lte': 5}
    }).limit(5)
    
    print(f'\nProperties in {col_name} near school & beach:')
    for prop in properties:
        print(f'  - {prop.get(\"complete_address\")}')
        print(f'    School: {prop[\"georeference_data\"][\"summary_stats\"][\"closest_primary_school_km\"]}km')
        print(f'    Beach: {prop[\"georeference_data\"][\"summary_stats\"][\"closest_beach_km\"]}km')
"
```

**Estimated Time**: 10 minutes

---

## Step 10: Generate Report

Create a summary report:

```bash
python3 -c "
from pymongo import MongoClient
import json

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']

report = {
    'processing_date': '2025-11-09',
    'total_properties_processed': 0,
    'average_distances': {},
    'properties_by_suburb': {}
}

collections = [col for col in db.list_collection_names() if not col.startswith('system')]

for col_name in collections:
    collection = db[col_name]
    count = collection.count_documents({'georeference_data': {'$exists': True}})
    
    if count > 0:
        report['total_properties_processed'] += count
        report['properties_by_suburb'][col_name] = count

# Calculate averages
all_properties = []
for col_name in collections:
    collection = db[col_name]
    props = collection.find({'georeference_data': {'$exists': True}})
    all_properties.extend(props)

if all_properties:
    avg_beach = sum(p['georeference_data']['summary_stats']['closest_beach_km'] 
                    for p in all_properties if p['georeference_data']['summary_stats'].get('closest_beach_km')) / len(all_properties)
    avg_school = sum(p['georeference_data']['summary_stats']['closest_primary_school_km'] 
                     for p in all_properties if p['georeference_data']['summary_stats'].get('closest_primary_school_km')) / len(all_properties)
    
    report['average_distances']['beach_km'] = round(avg_beach, 2)
    report['average_distances']['primary_school_km'] = round(avg_school, 2)

print(json.dumps(report, indent=2))

# Save to file
with open('logs/processing_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print('\nReport saved to: logs/processing_report.json')
"
```

**Estimated Time**: 5 minutes

---

## Summary: Complete Timeline

| Step | Task | Time | Cost |
|------|------|------|------|
| 1 | Review Plan | 30 min | $0 |
| 2 | API Setup | 20 min | $0 |
| 3 | Project Structure | 10 min | $0 |
| 4 | Copy Code | 15 min | $0 |
| 5 | Validate Setup | 5 min | $0 |
| 6 | Build POI Database | 45 min | **$4-10** |
| 7 | Process Properties | 20 min | $0 |
| 8 | Drive Distances (Optional) | 0-120 min | $0-521 |
| 9 | Validation | 10 min | $0 |
| 10 | Generate Report | 5 min | $0 |
| **TOTAL** | | **2-5 hours** | **$4-531** |

## Recommended Path

**For immediate start:**
1. Do Steps 1-7 today (~2 hours, ~$10 cost)
2. Skip Step 8 for now (drive distances)
3. Validate results (Steps 9-10)
4. Add drive distances later if needed for valuation

**This gives you:**
- ✓ Complete POI database
- ✓ Straight-line distances for all 6,950 properties
- ✓ All data needed for initial analysis
- ✓ Ability to add drive distances later
- ✓ Total cost: ~$10

---

## Questions or Issues?

If you encounter any problems:
1. Check logs in `logs/` directory
2. Verify API key is correct and has right permissions
3. Ensure MongoDB is running
4. Check you have enough free space for POI database (~50-100MB)

## Ready to Start?

**Next immediate action**: Begin with Step 2 (Google Cloud API Setup)
