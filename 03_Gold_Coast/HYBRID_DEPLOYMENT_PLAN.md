# Hybrid Deployment Plan - 16 Cloud + 10 Local Workers

## Overview

**Total Workers:** 26 (16 Google Cloud + 10 Local)
**Strategy:** Bypass Google Cloud quota limitations by running additional workers locally

---

## Architecture

### Google Cloud Workers (16 total)
- **CPUs:** 32 (16 workers × 2 CPUs = max quota)
- **Regions:** us-central1, us-east1, us-west1
- **Worker IDs:** 0-15
- **Processes:** ~12,739 addresses each (203,824 ÷ 16)
- **Duration:** ~13 hours
- **Cost:** ~$18

### Local Workers (10 total)
- **Machine:** Your local computer
- **Worker IDs:** 16-25
- **Processes:** ~12,740 addresses each (127,400 ÷ 10)
- **Duration:** Same ~13 hours (parallel with cloud)
- **Cost:** $0 (electricity)
- **Advantage:** Direct local MongoDB access!

---

## Benefits of Hybrid Approach

1. ✅ **No MongoDB connectivity issues** - Local workers access local MongoDB directly
2. ✅ **Bypasses cloud quotas** - Adds 10 more workers without quota increase
3. ✅ **Cost effective** - 10 workers run free locally
4. ✅ **Faster overall** - 26 workers vs 16 = ~40% faster
5. ✅ **Proven approach** - You mentioned you've run 15 workers before

---

## Worker Allocation

| Worker IDs | Location | Count | Addresses Each |
|------------|----------|-------|----------------|
| 0-7 | us-central1-a | 8 | ~12,739 |
| 8-15 | us-east1-b | 8 | ~12,739 |
| 16-25 | Local Machine | 10 | ~12,740 |
| **Total** | | **26** | **331,224** |

---

## Deployment Steps

### Step 1: Deploy 16 Google Cloud Workers
```bash
cd 03_Gold_Coast
./deploy_16_cloud_workers.sh
```

**What it does:**
- Deploys 8 workers in us-central1-a
- Deploys 8 workers in us-east1-b
- Each connects to your local MongoDB
- Total: 16 workers (32 CPUs)

### Step 2: Start 10 Local Workers
```bash
cd 03_Gold_Coast  
./start_10_local_workers.sh
```

**What it does:**
- Launches 10 Python processes on your local machine
- Worker IDs 16-25
- Direct local MongoDB access
- Saves results to same GCS bucket

---

## Monitoring

### Monitor All Workers
```bash
./monitor_hybrid.sh
```

Shows:
- Cloud workers status
- Local workers status  
- Total progress
- Estimated completion

### Check GCS Results
```bash
gsutil ls -r gs://property-scraper-production-data-477306/scraped_data/ | grep -c ".json$"
```

---

## Stopping Workers

### Stop Cloud Workers
```bash
# They auto-shutdown when done, or manually:
./cleanup_cloud_16.sh
```

### Stop Local Workers
```bash
# Press Ctrl+C in terminal, or:
pkill -f "domain_scraper_gcs.py"
```

---

## Expected Timeline

**Parallel Processing:**
- Start: T+0 hours (both cloud and local start together)
- Cloud + Local both processing simultaneously
- Complete: T+13 hours
- **Total time:** ~13 hours (vs 20+ hours with 16 workers alone)

---

## Cost Breakdown

**Google Cloud (16 workers × 13 hours):**
- Compute: 16 × $0.07/hr × 13 hrs = $14.56
- Network/Storage: ~$3
- **Total:** ~$18

**Local (10 workers × 13 hours):**
- **Cost:** $0 (just electricity)

**Combined Total:** ~$18 for all 331,224 properties

---

## Files Created

1. `deploy_16_cloud_workers.sh` - Deploy cloud workers
2. `start_10_local_workers.sh` - Start local workers
3. `monitor_hybrid.sh` - Monitor both deployments
4. `cleanup_cloud_16.sh` - Clean up cloud workers
5. `HYBRID_DEPLOYMENT_PLAN.md` - This file

---

## Next Steps

1. ✅ Review this plan
2. ⏳ Deploy 16 cloud workers
3. ⏳ Start 10 local workers
4. ⏳ Monitor progress
5. ⏳ Download results when complete

Ready to proceed with deployment scripts!
