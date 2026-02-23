# Property Change Monitoring Guide

## Overview

The `batch_processor.py` script now includes a **monitoring mode** that tracks changes in property listings over time. It monitors three key fields:

1. **price** - Property price or listing status
2. **agents_description** - The property description written by the agent
3. **inspection_times** - Scheduled inspection times

## How It Works

### Timeline Structure

Each property in MongoDB has a `timeline` field that records all changes:

```json
{
  "timeline": [
    {
      "timestamp": "2025-11-14T21:30:00+10:00",
      "event_type": "initial_record",
      "changes": {
        "price": {"value": "$850,000"},
        "agents_description": {"value": "Beautiful 4-bedroom home..."},
        "inspection_times": {"value": ["Saturday, 16 Nov 10:00am - 10:30am"]}
      }
    },
    {
      "timestamp": "2025-11-15T14:20:00+10:00",
      "event_type": "field_change",
      "changes": {
        "price": {
          "old_value": "$850,000",
          "new_value": "$825,000"
        }
      }
    }
  ]
}
```

### Process Flow

1. **First Run** - Initializes timeline from existing enrichment data
2. **Subsequent Runs** - Compares current data with latest timeline values
3. **Change Detection** - Records any differences in the three monitored fields
4. **Timeline Update** - Appends new events to MongoDB with timestamps

## Usage

### Running the Monitor

```bash
# Navigate to the script directory
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search

# Run monitoring for ALL properties in the database
python batch_processor.py --monitor
```

### Prerequisites

1. **MongoDB must be running**
   ```bash
   # Start MongoDB if not running
   mongod --dbpath /path/to/data
   ```

2. **Properties must have enrichment data**
   - Run enrichment first if needed:
   ```bash
   python batch_processor.py --mongodb
   ```

3. **Chrome browser** - The script uses Chrome automation to navigate to listings

## What Happens During Monitoring

For each property, the script:

1. ✓ Checks if timeline exists (initializes if needed)
2. ✓ Retrieves the listing URL from enrichment data
3. ✓ Navigates to the property listing page
4. ✓ Extracts current HTML
5. ✓ Parses: price, agents_description, inspection_times
6. ✓ Compares with previous values from timeline
7. ✓ Records any changes as new timeline events
8. ✓ Updates MongoDB with new timeline data

## Output

### Console Output

```
================================================================================
PROPERTY CHANGE MONITORING MODE
================================================================================

Monitoring fields: price, agents_description, inspection_times

Found 150 properties to monitor

================================================================================

================================================================================
Monitoring Property 1/150: 123 Example St, Robina QLD 4226
================================================================================
→ Timeline exists with 2 events
→ Navigating to listing URL: https://www.domain.com.au/...
  ✓ Navigation successful
→ Extracting current HTML...
  ✓ Extracted HTML (125,432 chars)
→ Parsing HTML for monitored fields...
  ✓ Parsed current data:
    • price: $825,000
    • agents_description: Beautiful 4-bedroom home with...
    • inspection_times: ['Saturday, 16 Nov 10:00am - 10:30am']
→ Comparing with previous values...
  ✓ Changes detected in 1 field(s):
    • price:
      - Old: $850,000
      - New: $825,000
  ✓ Timeline updated in MongoDB
```

### Report File

A JSON report is saved to `batch_results/monitoring_report_TIMESTAMP.json`:

```json
{
  "monitoring_info": {
    "timestamp": "2025-11-14T21:30:00+10:00",
    "total_properties": 150,
    "successful": 148,
    "failed": 2,
    "timeline_initialized": 25,
    "changes_detected": 12,
    "total_time_seconds": 2700.5,
    "average_time_seconds": 18.0
  },
  "results": [
    {
      "address": "123 Example St, Robina QLD 4226",
      "index": 1,
      "success": true,
      "timeline_initialized": false,
      "changes_detected": true,
      "changes": {
        "price": {
          "old_value": "$850,000",
          "new_value": "$825,000"
        }
      },
      "error": null,
      "time_seconds": 18.5
    }
  ]
}
```

## Monitoring Frequency

- **Manual execution** - Run the script when you want to check for changes
- **Recommended frequency** - Daily or weekly, depending on market activity
- **Performance** - Approximately 18-20 seconds per property

To automate, you could set up a cron job (macOS/Linux):

```bash
# Edit crontab
crontab -e

# Add entry to run daily at 9 AM
0 9 * * * cd /path/to/07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search && python batch_processor.py --monitor >> /path/to/logs/monitoring.log 2>&1
```

## Querying Timeline Data

### Get Properties with Changes

```javascript
// In MongoDB shell (mongosh)
use property_data

// Find all properties with timeline events
db.properties_for_sale.find(
  {"timeline": {"$exists": true, "$ne": []}}
)

// Find properties with recent changes (last 7 days)
db.properties_for_sale.find({
  "last_timeline_update": {
    "$gte": new Date(Date.now() - 7*24*60*60*1000)
  }
})

// Find properties where price changed
db.properties_for_sale.find({
  "timeline.changes.price": {"$exists": true}
})
```

### Get Timeline for Specific Property

```javascript
db.properties_for_sale.findOne(
  {"address": "123 Example St, Robina QLD 4226"},
  {"timeline": 1, "address": 1}
)
```

## Troubleshooting

### No Properties Found

```
⚠ No properties found with enrichment data
Run with --mongodb flag first to enrich properties
```

**Solution**: Run enrichment first:
```bash
python batch_processor.py --mongodb
```

### Navigation Failures

If many properties fail to navigate:
- Check internet connection
- Verify Chrome is installed and updated
- Check that property listing URLs are still valid

### Timeline Initialization Issues

If timeline initialization fails:
- Verify enrichment data exists in MongoDB
- Check that the monitored fields are present in enrichment_data

## Integration with Existing Workflow

The monitoring script integrates seamlessly with your existing pipeline:

```bash
# 1. Full scraping pipeline (as usual)
cd 07_Undetectable_method/Simple_Method
./process_all_sessions.sh

# 2. Monitor for changes (new step)
cd ../00_Production_System/02_Individual_Property_Google_Search
python batch_processor.py --monitor
```

## Timeline Event Types

1. **initial_record** - First time data is recorded for a property
   - Contains initial values for all three monitored fields
   
2. **field_change** - One or more fields changed
   - Contains old_value and new_value for each changed field

## Notes

- Timeline is **append-only** - old data is never deleted
- Changes are detected by **exact comparison** (string/list equality)
- Properties without `enrichment_data` are skipped
- Each monitoring run processes **all properties** in the collection
- Empty or null field values are handled gracefully

## Performance Tips

1. **Reduce processing time**: Only monitor during business hours
2. **Parallel processing**: Could be enhanced to run multiple browsers
3. **Selective monitoring**: Could be modified to only check properties updated in last N days

## Support

For issues or questions:
1. Check MongoDB is running and accessible
2. Verify Chrome automation is working
3. Review the monitoring report JSON for detailed error information
4. Check console output for specific property failures
