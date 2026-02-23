# Gold Coast Database Update Orchestrator
**Last Updated:** 31/01/2026, 8:40 am (Brisbane Time)

## Overview

Production-grade orchestration system for managing 25 parallel workers that update the Gold Coast database with fresh Domain.com.au data while preserving historical valuations and rental estimates.

**NEW: Time-Based Update System** - Only updates properties older than 15 days, enabling efficient 20-day scheduled runs that maintain continuous data freshness.

## Key Features

### ✅ Robust & Resilient
- **Automatic Resume**: Resumes from where it left off after any interruption
- **Worker Health Monitoring**: Detects and restarts failed or stuck workers
- **Survives Machine Restarts**: State persisted to disk
- **Graceful Shutdown**: Handles SIGINT/SIGTERM signals properly

### 📊 Comprehensive Logging
- **Centralized Logging**: All worker activity logged to central location
- **Error Tracking**: Dedicated error log for all worker failures
- **Per-Worker Logs**: Individual log files for each worker
- **State Persistence**: JSON state file tracks all worker progress

### 🔄 Smart Worker Management
- **25 Workers**: Parallel processing for maximum throughput
- **30-Second Stagger**: Workers start with 30s delay to avoid overwhelming Domain
- **Auto-Restart**: Failed workers automatically restarted
- **Idle Detection**: Workers restarted if idle for 5+ minutes

### 📈 Real-Time Monitoring
- **Live Dashboard**: Real-time progress monitoring
- **Worker Statistics**: Per-worker performance metrics
- **Progress Tracking**: Overall and per-suburb progress
- **ETA Calculation**: Estimated completion time

## Time-Based Update System

### How It Works

The system uses **intelligent date-based filtering** to only update stale data:

```
FOR each property with scraped_data:
    IF never updated (no updated_at):
        → UPDATE IT
    ELSE IF last updated > 15 days ago:
        → UPDATE IT
    ELSE:
        → SKIP IT (still fresh)
```

### 20-Day Scheduled Run Example

**Day 1-4:** First run
- Updates all 243,187 properties
- Sets `updated_at` timestamp
- All data fresh

**Day 5-19:** Scheduled runs
- Finds 0 properties >15 days old
- Exits quickly (no work)

**Day 20-24:** Second run
- Properties now 16-20 days old
- Updates all ~243,187 properties
- Appends to history arrays

**Result:** All properties stay fresh (max 16 days old) with complete history tracking

### Configuration

Control update frequency with environment variable:

```bash
# Default: Update if >15 days old
python3 orchestrator.py

# Custom: Update if >30 days old (monthly)
UPDATE_THRESHOLD_DAYS=30 python3 orchestrator.py

# Custom: Update if >7 days old (weekly)
UPDATE_THRESHOLD_DAYS=7 python3 orchestrator.py
```

## Quick Start

### 1. Start the Orchestrator

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 orchestrator.py
```

This will:
1. Connect to MongoDB
2. Calculate which properties need updating (>15 days old)
3. Start 25 workers with 30-second stagger
4. Monitor and auto-restart workers
5. Log all activity

### 2. Monitor Progress (Separate Terminal)

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 monitor_orchestrator.py
```

This displays a real-time dashboard showing:
- Orchestrator status and uptime
- Worker status (running/stopped)
- Database progress
- Top performing workers
- Recent errors
- Estimated completion time

### 3. Stop the Orchestrator

Press `Ctrl+C` in the orchestrator terminal. It will:
1. Gracefully stop all 25 workers
2. Save current state
3. Close MongoDB connections
4. Exit cleanly

## File Structure

```
03_Gold_Coast/
├── orchestrator.py              # Main orchestrator script
├── monitor_orchestrator.py      # Monitoring dashboard
├── update_gold_coast_database.py # Worker script
├── orchestrator_logs/           # All logs stored here
│   ├── central.log             # Central orchestrator log
│   ├── errors.log              # All worker errors
│   ├── orchestrator_state.json # Current state
│   └── workers/                # Per-worker logs
│       ├── worker_0.log
│       ├── worker_0_errors.log
│       ├── worker_1.log
│       ├── worker_1_errors.log
│       └── ... (50 files total)
```

