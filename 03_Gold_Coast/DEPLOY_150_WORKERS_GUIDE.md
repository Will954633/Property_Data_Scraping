# Deploy 150 Workers - Quick Start Guide
**Multi-Cloud Deployment with Local MongoDB**

This guide will deploy 150 workers across AWS, DigitalOcean, and Azure to scrape 331,224 properties in 24-30 hours.

---

## ✅ Pre-Flight Checklist

- [x] MongoDB local with 331,224 addresses
- [x] Addresses exported to `all_gold_coast_addresses.json`
- [x] JSON uploaded to GCS
- [x] Scraper code uploaded to GCS
- [x] 26 workers already running (16 GCP + 10 local)

**Total workers to deploy: 124 new workers (26 already running + 124 new = 150 total)**

---

## Worker Distribution

| Platform | Worker IDs | Count | Status | Cost |
|----------|------------|-------|--------|------|
| Google Cloud | 0-15 | 16 | ✅ Running | $18 |
| Local | 16-25 | 10 | ✅ Running | $0 |
| **AWS** | 26-65 | 40 | 🆕 Deploy | $32 |
| **DigitalOcean** | 66-119 | 54 | 🆕 Deploy | **FREE** |
| **Azure** | 120-149 | 30 | 🆕 Deploy | **FREE** |
| **TOTAL** | 0-149 | 150 | | **~$50** |

**Note:** Originally planned 14 Railway workers, but redistributed to DigitalOcean (54 instead of 40) due to Chrome/ChromeDriver complexity on Railway PaaS.

---

## Deployment Timeline

| Time | Task | Duration |
|------|------|----------|
| **Now** | Prerequisites setup | 30 min |
| **+30min** | Deploy AWS (40 workers) | 15 min |
| **+45min** | Deploy DigitalOcean (54 workers) | 20 min |
| **+65min** | Deploy Azure (30 workers) | 15 min |
| **+80min** | All 150 workers active! | - |
| **+80min - +30hrs** | Workers scraping | 24-30 hrs |

**Total time:** ~30 hours from now to completion

---

## Step 1: Prerequisites (30 minutes)

### 1.1 Install CLI Tools

```bash
# AWS CLI
brew install awscli
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1)

# DigitalOcean CLI
brew install doctl
doctl auth init
# Enter API token from DigitalOcean dashboard

# Azure CLI
brew install azure-cli
az login
```

### 1.2 Sign Up for Free Credits

1. **DigitalOcean:** https://try.digitalocean.com/freetrialoffer/
   - Get **$200 free credit**
   
2. **Azure:** https://azure.microsoft.com/free/
   - Get **$200 free credit**

### 1.3 Make Scripts Executable

```bash
cd 03_Gold_Coast
chmod +x deploy_aws_40workers.sh
chmod +x deploy_digitalocean_40workers.sh
chmod +x deploy_azure_30workers.sh
```

---

## Step 2: Deploy AWS Workers (15 minutes)

```bash
cd 03_Gold_Coast
./deploy_aws_40workers.sh
```

This will:
- Create GCS service account (if needed)
- Deploy 40 Lightsail instances
- Workers 26-65 across us-east-1, us-west-2, eu-west-1
- Each worker auto-starts scraping
- Auto-shutdown when complete

**Expected output:**
```
✓ AWS CLI configured
✓ Service account created
Deploying 20 workers to us-east-1...
  ✓ Worker 26 deployed
  ✓ Worker 27 deployed
  ...
```

**Verify:**
```bash
aws lightsail get-instances --region us-east-1 | grep RUNNING | wc -l
# Should show 20 (or growing)
```

---

## Step 3: Deploy DigitalOcean Workers (20 minutes)

