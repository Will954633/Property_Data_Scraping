# Railway Deployment Guide - 14 Workers (IDs 136-149)

Railway is a Platform-as-a-Service (PaaS) that simplifies deployment. No VM management needed!

## Prerequisites

1. **GitHub Account** (to host code)
2. **Railway Account** - Sign up at https://railway.app

## Step 1: Prepare GitHub Repository

```bash
cd 03_Gold_Coast

# Create a new repo or use existing
# Push code to GitHub (if not already done)
git init
git add domain_scraper_gcs_json.py
git commit -m "Add Railway scraper"
git branch -M main
git remote add origin YOUR_REPO_URL
git push -u origin main
```

## Step 2: Create Railway Project

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select your repository
6. Railway will detect it's a Python project

## Step 3: Configure Environment Variables

In Railway dashboard, add these environment variables:

```
WORKER_ID=136  # Change for each instance (136-149)
TOTAL_WORKERS=150
GCS_BUCKET=property-scraper-production-data-477306
ADDRESSES_FILE=all_gold_coast_addresses.json
```

**Important:** You'll need to add GCS credentials. Two options:

### Option A: Use Service Account Key (Recommended)

1. Create key (if not already done):
```bash
gcloud iam service-accounts keys create railway-gcs-key.json \
    --iam-account=aws-scraper-access@property-scraper-production-data-477306.iam.gserviceaccount.com
```

2. Base64 encode:
```bash
base64 -i railway-gcs-key.json
```

3. Add to Railway as environment variable:
```
GOOGLE_APPLICATION_CREDENTIALS_JSON=<base64 output>
```

4. Modify scraper startup to decode:
   - Railway will decode this and write to a file

### Option B: Make GCS Files Public (Not Recommended)

```bash
gsutil acl ch -u AllUsers:R gs://property-scraper-production-data-477306/all_gold_coast_addresses.json
gsutil acl ch -u AllUsers:R gs://property-scraper-production-data-477306/code/domain_scraper_gcs_json.py
```

## Step 4: Create Procfile

Create `/03_Gold_Coast/Procfile`:
```
worker: python3 domain_scraper_gcs_json.py
```

## Step 5: Create Requirements File

Create `/03_Gold_Coast/requirements.txt`:
```
selenium==4.15.2
google-cloud-storage==2.10.0
```

## Step 6: Deploy Multiple Instances

Railway allows scaling:

1. Deploy first instance (worker 136)
2. In Railway dashboard, duplicate the service 13 times
3. For each duplicate, change `WORKER_ID` environment variable:
   - Instance 1: WORKER_ID=136
   - Instance 2: WORKER_ID=137
   - ...
   - Instance 14: WORKER_ID=149

## Monitoring

Railway provides:
- Real-time logs
- Resource usage graphs
- Automatic crash recovery

Access logs:
1. Click on a service
2. View "Deployments"
3. Click on active deployment
4. View logs

## Limitations

- **Chrome/ChromeDriver:** Railway doesn't support Chrome by default
- **Alternative:** Use Selenium Grid or headless Chrome Docker image

### Recommended: Use Playwright Instead

For Railway, Playwright is better than Selenium:

1. Modify scraper to use Playwright
2. Update requirements.txt:
```
playwright==1.40.0
google-cloud-storage==2.10.0
```

3. Update scraper code (would need modification)

## Cost

Railway pricing:
- $5 free credit/month
- ~$0.000231/GB-second for additional usage
- 14 workers × 24 hours ≈ $10-15 total

## Alternative: Skip Railway

Given Chrome/ChromeDriver complexity on Railway, consider:
- Deploy 14 more workers on DigitalOcean instead (still FREE with $200 credit)
- Or deploy on Google Cloud if quota allows

## If You Still Want Railway

For simplest Railway deployment:

1. **Use Browserless** (headless Chrome service):
   - Add Browserless to Railway project
   - Connect scraper to Browserless instead of local Chrome
   - Requires scraper modification

2. **Or use Docker**:
   - Create Dockerfile with Chrome pre-installed
   - Railway supports Docker deployments
   - More complex but works

Due to these complexities, **recommend deploying these 14 workers on DigitalOcean or Azure instead** (both have free credits).

## Updated Allocation Without Railway

If skipping Railway, redistribute workers:

- **AWS:** 40 workers (IDs 26-65)
- **DigitalOcean:** 54 workers (IDs 66-119) - Still FREE
- **Azure:** 30 workers (IDs 120-149) - Still FREE
- **Google Cloud:** 16 workers (IDs 0-15) - Already running
- **Local:** 10 workers (IDs 16-25) - Already running

**Total: 150 workers, cost: ~$50 (AWS $32 + GCP $18)**
