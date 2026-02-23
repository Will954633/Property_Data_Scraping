# Gold Coast Address Importer

This system imports all Gold Coast addresses from the Queensland property location data file into a MongoDB database.

## Overview

- **Source Data**: Queensland Property Location Index (DP_PROP_LOCATION_INDEX_QLD_20251103.txt)
- **Target Database**: MongoDB at `mongodb://127.0.0.1:27017/`
- **Database Name**: `Gold_Coast`
- **Records**: ~331,224 addresses across 81 suburbs
- **Organization**: One collection per suburb, one document per address

## Features

- ✓ Filters addresses for "GOLD COAST CITY" local authority
- ✓ Creates sanitized collection names from suburb names
- ✓ Preserves all 24 data fields from source file
- ✓ Batch inserts for optimal performance (1000 documents per batch)
- ✓ Real-time progress tracking
- ✓ Comprehensive error handling
- ✓ Automatic type conversion (numeric fields)
- ✓ Detailed import summary and statistics

## Data Structure

Each address document contains 24 fields:

### Identification
- `ADDRESS_PID` - Unique address identifier
- `PLAN` - Plan number
- `LOT` - Lot number
- `LOTPLAN_STATUS` - Status of lot/plan
- `ADDRESS_STATUS` - Address status
- `ADDRESS_STANDARD` - Standard classification

### Property Details
- `UNIT_TYPE` - Unit type (if applicable)
- `UNIT_NUMBER` - Unit number
- `UNIT_SUFFIX` - Unit suffix
- `PROPERTY_NAME` - Property name

### Street Address
- `STREET_NO_1` - Primary street number
- `STREET_NO_1_SUFFIX` - Suffix for primary street number
- `STREET_NO_2` - Secondary street number (for ranges)
- `STREET_NO_2_SUFFIX` - Suffix for secondary street number
- `STREET_NAME` - Street name
- `STREET_TYPE` - Street type (ROAD, STREET, etc.)
- `STREET_SUFFIX` - Street suffix

### Location
- `LOCALITY` - Suburb/locality name
- `LOCAL_AUTHORITY` - Local government area
- `LGA_CODE` - LGA code
- `LATITUDE` - Geographic latitude
- `LONGITUDE` - Geographic longitude
- `GEOCODE_TYPE` - Type of geocoding
- `DATUM` - Geodetic datum (e.g., GDA94)

## Prerequisites

### 1. MongoDB Installation

**macOS (using Homebrew):**
```bash
# Install MongoDB Community Edition
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community

# Verify MongoDB is running
mongosh --eval "db.adminCommand('ping')"
```

**Alternative - Manual Start:**
```bash
mongod --config /opt/homebrew/etc/mongod.conf --fork
```

### 2. Python and Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

Or manually:
```bash
pip install pymongo
```

## Installation

1. Navigate to the Gold Coast directory:
```bash
cd 03_Gold_Coast
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure MongoDB is running:
```bash
brew services list | grep mongodb
# Should show "started"
```

## Usage

### Basic Import

```bash
python3 gold_coast_importer.py
```

### What Happens During Import

1. **Connection**: Connects to MongoDB at `mongodb://127.0.0.1:27017/`
2. **Database**: Creates/clears the `Gold_Coast` database
3. **Processing**: Reads the source file line-by-line
4. **Filtering**: Extracts only "GOLD COAST CITY" addresses
5. **Organizing**: Groups addresses by suburb (LOCALITY field)
6. **Importing**: Batch inserts documents into suburb collections
7. **Summary**: Displays comprehensive statistics

### Expected Output

```
======================================================================
Gold Coast Address Importer
======================================================================

✓ Connected to MongoDB at mongodb://127.0.0.1:27017/
✓ Using database: Gold_Coast
  Dropping existing database...

✓ Reading data from: /Users/projects/Documents/Fetcha_Addresses/QLD/DP_PROP_LOCATION_INDEX_QLD_20251103.txt
✓ Filtering for: GOLD COAST CITY

Processing addresses...

  Processed: 10,000 lines | Imported: xxx addresses | Suburbs: xx
  Processed: 20,000 lines | Imported: xxx addresses | Suburbs: xx
  ...

✓ Inserting remaining batches...

======================================================================
Import Summary
======================================================================

Total lines processed:    xxx,xxx
Total addresses imported: 331,224
Total suburbs:            81
Errors encountered:       0
Duration:                 0:xx:xx

Database: Gold_Coast
Collections created:      81

======================================================================
Top 20 Suburbs by Address Count
======================================================================

  SURFERS PARADISE                         xx,xxx → surfers_paradise
  SOUTHPORT                                xx,xxx → southport
  ...

======================================================================
✓ Import completed successfully!
======================================================================
```