**Note:** Deploying 54 workers instead of original 40 (absorbed Railway's 14 workers)

First, update the script to deploy 54 workers:

```bash
# Edit the script to change worker range from 66-105 to 66-119
# Or use this modified command:
```

Actually, let me create an updated script for you:

```bash
cd 03_Gold_Coast
./deploy_digitalocean_54workers.sh  # Will create this
```

This will:
- Reuse GCS service account
- Deploy 54 droplets
- Workers 66-119 across nyc1, sfo3, lon1, sgp1
- FREE using $200 credit

**Verify:**
```bash
doctl compute droplet list | grep scraper-worker | wc -l
# Should show 54 (or growing)
```

---

## Step 4: Deploy Azure Workers (15 minutes)

```bash
cd 03_Gold_Coast
./deploy_azure_30workers.sh
```

This will:
- Create resource group
- Reuse GCS service account
- Deploy 30 VMs
- Workers 120-149 across eastus, westeurope, southeastasia
- FREE using $200 credit

**Verify:**
```bash
az vm list --resource-group property-scraper-rg | jq length
# Should show 30 (or growing)
```

---

## Step 5: Monitor Progress

### All Workers Combined

```bash
cd 03_Gold_Coast
./monitor_progress.sh
```

Shows:
- Total properties scraped (all 150 workers)
- Combined scraping rate
- ETA to completion

### Platform-Specific Monitoring

AWS:
```bash
aws lightsail get-instances --region us-east-1 --query 'instances[*].[name,state.name]'
```

DigitalOcean:
```bash
doctl compute droplet list --format Name,Status,Region
```

Azure:
```bash
az vm list --resource-group property-scraper-rg --output table
```

Google Cloud (existing):
```bash
gcloud compute instances list --filter="name~'worker-'"
```

---

## Cost Breakdown

| Platform | Workers | Cost | Free Credits | Actual Cost |
|----------|---------|------|--------------|-------------|
| Google Cloud | 16 | $18 | - | $18 |
| Local | 10 | $0 | - | $0 |
| AWS | 40 | $32 | - | $32 |
| DigitalOcean | 54 | $43 | **$200** | **$0** |
| Azure | 30 | $28 | **$200** | **$0** |
| **TOTAL** | **150** | **$121** | **$400** | **~$50** |

**With free credits: ~$50 total cost**

---

## Troubleshooting

### Issue: AWS deployment fails

**Solution:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check quotas
aws service-quotas get-service-quota \
    --service-code lightsail \
    --quota-code L-43DA4232
```

### Issue: DigitalOcean droplet limit

**Solution:**
- New accounts limited to 25 droplets
- Request increase: https://cloud.digitalocean.com/account/team/droplet_limit_increase
- Or deploy in 2 batches

### Issue: Azure VM quota

**Solution:**
```bash
# Check quota
az vm list-usage --location eastus --output table

# Request increase in Azure Portal
```

### Issue: GCS authentication fails

**Solution:**
```bash
# Verify service account
gcloud iam service-accounts list

# Recreate key
rm aws-gcs-key.json
gcloud iam service-accounts keys create aws-gcs-key.json \
    --iam-account=aws-scraper-access@property-scraper-production-data-477306.iam.gserviceaccount.com
```

---

## Cleanup After Completion

When all workers finish (24-30 hours), clean up:

```bash
cd 03_Gold_Coast

# AWS
for worker_id in {26..65}; do
    aws lightsail delete-instance --region us-east-1 \
        --instance-name "domain-scraper-worker-${worker_id}"
done

# DigitalOcean
doctl compute droplet list --format ID,Name | grep scraper-worker | \
    awk '{print $1}' | xargs doctl compute droplet delete --force

# Azure
az group delete --name property-scraper-rg --yes --no-wait

# GCP (if desired)
./cleanup_cloud_16.sh

# Local (if desired)
pkill -f domain_scraper
```

---

## Expected Performance

- **150 workers total**
- **331,224 properties**
- **~2,208 properties per worker**
- **~8 seconds per property** (3s rate limit + 5s processing)
- **~5 hours per worker** (optimal)
- **~24-30 hours total** (with overhead)

**Completion:** Tomorrow evening (~6-8 PM)

---

## Next Steps

1. **Run prerequisite setup** (Step 1)
2. **Deploy AWS** (Step 2)
3. **Deploy DigitalOcean** (Step 3)  
4. **Deploy Azure** (Step 4)
5. **Monitor progress** (`./monitor_progress.sh`)
6. **Wait 24-30 hours**
7. **Download results** from GCS
8. **Cleanup** cloud resources

---

## Files Reference

```
03_Gold_Coast/
├── deploy_aws_40workers.sh              # Deploy AWS
├── deploy_digitalocean_54workers.sh     # Deploy DO (will create)
├── deploy_azure_30workers.sh            # Deploy Azure
├── monitor_progress.sh                  # Monitor all
├── LOCAL_MONGODB_IMPLEMENTATION_GUIDE.md # Detailed guide
├── LOCAL_MONGODB_PLAN_SUMMARY.md        # Executive summary
└── DEPLOY_150_WORKERS_GUIDE.md         # This file
```

---

## Ready to Deploy?

Run these commands in sequence:

```bash
cd 03_Gold_Coast

# 1. Make scripts executable
chmod +x deploy_*.sh

# 2. Deploy AWS (15 min)
./deploy_aws_40workers.sh

# 3. Deploy DigitalOcean (20 min) - will create updated script
./deploy_digitalocean_54workers.sh

# 4. Deploy Azure (15 min)
./deploy_azure_30workers.sh

# 5. Monitor
./monitor_progress.sh
```

**All 150 workers will be scraping within ~1 hour!** 🚀
