# Multi-Cloud Deployment with Local MongoDB
**Implementation Guide - 150 Workers - No MongoDB Migration Required**

This guide implements the 150-worker multi-cloud plan while keeping MongoDB local. Instead of migrating to Atlas, we export addresses once and distribute via GCS.

---

## Overview

**What Changed:**
- ✅ MongoDB stays local (no migration!)
- ✅ Addresses exported to JSON once
- ✅ JSON uploaded to GCS
- ✅ All workers read from GCS JSON
- ✅ Simpler and faster setup

**What Stayed the Same:**
- Worker coordination via worker_id
- Results saved to GCS
- Same monitoring tools
- Same multi-cloud strategy

---

## Phase 1: Prepare Local Setup (15 minutes)

### Step 1: Export Addresses from MongoDB

```bash
cd 03_Gold_Coast

# Run the export script
python3 export_addresses_to_json.py
```

**Expected output:**
```
Connecting to local MongoDB...
✓ Connected to MongoDB
Fetching all properties with Domain URLs...
✓ Found 331,224 properties with Domain URLs
Writing to all_gold_coast_addresses.json...
✓ Exported 331,224 addresses to all_gold_coast_addresses.json
✓ File size: 12.45 MB
```

### Step 2: Upload to GCS

```bash
# Upload the address list
gsutil cp all_gold_coast_addresses.json gs://property-scraper-production-data-477306/

# Upload the new scraper code
gsutil cp domain_scraper_gcs_json.py gs://property-scraper-production-data-477306/code/

# Upload the startup script
gsutil cp startup_script_production_json.sh gs://property-scraper-production-data-477306/code/
```

### Step 3: Verify Upload

```bash
# Check files are in GCS
gsutil ls gs://property-scraper-production-data-477306/

# Should see:
# gs://property-scraper-production-data-477306/all_gold_coast_addresses.json
# gs://property-scraper-production-data-477306/code/
```

**✓ Local setup complete! MongoDB stays local, addresses now in GCS.**

---

## Phase 2: Test Locally (Optional but Recommended)

Before deploying 150 workers, test the new scraper locally:

```bash
# Set environment variables
export WORKER_ID=999
export TOTAL_WORKERS=1000
export GCS_BUCKET=property-scraper-production-data-477306
export ADDRESSES_FILE=all_gold_coast_addresses.json

# Run scraper (will process ~331 addresses)
python3 domain_scraper_gcs_json.py
```

**Expected:**
- Loads addresses from GCS
- Processes assigned slice
- Saves to GCS under worker_999/

---

## Phase 3: Deploy to Google Cloud (Already Running)

**Current Status:**
- 16 workers (IDs 0-15) already running on GCP
- Using original `domain_scraper_gcs.py` (MongoDB version)
- These can continue OR be upgraded to JSON version

**Option A: Let them finish (simplest)**
- They'll complete their addresses
- No action needed

**Option B: Upgrade to JSON version**
```bash
# Stop current workers
gcloud compute instances delete worker-{0..15} --zone=us-central1-a --quiet

# Redeploy with new scraper (see deployment script below)
```

---

## Phase 4: Deploy AWS Workers (40 workers, IDs 26-65)

### Prerequisites

1. **AWS Account Setup:**
```bash
# Install AWS CLI (if not installed)
brew install awscli

# Configure
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)
```

2. **Create Deployment Script:**

Create `deploy_aws_40workers_json.sh`:

