# Google Cloud Paid Account Setup Guide
**For Large-Scale Property Scraping (331,224 addresses)**

## Current Situation

**Test Status:**
- ✅ 8 workers successfully deployed (free tier limit)
- ⏳ Workers are installing dependencies and will start scraping shortly
- 🎯 Will process ~24-30 addresses total (partial test)

**Free Tier Limitations:**
- **Maximum:** 8 external IP addresses per region
- **Impact:** Cannot scale beyond 8 concurrent workers
- **Time for full database:** ~46 hours with 8 workers

---

## Step 1: Upgrade to Paid Account

### A. Enable Billing

1. **Go to Google Cloud Console Billing:**
   ```
   https://console.cloud.google.com/billing
   ```

2. **Link a Payment Method:**
   - Click "Link a billing account" or "Add billing account"
   - Enter credit card information
   - Verify payment method

3. **Enable Billing for Project:**
   - Select project: `property-data-scraping-477306`
   - Link to your billing account

### B. Understand Costs

**Compute Engine Pricing (e2-medium instances):**
- **Cost per hour:** ~$0.07/hour per VM
- **Cost per VM (full 10-hour run):** ~$0.70
- **Total cost for 30 workers:** ~$21
- **Total cost for 50 workers:** ~$35

**Network Egress:**
- **Cost:** ~$0.12/GB for data leaving Google Cloud
- **Estimated:** ~$5-10 for full run

**Storage (GCS):**
- **Cost:** $0.020/GB/month
- **Estimated:** <$1 for storing scraped data

**Total Estimated Cost for Full Database:**
- **30 workers (~10 hours):** $25-30
- **50 workers (~7 hours):** $40-50

**Note:** These are pay-as-you-go costs. You only pay for what you use.

---

## Step 2: Request Quota Increases

### A. Required Quotas for 30 Workers

Navigate to: **APIs & Services → Quotas**
```
https://console.cloud.google.com/iam-admin/quotas
```

**Filter by:** `compute.googleapis.com`

**Request increases for:**

| Quota Name | Current Limit (Free) | Requested | Reason |
|------------|---------------------|-----------|---------|
| **In-use IP addresses** (us-central1) | 8 | 35 | Need 30 workers + buffer |
| **CPUs** (us-central1) | 24 | 70 | 30 workers × 2 CPUs + buffer |
| **Compute Engine API requests per minute** | 2000 | 5000 | Launching 30 VMs simultaneously |

### B. How to Request Quota Increase

For each quota:

1. **Find the quota** in the Quotas page
2. **Check the box** next to the quota
3. **Click "EDIT QUOTAS"** at the top
4. **Enter new limit:** (from table above)
5. **Provide justification:**

```
Business Justification:
Running distributed web scraping workload for property data collection.
Need to process 331,224 property records using 30 concurrent workers
over approximately 10 hours. Each worker requires 2 CPUs and 1 external IP.

Use Case:
- Workload: Property data scraping from public websites
- Duration: 10-12 hours (one-time run)
- Workers: 30 concurrent e2-medium instances
- Region: us-central1
```

6. **Submit request**

**Processing Time:** Usually approved within 1-2 business days for reasonable requests.

### C. Alternative: Use Multiple Regions

If you need to start immediately without waiting for quota approval:

**Deploy across multiple regions:**
- `us-central1`: 8 workers (current limit)
- `us-east1`: 8 workers
- `us-west1`: 8 workers  
- `europe-west1`: 6 workers

**Total:** 30 workers without quota increase

**Trade-offs:**
- More complex deployment scripts
- Slight cost variation by region
- Need to manage multiple zones

---

## Step 3: Update Deployment Configuration

### A. For Single Region (After Quota Approval)

Update `deploy_100_test_gcp.sh` or create production script:

```bash
# Configuration for full database
TOTAL_WORKERS=30
ZONE="us-central1-a"

# Use full address list (not test file)
# This would require modification to scraper to use MongoDB directly
```

