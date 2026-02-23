# Quick Start: Update Gold Coast Database
**Last Updated:** 30/01/2026, 7:40 pm (Brisbane Time)

## 🚀 Quick Start (5 Minutes)

### Step 1: Ensure MongoDB is Running
```bash
# Check if MongoDB is running
brew services list | grep mongodb

# If not running, start it
brew services start mongodb-community
```

### Step 2: Run Single Worker Update (Test)
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 update_gold_coast_database.py
```

### Step 3: Monitor Progress (Optional)
Open a new terminal and run:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && ./monitor_update_progress.sh
```

---

## 🏃 Fast Multi-Worker Update (Recommended)

### Run 4 Workers in Parallel
Open 4 separate terminal windows and run one command in each:

**Terminal 1:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=0 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

**Terminal 2:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=1 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

**Terminal 3:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=2 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

**Terminal 4:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=3 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

**Terminal 5 (Monitor):**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && ./monitor_update_progress.sh
```

---

## 📊 What to Expect

### Initial Output
```
Connecting to MongoDB...
✓ MongoDB connected
✓ Found 81 suburb collections

Updater Worker 0/4 initialized
MongoDB: localhost
Target: Update all properties with existing scraped_data

Retrieving properties with existing scraped_data...
  robina                        :  1,234 with scraped_data
  southport                     :    987 with scraped_data
  ...

Total properties with scraped_data: 50,000
My slice: 0 to 12,500 (12,500 properties)
```

### During Processing
```
[1/12,500] [robina] 12 Carnoustie Court Robina QLD 4226
  Accessing: https://www.domain.com.au/property-profile/...
  ✓ Extracted 5 timeline events
  ✓ Data: 4bed 2bath, 15 images, 5 timeline events
  📊 Valuation changed - added to history
  ✓ Updated in MongoDB: Gold_Coast.robina
```

### Progress Updates (Every 10 Properties)
```
──────────────────────────────────────────────────────────
  📊 PROGRESS UPDATE - Worker 0
──────────────────────────────────────────────────────────
  Processed:       100 / 12,500 properties (0.8%)
  Successful:      95 (95.0%)
  Failed:          5 (5.0%)
  Elapsed time:    0.83 hours
  Current rate:    120.5 properties/hour
  Est. remaining:  102.7 hours
  Est. completion: 2026-02-04 22:12:45
──────────────────────────────────────────────────────────
```

---

## ⏱️ Estimated Completion Times

| Workers | Properties | Time to Complete |
|---------|-----------|------------------|
| 1 worker | 50,000 | ~17 days |
| 4 workers | 50,000 | ~4.3 days |
| 10 workers | 50,000 | ~1.7 days |
| 20 workers | 50,000 | ~21 hours |

*Based on ~120 properties/hour per worker*

---

## ✅ Verification

### Check if Update is Working
```bash
# Connect to MongoDB
mongosh mongodb://127.0.0.1:27017/Gold_Coast

# Check for properties with valuation_history
db.robina.findOne({"scraped_data.valuation_history": {$exists: true}})

# Count updated properties
db.robina.countDocuments({"scraped_data.valuation_history": {$exists: true}})
```

### View Valuation History
```javascript
// In mongosh
db.robina.findOne(
  {"scraped_data.valuation_history": {$exists: true}},
  {"scraped_data.address": 1, "scraped_data.valuation_history": 1}
)
```

Expected output:
```javascript
{
  scraped_data: {
    address: '12 Carnoustie Court Robina QLD 4226',
    valuation_history: [
      {
        low: 1400000,
        mid: 1530000,
        high: 1650000,
        accuracy: 'high',
        date: '2025-11-03',
        recorded_at: '2025-11-03T17:10:00'
      },
      {
        low: 1450000,
        mid: 1580000,
        high: 1700000,
        accuracy: 'high',
        date: '2026-01-30',
        recorded_at: '2026-01-30T19:30:00'
      }
    ]
  }
}
```

---

## 🛑 Stopping Workers

To stop workers gracefully:
1. Press `Ctrl+C` in each terminal
2. Wait for "Chrome driver closed" and "MongoDB connection closed" messages
3. Workers will save progress before exiting

---

## 🔧 Troubleshooting

### "MongoDB connection failed"
```bash
# Start MongoDB
brew services start mongodb-community

# Verify it's running
brew services list | grep mongodb
```

### "ChromeDriver not found"
```bash
# Install ChromeDriver
brew install chromedriver

# Verify installation
which chromedriver
```

### "No properties to update"
This means no properties have `scraped_data` yet. Run the initial scraper first:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 domain_scraper_multi_suburb_mongodb.py
```

### Workers seem stuck
- Check if Domain.com.au is accessible
- Verify MongoDB is responding
- Check system resources (CPU, memory)
- Review worker logs for error messages

---

## 📚 Full Documentation

For complete details, see:
- **UPDATE_DATABASE_README.md** - Complete usage guide
- **GOLD_COAST_DATABASE_BUILD_SUMMARY.md** - Database structure
- **IMPLEMENTATION_PLAN.md** - Development plan

---

## 💡 Tips

1. **Start with 1 worker** to test everything works
2. **Monitor progress** using the monitoring script
3. **Run during off-peak hours** to avoid rate limiting
4. **Use 4-10 workers** for optimal speed without overwhelming Domain
5. **Check logs regularly** for any errors or issues

---

## 🎯 Success Indicators

✅ Workers are processing properties  
✅ Success rate > 90%  
✅ MongoDB shows increasing `valuation_history` counts  
✅ No repeated error messages  
✅ Progress updates show reasonable completion times  

---

## Next Steps After Update

1. **Analyze valuation trends** using MongoDB queries
2. **Export data** for analysis in Excel/Python
3. **Schedule monthly updates** to track market changes
4. **Create visualizations** of property value trends

Happy updating! 🚀
