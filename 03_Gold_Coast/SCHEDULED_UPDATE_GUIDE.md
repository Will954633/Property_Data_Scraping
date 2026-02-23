# Scheduled Update System - 20-Day Cycle Guide
**Last Updated:** 31/01/2026, 8:30 am (Brisbane Time)

## Overview

The Gold Coast database update system is designed for **automatic 20-day scheduled runs** that keep all data fresh while building complete historical records.

## How It Works

### Time-Based Update Logic

The system uses **intelligent date-based filtering**:

```
IF property has scraped_data:
    IF never updated (no updated_at field):
        → UPDATE IT
    ELSE IF last updated > 15 days ago:
        → UPDATE IT
    ELSE:
        → SKIP IT (still fresh)
```

### 20-Day Schedule Example

**Day 1-4:** First run completes
- Updates all 243,187 properties
- Each gets `updated_at` timestamp
- All data is now fresh

**Day 5-15:** Properties are fresh
- Scheduled runs find 0 properties to update
- System exits quickly (no work needed)
- Data stays current

**Day 16:** Properties start aging
- Properties from Day 1 are now 16 days old
- Next run will update them
- Continuous refresh cycle begins

**Day 20:** Scheduled run
- Updates all properties >15 days old
- Maintains rolling 15-day freshness
- History arrays grow with each update

### Result: Continuous Fresh Data

- **Every property** updated every ~16 days
- **Complete history** of valuations and rentals
- **Automatic scheduling** with cron/task scheduler
- **No manual intervention** required

## Configuration

### Update Threshold

Control how often properties are updated:

```bash
# Update properties older than 15 days (default)
UPDATE_THRESHOLD_DAYS=15 python3 orchestrator.py

# Update properties older than 30 days (monthly updates)
UPDATE_THRESHOLD_DAYS=30 python3 orchestrator.py

# Update properties older than 7 days (weekly updates)
UPDATE_THRESHOLD_DAYS=7 python3 orchestrator.py
```

### Recommended Settings

| Schedule | Threshold | Result |
|----------|-----------|--------|
| Every 20 days | 15 days | All properties refreshed every ~16 days |
| Every 30 days | 25 days | All properties refreshed every ~26 days |
| Every 14 days | 10 days | All properties refreshed every ~11 days |

**Recommended:** 20-day schedule with 15-day threshold

## Scheduling the Orchestrator

### Option 1: Cron (macOS/Linux)

Edit crontab:
```bash
crontab -e
```

Add this line to run every 20 days at 2 AM:
```bash
# Gold Coast Database Update - Every 20 days at 2 AM
0 2 */20 * * cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && /usr/bin/python3 orchestrator.py >> orchestrator_logs/cron.log 2>&1
```

### Option 2: launchd (macOS)

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
```

### Option 3: Manual Scheduling

Run manually every 20 days:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 orchestrator.py
```

## What Happens on Each Run

### First Run (Initial Update)

```
Day 1: Start orchestrator
├─ Finds 243,187 properties with scraped_data
├─ All have no updated_at (never updated)
├─ Updates all 243,187 properties
├─ Takes ~4 days with 25 workers
└─ All properties now have updated_at timestamp

Result: All data fresh, complete history started
```

### Second Run (20 Days Later)

```
Day 20: Start orchestrator
├─ Finds 243,187 properties with scraped_data
├─ Checks updated_at timestamps
├─ Properties from Day 1-4 are 16-20 days old
├─ Updates ~243,187 properties (all >15 days old)
├─ Takes ~4 days with 25 workers
└─ All properties get new updated_at timestamp

Result: All data refreshed, history arrays grow
```

### Third Run (40 Days Later)

```
Day 40: Start orchestrator
├─ Finds 243,187 properties with scraped_data
├─ Properties from Day 20-24 are 16-20 days old
├─ Updates ~243,187 properties (all >15 days old)
├─ Takes ~4 days with 25 workers
└─ History arrays now have 3 entries each

Result: Continuous refresh cycle established
```

## Example Timeline

```
Day 1-4:   First run - Update all properties
Day 5-15:  All properties fresh (<15 days old)
Day 16:    Some properties now >15 days old
Day 20-24: Second run - Update all properties >15 days old
Day 25-35: All properties fresh again
Day 40-44: Third run - Update all properties >15 days old
...continues indefinitely
```

## Monitoring Scheduled Runs

### Check if Run is Needed

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && mongosh mongodb://127.0.0.1:27017/Gold_Coast --quiet --eval "
let cutoff = new Date(Date.now() - 15 * 24 * 60 * 60 * 1000);
let needingUpdate = 0;

