# Batch Processing Guide

## Overview

The Batch Processor automatically processes multiple property addresses sequentially, using the hybrid smart clicking approach (fixed coordinates first, GPT Vision fallback).

## Quick Start

```bash
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/
python3 batch_processor.py
```

This will process all 20 addresses from `property_data_session_2.json`.

## What It Does

For each of the 20 addresses:
1. Opens/reuses Chrome tab
2. Searches for the address on Google
3. Tries fixed coordinates (350, 247) first
4. Validates URL contains "realestate.com.au"
5. If validation fails, uses GPT Vision fallback (max 2 attempts)
6. Logs all results and metrics

## Output Structure

### Console Output
```
================================================================================
BATCH ADDRESS PROCESSOR
Processing addresses from property_data_session_2.json
================================================================================

Loaded 20 addresses
Results will be saved to: batch_results/

================================================================================

================================================================================
Processing Address 1/20: 89 Parnell Boulevard, Robina
================================================================================
→ Attempting fixed coordinates...
✓ Success with fixed coordinates!

→ Waiting 2 seconds before next address...

================================================================================
Processing Address 2/20: 40 Peninsula Drive, Robina
================================================================================
→ Attempting fixed coordinates...
✗ Fixed coordinates failed
→ GPT Vision attempt 1...
✓ Success with GPT Vision!

...

================================================================================
BATCH PROCESSING COMPLETE
================================================================================

📊 SUMMARY:
  Total addresses: 20
  Successful: 18
  Failed: 2
  Success rate: 90.0%
  Total time: 240.5s
  Average time: 12.0s per address

  Fixed coordinates: 16
  GPT Vision: 2
  Fixed success rate: 80.0%

📁 Report saved: batch_results/batch_report_20251113_151230.json
```

### JSON Report

Saved in `batch_results/batch_report_[timestamp].json`:

```json
{
  "batch_info": {
    "start_time": "2025-11-13T15:12:30",
    "total_addresses": 20,
    "successful": 18,
    "failed": 2,
    "success_rate": "90.0%",
    "total_time_seconds": 240.5,
    "average_time_seconds": 12.0
  },
  "method_breakdown": {
    "fixed_coordinates": 16,
    "gpt_vision": 2,
    "fixed_success_rate": "80.0%"
  },
  "results": [
    {
      "address": "89 Parnell Boulevard, Robina",
      "index": 1,
      "success": true,
      "method": "FIXED_COORDINATES",
      "url": "https://www.realestate.com.au/property/...",
      "time_seconds": 11.5,
      "attempts": [
        {
          "method": "fixed",
          "success": true,
          "url": "https://www.realestate.com.au/..."
        }
      ],
      "error": null
    },
    ...
  ]
}
```

## Addresses Being Processed

The script processes these 20 addresses from the JSON:

1. 89 Parnell Boulevard, Robina
2. 40 Peninsula Drive, Robina
3. 739 Peninsula Drive, Robina
4. 13 Narrabeen Court, Robina
5. 4/189 Ron Penhaligon Way, Robina
6. 5 Picabeen Close, Robina
7. 3 Carpentaria Court, Robina
8. 8 Trinity Place, Robina
9. 5 Straite Drive, Robina
10. 2/38 Killarney Avenue, Robina
11. 24 Kirralee Drive, Robina
12. 27 Corvus Way, Robina
13. 12 Carnoustie Court, Robina
14. 44 Manly Drive, Robina
15. 29 Pine Valley Drive, Robina
16. 4 Springvale Street, Robina
17. 921 Medinah Avenue, Robina
18. 4 Tuggerah Close, Robina
19. 9 Applegum Court, Robina
20. 72 Woody Views Way, Robina

## Performance Metrics

### Expected Results (Based on Testing)

| Metric | Expected Value |
|--------|----------------|
| Total addresses | 20 |
| Fixed coordinates success | ~16-18 (80-90%) |
| GPT Vision fallback needed | ~2-4 (10-20%) |
| Overall success rate | ~90-95% |
| Average time per address | ~10-15 seconds |
| Total batch time | ~3-5 minutes |

### Cost Analysis