```bash
#!/bin/bash
# Deploy 40 Lightsail instances with GCS JSON scraper

BUCKET="property-scraper-production-data-477306"
ADDRESSES_FILE="all_gold_coast_addresses.json"
TOTAL_WORKERS=150

# Deploy 40 workers (IDs 26-65)
for worker_id in {26..65}; do
    echo "Deploying worker $worker_id..."
    
    aws lightsail create-instances \
        --instance-names "domain-scraper-worker-${worker_id}" \
        --availability-zone us-east-1a \
        --blueprint-id ubuntu_20_04 \
        --bundle-id medium_2_0 \
        --user-data "$(cat <<EOF
#!/bin/bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip wget unzip

# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=\$(google-chrome --version | awk '{print \$3}' | cut -d'.' -f1)
DRIVER_VERSION=\$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_\${CHROME_VERSION})
wget https://chromedriver.storage.googleapis.com/\${DRIVER_VERSION}/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/
sudo chmod +x /usr/bin/chromedriver

# Install Python packages
pip3 install selenium google-cloud-storage

# Download scraper
wget -O /home/ubuntu/scraper.py https://storage.googleapis.com/${BUCKET}/code/domain_scraper_gcs_json.py

# Set environment and run
export WORKER_ID=${worker_id}
export TOTAL_WORKERS=${TOTAL_WORKERS}
export GCS_BUCKET=${BUCKET}
export ADDRESSES_FILE=${ADDRESSES_FILE}
export GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/gcs-key.json

# Note: You'll need to add GCS credentials to this instance
# For now, this is a template

cd /home/ubuntu
python3 scraper.py > worker_${worker_id}.log 2>&1
EOF
)"
    
    sleep 5  # Rate limiting
done

echo "Deployed 40 AWS workers (IDs 26-65)"
```

**Note:** AWS workers need GCS credentials. Options:
1. Create service account key and upload to each instance
2. Use AWS S3 + sync to GCS (requires setup)
3. Make GCS bucket public (not recommended)

**Recommended:** Create service account with Storage permissions:
```bash
# Create service account
gcloud iam service-accounts create aws-worker-access --display-name="AWS Worker GCS Access"

# Grant Storage permissions
gcloud projects add-iam-policy-binding property-scraper-production-477306 \
    --member="serviceAccount:aws-worker-access@property-scraper-production-477306.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create key
gcloud iam service-accounts keys create aws-gcs-key.json \
    --iam-account=aws-worker-access@property-scraper-production-477306.iam.gserviceaccount.com

# Upload key to each AWS instance (modify script to include this)
```

---

## Phase 5: Deploy DigitalOcean Workers (40 workers, IDs 66-105)

### Prerequisites

1. **Sign up for DigitalOcean:**
   - Get $200 free credit: https://try.digitalocean.com/freetrialoffer/

2. **Install doctl:**
```bash
brew install doctl

# Authenticate
doctl auth init
# Enter API token from DO dashboard
```

3. **Create Deployment Script:**

Similar to AWS, create `deploy_digitalocean_40workers_json.sh` with droplet creation commands.

---

## Phase 6: Deploy Azure Workers (30 workers, IDs 106-135)

### Prerequisites

1. **Sign up for Azure:**
   - Get $200 free credit: https://azure.microsoft.com/free/

2. **Install Azure CLI:**
```bash
brew install azure-cli

# Login
az login
```

3. **Create deployment script** similar to AWS/DO patterns.

---

## Phase 7: Deploy Railway Workers (14 workers, IDs 136-149)

Railway is the simplest - it's a PaaS:

1. Push code to GitHub
2. Connect Railway to repo
3. Set environment variables
4. Scale to 14 instances

---

## Simplified Alternative: Google Cloud Only

Instead of multi-cloud complexity, you can deploy all workers on Google Cloud:

```bash
# Request quota increase for 150 CPUs
gcloud compute quotas describe CPUS --region=us-central1

# Once approved, deploy 124 more workers (to reach 150 total)
./deploy_gcp_124workers_json.sh
```

This is simpler but requires waiting 1-2 days for quota approval.

---

## Monitoring Progress

The existing monitor works with both MongoDB and JSON scrapers:

```bash
cd 03_Gold_Coast
./monitor_progress.sh
```

Shows:
- Total properties scraped
- Combined rate from all workers
- ETA to completion

---

## Key Differences from Original Plan

| Aspect | Original Plan | Local MongoDB Plan |
|--------|---------------|-------------------|
| **MongoDB** | Migrate to Atlas | Keep local, export once |
| **Setup Time** | 30 min (migration) | 15 min (export + upload) |
| **Worker Startup** | Connect to Atlas | Read from GCS JSON |
| **Complexity** | Higher | Lower |
| **Cost** | Free (Atlas M0) | Free (GCS storage) |
| **Dependencies** | pymongo + Atlas | Only GCS |

