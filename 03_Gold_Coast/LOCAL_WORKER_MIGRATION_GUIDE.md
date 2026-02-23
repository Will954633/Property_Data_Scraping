# Local Worker Migration Guide
## Transition from Google Cloud to Local MongoDB System

**Date:** January 7, 2025  
**Objective:** Migrate from Google Cloud Workers to 50 Local Workers with nightly scheduling

---

## Overview

This guide walks through the complete process of:
1. Stopping all Google Cloud workers
2. Downloading JSON data from GCS to local MongoDB
3. Analyzing completion status
4. Running 50 local workers
5. Setting up nightly automated processing

---

## Prerequisites

### Required Software
- **MongoDB** running locally on `mongodb://127.0.0.1:27017/`
- **Python 3** with packages: `pymongo`, `selenium`, `google-cloud-storage`
- **ChromeDriver** installed (for Selenium)
- **gcloud CLI** authenticated

### Verify Prerequisites

```bash
# Check MongoDB
mongosh --eval "db.adminCommand('ping')"

# Check Python packages
pip3 list | grep -E "pymongo|selenium|google-cloud-storage"

# Check ChromeDriver
which chromedriver

# Check gcloud authentication
gcloud auth list
```

---

## Step 1: Stop Google Cloud Workers

Stop all running GCP instances to avoid duplicate processing and reduce costs.

```bash
cd 03_Gold_Coast
chmod +x stop_all_gcp_workers.sh
./stop_all_gcp_workers.sh
```

**What this does:**
- Lists all running `property-scraper-*` instances
- Prompts for confirmation
- Deletes all instances across all zones
- Confirms shutdown

**Expected output:**
```
Found running instances:
property-scraper-hybrid-0    us-central1-a
property-scraper-hybrid-1    us-central1-a
...

Total instances to stop: 16
Stop all 16 instances? (y/n) y

✓ All Google Cloud Workers Stopped
```

---

## Step 2: Download GCS Data to MongoDB

Import all scraped JSON files from Google Cloud Storage into local MongoDB.

```bash
# Ensure you're authenticated
gcloud auth application-default login

# Run the import
chmod +x download_gcs_to_mongodb.py
python3 download_gcs_to_mongodb.py
```

**What this does:**
- Connects to GCS bucket: `property-scraper-production-data-477306`
- Scans for all JSON files in `scraped_data/` folder
- Downloads each file and imports to MongoDB
- Organizes data by suburb in separate collections
- Updates existing documents or inserts new ones

**Expected output:**
```
======================================================================
GCS TO MONGODB IMPORT
======================================================================

✓ Connected to gs://property-scraper-production-data-477306
✓ Found 1,234 JSON files

Importing 1,234 files to MongoDB...
[500/1,234] scraped_data/worker_003/properties/...

======================================================================
IMPORT COMPLETE
======================================================================
Total files:     1,234
Imported:        1,150 (93.2%)
Skipped:         84 (already existed)
Failed:          0
Duration:        0:03:45
Rate:            5.5 files/second
```

**Duration:** ~5-10 minutes depending on data size

---

## Step 3: Analyze Completion Status

Identify which addresses are complete vs incomplete across all suburbs.

```bash
chmod +x analyze_completion_status.py
python3 analyze_completion_status.py
```

**What this does:**
- Connects to MongoDB `Gold_Coast` database
- Scans all suburb collections
- Counts total, completed, and remaining addresses
- Generates detailed statistics per suburb
- Exports remaining addresses to `remaining_addresses.json`

**Expected output:**
```
======================================================================
COMPLETION STATUS ANALYSIS
======================================================================

Suburb                         Total Complete   Remain      %
----------------------------------------------------------------------
biggera_waters                 8,234    6,150    2,084   74.7%
surfers_paradise              12,456    9,234    3,222   74.1%
southport                     15,678   10,456    5,222   66.7%
...
----------------------------------------------------------------------
TOTAL                        234,567  156,789   77,778   66.8%

Top 20 suburbs by remaining addresses:
Suburb                         Remaining  % Incomplete
-------------------------------------------------------
southport                          5,222        33.3%
surfers_paradise                   3,222        25.9%
...

✓ Exported 77,778 remaining addresses to: remaining_addresses.json

======================================================================
SUMMARY
======================================================================
Total addresses:        234,567
Completed:              156,789 (66.8%)
Remaining:              77,778 (33.2%)
Suburbs analyzed:       45

Work distribution for 50 workers:
  Addresses per worker:  ~1,555
  At 120 addr/hr:        ~13.0 hours per worker
  Total processing time: ~13.0 hours (with 50 parallel)
```

**Output file:** `remaining_addresses.json` - list of all unscraped addresses

---

## Step 4: Start 50 Local Workers

Launch 50 parallel workers to process remaining addresses.

```bash
chmod +x start_50_local_workers.sh
./start_50_local_workers.sh
```

**What this does:**
- Validates MongoDB connection
- Checks script exists
- Starts 50 Python worker processes in background
- Each worker gets a unique ID (0-49)
- Logs to `local_worker_logs/worker_N.log`

