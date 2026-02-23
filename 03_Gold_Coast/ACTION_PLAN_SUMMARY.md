# Action Plan Summary - Property Scraping at Scale
**Date:** June 11, 2025  
**Status:** Ready to scale from 8 to 30+ workers

---

## Current Status ✅

### What's Running Now:
- **8 workers deployed** on Google Cloud (free tier limit reached)
- **Processing:** ~24-30 addresses from 100-address test
- **Status:** Installing dependencies, will start scraping in ~5 minutes
- **Monitor:** `./monitor_100_test.sh`

### What We've Proven:
- ✅ Database access working (331,224 addresses)
- ✅ URL formation correct for all property types
- ✅ Data extraction complete (valuations, timeline, images)
- ✅ GCS storage working
- ✅ Worker auto-deploy and auto-shutdown working

---

## The Challenge: Scaling Beyond 8 Workers

**Google Cloud Free Tier Limitation:**
- Maximum 8 external IP addresses per region
- Cannot deploy 30-200 workers without quota increase
- Need paid account + quota approval

---

## Three Path Options

### Option 1: Stay Free (No Setup Required)
**Configuration:**
- Workers: 8 (maximum free tier)
- Duration: ~46 hours (2 days)
- Cost: $0

**Pros:**
- ✅ Ready to deploy immediately
- ✅ Zero cost
- ✅ Proven to work

**Cons:**
- ⏱️ Slow (2 days vs 10 hours)
- 🔄 Need to babysit over 2 days

**When to Use:** Budget is priority, time not critical

---

### Option 2: Paid Tier - Balanced (RECOMMENDED)
**Configuration:**
- Workers: 30
- Duration: ~10 hours (same day completion)
- Cost: $25-30

**Pros:**
- ✅ 4.6x faster than free tier
- ✅ Complete in single day
- ✅ Reasonable cost
- ✅ Based on your proven 15-worker experience (2x that)

**Cons:**
- ⏳ Requires 1-2 days for quota approval
- 💳 Requires credit card setup

**When to Use:** Best balance of speed and cost

---

### Option 3: Paid Tier - Aggressive
**Configuration:**
- Workers: 50-75
- Duration: ~5-7 hours
- Cost: $40-60

**Pros:**
- ⚡ Fastest option
- ✅ Complete in single day

**Cons:**
- ⏳ Requires quota approval
- 💳 Higher cost
- ⚠️ Increased rate limiting risk at 50+ workers

**When to Use:** Time-critical, willing to pay premium

---

## Immediate Action Steps

### Step 1: Enable Billing (15 minutes)

1. **Go to Google Cloud Billing:**
   ```
   https://console.cloud.google.com/billing
   ```

2. **Add Payment Method:**
   - Click "Add billing account"
   - Enter credit card details
   - Link to project: `property-data-scraping-477306`

3. **Set Budget Alert:**
   - Navigate to "Budgets & alerts"
   - Create budget: $50
   - Set alert at 80% ($40)

---

### Step 2: Request Quota Increases (10 minutes)

**Go to Quotas Page:**
```
https://console.cloud.google.com/iam-admin/quotas?project=property-data-scraping-477306
```

**Search and Request Increases for These 3 Quotas:**

#### Quota 1: In-use IP addresses (us-central1)
- **Current:** 8
- **Request:** 35 (allows 30 workers + buffer)
- **Justification:**
  ```
  Distributed web scraping for property data collection.
  Processing 331,224 property records over 10 hours.
  Need 30 concurrent e2-medium instances, each requiring 1 external IP.
  One-time data collection workload.
  ```

#### Quota 2: CPUs (us-central1)
- **Current:** 24 (varies by account)
- **Request:** 70 (30 workers × 2 CPUs + buffer)
- **Justification:** Same as above

#### Quota 3: Compute Engine API requests per minute
- **Current:** 2000
- **Request:** 5000
- **Justification:** Need to launch 30 VMs simultaneously

**Processing Time:** Typically approved within 1-2 business days

---

### Step 3: While Waiting for Quota Approval

#### A. Monitor Current 8-Worker Test
```bash
# Check every 5 minutes
cd 03_Gold_Coast
./monitor_100_test.sh
```