### B. For Multi-Region Deployment

Create `deploy_multiregion.sh`:

```bash
#!/bin/bash

declare -A REGIONS=(
  ["us-central1-a"]=8
  ["us-east1-b"]=8
  ["us-west1-b"]=8
  ["europe-west1-b"]=6
)

WORKER_ID=0
for REGION in "${!REGIONS[@]}"; do
  WORKER_COUNT=${REGIONS[$REGION]}
  for ((i=0; i<WORKER_COUNT; i++)); do
    echo "Launching worker $WORKER_ID in $REGION"
    # Launch VM command here
    ((WORKER_ID++))
  done
done
```

---

## Step 4: Production Deployment Strategy

### Recommended Approach: Phased Deployment

#### Phase 1: Validate Current 8-Worker Test (2-3 hours)
- ✅ **Current status:** In progress
- **Wait for:** Test completion (~15 minutes from now)
- **Analyze:** Data quality, timeline extraction, processing speed
- **Decision point:** Proceed if >90% success rate

#### Phase 2: Full Test with Quotas (1 day)
- **If quota approved:** Deploy 30 workers with 100-address test
- **Duration:** ~10 minutes
- **Validate:** Worker coordination, no rate limiting at scale
- **Cost:** ~$2

#### Phase 3: Full Database Run (10 hours)
- **Workers:** 30 (or 50 if aggressive)
- **Duration:** 7-10 hours
- **Monitoring:** Check progress every hour
- **Cost:** $25-50

### Alternative: Conservative Approach with Free Tier

If you want to avoid paid account setup:

**Option:** Run with 8 workers over 2 days
- **Day 1:** 24 hours (first 23,000 addresses)
- **Day 2:** 22 hours (remaining addresses)
- **Cost:** FREE
- **Trade-off:** Longer duration but zero cost

---

## Step 5: Optimize for Cost & Speed

### Cost Optimization Strategies

1. **Use Preemptible VMs:**
   - Cost: 60-80% cheaper than regular VMs
   - Trade-off: Can be interrupted (with 30sec warning)
   - For scraping: Acceptable risk, good cost savings

2. **Right-size VM Instances:**
   - Current: e2-medium (2 vCPU, 4GB RAM)
   - Alternative: e2-small (2 vCPU, 2GB RAM) - cheaper
   - Test first to ensure Chrome runs smoothly

3. **Use Committed Use Discounts:**
   - Not applicable for one-time runs
   - Useful if doing repeated scraping

### Speed Optimization Strategies

1. **Increase Workers (with monitoring):**
   - Start: 30 workers
   - If no rate limiting after 1 hour: Scale to 50
   - Max recommended: 50-75 workers

2. **Reduce Rate Limiting Delay:**
   - Current: 3 seconds between requests
   - If no issues: Reduce to 2 seconds
   - Monitor for empty timeline data (indicates rate limiting)

3. **Parallel Regions:**
   - Deploy across multiple regions simultaneously
   - No shared quota limits
   - Faster overall completion

---

## Step 6: Monitoring & Safety

### Real-Time Monitoring Script

Create `monitor_production.sh`:

```bash
#!/bin/bash

while true; do
  clear
  echo "======================================"
  echo "Production Scraping Monitor"
  echo "Time: $(date)"
  echo "======================================"
  
  # Count running workers
  RUNNING=$(gcloud compute instances list --filter="name:property-scraper AND status:RUNNING" --format="value(name)" | wc -l)
  
  # Count results in bucket
  RESULTS=$(gsutil ls -r gs://property-scraper-production-data/scraped_data/ 2>/dev/null | grep -c "\.json$" || echo "0")
  
  echo "Workers running: $RUNNING / 30"
  echo "Properties scraped: $RESULTS / 331,224"
  echo "Progress: $(echo "scale=2; $RESULTS / 331224 * 100" | bc)%"
  
  # Estimate completion
  if [ $RESULTS -gt 0 ]; then
    RATE=$(echo "scale=2; $RESULTS / (($(date +%s) - START_TIME) / 3600)" | bc)
    REMAINING=$(echo "scale=2; (331224 - $RESULTS) / $RATE" | bc)
    echo "Rate: $RATE addresses/hour"
    echo "Est. completion: $REMAINING hours"
  fi
  
  echo "======================================"
  sleep 60
done
```

