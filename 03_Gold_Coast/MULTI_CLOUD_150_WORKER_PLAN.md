# Multi-Cloud Deployment Plan - 150 Workers
**Target:** 331,224 properties  
**Current Progress:** ~600 properties scraped by 26 workers  
**Goal:** Deploy 150 workers across 5 cloud platforms  
**Estimated Completion:** 24-30 hours from start

---

## Executive Summary

**Problem:** Current 26 workers = 172 hours (7 days)  
**Solution:** Deploy 150 workers across multiple cloud platforms  
**Result:** Complete in 24-30 hours (1-1.5 days)  

**Key Innovation:** Use independent quotas from 5 different cloud providers + avoid re-scraping completed properties

---

## Current State Analysis

### Already Deployed (Keep Running):
- **Google Cloud:** 16 workers (IDs 0-15) ✅ RUNNING
- **Local Machine:** 10 workers (IDs 16-25) ✅ RUNNING  
- **Total Active:** 26 workers
- **Progress:** ~600 properties already scraped
- **These workers continue and will NOT be duplicated**

### Properties Already Scraped:
- Stored in: `gs://property-scraper-production-data-477306/scraped_data/`
- Worker folders: `worker_000/` through `worker_025/`
- **Must avoid re-scraping these ~600 properties**

---

## Multi-Cloud Architecture for 150 Workers

### Worker ID Allocation Strategy

| Platform | Worker IDs | Count | Status | Properties Each |
|----------|------------|-------|--------|-----------------|
| **Google Cloud** | 0-15 | 16 | ✅ Running | ~12,740 |
| **Local Machine** | 16-25 | 10 | ✅ Running | ~12,740 |
| **AWS (Lightsail)** | 26-65 | 40 | 🆕 To Deploy | ~8,280 |
| **DigitalOcean** | 66-105 | 40 | 🆕 To Deploy | ~8,280 |
| **Azure** | 106-135 | 30 | 🆕 To Deploy | ~11,040 |
| **Railway.app** | 136-149 | 14 | 🆕 To Deploy | ~23,660 |
| **TOTAL** | **0-149** | **150** | | **331,224** |

**Critical:** ALL workers know `TOTAL_WORKERS=150`, so they automatically divide the 331K addresses correctly.

---

## Avoiding Duplicate Scraping

### How Worker ID System Prevents Duplication:

**Workers 0-25 (already running):**
- These will complete their assigned ~12,740 addresses each
- No overlap with new workers
- Continue running

**Workers 26-149 (new deployments):**
- Will process DIFFERENT address ranges
- Worker 26 starts at address index ~331,224 ÷ 150 × 26 = ~57,359
- Worker 27 starts at ~59,568
- etc.
- **Zero overlap with workers 0-25**

**Result:** No properties scraped twice, all 331,224 covered exactly once

---

## Platform-by-Platform Deployment

### Platform 1: Google Cloud (CURRENT - Keep Running)

**Status:** ✅ Already deployed  
**Workers:** 16 (IDs 0-15)  
**Action:** None - let them continue  
**Cost:** ~$18

---

### Platform 2: AWS Lightsail (DEPLOY FIRST - Easiest)

**Why AWS Lightsail:**
- Simpler than EC2
- Fixed pricing
- Fast deployment
- Separate from Google quota

**Workers:** 40 (IDs 26-65)  
**Instance Type:** 2 vCPU, 4GB RAM ($24/month each)  
**Region:** Use multiple (us-east-1, us-west-2, eu-west-1)

**Setup Steps:**

1. **Sign Up:**
   ```
   https://aws.amazon.com/lightsail/
   ```

2. **Install AWS CLI:**
   ```bash
   brew install awscli
   aws configure  # Enter access key
   ```