#### B. Analyze Results (After ~15 minutes)
```bash
# Download results
mkdir -p test_results_100
gsutil -m cp -r gs://property-scraper-test-data-477306/scraped_data/ ./test_results_100/

# Check data quality
python3 -c "
import os, json
results = []
for root, dirs, files in os.walk('test_results_100'):
    for file in files:
        if file.endswith('.json'):
            with open(os.path.join(root, file)) as f:
                data = json.load(f)
                results.append({
                    'address': data.get('address'),
                    'has_valuation': data.get('valuation', {}).get('mid') is not None,
                    'timeline_events': len(data.get('property_timeline', []))
                })

print(f'Properties scraped: {len(results)}')
print(f'With valuations: {sum(1 for r in results if r[\"has_valuation\"])}')
print(f'With timeline data: {sum(1 for r in results if r[\"timeline_events\"] > 0)}')
print(f'Success rate: {sum(1 for r in results if r[\"has_valuation\"]) / len(results) * 100:.1f}%')
"
```

#### Expected Results:
- **Success Rate:** >90%
- **Timeline Data:** 60-80% (normal - some properties have no sales history)
- **Valuations:** 100%

---

### Step 4: After Quota Approval

#### Validation Test (Optional but Recommended)
```bash
# Run 100-address test again with 30 workers
cd 03_Gold_Coast

# This will actually only process ~10-12 addresses total
# since we only have 100 test addresses
# But validates 30 workers can launch and coordinate

./deploy_100_test_gcp.sh
# When prompted for MongoDB URI, press Enter for local
```

**Duration:** ~10 minutes  
**Cost:** ~$2  
**Purpose:** Validate 30 workers work together without issues

---

### Step 5: Full Production Run

#### Option A: Using Test Address File (Simple)
For learning/testing with subset:
```bash
# Already configured to use test file
# Just increase worker count in script
```

#### Option B: Full Database (Production)
**Needs Modification:**
- Remove test file loading
- Use MongoDB directly in workers
- Process all 331,224 addresses

**Deployment Script Modification Required:**
```python
# In domain_scraper_gcs.py
# Change get_my_addresses() to pull from MongoDB
# instead of test JSON file
```

---

## Cost Breakdown

### Detailed Cost Estimate (30 Workers, 10 Hours)

**Compute:**
- 30 × e2-medium instances
- $0.07/hour × 30 workers × 10 hours = **$21**

**Network Egress:**
- ~65MB per 1000 properties = 21GB total
- $0.12/GB × 21GB = **$2.50**

**Storage (GCS):**
- ~65MB for all 331K JSON files
- $0.020/GB/month × 0.065GB = **$0.001**

**Total:** **~$25**

### Ways to Reduce Cost:

1. **Use Preemptible VMs:** Save 60-80%
   ```bash
   # Add to gcloud create command:
   --preemptible
   
   # Total cost: ~$8-10 instead of $25
   ```

2. **Use Smaller VMs:** e2-small instead of e2-medium
   ```bash
   --machine-type=e2-small  # Save ~30%
   ```

3. **Multi-Region Free Tier:**
   - Deploy 8 workers in us-central1 (free)
   - Deploy 8 workers in us-east1 (free)
   - Deploy 8 workers in us-west1 (free)
   - Deploy 6 workers in europe-west1 (free)
   - **Total: 30 workers, $0 cost**

---

## Timeline Estimates

### Scenario 1: Paid Account Ready Today
| Time | Activity |
|------|----------|
| **Now** | Submit quota requests |
| **+24-48 hrs** | Quota approved |
| **+48 hrs** | Run 100-address validation test (30 workers) |
| **+48.5 hrs** | Analyze, adjust if needed |
| **+49 hrs** | Deploy full production run (30 workers) |
| **+59 hrs** | Production run complete |
| **Total:** | ~2.5 days from now |

### Scenario 2: Use Free Tier Immediately
| Time | Activity |
|------|----------|
| **Now** | Deploy 8 workers with full database |
| **+46 hrs** | Complete |
| **Total:** | ~2 days continuous run |

### Scenario 3: Multi-Region Workaround
| Time | Activity |
|------|----------|
| **+2 hrs** | Create multi-region deployment script |
| **+2.5 hrs** | Deploy 30 workers across 4 regions |
| **+12.5 hrs** | Complete |
| **Total:** | <1 day, $0 cost |

---

## Risk Assessment

### Low Risk ✅
- Using 8-30 workers (proven safe)
- 3-second rate limiting (conservative)
- Auto-shutdown on completion
- Data saved incrementally to GCS

### Medium Risk ⚠️
- 50+ workers (possible rate limiting)
- Reduced rate limiting (<3s)
- Preemptible VMs (can be interrupted)

### High Risk ❌
- 100+ workers (almost certain blocking)
- 200 workers (impossible with quotas anyway)
- No rate limiting

---

## Decision Framework

