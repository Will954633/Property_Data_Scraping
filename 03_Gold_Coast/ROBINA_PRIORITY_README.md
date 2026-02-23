# Robina Priority Scraping - 20 Local Workers

## Overview

This setup deploys **20 local workers** to process **ONLY Robina addresses** as a priority task. The scraped data is saved directly to MongoDB (`Gold_Coast.robina` collection), leveraging your local PC's 80% idle capacity.

## Key Features

✅ **20 parallel workers** running locally  
✅ **Robina addresses only** (~11,761 addresses)  
✅ **Direct MongoDB storage** - Gold_Coast database, robina collection  
✅ **Automatic resume** - skips already-scraped addresses  
✅ **Complete data extraction** - features, valuations, rental estimates, timeline, images  
✅ **Retry logic** - handles rate limiting and transient errors  
✅ **Real-time monitoring** - track progress across all workers  

## Files Created

1. **`domain_scraper_robina_mongodb.py`** - Specialized scraper for Robina addresses with MongoDB storage
2. **`start_20_robina_workers.sh`** - Launcher script for 20 workers
3. **`monitor_robina_workers.sh`** - Monitoring dashboard for worker progress

## Prerequisites

### 1. MongoDB Running Locally
```bash
# Check if MongoDB is running
mongosh --eval "db.version()"

# If not running, start MongoDB:
brew services start mongodb-community
# OR
mongod --config /opt/homebrew/etc/mongod.conf
```

### 2. Python Dependencies
```bash
pip3 install selenium pymongo
```

### 3. ChromeDriver
```bash
# Install ChromeDriver (macOS)
brew install --cask chromedriver

# Verify installation
which chromedriver
```

### 4. Robina Collection in MongoDB
The script expects the `robina` collection to exist in the `Gold_Coast` database with address documents.

## Quick Start

### Step 1: Make Scripts Executable
```bash
cd 03_Gold_Coast
chmod +x start_20_robina_workers.sh
chmod +x monitor_robina_workers.sh
```

### Step 2: Start Workers (DON'T RUN YET - WAIT FOR APPROVAL)
```bash
./start_20_robina_workers.sh
```

This will:
- Check all dependencies (Python, MongoDB, ChromeDriver)
- Verify MongoDB connection and Robina collection
- Launch 20 workers in parallel (Worker IDs: 0-19)
- Create logs in `robina_worker_logs/` directory

### Step 3: Monitor Progress
```bash
./monitor_robina_workers.sh
```

This displays:
- Total addresses and scraped count
- Progress percentage
- Running worker count
- Recent activity from each worker

## Expected Performance

| Metric | Value |
|--------|-------|
| Total Addresses | ~11,761 |
| Workers | 20 |
| Addresses per Worker | ~588 |
| Rate per Worker | ~120 addresses/hour |
| **Total Completion Time** | **~5 hours** |

## Monitoring Options

### Option 1: Dashboard View
```bash
./monitor_robina_workers.sh
```

### Option 2: Watch All Worker Logs
```bash
tail -f robina_worker_logs/worker_*.log
```

### Option 3: Watch Specific Worker
```bash
tail -f robina_worker_logs/worker_0.log
```

### Option 4: Check MongoDB Directly
```bash
# Count scraped addresses
mongosh --eval "db.getSiblingDB('Gold_Coast').robina.countDocuments({scraped_data: {\$exists: true}})"

# View a sample scraped document
mongosh --eval "db.getSiblingDB('Gold_Coast').robina.findOne({scraped_data: {\$exists: true}})"
```

### Option 5: Check Running Processes
```bash
ps aux | grep domain_scraper_robina_mongodb.py
```

## Data Structure

Each MongoDB document in the `robina` collection will be updated with a `scraped_data` field containing:

```javascript
{
  "_id": ObjectId("..."),
  "ADDRESS_PID": 1234567,
  "STREET_NO_1": "15",
  "STREET_NAME": "MAIN",
  "STREET_TYPE": "STREET",
  "LOCALITY": "ROBINA",
  // ... other address fields ...
  
  // NEW: Scraped data added by workers
  "scraped_data": {
    "url": "https://www.domain.com.au/property-profile/...",
    "address": "15 MAIN STREET ROBINA QLD 4226",
    "scraped_at": "2025-01-06T20:15:30.123456",
    "worker_id": 5,
    "features": {
      "bedrooms": 4,
      "bathrooms": 2,
      "car_spaces": 2,
      "land_size": 450,
      "property_type": "House"
    },
    "valuation": {
      "low": 850000,
      "mid": 900000,
      "high": 950000,
      "accuracy": "High",
      "date": "2025-01-01"
    },
    "rental_estimate": {
      "weekly_rent": 650,
      "yield": 3.75
    },
    "property_timeline": [
      {
        "date": "2024-03-15",
        "month_year": "Mar 2024",
        "category": "Sold",
        "type": "Sold",
        "price": 875000,
        "days_on_market": 21,
        "is_major_event": true,
        "agency_name": "Example Realty",
        "agency_url": "https://www.domain.com.au/...",
        "is_sold": true
      },
      // ... more timeline events
    ],
    "images": [
      {
        "url": "https://bucket.cloud.domain.com.au/...",
        "index": 0,
        "date": "2024-03-01"
      },
      // ... up to 20 images
    ]
  },
  "scraped_at": ISODate("2025-01-06T20:15:30.123Z")
}
```