## Collection Naming

Suburb names are sanitized to create valid MongoDB collection names:

- Spaces replaced with underscores
- Special characters removed
- Converted to lowercase
- Consecutive underscores consolidated

**Examples:**
- "SURFERS PARADISE" → `surfers_paradise`
- "CEDAR CREEK (GOLD COAST CITY)" → `cedar_creek_gold_coast_city`
- "BROADBEACH WATERS" → `broadbeach_waters`

## Querying the Database

### Using mongosh (MongoDB Shell)

```bash
# Connect to MongoDB
mongosh

# Switch to Gold_Coast database
use Gold_Coast

# List all collections (suburbs)
show collections

# Count documents in a collection
db.surfers_paradise.countDocuments()

# Find addresses on a specific street
db.southport.find({ "STREET_NAME": "QUEEN" }).limit(5)

# Find addresses with coordinates
db.broadbeach.find({
  "LATITUDE": { $ne: null },
  "LONGITUDE": { $ne: null }
}).limit(5)

# Get all addresses in a suburb
db.burleigh_heads.find().pretty()

# Count addresses per suburb (example)
db.getCollectionNames().forEach(function(collName) {
  var count = db[collName].countDocuments();
  print(collName + ": " + count);
})
```

### Using Python

```python
from pymongo import MongoClient

# Connect to database
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Gold_Coast"]

# Get all collections (suburbs)
collections = db.list_collection_names()
print(f"Total suburbs: {len(collections)}")

# Query a specific suburb
surfers_paradise = db["surfers_paradise"]
addresses = surfers_paradise.find({"STREET_TYPE": "BOULEVARD"}).limit(5)

for address in addresses:
    print(f"{address['STREET_NO_1']} {address['STREET_NAME']} {address['STREET_TYPE']}")

# Get address by coordinates
result = db["southport"].find_one({
    "LATITUDE": {"$exists": True},
    "LONGITUDE": {"$exists": True}
})
print(f"Location: {result['LATITUDE']}, {result['LONGITUDE']}")
```

## Performance

- **Import Time**: Approximately 5-15 minutes (depending on system)
- **Batch Size**: 1000 documents per insert
- **Memory Usage**: Efficient streaming (line-by-line reading)
- **Database Size**: ~150-300 MB (after import)

## Troubleshooting

### MongoDB Connection Failed

**Error**: `Failed to connect to MongoDB`

**Solutions**:
1. Check if MongoDB is running:
   ```bash
   ps aux | grep mongod
   ```

2. Start MongoDB:
   ```bash
   brew services start mongodb-community
   ```

3. Verify connection:
   ```bash
   mongosh --eval "db.adminCommand('ping')"
   ```

### Data File Not Found

**Error**: `Data file not found`

**Solution**: Verify the file path in the script matches your actual file location:
```python
DATA_FILE = "/Users/projects/Documents/Fetcha_Addresses/QLD/DP_PROP_LOCATION_INDEX_QLD_20251103.txt"
```

### Import Taking Too Long

**Solutions**:
- Ensure you're not running other heavy processes
- Check disk space: `df -h`
- Monitor MongoDB logs: `tail -f /opt/homebrew/var/log/mongodb/mongo.log`

### Interrupted Import

If the import is interrupted, simply run the script again. The database is dropped and recreated at the start of each run, ensuring a clean import.

## Configuration

You can modify these settings at the top of `gold_coast_importer.py`:

```python
MONGODB_URI = "mongodb://127.0.0.1:27017/"  # MongoDB connection string
DATABASE_NAME = "Gold_Coast"                 # Database name
DATA_FILE = "..."                            # Source data file path
FILTER_AUTHORITY = "GOLD COAST CITY"         # Local authority filter
BATCH_SIZE = 1000                            # Documents per batch insert
```

## File Structure

```
03_Gold_Coast/
├── gold_coast_importer.py    # Main import script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Data Source

The source data file contains addresses for all of Queensland. This importer:
- Filters for entries where `LOCAL_AUTHORITY = "GOLD COAST CITY"`
- Extracts all 24 fields for each address
- Organizes by the `LOCALITY` field (suburb name)

## License

This tool is provided as-is for data processing purposes.