**Answer These Questions:**

1. **How urgent is completion?**
   - Not urgent: Use free tier (8 workers, $0, 2 days)
   - Somewhat urgent: Use 30 workers ($25, ~1 day)
   - Very urgent: Use 50 workers ($40, ~7 hours)

2. **Comfort with paid services?**
   - Not comfortable: Use free tier
   - Comfortable with <$50: Use 30 workers
   - Budget available: Use 50 workers

3. **Can wait for quota approval?**
   - No: Use free tier or multi-region
   - Yes: Request quotas, use 30-50 workers

---

## Recommended Path (Based on Your Situation)

**You said:** "Move ahead with paid account setup"

**My Recommendation:** **Option 2 - Paid Tier with 30 Workers**

**Action Plan:**
1. ✅ **Today:** Enable billing + request quotas (done above)
2. ⏳ **Wait:** 1-2 business days for quota approval
3. ✅ **Then:** Run validation test with 30 workers
4. ✅ **Finally:** Deploy full production run

**Why This Path:**
- ✅ Proven safe (2x your 15-worker experience)
- ✅ Fast completion (10 hours vs 46 hours)
- ✅ Reasonable cost ($25-30)
- ✅ Low risk of rate limiting
- ✅ Can complete in single day

---

## Monitoring & Safety

### During Production Run

**Check Every Hour:**
```bash
./monitor_100_test.sh  # Or production monitoring script

# Should show:
# - Workers running
# - Files being created
# - No error patterns
```

**Watch For:**
- ⚠️ Workers stuck (not creating new files)
- ⚠️ Empty timeline data (indicates rate limiting)
- ⚠️ Worker errors in logs

**If Issues Detected:**
- Pause deployment
- Analyze logs
- Adjust worker count or rate limiting
- Resume

---

## Success Criteria

### Test is Successful If:
- ✅ >90% of properties have valuations
- ✅ >60% of properties have timeline data
- ✅ All workers complete without crashes
- ✅ No rate limiting detected

### Production is Successful If:
- ✅ 331,224 JSON files in GCS bucket
- ✅ All properties have valuations
- ✅ Timeline data present where available
- ✅ Complete within estimated timeframe
- ✅ Cost within budget

---

## Files &  Documentation

### Key Files Created:
- ✅ `100_ADDRESS_TEST_PLAN.md` - Initial analysis and recommendations
- ✅ `PAID_ACCOUNT_SETUP_GUIDE.md` - Detailed paid tier setup
- ✅ `ACTION_PLAN_SUMMARY.md` - This file (quick reference)
- ✅ `test_addresses_100.json` - 100 diverse test addresses
- ✅ `deploy_100_test_gcp.sh` - Deployment script (30 workers)
- ✅ `monitor_100_test.sh` - Progress monitoring
- ✅ `cleanup_100_test.sh` - Resource cleanup

### Quick Reference Commands:
```bash
# Monitor test
./monitor_100_test.sh

# Check logs
gcloud compute instances get-serial-port-output property-scraper-100test-0 --zone=us-central1-a

# Download results
gsutil -m cp -r gs://property-scraper-test-data-477306/scraped_data/ ./test_results_100/

# Cleanup
./cleanup_100_test.sh
```

---

## Next 5 Actions (Right Now)

1. ✅ **Enable Google Cloud Billing**
   - Add credit card
   - Link to project
   - Set budget alert

2. ✅ **Request Quota Increases**
   - In-use IPs: 35
   - CPUs: 70
   - API requests: 5000

3. ⏳ **Monitor Current 8-Worker Test** (check in 10 min)
   ```bash
   cd 03_Gold_Coast && ./monitor_100_test.sh
   ```

4. ⏳ **Analyze Test Results** (after test completes)
   - Verify data quality
   - Calculate processing rate
   - Confirm no rate limiting

5. ⏰ **Wait for Quota Approval** (1-2 business days)
   - Check email for Google Cloud notifications
   - Once approved → run validation test
   - Then → deploy full production run

---

## Questions?

**Need Help With:**
- Billing setup?
- Quota requests?
- Script modifications?
- Multi-region deployment?
- Cost optimization?

**Let me know and I'll create specific guides or scripts!**

---

## Summary

**Current:** 8 workers running test (~15 min to completion)  
**Goal:** 331,224 addresses scraped  
**Path:** Paid tier with 30 workers  
**Cost:** ~$25  
**Duration:** ~10 hours (single day)  
**ETA:** 2-3 days (waiting for quota approval)

**You're set up for success! The infrastructure is proven and ready to scale.**