## Worker Management

### Stop All Workers
```bash
pkill -f domain_scraper_robina_mongodb.py
```

### Restart Workers
```bash
./start_20_robina_workers.sh
```

The script automatically resumes from where it left off - it skips addresses that already have `scraped_data`.

### Stop a Specific Worker
```bash
# Find the PID
ps aux | grep domain_scraper_robina_mongodb.py

# Kill specific process
kill <PID>
```

## Troubleshooting

### Issue: "MongoDB connection failed"
**Solution:**
```bash
# Check MongoDB status
brew services list | grep mongodb

# Start MongoDB
brew services start mongodb-community

# Test connection
mongosh --eval "db.version()"
```

### Issue: "ChromeDriver not found"
**Solution:**
```bash
# Install ChromeDriver
brew install --cask chromedriver

# If permission issues on macOS:
xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
```

### Issue: Workers crashing
**Check logs:**
```bash
tail -n 50 robina_worker_logs/worker_0.log
```

Common causes:
- Rate limiting by Domain.com.au (script has retry logic)
- Memory issues (reduce worker count to 10-15)
- Chrome/ChromeDriver mismatch

### Issue: Slow progress
**Check:**
- Network speed
- Domain.com.au response times
- CPU/Memory usage: `top` or `htop`

**Reduce workers if needed:**
Edit `start_20_robina_workers.sh` and change:
```bash
TOTAL_WORKERS=15  # Reduce from 20
```

## Architecture

### Data Flow
```
MongoDB (Gold_Coast.robina)
    ↓
Workers read addresses (filtered: no scraped_data)
    ↓
Each worker gets 1/20th of unscraped addresses
    ↓
Worker scrapes Domain.com.au
    ↓
Data extracted from page JSON and HTML
    ↓
Data saved back to same MongoDB document
    ↓
Progress tracked in real-time
```

### Worker Distribution
- **Worker 0:** Addresses 0 - 587
- **Worker 1:** Addresses 588 - 1175
- **Worker 2:** Addresses 1176 - 1763
- ...
- **Worker 19:** Addresses 11174 - 11761 (last worker gets remainder)

### Rate Limiting
- 3-second delay between requests per worker
- Retry logic with exponential backoff (30s, 60s, 90s)
- Automatic skip of already-scraped addresses

## Comparison to Other Workers

| Aspect | Robina Priority | Standard Workers |
|--------|----------------|------------------|
| Target | Robina only | All suburbs |
| Storage | MongoDB direct | Google Cloud Storage |
| Workers | 20 local | Varies (cloud) |
| Collection | `robina` | Multiple collections |
| Resume | Automatic | Manual |

## Next Steps After Completion

Once all Robina addresses are scraped:

1. **Verify completion:**
   ```bash
   mongosh --eval "db.getSiblingDB('Gold_Coast').robina.countDocuments({scraped_data: {\$exists: true}})"
   ```

2. **Export to JSON (optional):**
   ```bash
   mongoexport --db=Gold_Coast --collection=robina --out=robina_complete.json
   ```

3. **Stop workers:**
   ```bash
   pkill -f domain_scraper_robina_mongodb.py
   ```

4. **Analyze data:**
   - Average property values
   - Rental yields
   - Property types distribution
   - Sales timeline trends

## Configuration

### Change Worker Count
Edit `start_20_robina_workers.sh`:
```bash
TOTAL_WORKERS=20  # Change this value
```

### Change MongoDB Connection
Edit `start_20_robina_workers.sh`:
```bash
MONGODB_URI="mongodb://127.0.0.1:27017/"  # Change to remote MongoDB if needed
```

### Change Rate Limiting
Edit `domain_scraper_robina_mongodb.py`:
```python
time.sleep(3)  # Change delay between requests (line ~465)
```

## Support

For issues or questions:
1. Check logs: `tail -f robina_worker_logs/worker_*.log`
2. Review this README
3. Check MongoDB connection and data

---

**Status:** Ready to deploy (DO NOT RUN YET - AWAITING APPROVAL)

**Created:** January 6, 2025  
**Version:** 1.0
