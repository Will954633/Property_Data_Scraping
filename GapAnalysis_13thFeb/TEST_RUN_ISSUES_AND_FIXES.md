# Test Run Issues and Required Fixes
# Last Edit: 14/02/2026, 9:30 AM (Friday) — Brisbane Time
#
# Description: Summary of issues discovered during test run and fixes needed
#
# Edit History:
# - 14/02/2026 9:30 AM: Initial creation after first test run

---

## Test Run Summary

**Date:** 14/02/2026, 9:26 AM
**Mode:** Test mode (1 property per suburb = 8 total)
**Result:** 0/8 successful (0% success rate)
**Time:** 144.9 seconds (2.4 minutes)

---

## ✅ What Worked

1. **Pipeline Infrastructure**
   - ✅ Successfully connected to Azure Cosmos DB
   - ✅ Retrieved 8 properties (1 from each suburb)
   - ✅ Parallel processing started correctly (10 workers)
   - ✅ All enrichment fields attempted
   - ✅ Logging system working

2. **API Integrations**
   - ✅ GPT-4 Vision API calls working (with some timeouts)
   - ✅ OpenStreetMap API calls working (1 error, 7 successful)
   - ✅ Google Maps API calls working
   - ✅ Retry logic working (retried failed image downloads)

---

## ❌ Issues Discovered

### Issue 1: Image Download Timeouts (Non-Critical)

**Error:**
```
Error code: 400 - {'error': {'message': 'Timeout while downloading https://rimh2.domainstatic.com.au/...', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_image_url'}}
```

**Frequency:** 3 out of 8 properties had at least one image timeout

**Impact:** Causes retry delays but eventually succeeds or moves to next image

**Solution:** Already handled by retry logic - this is expected behavior

---

### Issue 2: String Formatting Error (CRITICAL)

**Error:**
```
Unknown format code 'f' for object of type 'str'
```

**Frequency:** 8 out of 8 properties failed with this error

**Impact:** ALL properties fail after enrichment completes

**Root Cause:** Somewhere in the code, we're trying to format a string value with an 'f' format specifier (for floats)

**Likely Location:** 
- Probably in `batch_processor.py` or `mongodb_enrichment_client.py`
- Happens after all enrichment fields are processed
- Likely when saving results to MongoDB or logging progress

**Example of what's wrong:**
```python
# This would cause the error if lat/lon are strings:
f"{lat:.6f}, {lon:.6f}"  # If lat="string" instead of lat=123.456
```

**Fix Needed:** Find where we're formatting coordinates or other numeric values and ensure they're converted to float first:
```python
# Correct way:
f"{float(lat):.6f}, {float(lon):.6f}"
```

---

### Issue 3: OSM JSON Parse Error (Minor)

**Error:**
```
OSM query error: Expecting value: line 1 column 1 (char 0)
```

**Frequency:** 1 out of 8 properties

**Impact:** One property couldn't determine busy_road status

**Root Cause:** OpenStreetMap Nominatim API returned empty response or rate limit hit

**Solution:** Already handled - falls back to null/unknown

---

## 🔍 Next Steps to Fix

### Step 1: Find the String Formatting Bug

Search for formatting code that might be receiving string values:

```bash
cd /Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb
grep -n ":.f}" *.py
```

Look for:
- Coordinate formatting (lat/lon)
- Price formatting
- Any numeric field formatting

### Step 2: Add Type Conversion

Ensure all numeric values are converted to appropriate types before formatting:

```python
# Before formatting coordinates:
if isinstance(lat, str):
    lat = float(lat)
if isinstance(lon, str):
    lon = float(lon)
```

### Step 3: Re-test

Run test again after fixes:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb && python3 run_production.py --test
```

---

## 📊 Expected Behavior After Fix

**Success Rate:** 90-95% (based on validation testing)

**Common Failures:**
- Properties with no images
- Properties with all images timing out
- Properties with invalid addresses (OSM can't geocode)

**These are acceptable failures** - the pipeline should handle them gracefully and continue.

---

## 🎯 Performance Notes

**Current Performance:**
- Average time per property: 18.11 seconds
- With 10 workers: ~2.5 properties/minute
- For 2,222 properties: ~14.8 hours

**This is slower than expected** due to:
1. Image download timeouts (adds retry delays)
2. Sequential enrichment of 7 fields per property
3. API rate limiting

**Optimization Options:**
1. Increase workers to 20 (if API limits allow)
2. Skip properties with no images
3. Reduce max retries from 3 to 2
4. Increase timeout thresholds

---

## 📝 Summary

The pipeline infrastructure is working correctly. The main blocker is a string formatting bug that causes all properties to fail after enrichment completes. Once this is fixed, the pipeline should achieve 90-95% success rate as validated in testing.

**Priority:** Fix the string formatting error in Step 1 above, then re-test.