---

## Cost Estimate with Local MongoDB

Same as original:
- **Google Cloud:** $18 (16 workers)
- **AWS:** $32 (40 workers)
- **DigitalOcean:** $0 (free $200 credit)
- **Azure:** $0 (free $200 credit)
- **Railway:** $12 (14 workers)

**Total:** ~$62 (with free credits) or ~$122 (without)

---

## Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| **Prep** | 15 min | Export addresses, upload to GCS |
| **Test** | 15 min | Test locally (optional) |
| **AWS** | 60 min | Deploy 40 Lightsail instances |
| **DigitalOcean** | 60 min | Deploy 40 droplets |
| **Azure** | 60 min | Deploy 30 VMs |
| **Railway** | 30 min | Deploy 14 PaaS instances |
| **Processing** | 24-30 hrs | All 150 workers scraping |

**Total:** Complete in ~30 hours from start

---

## Next Steps

1. **Run the export script** to create `all_gold_coast_addresses.json`
2. **Upload to GCS** (addresses + code)
3. **Test locally** with the new scraper
4. **Deploy to AWS** (or other platforms)
5. **Monitor progress** with existing tools

---

## Troubleshooting

### Issue: Export script can't connect to MongoDB

**Solution:**
```bash
# Check MongoDB is running
brew services list | grep mongodb

# Start if needed
brew services start mongodb-community

# Test connection
mongosh --eval "db.adminCommand('ping')"
```

### Issue: GCS upload fails

**Solution:**
```bash
# Check authentication
gcloud auth list

# Login if needed
gcloud auth login

# Set project
gcloud config set project property-scraper-production-477306
```

### Issue: Workers can't read from GCS

**Solution:**
```bash
# Make address file publicly readable (temporary test)
gsutil acl ch -u AllUsers:R gs://property-scraper-production-data-477306/all_gold_coast_addresses.json

# Or create service account (production)
# See AWS deployment section above
```

---

## Files Created

1. **`export_addresses_to_json.py`** - Exports MongoDB addresses to JSON
2. **`domain_scraper_gcs_json.py`** - Modified scraper (reads from GCS JSON)
3. **`startup_script_production_json.sh`** - Cloud worker startup script
4. **`LOCAL_MONGODB_IMPLEMENTATION_GUIDE.md`** - This guide

---

## Advantages of This Approach

✅ **Simpler** - No MongoDB migration  
✅ **Faster** - 15 min setup vs 30 min  
✅ **Fewer dependencies** - Workers don't need MongoDB  
✅ **More portable** - JSON works everywhere  
✅ **Easier debugging** - Static file vs database queries  
✅ **Better for cloud** - GCS native integration  

---

## Summary

The local MongoDB approach is **simpler and faster** than migrating to Atlas:

1. Export addresses once (15 min)
2. Upload to GCS
3. Deploy workers that read from GCS
4. Monitor as normal

All the benefits of the multi-cloud plan, with less complexity!

---

## Ready to Deploy?

Run these commands to start:

```bash
cd 03_Gold_Coast

# 1. Export addresses
python3 export_addresses_to_json.py

# 2. Upload to GCS  
gsutil cp all_gold_coast_addresses.json gs://property-scraper-production-data-477306/
gsutil cp domain_scraper_gcs_json.py gs://property-scraper-production-data-477306/code/

# 3. Test locally
export WORKER_ID=999 TOTAL_WORKERS=1000 GCS_BUCKET=property-scraper-production-data-477306
python3 domain_scraper_gcs_json.py

# 4. Deploy to clouds (use deployment scripts)
# ./deploy_aws_40workers_json.sh
# ./deploy_digitalocean_40workers_json.sh
# etc.
```

**Questions?** Check the troubleshooting section or review the original plan at `MULTI_CLOUD_150_WORKER_PLAN.md`.