## How It Works

### Automatic Resume

The orchestrator automatically resumes from interruptions:

1. **State Tracking**: Worker progress saved every 60 seconds
2. **Database Queries**: Only selects properties without `updated_at` timestamp
3. **Worker Assignment**: Properties divided among active workers
4. **No Duplicates**: Already-updated properties automatically skipped

**Example:**
- Run 1: Updates 10,000 properties, then crashes
- Run 2: Automatically skips those 10,000, continues with remaining

### Worker Health Checks

Every 60 seconds, the orchestrator:

1. **Process Check**: Verifies worker process is running
2. **Activity Check**: Queries MongoDB for recent updates from worker
3. **Idle Detection**: Restarts worker if no updates in 5 minutes
4. **Auto-Restart**: Failed workers restarted immediately

### Error Tracking

All errors logged to multiple locations:

1. **Central Error Log**: `orchestrator_logs/errors.log`
   - All worker errors with timestamps
   - Worker ID tagged on each error
   
2. **Per-Worker Error Log**: `orchestrator_logs/workers/worker_N_errors.log`
   - Stderr output from specific worker
   - Stack traces and exceptions

3. **Central Log**: `orchestrator_logs/central.log`
   - Orchestrator events
   - Worker start/stop events
   - Health check results

## Configuration

Edit `orchestrator.py` to customize:

```python
NUM_WORKERS = 25              # Number of parallel workers
STAGGER_DELAY = 30            # Seconds between worker starts
HEALTH_CHECK_INTERVAL = 60    # Seconds between health checks
MAX_WORKER_IDLE_TIME = 300    # Restart if idle this long (seconds)
```

## Monitoring Dashboard

The dashboard (`monitor_orchestrator.py`) shows:

### Orchestrator Status
- Start time and uptime
- Last state update
- Warning if orchestrator appears stuck

### Worker Status
- Total workers and running count
- Total properties processed
- Top 10 workers by performance
- Per-worker uptime

### Database Progress
- Total properties to update
- Properties updated so far
- Progress percentage
- Current processing rate
- Estimated completion time
- Top 10 suburbs by progress

### Recent Errors
- Last 5 errors from any worker
- Timestamp and worker ID
- Error message

## All Run Commands

### Basic Usage

**Start orchestrator (default: 15-day threshold):**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 orchestrator.py
```

**Start with custom threshold:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && UPDATE_THRESHOLD_DAYS=30 python3 orchestrator.py
```

**Monitor progress:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 monitor_orchestrator.py
```

**Test with 2 properties:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 test_update_2_properties.py
```

### Advanced Usage

**Custom MongoDB URI:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && MONGODB_URI="mongodb://user:pass@host:port/" python3 orchestrator.py
```

**Different number of workers:**
Edit `orchestrator.py` and change `NUM_WORKERS = 25` to desired number

**Custom stagger delay:**
Edit `orchestrator.py` and change `STAGGER_DELAY = 30` to desired seconds

### Monitoring Commands

**View central log:**
```bash
tail -f /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/orchestrator_logs/central.log
```

**View error log:**
```bash
tail -f /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/orchestrator_logs/errors.log
```

**View specific worker log:**
```bash
tail -f /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/orchestrator_logs/workers/worker_0.log
```

**Check orchestrator state:**
```bash
cat /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/orchestrator_logs/orchestrator_state.json | jq
```

### Database Queries

**Count properties needing update:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && mongosh mongodb://127.0.0.1:27017/Gold_Coast --quiet --eval "
let cutoff = new Date(Date.now() - 15 * 24 * 60 * 60 * 1000);
let total = 0;
db.getCollectionNames().forEach(function(collName) {
    if (collName !== 'system.indexes') {
        total += db[collName].countDocuments({
            'scraped_data': {\$exists: true},
            '\$or': [
                {'updated_at': {\$exists: false}},
                {'updated_at': {\$lt: cutoff}}
            ]
        });
    }
});
print('Properties needing update: ' + total.toLocaleString());
"
```

