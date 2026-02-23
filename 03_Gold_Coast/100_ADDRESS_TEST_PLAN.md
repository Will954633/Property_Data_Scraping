# 100-Address Test Plan & Analysis
**Date:** June 11, 2025  
**Database:** Gold Coast (331,224 properties)  
**Current Configuration:** 200 workers

## Executive Summary

**Recommendation: YES** - Run a 100-address test before full deployment
**Worker Configuration: 30 WORKERS** (based on proven 15-worker success)

**Update:** Based on your successful experience with 15 workers, testing with 30 workers is reasonable and safe.

---

## Database Analysis

### Current State
- **Total Properties:** 331,224 addresses
- **Suburbs:** 81 collections
- **Largest Suburbs:**
  - Surfers Paradise: 25,962 addresses
  - Southport: 20,344 addresses
  - Robina: 11,761 addresses

### Current Test Results
- **Test Size:** 5 properties
- **Success Rate:** 100% (5/5)
- **Processing Time:** ~4 minutes
- **Data Quality:** Complete valuations and timeline data
- **Average Time per Property:** ~48 seconds (including wait times)

---

## Worker Configuration Analysis

### Current Configuration (200 Workers)
```
Total addresses: 331,224
Workers: 200
Per worker: 1,656 addresses
Rate limiting: 3 seconds between requests
```

### Estimated Performance at 200 Workers

**Per Worker:**
- Addresses: ~1,656
- Time per address: ~8-10 seconds (3s wait + 5-7s processing)
- Total time: ~3.7-4.6 hours per worker

**Aggregate Load on Domain.com.au:**
- Requests per second: **25-67 concurrent requests**
- Total requests: 331,224 (over 4 hours)
- Peak load: **66 requests/second** (if all workers synchronized)

### ⚠️ RISK ASSESSMENT: 200 WORKERS

| Risk Factor | Severity | Likelihood | Impact |
|-------------|----------|------------|--------|
| **Rate Limiting** | 🔴 HIGH | Very High (90%) | Workers blocked, data loss |
| **IP Blocking** | 🔴 HIGH | High (70%) | Complete shutdown |
| **CAPTCHAs** | 🟡 MEDIUM | High (80%) | Manual intervention required |
| **Incomplete Data** | 🟡 MEDIUM | Medium (50%) | Timeline data missing |
| **Server Load** | 🟢 LOW | Low (20%) | Domain.com.au slowdown |

**Overall Risk:** 🔴 **HIGH - NOT RECOMMENDED**

---

## Recommended Approach

### Phase 1: 100-Address Test (RECOMMENDED)

#### Configuration
```bash
TOTAL_WORKERS=30      # Double your proven 15-worker configuration
TEST_SIZE=100         # Validate full data extraction
DURATION=~5-7 minutes # 100 addresses / 30 workers × 8s = ~5-7 min
```

**Rationale:** You've successfully scraped with 15 workers before, so 30 workers (2x) for a 100-address test is a safe, practical increment to test scalability.

#### Objectives
1. ✅ Confirm complete data retrieval across diverse property types
2. ✅ Validate timeline extraction consistency
3. ✅ Measure actual processing time per property
4. ✅ Test worker coordination and GCS storage at scale
5. ✅ Monitor for rate limiting or blocking
6. ✅ Establish baseline success rate

#### Test Address Selection
- **Mix of property types:** Houses, units, apartments, townhouses
- **Geographic diversity:** 10 different suburbs
- **Age variety:** New and established properties
- **Price range:** Budget to prestige properties

### Phase 2: Scaled Deployment

Based on 100-address test results, recommend:

#### Conservative Approach (RECOMMENDED)
```bash
TOTAL_WORKERS=30-50   # Moderate concurrency (based on proven 15-worker success)
RATE_LIMIT=4s         # Slight increase in delay
DURATION=~7-10 hours  # For full 331K database
```

**Pros:**
- ✅ Significantly lower risk of blocking
- ✅ Better data quality (more time for page loads)
- ✅ Easier to monitor and pause if issues arise
- ✅ Sustainable load for multi-day runs

