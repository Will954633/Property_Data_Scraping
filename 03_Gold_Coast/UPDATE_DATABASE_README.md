# Gold Coast Database Update Guide
**Last Updated:** 30/01/2026, 7:38 pm (Brisbane Time)

## Overview
The `update_gold_coast_database.py` script updates the Gold Coast database with fresh Domain.com.au data while preserving historical valuations and rental estimates.

## Update Strategy

### What Gets REPLACED (Always Current):
- ✅ `property_timeline` - Fresh timeline events from Domain
- ✅ `images` - Current property images

### What Gets PRESERVED (History Tracking):
- 📊 `valuation_history` - Array of all historical valuations with timestamps
- 📊 `rental_estimate_history` - Array of all historical rental estimates with timestamps

### What Stays UNCHANGED:
- All base address fields (ADDRESS_PID, LOT, PLAN, etc.)
- Cadastral data (lot_area, tenure, parcel_typ, etc.)
- Postcode
- Features (bedrooms, bathrooms, etc.)

## Requirements

### System Requirements
- Python 3.7+
- MongoDB running locally or accessible via URI
- Chrome/Chromium browser
- ChromeDriver installed

### Python Dependencies
```bash
pip install pymongo selenium
```

### ChromeDriver Installation
**macOS:**
```bash
brew install chromedriver
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install chromium-chromedriver
```

## Usage

### Single Worker (Local Testing)
Update all properties with existing scraped_data:

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 update_gold_coast_database.py
```

### Multi-Worker Deployment
For faster processing, run multiple workers in parallel:

**Worker 0 of 4:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=0 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

**Worker 1 of 4:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=1 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

**Worker 2 of 4:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=2 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

**Worker 3 of 4:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && WORKER_ID=3 TOTAL_WORKERS=4 python3 update_gold_coast_database.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKER_ID` | 0 | Worker identifier (0-indexed) |
| `TOTAL_WORKERS` | 1 | Total number of parallel workers |
| `MONGODB_URI` | `mongodb://127.0.0.1:27017/` | MongoDB connection string |

### Custom MongoDB URI
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && MONGODB_URI="mongodb://username:password@host:port/" python3 update_gold_coast_database.py
```

## How It Works

### 1. Initialization
- Connects to MongoDB Gold_Coast database
- Discovers all suburb collections
- Calculates worker's slice of properties

### 2. Property Selection
- Finds all documents with existing `scraped_data` field
- Distributes properties evenly across workers
- Sorts by suburb and address for consistent ordering

### 3. Update Process
For each property:
1. **Scrape fresh data** from Domain.com.au
2. **Replace** `property_timeline` and `images` with fresh data
3. **Compare** new valuation with existing valuation
   - If changed: Append to `valuation_history` array
   - If unchanged: Preserve existing history
4. **Compare** new rental estimate with existing rental estimate
   - If changed: Append to `rental_estimate_history` array
   - If unchanged: Preserve existing history
5. **Update** MongoDB document with new data

### 4. Rate Limiting
- 3 seconds between requests to avoid overwhelming Domain.com.au
- Retry logic with exponential backoff for failed requests

## Document Structure After Update

```javascript
{
  // BASE FIELDS (unchanged)
  "ADDRESS_PID": 123456,
  "LOT": "12",
  "PLAN": "SP123456",
  // ... other base fields
  
  // CADASTRAL DATA (unchanged)
  "lot_area": 819,
  "tenure": "Freehold",
  // ... other cadastral fields
  
  // UPDATED SCRAPED DATA
  "scraped_data": {
    "url": "https://www.domain.com.au/property-profile/...",
    "address": "12 Carnoustie Court Robina QLD 4226",
    "scraped_at": "2026-01-30T19:30:00",
    
    "features": { /* unchanged */ },
    
    // CURRENT VALUATION (replaced)
    "valuation": {
      "low": 1450000,
      "mid": 1580000,
      "high": 1700000,
      "accuracy": "high",
      "date": "2026-01-30"
    },
    
    // CURRENT RENTAL ESTIMATE (replaced)
    "rental_estimate": {
      "weekly_rent": 900,
      "yield": 3.0
    },
    
    // REPLACED TIMELINE (always current)
    "property_timeline": [
      {
        "date": "2026-01-15",
        "month_year": "Jan 2026",
        "category": "listing",
        "type": "For Sale",
        "price": 1580000,
        // ... more fields
      }
      // ... more events
    ],
    
    // REPLACED IMAGES (always current)
    "images": [
      {
        "url": "https://bucket-api.domain.com.au/...",
        "index": 0,
        "date": "2026-01-30"
      }
      // ... more images
    ],
    
    // VALUATION HISTORY (append-only)
    "valuation_history": [
      {
        "low": 1350000,
        "mid": 1450000,
        "high": 1550000,
        "accuracy": "high",
        "date": "2025-01-15",
        "recorded_at": "2025-01-15T10:00:00"
      },
      {
        "low": 1400000,
        "mid": 1530000,
        "high": 1650000,
        "accuracy": "high",
        "date": "2025-11-03",
        "recorded_at": "2025-11-03T17:10:00"
      },
      {
        "low": 1450000,
        "mid": 1580000,
        "high": 1700000,
        "accuracy": "high",
        "date": "2026-01-30",
        "recorded_at": "2026-01-30T19:30:00"
      }
    ],
    
    // RENTAL ESTIMATE HISTORY (append-only)
    "rental_estimate_history": [
      {
        "weekly_rent": 800,
        "yield": 2.7,
        "recorded_at": "2025-01-15T10:00:00"
      },
      {
        "weekly_rent": 850,
        "yield": 2.9,
        "recorded_at": "2025-11-03T17:10:00"
      },
      {
        "weekly_rent": 900,
        "yield": 3.0,
        "recorded_at": "2026-01-30T19:30:00"
      }
    ]
  },
  
  "updated_at": "2026-01-30T19:30:00"
}
```

## Performance

### Expected Rates
- **Single worker:** ~120 properties/hour
- **4 workers:** ~480 properties/hour
- **10 workers:** ~1,200 properties/hour

### Estimated Duration
For ~331,224 properties (if all have scraped_data):
- **Single worker:** ~2,760 hours (~115 days)
- **4 workers:** ~690 hours (~29 days)
- **10 workers:** ~276 hours (~11.5 days)
- **50 workers:** ~55 hours (~2.3 days)

## Monitoring Progress

The script provides real-time progress updates every 10 properties:

```
──────────────────────────────────────────────────────────
  📊 PROGRESS UPDATE - Worker 0