**Check overall progress:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && mongosh mongodb://127.0.0.1:27017/Gold_Coast --quiet --eval "
let totalScraped = 0;
let totalUpdated = 0;
db.getCollectionNames().forEach(function(collName) {
    if (collName !== 'system.indexes') {
        totalScraped += db[collName].countDocuments({'scraped_data': {\$exists: true}});
        totalUpdated += db[collName].countDocuments({'updated_at': {\$exists: true}});
    }
});
print('Total: ' + totalScraped.toLocaleString());
print('Updated: ' + totalUpdated.toLocaleString());
print('Progress: ' + ((totalUpdated/totalScraped)*100).toFixed(2) + '%');
"
```

**View property with history:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && mongosh mongodb://127.0.0.1:27017/Gold_Coast --quiet --eval "
db.carrara.findOne(
    {'scraped_data.valuation_history.1': {\$exists: true}},
    {
        'scraped_data.address': 1,
        'scraped_data.valuation_history': 1,
        'updated_at': 1
    }
)
" | jq
```

## Task Scheduler Integration

The orchestrator is designed for task schedulers (cron, systemd, etc.):

### Recommended: 20-Day Cron Schedule

```bash
# Edit crontab
crontab -e

# Add this line (runs every 20 days at 2 AM)
0 2 */20 * * cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && UPDATE_THRESHOLD_DAYS=15 /usr/bin/python3 orchestrator.py >> orchestrator_logs/cron.log 2>&1
```

**Result:** All properties refreshed every ~16 days with complete history tracking

### Alternative: Monthly Schedule

```bash
# Runs on 1st of every month at 2 AM
0 2 1 * * cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && UPDATE_THRESHOLD_DAYS=25 /usr/bin/python3 orchestrator.py >> orchestrator_logs/cron.log 2>&1
```

**Result:** All properties refreshed every ~26 days

### launchd Example (macOS)

Create `~/Library/LaunchAgents/com.goldcoast.updater.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.goldcoast.updater</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/orchestrator.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>UPDATE_THRESHOLD_DAYS</key>
        <string>15</string>
    </dict>
    
    <key>StartInterval</key>
    <integer>1728000</integer> <!-- 20 days in seconds -->
    
    <key>StandardOutPath</key>
    <string>/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/orchestrator_logs/launchd.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/orchestrator_logs/launchd_error.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.goldcoast.updater.plist
launchctl start com.goldcoast.updater
```

Check status:
```bash
launchctl list | grep goldcoast
```

Stop it:
```bash
launchctl stop com.goldcoast.updater
launchctl unload ~/Library/LaunchAgents/com.goldcoast.updater.plist
```

### Systemd Service Example