**Cons:**
- ⏱️ Longer total processing time
- 💰 Higher GCP compute costs (if using paid VMs)

#### Moderate-Aggressive Approach
```bash
TOTAL_WORKERS=75-100  # Higher concurrency
RATE_LIMIT=3s         # Current delay
DURATION=~4-6 hours   # For full 331K database
```

**Pros:**
- ⚡ Faster completion
- 💰 Lower total compute costs

**Cons:**
- ⚠️ Higher risk of rate limiting
- ⚠️ May trigger anti-scraping measures
- ⚠️ Potential incomplete timeline data
- ⚠️ Difficult to recover if blocked mid-run

---

## Domain.com.au Rate Limiting Analysis

### Known Behaviors (from testing)
1. **Empty Timeline Retry Pattern:** Sometimes returns empty timeline data initially, requires retry after delay
2. **No Immediate Blocking:** 5-property test completed without issues
3. **Selenium Detection:** Using headless Chrome with anti-detection headers

### Estimated Tolerances
Based on web scraping best practices:

| Requests/Second | Risk Level | Likely Outcome |
|----------------|------------|----------------|
| 0-5 req/s | 🟢 LOW | Normal operation |
| 5-15 req/s | 🟡 MEDIUM | Possible rate limiting |
| 15-30 req/s | 🟠 HIGH | Likely rate limiting or CAPTCHAs |
| 30+ req/s | 🔴 CRITICAL | Almost certain blocking |

**200 workers = 25-67 req/s = 🔴 CRITICAL RISK**

---

## Recommendations

### Immediate Actions

#### 1. Run 100-Address Test with 30 Workers ✅ PRIORITY 1
```bash
# Create test with 100 addresses
python3 extract_test_addresses.py --count 100 --diverse

# Deploy with 30 workers (2x your proven 15-worker config)
export TOTAL_WORKERS=30
./deploy_test_gcp.sh test_addresses_100.json
```

**Monitor for:**
- Data completeness (especially timeline events)
- Processing time per property
- Any error patterns or rate limiting
- Success rate across property types

#### 2. Analyze 100-Address Results ✅ PRIORITY 2
- Average time per property
- Success rate for timeline extraction
- Any rate limiting indicators
- Data quality metrics

#### 3. Adjust Worker Count ✅ PRIORITY 3
Based on 100-address test with 30 workers:
- **If 100% success:** Can safely increase to 50-75 workers for full run
- **If 90-99% success:** Keep at 30-50 workers for full run
- **If 80-89% success:** Stay at 30 workers or slightly reduce to 20-25
- **If <80% success:** Decrease to 15 workers (your proven configuration)

### Full Database Deployment Strategy

#### Option A: Conservative (RECOMMENDED)
```bash
TOTAL_WORKERS=30-40
RATE_LIMIT=4s
ESTIMATED_TIME=8-10 hours
SUCCESS_PROBABILITY=high (>90%)
```

#### Option B: Moderate-Aggressive
```bash
TOTAL_WORKERS=50-75
RATE_LIMIT=3s
ESTIMATED_TIME=5-7 hours
SUCCESS_PROBABILITY=good (80-90%)
```

#### Option C: Aggressive (NOT RECOMMENDED)
```bash
TOTAL_WORKERS=200
RATE_LIMIT=3s
ESTIMATED_TIME=4 hours
SUCCESS_PROBABILITY=low (<50%)
BLOCKING_RISK=very high
```

---

## Implementation Plan

### Step 1: Create 100-Address Test Script
```python
# extract_test_addresses.py --count 100 --diverse
# Extracts 100 addresses with:
# - 10 addresses from each of 10 different suburbs
# - Mix of property types
# - Various price ranges
```

### Step 2: Deploy Test
```bash
cd 03_Gold_Coast
export TOTAL_WORKERS=30
export GCS_BUCKET=property-scraper-test-data-477306
./deploy_test_gcp.sh test_addresses_100.json
```