### Safety Measures

1. **Cost Alerts:**
   - Set budget alert at $50
   - Get notification if costs exceed threshold

2. **Auto-Shutdown:**
   - Workers automatically shut down after completing
   - Verify all workers shut down to avoid ongoing charges

3. **Progress Checkpoints:**
   - Monitor after 1 hour, 3 hours, 6 hours
   - Pause if issues detected
   - Can resume later without losing progress

---

## Step 7: Post-Deployment Cleanup

### A. Verify Completion

```bash
# Check all results downloaded
gsutil ls -r gs://property-scraper-production-data/scraped_data/ | wc -l

# Should be ~331,224 JSON files
```

### B. Clean Up Resources

```bash
# Delete all worker VMs
gcloud compute instances delete $(gcloud compute instances list --filter="name:property-scraper" --format="value(name)") --zone=us-central1-a --quiet

# Optional: Delete GCS bucket if no longer needed
# gsutil -m rm -r gs://property-scraper-production-data/
```

### C. Cost Review

```bash
# View billing for project
https://console.cloud.google.com/billing/[BILLING_ID]/reports

# Filter by: property-data-scraping-477306
# Date range: Last 30 days
```

---

## Decision Matrix

### Choose Your Path:

| Criteria | Free Tier (8 Workers) | Paid Tier (30 Workers) | Aggressive (50 Workers) |
|----------|----------------------|------------------------|------------------------|
| **Setup Time** | Ready now ✅ | 1-2 days (quota) | 1-2 days (quota) |
| **Duration** | 46 hours | 10 hours | 7 hours |
| **Cost** | $0 | $25-30 | $40-50 |
| **Risk** | Minimal | Low | Medium |
| **Recommended for** | Budget-conscious | Balanced approach | Time-critical |

---

## Next Immediate Actions

### Now (While Current Test Runs):

1. ✅ **Monitor current 8-worker test** (check status in 10 min)
2. ✅ **This guide created** - review and decide on approach
3. ⏳ **Set up billing account** (if going paid route)
4. ⏳ **Submit quota increase requests** (if going paid route)

###Wait 10-15 Minutes:

5. **Analyze test results** from 8 workers
6. **Verify data quality** and timeline extraction
7. **Calculate actual processing rate**

### Within 24-48 Hours:

8. **Quota approval** (if requested)
9. **Run full 100-address test** with 30 workers
10. **Final validation** before full database run

### When Ready (After Validation):

11. **Deploy full production run** (331K addresses)
12. **Monitor progress** hourly
13. **Download and verify results**
14. **Clean up resources**

---

## Questions & Troubleshooting

### Common Issues:

**Q: Quota request denied?**
- A: Start with smaller request (20 workers vs 30)
- A: Use multi-region deployment instead

**Q: Cost higher than expected?**
- A: Check for workers not shutting down
- A: Verify no additional services running
- A: Use preemptible VMs next time

**Q: Workers failing mid-run?**
- A: Usually due to rate limiting - reduce concurrency
- A: Check Cloud Console logs for specific errors
- A: Workers save progress to GCS, can resume

**Q: How long for quota approval?**
- A: Typically 1-2 business days for reasonable requests
- A: Can expedite by explaining use case clearly

---

## Summary

You're ready to scale this operation! The current 8-worker test will provide validation, and then you can choose:

- **Quick & Free:** 8 workers over 46 hours ($0)
- **Balanced:** 30 workers over 10 hours ($25-30) ← **Recommended**
- **Fast:** 50 workers over 7 hours ($40-50)

All paths lead to successfully scraping the full 331,224-property database. The paid tier option gives you the best balance of speed and cost.