```ini
[Unit]
Description=Gold Coast Database Update Orchestrator
After=network.target mongod.service

[Service]
Type=simple
User=projects
WorkingDirectory=/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast
ExecStart=/usr/bin/python3 orchestrator.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

## Performance

### Expected Throughput

**With 25 Workers:**
- Rate: ~3,000 properties/hour
- For 243,187 properties: ~81 hours (~3.4 days)

**Actual Performance:**
- Depends on Domain.com.au response times
- Network latency
- MongoDB performance
- System resources

### Resource Requirements

**Per Worker:**
- CPU: ~10-20% (Chrome + Python)
- RAM: ~200-300 MB
- Network: ~1-2 Mbps

**Total (25 Workers):**
- CPU: ~250-500% (2.5-5 cores)
- RAM: ~5-7.5 GB
- Network: ~25-50 Mbps

## Troubleshooting

### Orchestrator Won't Start

**Check MongoDB:**
```bash
brew services list | grep mongodb
brew services start mongodb-community
```

**Check Logs:**
```bash
tail -f orchestrator_logs/central.log
```

### Workers Keep Failing

**Check Worker Logs:**
```bash
tail -f orchestrator_logs/workers/worker_0_errors.log
```

**Common Issues:**
- ChromeDriver not installed: `brew install chromedriver`
- MongoDB connection issues: Check `MONGODB_URI` environment variable
- Domain.com.au rate limiting: Reduce `NUM_WORKERS`

### No Progress Being Made

**Check Worker Activity:**
```bash
python3 monitor_orchestrator.py
```

**Verify Workers Running:**
```bash
ps aux | grep update_gold_coast_database.py
```

**Check Database:**
```bash
mongosh mongodb://127.0.0.1:27017/Gold_Coast --eval "db.carrara.countDocuments({'updated_at': {\$exists: true}})"
```

### High Error Rate

**View Recent Errors:**
```bash
tail -50 orchestrator_logs/errors.log
```

**Common Errors:**
- `'list' object has no attribute 'get'`: Fixed in latest version
- `Connection refused`: Domain.com.au blocking or rate limiting
- `Timeout`: Increase timeout in worker script

## Logs Analysis

### View All Errors

```bash
cat orchestrator_logs/errors.log | grep "WORKER_"
```

### Count Errors Per Worker

```bash
cat orchestrator_logs/errors.log | grep -o "WORKER_[0-9]*" | sort | uniq -c
```

### View Specific Worker Log

```bash
tail -f orchestrator_logs/workers/worker_5.log
```

### Check Orchestrator Health

```bash
tail -20 orchestrator_logs/central.log
```

## Best Practices

### 1. Monitor Regularly
- Check dashboard every few hours
- Review error logs daily
- Verify progress is being made

### 2. Resource Management
- Don't run other heavy processes simultaneously
- Ensure adequate disk space for logs
- Monitor system resources

### 3. Error Handling
- Review error logs after each run
- Identify patterns in failures
- Adjust configuration if needed

### 4. Backup Strategy
- MongoDB backups before major updates
- Keep orchestrator logs for analysis
- Save state files for recovery

### 5. Scheduling
- Run during off-peak hours
- Allow adequate time for completion
- Don't interrupt mid-run unless necessary

## Recovery Procedures

### After Machine Restart

1. **Start MongoDB:**
   ```bash
   brew services start mongodb-community
   ```

2. **Restart Orchestrator:**
   ```bash
   cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast
   python3 orchestrator.py
   ```

3. **Verify Resume:**
   - Check `orchestrator_logs/central.log`
   - Should see "Resuming from previous state..."
   - Workers will skip already-updated properties

### After Orchestrator Crash

1. **Check Logs:**
   ```bash
   tail -100 orchestrator_logs/central.log
   ```

2. **Verify State File:**
   ```bash
   cat orchestrator_logs/orchestrator_state.json
   ```

3. **Restart:**
   ```bash
   python3 orchestrator.py
   ```

### After Database Corruption

1. **Restore from Backup:**
   ```bash
   mongorestore --db Gold_Coast /path/to/backup
   ```

2. **Verify Data:**
   ```bash
   mongosh mongodb://127.0.0.1:27017/Gold_Coast
   db.carrara.countDocuments({'updated_at': {$exists: true}})
   ```

3. **Resume Update:**
   ```bash
   python3 orchestrator.py
   ```

## Support

For issues:
1. Check this README
2. Review orchestrator logs
3. Check worker error logs
4. Verify MongoDB is running
5. Test with single worker first

## Version History

- **v2.0** (31/01/2026) - Time-Based Update System
  - **NEW:** Only updates properties >15 days old
  - **NEW:** Configurable UPDATE_THRESHOLD_DAYS
  - **NEW:** Perfect for 20-day scheduled runs
  - **NEW:** Maintains continuous data freshness
  - 25 workers with 30s stagger
  - Automatic resume capability
  - Centralized logging
  - Worker health monitoring
  - Real-time dashboard
  - Task scheduler compatible
  - Complete history preservation

- **v1.0** (30/01/2026) - Initial release
  - Basic orchestrator functionality
  - Multi-worker support
  - Logging and monitoring