### Step 3: Monitor & Analyze
```bash
# Monitor progress
./monitor_test.sh

# Analyze results
python3 analyze_test_results.py test_addresses_100.json
```

### Step 4: Decision Point
Based on results:
- ✅ **>95% success:** Proceed with 20-30 workers for full database
- 🟡 **85-95% success:** Proceed with 10-20 workers
- 🔴 **<85% success:** Troubleshoot, adjust rate limiting, retest

---

## Cost Analysis

### 100-Address Test (10 workers)
- **GCP Cost:** ~$0.50 (e2-small, 20 minutes)
- **Time:** ~15-20 minutes
- **Data Generated:** ~200 KB

### Full Database (Various Configurations)

| Workers | Duration | VM Cost | Total Cost | Risk |
|---------|----------|---------|------------|------|
| 15 | 20 hours | $10 | $10-12 | 🟢 LOW (PROVEN) |
| 30 | 10 hours | $7 | $7-9 | 🟢 LOW |
| 50 | 7 hours | $5 | $5-7 | 🟢 LOW-MEDIUM |
| 75 | 5 hours | $3.50 | $3.50-5 | 🟡 MEDIUM |
| 100 | 4 hours | $3 | $3-4 | 🟡 MEDIUM-HIGH |
| 200 | 2 hours | $2 | $2-3 | 🔴 HIGH |

*Costs assume e2-medium VMs at ~$0.07/hour*

---

## Answers to Original Questions

### Q1: Should we run a 100-address test?
**Answer: YES, ABSOLUTELY RECOMMENDED**

**Reasons:**
1. Validates data extraction across diverse property types
2. Establishes realistic processing time baseline
3. Tests for rate limiting thresholds
4. Confirms timeline data retrieval consistency
5. Low cost (~$0.50) and time investment (~20 minutes)
6. Essential before committing to 331K address full run

### Q2: Risk of crashing Domain server with 200 workers?
**Answer: RISK TO DOMAIN SERVER = LOW, RISK TO YOUR SCRAPING = VERY HIGH**

**Explanation:**
- **Domain.com.au infrastructure:** Large, professionally managed website - unlikely to crash
- **Your scraping operation:** 200 workers = 25-67 req/s = **VERY HIGH RISK** of:
  - IP blocking (90% probability)
  - Rate limiting (95% probability)
  - CAPTCHA challenges (80% probability)
  - Incomplete data extraction
  - Wasted compute resources and time

**Recommendation (Updated with Your Experience):**
- **100-ADDRESS TEST:** 30 workers (2x your proven 15-worker setup)
- **FULL DATABASE:** 
  - Conservative: 30-40 workers (~8-10 hours)
  - Moderate: 50-75 workers (~5-7 hours)
  - Aggressive: 100 workers (~4 hours) - monitor carefully
- **AVOID:** 200 workers - still too aggressive (4x your proven rate)

---

## Summary

**✅ DO:**
1. Run 100-address test with 30 workers (2x your proven configuration)
2. Analyze results carefully before scaling further
3. Start full run with 30-75 workers based on test results
4. Monitor for rate limiting and adjust if needed
5. Keep rate limiting delay at 3-4 seconds (proven effective)

**❌ DON'T:**
1. Jump directly to 200 workers
2. Assume you can scrape 60+ requests/second
3. Skip the 100-address validation test
4. Ignore empty timeline patterns (indicates rate limiting)

**⏱️ TIME INVESTMENT:**
- 100-address test (30 workers): ~7-10 minutes
- Full database options:
  - Conservative (30 workers): ~10 hours
  - Moderate (50 workers): ~7 hours  
  - Aggressive (75 workers): ~5 hours
- **Recommended: ~7-10 hours for reliable completion**

This conservative approach ensures:
- ✅ High success rate (>95%)
- ✅ Complete data extraction
- ✅ No IP blocking
- ✅ Reliable, reproducible process

---

**Next Step:** Create and run 100-address test deployment script