**If 80% succeed with fixed coordinates:**
- Fixed coordinate clicks: 16 addresses (FREE)
- GPT Vision calls: 4 addresses (~$0.02-0.04)
- **Total cost**: ~$0.02-0.04 for 20 addresses

**vs Pure GPT Vision:**
- GPT Vision calls: 20 addresses (~$0.10-0.20)
- **Savings**: ~80% cost reduction

## Configuration

```python
# Fixed coordinates (first Google result)
FIXED_CLICK_COORDINATES = (350, 247)

# Retry logic
MAX_GPT_RETRIES = 2  # GPT attempts if fixed fails

# Timing (adjust based on network speed)
INITIAL_LOAD_DELAY = 5     # Google page load
PAGE_LOAD_WAIT = 3         # After clicking
VALIDATION_DELAY = 1       # Before URL check
BETWEEN_ADDRESS_DELAY = 2  # Between addresses
```

## Results Directory Structure

```
batch_results/
├── batch_report_20251113_151230.json  # Main report
├── gpt_attempt_1_20251113_151245.png  # GPT screenshots (if used)
├── gpt_attempt_2_20251113_151250.png
└── ...
```

## Analyzing Results

### View Summary
```bash
# Pretty print the summary
cat batch_results/batch_report_*.json | jq '.batch_info'
```

### Check Failed Addresses
```bash
# Find failed addresses
cat batch_results/batch_report_*.json | jq '.results[] | select(.success == false) | .address'
```

### Method Breakdown
```bash
# Count by method
cat batch_results/batch_report_*.json | jq '.method_breakdown'
```

## Troubleshooting

### Issue: Too Many GPT Fallbacks
If more than 20% of addresses need GPT Vision:
- Adjust `FIXED_CLICK_COORDINATES` for your screen
- Increase `INITIAL_LOAD_DELAY` for slower networks
- Check Google search result layout hasn't changed

### Issue: High Failure Rate
- Check Chrome window stays visible during processing
- Verify network connection is stable
- Review failed addresses in report JSON
- Check screenshots in batch_results/ folder

### Issue: Process Too Slow
- Reduce `BETWEEN_ADDRESS_DELAY` to 1 second
- Reduce `PAGE_LOAD_WAIT` to 2 seconds
- Reduce `INITIAL_LOAD_DELAY` to 4 seconds (if network is fast)

### Issue: Process Too Fast (Errors)
- Increase delays if pages aren't loading fully
- Add human-like randomness to delays

## Monitoring Progress

The script provides real-time console output:
- Current address being processed (X/20)
- Success/failure for each attempt
- Method used (fixed or GPT)
- Final URL reached
- Time taken per address

## Next Steps

After batch completion:
1. Review the JSON report in `batch_results/`
2. Check success rate and method breakdown
3. Investigate any failures
4. Adjust configuration if needed
5. Run with larger datasets

## Production Deployment

### For Large-Scale Processing

```python
# Optimize for speed (if network is fast)
INITIAL_LOAD_DELAY = 4
PAGE_LOAD_WAIT = 2
BETWEEN_ADDRESS_DELAY = 1

# Reduce GPT retries for speed
MAX_GPT_RETRIES = 1  # Single fallback attempt
```

### Monitoring Metrics to Track

1. **Fixed coordinate success rate** - Should be 80-90%
2. **Overall success rate** - Should be 90-95%
3. **Average processing time** - Should be 10-15s per address
4. **GPT API costs** - Track per batch
5. **Failure patterns** - Which addresses fail most

## Estimated Processing Times

| Addresses | Fixed Success (90%) | With GPT Fallback (10%) | Total Time |
|-----------|---------------------|-------------------------|------------|
| 20 | ~3 min | ~4 min | ~4 minutes |
| 100 | ~15 min | ~20 min | ~20 minutes |
| 1,000 | ~2.5 hours | ~3.5 hours | ~3.5 hours |

**Note**: Times assume 90% fixed coordinate success rate

## Support

If you encounter issues:
- Check console output for errors
- Review batch report JSON file
- Examine screenshots in batch_results/ folder
- Verify Chrome stays visible during processing
- Ensure sufficient API credits for GPT Vision fallback

https://www.domain.com.au/property-profile/18-pine-valley-drive-robina-qld-4226
https://www.domain.com.au/property-profile/18-pine-valley-dr-robina-qld-4226 