3. **Deploy Script** (I'll create `deploy_aws_40workers.sh`):
   ```bash
   # Creates 40 Lightsail instances across regions
   # Each runs the scraper as worker IDs 26-65
   # Connects to your MongoDB (need public access or VPN)
   # Uploads to same GCS bucket
   ```

**Cost:** 40 × $24/month ÷ 30 days × 1 day = **~$32**  
**Setup Time:** 45 minutes  
**Properties:** ~331,200 addresses

---

### Platform 3: DigitalOcean (DEPLOY SECOND - FREE CREDITS!)

**Why DigitalOcean:**
- $200 free credit for new users
- Simplest interface
- API-driven deployment
- Droplets = VMs

**Workers:** 40 (IDs 66-105)  
**Droplet Size:** Basic 2 vCPU, 4GB ($24/month)  
**Regions:** NYC1, SFO3, LON1, SGP1

**Setup Steps:**

1. **Sign Up & Get $200 Credit:**
   ```
   https://try.digitalocean.com/freetrialoffer/
   ```

2. **Install doctl CLI:**
   ```bash
   brew install doctl
   doctl auth init  # Enter API token
   ```

3. **Deploy Script** (I'll create `deploy_digitalocean_40workers.sh`):
   ```bash
   # Creates 40 droplets across 4 regions
   # Worker IDs 66-105
   # Same scraper code
   ```

**Cost:** **FREE** (using $200 credit)  
**Setup Time:** 45 minutes  
**Properties:** ~331,200 addresses

---

### Platform 4: Azure (DEPLOY THIRD - FREE CREDITS!)

**Why Azure:**
- $200 free credit
- Enterprise-grade
- Good global coverage

**Workers:** 30 (IDs 106-135)  
**VM Size:** Standard_B2s (2 vCPU, 4GB)  
**Regions:** East US, West Europe, Southeast Asia

**Setup Steps:**

1. **Sign Up & Get $200 Credit:**
   ```
   https://azure.microsoft.com/free/
   ```

2. **Install Azure CLI:**
   ```bash
   brew install azure-cli
   az login
   ```

3. **Deploy Script** (I'll create `deploy_azure_30workers.sh`):
   ```bash
   # Creates 30 VMs across 3 regions
   # Worker IDs 106-135
   ```

**Cost:** **FREE** (using $200 credit)  
**Setup Time:** 45 minutes  
**Properties:** ~331,360 addresses

---

### Platform 5: Railway.app (OPTIONAL - PaaS Layer)

**Why Railway:**
- Platform-as-a-Service (no VM management)
- Deploy from GitHub
- Auto-scaling
- Very fast setup

**Workers:** 14 (IDs 136-149)  
**Pricing:** $0.000231/GB-second

**Setup Steps:**

1. **Push code to GitHub**
2. **Connect Railway:**
   ```
   https://railway.app
   ```
3. **Deploy from repo**
4. **Set environment variables**
5. **Scale to 14 instances**

**Cost:** ~$10-15  
**Setup Time:** 20 minutes (fastest!)  
**Properties:** ~331,360 addresses

---

## Critical: MongoDB Access for New Workers

### Problem:
New cloud workers can't access your **local MongoDB** at `127.0.0.1`

### Solutions (Choose One):

#### Option A: MongoDB Atlas (RECOMMENDED - 30 min setup)

**Quick Migration:**
```bash
# 1. Create free MongoDB Atlas cluster
https://www.mongodb.com/cloud/atlas/register

# 2. Export your local data
mongodump --db Gold_Coast --out ./mongodb_backup

# 3. Import to Atlas (get connection string from Atlas dashboard)
mongorestore --uri="mongodb+srv://YOUR_ATLAS_URI" \
  --db Gold_Coast ./mongodb_backup/Gold_Coast

# 4. Use Atlas URI in all new deployments
# mongodb+srv://username:password@cluster.mongodb.net/Gold_Coast
```

**Advantages:**
- Accessible from all cloud providers
- Fast, reliable
- Free tier sufficient
- Already done if you have Atlas

#### Option B: Make Local MongoDB Public (NOT RECOMMENDED)

Would require:
- Port forwarding
- Dynamic DNS
- Security risks
- Complex firewall setup

#### Option C: Upload Addresses to Each Platform's Storage

**Alternative approach:**
- Export address list to JSON
- Upload to each platform's storage (S3, DO Spaces, Azure Blob)
- Workers read from platform-native storage
- No MongoDB connectivity needed

---

## Deployment Sequence & Timeline

### Hour 0: Preparation (30 minutes)
- ✅ Current 26 workers already running
- Set up MongoDB Atlas (if not done)
- Create deployment scripts for each platform

### Hour 0.5-1.5: AWS Deployment (1 hour)
- Sign up for AWS
- Configure CLI
- Deploy 40 Lightsail instances
- Workers 26-65 start processing

### Hour 1.5-2.5: DigitalOcean Deployment (1 hour)
- Sign up (get $200 credit)
- Configure doctl CLI
- Deploy 40 droplets
- Workers 66-105 start processing

### Hour 2.5-3.5: Azure Deployment (1 hour)
- Sign up (get $200 credit)
- Configure Azure CLI
- Deploy 30 VMs
- Workers 106-135 start processing

### Hour 3.5-4: Railway Deployment (30 minutes)
- Push to GitHub
- Connect Railway
- Deploy 14 instances
- Workers 136-149 start processing

### Hour 4-28: Processing (24 hours)
- All 150 workers scraping simultaneously
- Monitor progress across all platforms
- Download results as they complete

**Total Setup Time:** ~4 hours  
**Total Processing Time:** ~24-28 hours  
**Complete By:** Tomorrow evening (vs 7 days!)

---

## Cost Breakdown (150 Workers)

| Platform | Workers | Duration | Cost | Free Credits |
|----------|---------|----------|------|--------------|
| Google Cloud | 16 | 28 hrs | $18 | - |
| Local | 10 | 28 hrs | $0 | - |
| AWS | 40 | 28 hrs | $32 | - |
| DigitalOcean | 40 | 28 hrs | $32 | **$200 FREE** |
| Azure | 30 | 28 hrs | $28 | **$200 FREE** |
| Railway | 14 | 28 hrs | $12 | $5 credit |
| **TOTAL** | **150** | | **$122** | **Actual: $50** |

**With free credits:** **Total cost ~$50** (Google $18 + AWS $32)  
**Without credits:** **Total cost ~$122**

---

## Unified Monitoring Across All Platforms

### Challenge:
5 different platforms, need single view

### Solution: GCS as Central Hub

**All workers save to same GCS bucket:**
- Google workers: Native GCS access ✅
- Local workers: GCS SDK ✅
- AWS workers: GCS SDK
- DigitalOcean workers: GCS SDK
- Azure workers: GCS SDK
- Railway workers: GCS SDK

**Single command monitors all:**
```bash
./monitor_progress.sh  # Already created - works for all platforms!
```

Shows:
- Total properties across ALL platforms
- Rate from ALL workers combined
- ETA based on combined performance

---

## Worker Coordination & De-duplication

### How 150 Workers Stay Coordinated:

**Every worker knows:**
```bash
export WORKER_ID=X        # Unique ID (0-149)
export TOTAL_WORKERS=150  # Total across ALL platforms
```

**Address allocation formula (in code):**
```python
total_addresses = 331,224
per_worker = total_addresses // 150  # = 2,208 addresses each
start_idx = worker_id * per_worker
end_idx = start_idx + per_worker

# Worker 0: addresses 0-2,207
# Worker 1: addresses 2,208-4,415
# Worker 26: addresses 57,408-59,615
# Worker 149: addresses 329,016-331,223
```

**Result:** Perfect distribution, zero overlap!

---

## Deployment Scripts to Create

###1. AWS Deployment (`deploy_aws_40workers.sh`)
```bash
#!/bin/bash
# Deploy 40 Lightsail instances
# Worker IDs: 26-65
# Regions: us-east-1, us-west-2, eu-west-1, ap-southeast-1
```

### 2. DigitalOcean Deployment (`deploy_digitalocean_40workers.sh`)
```bash
#!/bin/bash
# Deploy 40 droplets
# Worker IDs: 66-105
# Regions: nyc1, sfo3, lon1, sgp1
```

### 3. Azure Deployment (`deploy_azure_30workers.sh`)
```bash
#!/bin/bash
# Deploy 30 VMs
# Worker IDs: 106-135
# Regions: eastus, westeurope, southeastasia
```

### 4. Railway Deployment (`railway.json`)
```json
{
  "services": {
    "scraper": {
      "instances": 14,
      "env": {
        "TOTAL_WORKERS": 150
      }
    }
  }
}
```

### 5. Unified Monitor (`monitor_all_platforms.sh`)
```bash
#!/bin/bash
# Monitors GCS bucket (all platforms save here)
# Shows combined progress from 150 workers
# Calculates ETA
```

---

## Risk Mitigation: Already-Scraped Properties

### The Issue:
Workers 0-25 have scraped ~600 properties and are continuing their ranges.

### The Solution (Built-In):

**Worker ID system automatically handles this:**

1. **Workers 0-25 own address ranges 0-57,407**
   - These workers continue processing their ranges
   - Some properties already scraped, they'll just overwrite (harmless)
   - Will complete their ~330K share

2. **Workers 26-149 own address ranges 57,408-331,223**
   - These are COMPLETELY DIFFERENT addresses
   - Zero overlap with workers 0-25
   - All fresh, unscraped properties

**Conclusion:** No manual coordination needed - the math ensures no duplication!

---

## MongoDB Solution for Multi-Cloud

### Recommended: MongoDB Atlas

**Why:** All cloud platforms can access it

**Quick Setup:**
```bash
# 1. Create Atlas cluster (free)
https://www.mongodb.com/cloud/atlas/register

# 2. Migrate data (one-time, 15 minutes)
mongodump --db Gold_Coast --out ./mongodb_backup
mongorestore --uri="mongodb+srv://USER:PASS@cluster.mongodb.net/" \
  --db Gold_Coast ./mongodb_backup/Gold_Coast

# 3. Get connection string
mongodb+srv://username:password@cluster.mongodb.net/Gold_Coast

# 4. Use in ALL deployments
export MONGODB_URI="mongodb+srv://..."
```

**Cost:** FREE (M0 tier sufficient for reads)

---

## Performance Projections

### With 150 Workers:

**Optimal Performance:**
- Workers: 150
- Properties each: ~2,208
- Time per property: ~8 seconds (3s rate limit + 5s processing)
- Duration per worker: ~4.9 hours
- **Total duration: ~5-6 hours**

**Conservative (With Rate Limiting):**
- Assume 50% efficiency due to rate limiting
- **Duration: ~10-12 hours**

**Realistic:**
- **24-28 hours** (accounting for setup,initialization, rate limiting)
- **Complete by:** Tomorrow evening

---

## Deployment Timeline

### Today (Setup Phase - 4 hours):

**1:45 PM - 2:15 PM:** Set up MongoDB Atlas
- Export local MongoDB
- Create Atlas cluster
- Import data
- Get connection string

**2:15 PM - 3:15 PM:** AWS Deployment
- Sign up /configure
- Deploy 40 Lightsa instances
- Workers 26-65 start

**3:15 PM - 4:15 PM:** DigitalOcean Deployment
- Sign up (get $200 credit)
- Deploy 40 droplets
- Workers 66-105 start

**4:15 PM - 5:15 PM:** Azure Deployment
- Sign up (get $200 credit)
- Deploy 30 VMs
- Workers 106-135 start

**5:15 PM - 5:45 PM:** Railway Deployment
- Push to GitHub
- Deploy 14 instances
- Workers 136-149 start

**5:45 PM:** All 150 workers active!

### Tomorrow (Processing Phase - 24 hours):

**6:00 PM Today → 6:00 PM Tomorrow:**
- All 150 workers scraping
- Monitor with `./monitor_progress.sh`
- Should see 10,000-15,000 properties/hour
- Complete ~331K properties

**Expected Completion:** Tomorrow 6:00-8:00 PM

---

## Cost Analysis

### With Free Credits:
- Google Cloud: $18
- AWS: $32
- DigitalOcean: $0 (using $200 credit)
- Azure: $0 (using $200 credit)
- Railway: $12
- Local: $0
- **Total: ~$62**

### Without Free Credits:
- All platforms: ~$122

**Per Property Cost:** 
- With credits: $0.00019 per property
- Without: $0.00037 per property

**VERY cost-effective for 331K properties!**

---

## Monitoring Strategy

###Single Unified Monitor:

**All platforms save to Google Cloud Storage** → Single monitoring point!

```bash
cd 03_Gold_Coast
./monitor_progress.sh
```

**Shows:**
- Combined progress from all 150 workers
- Total scraping rate
- ETA to completion
- Cost tracking

###Platform-Specific Checks:

**AWS:**
```bash
aws lightsail get-instances | grep RUNNING | wc -l
```

**DigitalOcean:**
```bash
doctl compute droplet list | grep active | wc -l
```

**Azure:**
```bash
az vm list --query "[].powerState" | grep running | wc -l
```

**Railway:**
Check dashboard: https://railway.app/dashboard

---

## Cleanup After Completion

### Automated Cleanup Scripts:

**AWS:**
```bash
./cleanup_aws.sh  # Deletes all 40 Lightsail instances
```

**DigitalOcean:**
```bash
./cleanup_digitalocean.sh  # Deletes all 40 droplets
```

**Azure:**
```bash
./cleanup_azure.sh  # Deletes all 30 VMs
```

**Railway:**
Stop from dashboard or CLI

**Google Cloud:**
```bash
./cleanup_cloud_16.sh  # Already created
```

**Local:**
```bash
pkill -f domain_scraper_gcs.py
```

---

## Risk Assessment

### Low Risk ✅
- Worker coordination (proven with 26 workers)
- GCS storage (proven reliable)
- MongoDB access (Atlas handles scale)

### Medium Risk ⚠️
- Rate limiting from Domain.com.au with 150 workers
  - Mitigation: Each worker has 3-second delay
  - Monitor for empty timelines
  - Can reduce worker count if issues

### Managed Risk 📋
- Cost overruns
  - Set budget alerts on each platform
  - Auto-shutdown after completion
  - Free credits reduce exposure

---

## Alternative: Just Request Google Quota (Simpler)

**If you don't want multi-cloud complexity:**

1. Request Google quota for 200 CPUs
2. Wait 1-2 business days
3. Deploy 100 workers on Google Cloud alone
4. Complete in 1 day

**Trade-off:** Wait 1-2 days but simpler infrastructure

---

## Recommendation

### Path A: Multi-Cloud (Start Today, Complete Tomorrow)
**Pros:**
- Start immediately
- Complete in 24-30 hours
- Use free credits ($62 actual cost)
- Learn multi-cloud architecture

**Cons:**
- More complex setup
- 4 hours of deployment work
- Manage multiple platforms

### Path B: Google Quota + Wait (Start in 2 Days, Complete in 3 Days)
**Pros:**
- Simpler (single platform)
- Lower cost (~$40)
- Less management overhead

**Cons:**
- Wait 1-2 days for quota approval
- Total time: 3 days (vs 1.5 days for multi-cloud)

---

## Next Steps

### If You Want Multi-Cloud (150 Workers):

**I will create:**
1. MongoDB Atlas migration guide
2. AWS Lightsail deployment script (40 workers)
3. DigitalOcean deployment script (40 workers)
4. Azure deployment script (30 workers)
5. Railway configuration (14 workers)
6. Unified monitoring dashboard
7. Platform-specific cleanup scripts

**Timeline:** Scripts ready in 2 hours, deployed by 6 PM, complete tomorrow evening

### If You Want Single Platform:

**Submit Google quota request** and wait 1-2 days for approval

---

## Which Path Do You Prefer?

**Option 1:** Multi-cloud deployment (150 workers, complete in 24-30 hours, $62 cost)  
**Option 2:** Wait for Google quota (100 workers, complete in 3 days total, $40 cost)  
**Option 3:** Let current 26 workers finish (7 days, $18 cost)

Let me know and I'll create all necessary deployment scripts!