**Expected output:**
```
==========================================
Starting 50 Local MongoDB Workers
==========================================

Configuration:
  Total Workers:   50
  MongoDB URI:     mongodb://127.0.0.1:27017/
  Script:          domain_scraper_multi_suburb_mongodb.py
  Log Directory:   ./local_worker_logs

✓ MongoDB connection OK

Starting 50 workers...

  Worker 0 started (PID: 12345) -> local_worker_logs/worker_0.log
  Worker 1 started (PID: 12346) -> local_worker_logs/worker_1.log
  ...
  Worker 49 started (PID: 12394) -> local_worker_logs/worker_49.log

==========================================
✓ All 50 Workers Started
==========================================
```

**Worker behavior:**
- Each worker queries MongoDB for unscraped addresses
- Divides work evenly across 50 workers
- Scrapes assigned addresses (3 second delay between each)
- Saves directly to MongoDB
- Expected rate: ~120 addresses/hour per worker
- Total throughput: ~6,000 addresses/hour (50 workers)

---

## Step 5: Monitor Progress

Monitor active workers and scraping progress.

```bash
chmod +x monitor_local_workers.sh
./monitor_local_workers.sh
```

**What this does:**
- Counts running worker processes
- Queries MongoDB for real-time statistics
- Shows recent activity from first 10 workers
- Displays completion percentage

**Expected output:**
```
==========================================
Local Workers Monitor
==========================================

Status: 50 workers running

MongoDB Statistics:
  Total addresses:    234,567
  Scraped:            158,234 (67.5%)
  Remaining:          76,333 (32.5%)
  Collections:        45

Recent Worker Activity (last 10 lines from each worker):
─────────────────────────────────────────────────────────

Worker 0:
[125/1555] [southport] 45 Main Street SOUTHPORT QLD 4215
  ✓ Data: 3bed 2bath, 15 images, 8 timeline events

Worker 1:
[98/1556] [surfers_paradise] 12/88 Cavill Avenue SURFERS PARADISE QLD 4217
  ✓ Data: 2bed 2bath, 12 images, 5 timeline events
...
```

**Refresh monitor:**
```bash
watch -n 30 ./monitor_local_workers.sh  # Updates every 30 seconds
```

**View specific worker:**
```bash
tail -f local_worker_logs/worker_0.log
```

**Stop all workers:**
```bash
pkill -f "python3.*domain_scraper_multi_suburb_mongodb.py"
```

---

## Step 6: Setup Nightly Scheduler

Configure automatic nightly runs to process remaining addresses.

```bash
chmod +x setup_nightly_scheduler.sh
./setup_nightly_scheduler.sh
```

**What this does:**
- Creates macOS LaunchAgent (scheduled task)
- Configures to run at 10 PM (22:00) every night
- Starts 50 workers automatically
- Logs to `nightly_scheduler.log`

**Expected output:**
```
==========================================
Setup Nightly Scheduler (launchd - macOS)
==========================================

Configuration:
  Worker directory:    /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast
  Start script:        start_50_local_workers.sh
  Schedule:            22:00 daily
  LaunchAgent plist:   ~/Library/LaunchAgents/com.goldcoast.nightly.scraper.plist

✓ Created: ~/Library/LaunchAgents/com.goldcoast.nightly.scraper.plist
✓ LaunchAgent loaded successfully
✓ LaunchAgent is registered

==========================================
✓ Nightly Scheduler Configured
==========================================

Schedule Details:
  Run time:           22:00 daily
  Workers:            50 parallel workers
  Log file:           nightly_scheduler.log
  Error log:          nightly_scheduler_error.log
```

**Management commands:**
```bash
# Check scheduler status
launchctl list | grep com.goldcoast.nightly.scraper

# View scheduler logs
tail -f nightly_scheduler.log

# Disable scheduler
launchctl unload ~/Library/LaunchAgents/com.goldcoast.nightly.scraper.plist

# Re-enable scheduler
launchctl load ~/Library/LaunchAgents/com.goldcoast.nightly.scraper.plist

# Test manually (don't wait for 10 PM)
./start_50_local_workers.sh
```

---

## Architecture Overview

### Data Flow
```
1. GCS Bucket (gs://property-scraper-production-data-477306)
   └─> download_gcs_to_mongodb.py
       └─> MongoDB (Gold_Coast database)
           └─> 50 Local Workers
               └─> MongoDB (scraped_data field updated)

2. Nightly Scheduler (LaunchAgent)
   └─> Triggers at 22:00
       └─> start_50_local_workers.sh
           └─> 50 Workers process remaining addresses
               └─> Continue until all addresses complete
```

### File Structure
```
03_Gold_Coast/
├── stop_all_gcp_workers.sh           # Step 1: Stop GCP
├── download_gcs_to_mongodb.py        # Step 2: Import GCS data
├── analyze_completion_status.py      # Step 3: Analyze status
├── start_50_local_workers.sh         # Step 4: Start workers
├── monitor_local_workers.sh          # Step 5: Monitor
├── setup_nightly_scheduler.sh        # Step 6: Schedule
├── domain_scraper_multi_suburb_mongodb.py  # Core scraper
├── local_worker_logs/                # Worker logs
│   ├── worker_0.log
│   ├── worker_1.log
│   └── ...
├── remaining_addresses.json          # Export from analysis
├── nightly_scheduler.log             # Scheduler output
└── nightly_scheduler_error.log       # Scheduler errors
```