db.getCollectionNames().forEach(function(collName) {
    if (collName !== 'system.indexes') {
        let count = db[collName].countDocuments({
            'scraped_data': {\$exists: true},
            '\$or': [
                {'updated_at': {\$exists: false}},
                {'updated_at': {\$lt: cutoff}}
            ]
        });
        needingUpdate += count;
    }
});

print('Properties needing update (>15 days old): ' + needingUpdate.toLocaleString());
"
```

### View Update Schedule

```bash
# For cron
crontab -l | grep goldcoast

# For launchd
launchctl list | grep goldcoast
```

## Benefits of This System

### 1. Always Fresh Data
- No property older than ~16 days
- Continuous data refresh
- Automatic scheduling

### 2. Complete History
- Every update adds to history arrays
- Track valuation trends over months/years
- Rental estimate changes tracked

### 3. Efficient Processing
- Only updates stale data
- Skips fresh properties
- Minimal wasted processing

### 4. Fault Tolerant
- Survives interruptions
- Resumes automatically
- No data loss

### 5. Zero Maintenance
- Set it and forget it
- Runs automatically
- Self-monitoring

## Customization Examples

### Monthly Updates (30-Day Cycle)

```bash
# Schedule: Every 30 days
# Threshold: 25 days
UPDATE_THRESHOLD_DAYS=25 python3 orchestrator.py
```

Result: Properties refreshed every ~26 days

### Bi-Weekly Updates (14-Day Cycle)

```bash
# Schedule: Every 14 days
# Threshold: 10 days
UPDATE_THRESHOLD_DAYS=10 python3 orchestrator.py
```

Result: Properties refreshed every ~11 days

### Quarterly Updates (90-Day Cycle)

```bash
# Schedule: Every 90 days
# Threshold: 85 days
UPDATE_THRESHOLD_DAYS=85 python3 orchestrator.py
```

Result: Properties refreshed every ~86 days

## Verification

### Check Property Ages

```javascript
// In mongosh
db.carrara.aggregate([
    {$match: {'updated_at': {$exists: true}}},
    {$project: {
        address: '$scraped_data.address',
        updated_at: 1,
        days_old: {
            $divide: [
                {$subtract: [new Date(), '$updated_at']},
                1000 * 60 * 60 * 24
            ]
        }
    }},
    {$group: {
        _id: null,
        avg_age: {$avg: '$days_old'},
        max_age: {$max: '$days_old'},
        min_age: {$min: '$days_old'}
    }}
])
```

Expected result with 20-day schedule:
- Average age: ~8 days
- Max age: ~16 days
- Min age: ~0 days

### Check History Growth

```javascript
// Properties with multiple history entries
db.carrara.countDocuments({
    'scraped_data.valuation_history.1': {$exists: true}
})
```

After 2nd run: Should have properties with 2+ history entries
After 3rd run: Should have properties with 3+ history entries

## Troubleshooting

### "No properties to update" on First Run

**Cause:** Properties don't have `scraped_data` yet

**Solution:** Run initial scraper first:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast && python3 domain_scraper_multi_suburb_mongodb.py
```

### All Properties Being Updated Every Run

**Cause:** `UPDATE_THRESHOLD_DAYS` set too low or `updated_at` not being set

**Check:**
```bash
mongosh mongodb://127.0.0.1:27017/Gold_Coast --eval "db.carrara.findOne({'updated_at': {\$exists: true}}, {'updated_at': 1})"
```

**Solution:** Verify `updated_at` is being set correctly

### No Properties Being Updated

**Cause:** All properties are fresh (<15 days old)

**Verify:**
```bash
# Check oldest property
mongosh mongodb://127.0.0.1:27017/Gold_Coast --eval "db.carrara.findOne({'updated_at': {\$exists: true}}, {sort: {'updated_at': 1}, projection: {'updated_at': 1}})"
```

**Solution:** This is normal! Wait until properties age past threshold

## Best Practices

1. **Set and Forget**: Schedule it and let it run automatically
2. **Monitor Logs**: Check orchestrator logs weekly
3. **Verify History**: Periodically check history arrays are growing
4. **Backup MongoDB**: Before major changes
5. **Test First**: Run manually before scheduling

## Summary

The time-based update system ensures:
- ✅ All properties stay fresh (updated every ~16 days)
- ✅ Complete historical records maintained
- ✅ Automatic scheduling compatible
- ✅ Efficient processing (only updates stale data)
- ✅ Zero manual intervention required

Perfect for production deployment with task schedulers!