──────────────────────────────────────────────────────────
  Processed:       100 / 1,000 properties (10.0%)
  Successful:      95 (95.0%)
  Failed:          5 (5.0%)
  Elapsed time:    0.83 hours
  Current rate:    120.5 properties/hour
  Est. remaining:  7.47 hours
  Est. completion: 2026-01-31 03:15:23
──────────────────────────────────────────────────────────
```

## Recommended Update Frequency

### Monthly Updates (Recommended)
- Captures seasonal market trends
- Tracks quarterly valuation changes
- Reasonable data freshness

### Quarterly Updates
- Lower scraping load
- Still captures major market movements
- Good for stable markets

### Weekly Updates (Not Recommended)
- High scraping load
- Minimal data changes week-to-week
- Risk of rate limiting

## Troubleshooting

### MongoDB Connection Failed
```
Error: MongoDB connection failed: [Errno 61] Connection refused
```
**Solution:** Ensure MongoDB is running:
```bash
brew services start mongodb-community
# or
sudo systemctl start mongod
```

### ChromeDriver Not Found
```
Error: 'chromedriver' executable needs to be in PATH
```
**Solution:** Install ChromeDriver:
```bash
brew install chromedriver  # macOS
# or
sudo apt-get install chromium-chromedriver  # Linux
```

### Rate Limiting / Empty Timeline
```
⚠ Empty timeline - retrying after delay...
```
**Solution:** The script automatically retries with exponential backoff. If persistent, reduce number of workers or increase delay between requests.

### No Properties to Update
```
No properties to update
```
**Solution:** This means no properties have existing `scraped_data`. Run the initial scraper first:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 domain_scraper_multi_suburb_mongodb.py
```

## Cloud Deployment

For faster updates, deploy workers to cloud instances:

### AWS EC2 / Google Cloud / DigitalOcean
1. Launch multiple instances
2. Install dependencies on each
3. Set unique `WORKER_ID` for each instance
4. Point all workers to same MongoDB (use MongoDB Atlas or self-hosted)
5. Run update script on each instance

Example for 10 cloud workers:
```bash
# Instance 0
WORKER_ID=0 TOTAL_WORKERS=10 MONGODB_URI="mongodb://..." python3 update_gold_coast_database.py

# Instance 1
WORKER_ID=1 TOTAL_WORKERS=10 MONGODB_URI="mongodb://..." python3 update_gold_coast_database.py

# ... etc
```

## Data Analysis Examples

### Query Properties with Valuation Increases
```javascript
db.robina.find({
  "scraped_data.valuation_history.1": { $exists: true }
}).forEach(doc => {
  const history = doc.scraped_data.valuation_history;
  const first = history[0].mid;
  const latest = history[history.length - 1].mid;
  const increase = ((latest - first) / first * 100).toFixed(2);
  
  if (increase > 10) {
    print(`${doc.scraped_data.address}: +${increase}% (${first} → ${latest})`);
  }
});
```

### Average Rental Yield by Suburb
```javascript
db.robina.aggregate([
  { $match: { "scraped_data.rental_estimate.yield": { $exists: true } } },
  { $group: {
    _id: "$scraped_data.suburb",
    avgYield: { $avg: "$scraped_data.rental_estimate.yield" },
    count: { $sum: 1 }
  }},
  { $sort: { avgYield: -1 } }
]);
```

## Support

For issues or questions:
1. Check this README
2. Review the implementation plan: `IMPLEMENTATION_PLAN.md`
3. Review the database build summary: `GOLD_COAST_DATABASE_BUILD_SUMMARY.md`
4. Check script logs for error messages

## Version History

- **v1.0** (30/01/2026) - Initial release
  - Update existing scraped_data with fresh Domain data
  - Preserve valuation and rental estimate history
  - Multi-worker support
  - Automatic retry logic