### MongoDB Collections
```
Gold_Coast/
├── biggera_waters      (8,234 documents)
├── surfers_paradise    (12,456 documents)
├── southport           (15,678 documents)
├── broadbeach          (7,890 documents)
└── ... (45 suburb collections total)

Each document structure:
{
  "_id": ObjectId("..."),
  "ADDRESS_PID": "QLDXXXXX",
  "STREET_NO_1": "123",
  "STREET_NAME": "Main",
  "STREET_TYPE": "Street",
  "LOCALITY": "SOUTHPORT",
  "POSTCODE": "4215",
  "scraped_data": {           // Added by workers
    "url": "https://...",
    "address": "123 Main Street...",
    "features": {...},
    "valuation": {...},
    "property_timeline": [...],
    "images": [...]
  },
  "scraped_at": ISODate("2025-01-07T...")
}
```

---

## Performance Expectations

### Single Worker
- **Rate:** ~120 addresses/hour
- **Success rate:** ~95%
- **Duration per address:** ~30 seconds (including 3s rate limit)

### 50 Workers (Parallel)
- **Total rate:** ~6,000 addresses/hour
- **For 77,778 remaining:** ~13 hours total
- **Nightly processing:** 4-5 hours (assuming 10 PM - 3 AM)

### MongoDB Requirements
- **Storage:** ~500 MB per 10,000 addresses
- **RAM:** 2-4 GB recommended
- **CPU:** Minimal (workers are I/O bound, not CPU bound)

---

## Troubleshooting

### MongoDB Connection Failed
```bash
# Check if MongoDB is running
brew services list | grep mongodb

# Start MongoDB
brew services start mongodb-community

# Verify connection
mongosh --eval "db.adminCommand('ping')"
```

### GCS Authentication Failed
```bash
# Re-authenticate
gcloud auth application-default login

# Set project
gcloud config set project property-data-scraping-477306

# Test connection
gsutil ls gs://property-scraper-production-data-477306
```

### Workers Not Starting
```bash
# Check Python packages
pip3 install pymongo selenium google-cloud-storage

# Check ChromeDriver
brew install chromedriver

# Verify script exists
ls -l domain_scraper_multi_suburb_mongodb.py
```

### Scheduler Not Running
```bash
# Check LaunchAgent status
launchctl list | grep com.goldcoast.nightly.scraper

# View error logs
cat nightly_scheduler_error.log

# Reload scheduler
launchctl unload ~/Library/LaunchAgents/com.goldcoast.nightly.scraper.plist
launchctl load ~/Library/LaunchAgents/com.goldcoast.nightly.scraper.plist
```

### Workers Crashing
```bash
# Check worker logs
tail -100 local_worker_logs/worker_0.log

# Common issues:
# - ChromeDriver not installed
# - MongoDB connection lost
# - Memory issues (reduce workers to 25)

# Restart with fewer workers
export TOTAL_WORKERS=25
./start_50_local_workers.sh  # Will actually start 25
```

---

## Cost Savings

### Before (Google Cloud)
- **16 GCP instances:** e2-medium @ $0.033/hour
- **Cost:** ~$13/day (assuming 24/7 operation)
- **Monthly:** ~$390

### After (Local Workers)
- **Cost:** $0 (uses local machine)
- **Electricity:** ~$1-2/day (estimate)
- **Monthly:** ~$30-60

**Savings:** ~$330-360/month (85-90% reduction)

---

## Next Steps

Once all addresses are scraped:

1. **Verify completion:**
   ```bash
   python3 analyze_completion_status.py
   ```

2. **Export data for analysis:**
   ```bash
   mongoexport --db Gold_Coast --collection surfers_paradise --out surfers_paradise.json
   ```

3. **Disable scheduler** (if desired):
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.goldcoast.nightly.scraper.plist
   ```

4. **Backup MongoDB:**
   ```bash
   mongodump --db Gold_Coast --out ./mongodb_backup
   ```

---

## Summary

✅ **Completed Steps:**
1. ✓ Stopped all Google Cloud workers
2. ✓ Downloaded GCS data to MongoDB
3. ✓ Analyzed completion status
4. ✓ Created 50 local worker system
5. ✓ Configured nightly scheduler

🎯 **Result:**
- Zero ongoing cloud costs
- Automated nightly processing
- ~6,000 addresses/hour throughput
- Complete in ~2-3 weeks (nightly runs)

📊 **Monitoring:**
- Run `./monitor_local_workers.sh` anytime
- Check `local_worker_logs/` for details
- MongoDB directly queryable for analysis

---

**Need Help?**
- Check logs: `tail -f local_worker_logs/worker_0.log`
- MongoDB stats: `python3 analyze_completion_status.py`
- Stop workers: `pkill -f "domain_scraper_multi_suburb_mongodb.py"`
