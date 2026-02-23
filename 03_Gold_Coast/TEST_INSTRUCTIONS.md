# Test Instructions - 10 Property Update Test
**Last Updated:** 30/01/2026, 8:12 pm (Brisbane Time)

## 🧪 Test Script Overview

The `test_update_10_properties.py` script is currently running and will:

1. ✅ Find 10 properties with existing scraped_data
2. ✅ Backup their current state to a JSON file
3. ⏳ Update each property with fresh Domain data (currently in progress)
4. ⏳ Compare before/after states
5. ⏳ Generate detailed report showing what changed

## ⏱️ Expected Duration

- **Total time:** ~5-10 minutes
- **Per property:** ~30-60 seconds (scraping + processing)
- The script is running in the background

## 📊 What the Test Will Show

For each of the 10 properties, you'll see:

### 1. Valuation Comparison
```
📊 VALUATION:
  BEFORE: Low=$1,400,000 Mid=$1,530,000 High=$1,650,000
  AFTER:  Low=$1,450,000 Mid=$1,580,000 High=$1,700,000
  ✓ HISTORY: 2 entries
    1. Mid=$1,530,000 @ 2025-11-03T17:10:00
    2. Mid=$1,580,000 @ 2026-01-30T20:12:00
```

### 2. Rental Estimate Comparison
```
🏠 RENTAL ESTIMATE:
  BEFORE: $850/week, 2.9% yield
  AFTER:  $900/week, 3.0% yield
  ✓ HISTORY: 2 entries
    1. $850/week @ 2025-11-03T17:10:00
    2. $900/week @ 2026-01-30T20:12:00
```

### 3. Timeline Replacement
```
📅 TIMELINE:
  BEFORE: 5 events
  AFTER:  5 events
  ✓ REPLACED with fresh timeline
    Latest event: For Sale - 2026-01-15
```

### 4. Images Replacement
```
🖼️  IMAGES:
  BEFORE: 15 images
  AFTER:  15 images
  ✓ REPLACED with fresh images
```

## 📁 Output Files

The test creates a backup file:
```
test_backup_YYYYMMDD_HHMMSS.json
```

This contains the complete before-state of all 10 properties for reference.

## ✅ Success Criteria

The test passes if:
- ✅ All 10 properties update successfully
- ✅ `valuation_history` arrays are created/appended
- ✅ `rental_estimate_history` arrays are created/appended
- ✅ `property_timeline` is replaced with fresh data
- ✅ `images` are replaced with fresh data
- ✅ `updated_at` timestamp is set

## 🔍 Checking Test Progress

### Option 1: Check the log file
```bash
tail -f /var/folders/t6/rnm9m1ds6qxg8t7224_j12j80000gn/T/cline/background-1769767970766-oda3ffg.log
```

### Option 2: Check MongoDB directly
```bash
mongosh mongodb://127.0.0.1:27017/Gold_Coast

# Count properties with valuation_history
db.robina.countDocuments({"scraped_data.valuation_history": {$exists: true}})

# View a property with history
db.robina.findOne(
  {"scraped_data.valuation_history": {$exists: true}},
  {"scraped_data.address": 1, "scraped_data.valuation_history": 1}
)
```

### Option 3: Wait for completion
The script will output a final summary when complete:
```
======================================================================
TEST COMPLETE
======================================================================

Backup saved to: test_backup_20260130_201200.json
Total properties tested: 10
Successful updates: 10
Failed updates: 0

✅ ALL TESTS PASSED - Update system working correctly!
```

## 🐛 If Test Fails

### Common Issues:

**1. MongoDB not running**
```bash
brew services start mongodb-community
```

**2. ChromeDriver not found**
```bash
brew install chromedriver
```

**3. No properties with scraped_data**
Run the initial scraper first:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 domain_scraper_multi_suburb_mongodb.py
```

**4. Domain.com.au rate limiting**
- Wait a few minutes
- Reduce number of test properties
- Check internet connection

## 📋 After Test Completes

### 1. Review the detailed output
Look for:
- ✅ Green checkmarks indicating success
- 📊 History arrays being populated
- ⚠️ Any warnings or errors

### 2. Verify in MongoDB
```javascript
// Check one of the updated properties
db.robina.findOne(
  {"updated_at": {$exists: true}},
  {
    "scraped_data.address": 1,
    "scraped_data.valuation": 1,
    "scraped_data.valuation_history": 1,
    "scraped_data.rental_estimate": 1,
    "scraped_data.rental_estimate_history": 1,
    "updated_at": 1
  }
)
```

### 3. Check the backup file
```bash
# View the backup
cat test_backup_*.json | jq '.[0].before.valuation'
```

## ✨ If Test Passes

You're ready to run the full update! Choose one:

**Single worker (slow but safe):**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 update_gold_coast_database.py
```

**4 workers (recommended):**
```bash
# Terminal 1
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=0 TOTAL_WORKERS=4 python3 update_gold_coast_database.py

# Terminal 2
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=1 TOTAL_WORKERS=4 python3 update_gold_coast_database.py

# Terminal 3
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=2 TOTAL_WORKERS=4 python3 update_gold_coast_database.py

# Terminal 4
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=3 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

## 🔄 Re-running the Test

To run the test again:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 test_update_10_properties.py
```

Each run creates a new backup file with timestamp, so previous tests are preserved.

## 📞 Need Help?

1. Check the log file for errors
2. Review UPDATE_DATABASE_README.md for troubleshooting
3. Verify MongoDB and ChromeDriver are installed
4. Check that properties have existing scraped_data

---

**The test is currently running. It will complete in approximately 5-10 minutes.**
