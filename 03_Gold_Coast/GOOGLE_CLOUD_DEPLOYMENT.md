# Google Cloud Deployment Guide - Domain Scraping with 200 Workers

## Overview

This guide explains how to deploy 200 workers on Google Cloud to scrape 300,000+ property addresses from Domain.com.au. The scraped data will be stored as JSON files in Google Cloud Storage, which can then be downloaded and imported to your local MongoDB database.

**Architecture:**
- 200 × Google Compute Engine Preemptible VMs (low cost)
- Worker partitioning (each worker processes a specific address range)
- Google Cloud Storage for JSON output
- MongoDB connection to read addresses from local/Atlas database
- Final import back to local MongoDB

**Estimated Cost:** $10-20 for entire 300k address scrape
**Estimated Time:** 15-20 hours to complete

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Google Cloud Setup](#google-cloud-setup)
3. [MongoDB Configuration](#mongodb-configuration)
4. [Worker Architecture](#worker-architecture)
5. [Modified Scraper Code](#modified-scraper-code)
6. [Deployment Scripts](#deployment-scripts)
7. [Monitoring Progress](#monitoring-progress)
8. [Download and Import Data](#download-and-import-data)
9. [Cost Breakdown](#cost-breakdown)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Local Requirements

- Google Cloud SDK installed (`gcloud` CLI)
- Python 3.8+
- MongoDB running locally with Gold_Coast database
- Git (for code deployment)

### Install Google Cloud SDK

```bash
# macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and authenticate
gcloud init
gcloud auth login
```

### Create Google Cloud Project

```bash
# Create new project
gcloud projects create property-scraper-[UNIQUE-ID]

# Set as active project
gcloud config set project property-scraper-[UNIQUE-ID]

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
```

---

## Google Cloud Setup

### 1. Create Cloud Storage Bucket

```bash
# Create bucket for scraped JSON files
gsutil mb -l us-central1 gs://property-scraper-data-[UNIQUE-ID]

# Verify bucket creation
gsutil ls
```

### 2. Set Up Service Account

```bash
# Create service account
gcloud iam service-accounts create property-scraper \
    --display-name="Property Scraper Service Account"

# Grant Storage Admin role
gcloud projects add-iam-policy-binding property-scraper-[UNIQUE-ID] \
    --member="serviceAccount:property-scraper@property-scraper-[UNIQUE-ID].iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Download credentials
gcloud iam service-accounts keys create ~/gcloud-credentials.json \
    --iam-account=property-scraper@property-scraper-[UNIQUE-ID].iam.gserviceaccount.com
```

### 3. Create VM Instance Template

```bash
# Create startup script
cat > startup-script.sh << 'EOF'
#!/bin/bash
set -e

# Update system
apt-get update
apt-get install -y python3-pip git chromium-driver chromium

# Install Python dependencies
pip3 install selenium pymongo google-cloud-storage webdriver-manager requests

# Clone repository (replace with your repo)
cd /opt
git clone https://github.com/YOUR_USERNAME/property_scraper.git
cd property_scraper

# Set environment variables
export MONGODB_URI="${MONGODB_URI}"
export GCS_BUCKET="${GCS_BUCKET}"
export WORKER_ID="${WORKER_ID}"
export TOTAL_WORKERS="${TOTAL_WORKERS}"

# Run scraper
python3 03_Gold_Coast/domain_scraper_gcs.py

# Shutdown when complete (to save costs)
sudo shutdown -h now
EOF

# Create instance template
gcloud compute instance-templates create property-scraper-template \
    --machine-type=e2-micro \
    --preemptible \
    --metadata-from-file startup-script=startup-script.sh \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --service-account=property-scraper@property-scraper-[UNIQUE-ID].iam.gserviceaccount.com \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --boot-disk-size=10GB
```

---

## MongoDB Configuration

### Option 1: MongoDB Atlas (Recommended for Cloud Access)

```bash
# Create free cluster at https://www.mongodb.com/cloud/atlas
# Get connection string, e.g.:
# mongodb+srv://username:password@cluster.mongodb.net/Gold_Coast?retryWrites=true&w=majority

export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/Gold_Coast"
```

### Option 2: Expose Local MongoDB (Less Secure)

```bash
# Edit MongoDB config to allow external connections
sudo vim /usr/local/etc/mongod.conf

# Change bindIp to allow your IP or 0.0.0.0 (less secure)
net:
  bindIp: 0.0.0.0

# Restart MongoDB
brew services restart mongodb-community

# Get your public IP
curl ifconfig.me

# Use connection string with your public IP
export MONGODB_URI="mongodb://YOUR_PUBLIC_IP:27017/Gold_Coast"
```

**Security Note:** For production, use MongoDB Atlas or set up VPN. Exposing MongoDB publicly is risky.

---

## Worker Architecture

### Partitioning Strategy

Each of 200 workers processes a unique slice of addresses:

```
Total Addresses: 300,000
Workers: 200
Addresses per Worker: 1,500

Worker 0: Addresses 0 - 1,499
Worker 1: Addresses 1,500 - 2,999
Worker 2: Addresses 3,000 - 4,499
...
Worker 199: Addresses 298,500 - 299,999
```

### Data Flow

```
Local MongoDB (Gold_Coast) 
    ↓ (read addresses)
GCP Worker 0-199 (scrape)
    ↓ (write JSON)
Google Cloud Storage
    ↓ (download)
Local Storage
    ↓ (import)
Local MongoDB (with domain_data)
```

---

## Modified Scraper Code

Create `03_Gold_Coast/domain_scraper_gcs.py`:

```python
#!/usr/bin/env python3
"""
Domain Property Scraper - Google Cloud Storage Version
Scrapes properties and saves JSON files to GCS instead of MongoDB
"""

import json
import os
import time
import sys
from datetime import datetime
from typing import Dict, Optional
from pymongo import MongoClient
from google.cloud import storage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import re


class DomainScraperGCS:
    """Domain scraper that saves to Google Cloud Storage"""
    
    def __init__(self):
        # Configuration from environment
        self.worker_id = int(os.getenv('WORKER_ID', 0))
        self.total_workers = int(os.getenv('TOTAL_WORKERS', 200))
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.gcs_bucket = os.getenv('GCS_BUCKET')
        
        # Validate configuration
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable required")
        if not self.gcs_bucket:
            raise ValueError("GCS_BUCKET environment variable required")
        
        # Initialize MongoDB connection
        self.mongo_client = MongoClient(self.mongodb_uri)
        self.db = self.mongo_client['Gold_Coast']
        
        # Initialize GCS client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.gcs_bucket)
        
        # Selenium driver
        self.driver = None
        
        print(f"Worker {self.worker_id}/{self.total_workers} initialized")
        print(f"MongoDB: {self.mongodb_uri.split('@')[1] if '@' in self.mongodb_uri else 'localhost'}")
        print(f"GCS Bucket: {self.gcs_bucket}")
    
    def setup_driver(self):
        """Setup Chrome WebDriver for GCP environment"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        
        # Use system chromium-driver
        service = Service('/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        
        print("Chrome driver initialized")
    
    def get_my_addresses(self):
        """Get addresses assigned to this worker"""
        # Get all collections (suburbs)
        collections = self.db.list_collection_names()
        
        addresses = []
        for collection_name in collections:
            collection = self.db[collection_name]
            docs = list(collection.find({}, {
                'ADDRESS_PID': 1,
                'ADDRESS_STANDARD': 1,
                'LOCALITY': 1,
                '_id': 1
            }))
            
            for doc in docs:
                addresses.append({
                    'address_pid': doc.get('ADDRESS_PID'),
                    'address': doc.get('ADDRESS_STANDARD'),
                    'suburb': doc.get('LOCALITY'),
                    'doc_id': str(doc.get('_id')),
                    'collection': collection_name
                })
        
        # Sort to ensure consistent ordering across workers
        addresses.sort(key=lambda x: x['address_pid'] or 0)
        
        # Calculate this worker's slice
        total = len(addresses)
        per_worker = total // self.total_workers
        start_idx = self.worker_id * per_worker
        
        # Last worker gets any remainder
        if self.worker_id == self.total_workers - 1:
            end_idx = total
        else:
            end_idx = start_idx + per_worker
        
        my_addresses = addresses[start_idx:end_idx]
        
        print(f"Total addresses: {total:,}")
        print(f"My slice: {start_idx:,} to {end_idx:,} ({len(my_addresses):,} addresses)")
        
        return my_addresses
    
    def build_domain_url(self, address: str) -> str:
        """Build Domain property profile URL"""
        address_clean = address.lower().strip()
        address_clean = re.sub(r'[,\s]+', '-', address_clean)
        address_clean = re.sub(r'-+', '-', address_clean)
        address_clean = address_clean.strip('-')
        
        return f"https://www.domain.com.au/property-profile/{address_clean}"
    
    def extract_property_data(self, url: str, address: str) -> Optional[Dict]:
        """
        Extract property data from Domain
        (Simplified version - use full scraper logic from domain_scraper.py)
        """
        try:
            print(f"  Scraping: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            html = self.driver.page_source
            
            # Extract JSON data
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', 
                            html, re.DOTALL)
            
            if not match:
                print(f"  Warning: No JSON data found")
                return None
            
            page_data = json.loads(match.group(1))
            apollo_state = page_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})
            
            # Find Property object
            property_obj = {}
            for key, value in apollo_state.items():
                if key.startswith('Property:') and value.get('__typename') == 'Property':
                    property_obj = value
                    break
            
            if not property_obj:
                print(f"  Warning: No property object found")
                return None
            
            # Extract data
            features = property_obj.get('features', {})
            valuation = property_obj.get('valuation', {})
            
            property_data = {
                'url': url,
                'address': address,
                'scraped_at': datetime.now().isoformat(),
                'features': {
                    'bedrooms': features.get('beds'),
                    'bathrooms': features.get('baths'),
                    'car_spaces': features.get('parking'),
                    'land_size': features.get('landSize'),
                    'property_type': features.get('propertyType')
                },
                'valuation': {
                    'low': valuation.get('lowerPrice'),
                    'mid': valuation.get('midPrice'),
                    'high': valuation.get('upperPrice'),
                    'accuracy': valuation.get('priceConfidence'),
                    'date': valuation.get('date')
                },
                'rental_estimate': {
                    'weekly_rent': valuation.get('rentPerWeek'),
                    'yield': valuation.get('rentYield')
                }
            }
            
            print(f"  ✓ Extracted data")
            return property_data
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def save_to_gcs(self, address_pid: str, suburb: str, property_data: Dict):
        """Save property data to Google Cloud Storage as JSON"""
        try:
            # Create file path: worker_XXX/suburb/address_pid.json
            blob_name = f"scraped_data/worker_{self.worker_id:03d}/{suburb}/{address_pid}.json"
            blob = self.bucket.blob(blob_name)
            
            # Upload JSON
            blob.upload_from_string(
                json.dumps(property_data, indent=2),
                content_type='application/json'
            )
            
            print(f"  ✓ Saved to GCS: {blob_name}")
            return True
            
        except Exception as e:
            print(f"  Error saving to GCS: {e}")
            return False
    
    def run(self):
        """Main worker execution"""
        print(f"\n{'='*70}")
        print(f"Worker {self.worker_id} Starting")
        print(f"{'='*70}\n")
        
        # Get my addresses
        addresses = self.get_my_addresses()
        
        if not addresses:
            print("No addresses to process")
            return
        
        # Setup driver
        self.setup_driver()
        
        # Process addresses
        successful = 0
        failed = 0
        
        try:
            for i, addr_info in enumerate(addresses, 1):
                print(f"\n[{i}/{len(addresses)}] {addr_info['address']}")
                
                # Build URL
                url = self.build_domain_url(addr_info['address'])
                
                # Scrape
                property_data = self.extract_property_data(url, addr_info['address'])
                
                if property_data:
                    # Add metadata
                    property_data.update({
                        'address_pid': addr_info['address_pid'],
                        'suburb': addr_info['suburb'],
                        'collection': addr_info['collection'],
                        'doc_id': addr_info['doc_id'],
                        'worker_id': self.worker_id
                    })
                    
                    # Save to GCS
                    if self.save_to_gcs(str(addr_info['address_pid']), addr_info['suburb'], property_data):
                        successful += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                
                # Rate limiting
                time.sleep(3)
                
                # Progress update
                if i % 10 == 0:
                    print(f"\nProgress: {i}/{len(addresses)} | Success: {successful} | Failed: {failed}")
        
        finally:
            if self.driver:
                self.driver.quit()
            
            self.mongo_client.close()
        
        # Summary
        print(f"\n{'='*70}")
        print(f"Worker {self.worker_id} Complete")
        print(f"{'='*70}")
        print(f"Total: {len(addresses)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        scraper = DomainScraperGCS()
        scraper.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

---

## Deployment Scripts

### Launch Script: `launch_workers.sh`

```bash
#!/bin/bash

# Configuration
PROJECT_ID="property-scraper-[UNIQUE-ID]"
BUCKET_NAME="property-scraper-data-[UNIQUE-ID]"
MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/Gold_Coast"
TOTAL_WORKERS=200

# Set project
gcloud config set project $PROJECT_ID

echo "Launching $TOTAL_WORKERS workers..."

for i in $(seq 0 $((TOTAL_WORKERS - 1))); do
    INSTANCE_NAME="worker-$(printf "%03d" $i)"
    
    echo "Launching $INSTANCE_NAME..."
    
    gcloud compute instances create $INSTANCE_NAME \
        --source-instance-template=property-scraper-template \
        --zone=us-central1-a \
        --metadata=WORKER_ID=$i,TOTAL_WORKERS=$TOTAL_WORKERS,MONGODB_URI="$MONGODB_URI",GCS_BUCKET=$BUCKET_NAME \
        --quiet &
    
    # Launch in batches to avoid rate limits
    if [ $((i % 20)) -eq 19 ]; then
        echo "Waiting for batch to launch..."
        wait
        sleep 5
    fi
done

wait

echo "All workers launched!"
echo "Monitor progress with: gcloud compute instances list"
```

### Monitor Script: `monitor_workers.sh`

```bash
#!/bin/bash

PROJECT_ID="property-scraper-[UNIQUE-ID]"
gcloud config set project $PROJECT_ID

echo "Active workers:"
gcloud compute instances list --filter="name:worker-*" --format="table(name,status,zone)"

echo ""
echo "Worker count by status:"
gcloud compute instances list --filter="name:worker-*" --format="value(status)" | sort | uniq -c
```

### Check Progress Script: `check_progress.sh`

```bash
#!/bin/bash

BUCKET_NAME="property-scraper-data-[UNIQUE-ID]"

echo "Checking scraped data in GCS..."
echo ""

# Count JSON files
TOTAL_FILES=$(gsutil ls -r gs://$BUCKET_NAME/scraped_data/**/*.json | wc -l)

echo "Total JSON files in GCS: $TOTAL_FILES"
echo ""

# Files per worker
echo "Files per worker (top 20):"
gsutil ls -r gs://$BUCKET_NAME/scraped_data/ | grep "worker_" | cut -d'/' -f4 | sort | uniq -c | sort -rn | head -20
```

---

## Monitoring Progress

### View Worker Logs

```bash
# View logs for specific worker
gcloud compute instances get-serial-port-output worker-000 --zone=us-central1-a

# View logs for all workers
for i in {0..199}; do
    echo "=== Worker $(printf "%03d" $i) ==="
    gcloud compute instances get-serial-port-output worker-$(printf "%03d" $i) --zone=us-central1-a | tail -20
done
```

### Monitor GCS Storage

```bash
# List all scraped files
gsutil ls -r gs://property-scraper-data-[UNIQUE-ID]/scraped_data/

# Count files per suburb
gsutil ls -r gs://property-scraper-data-[UNIQUE-ID]/scraped_data/**/*.json | \
    cut -d'/' -f5 | sort | uniq -c | sort -rn

# Check storage size
gsutil du -sh gs://property-scraper-data-[UNIQUE-ID]/
```

### Cleanup Complete Workers

```bash
# List terminated workers
gcloud compute instances list --filter="name:worker-* AND status=TERMINATED"

# Delete terminated workers
gcloud compute instances delete $(gcloud compute instances list --filter="name:worker-* AND status=TERMINATED" --format="value(name)") --zone=us-central1-a --quiet
```

---

## Download and Import Data

### Download All JSON Files

```bash
# Create local directory
mkdir -p ~/scraped_property_data

# Download all files from GCS
gsutil -m rsync -r gs://property-scraper-data-[UNIQUE-ID]/scraped_data/ ~/scraped_property_data/

# Verify download
find ~/scraped_property_data -name "*.json" | wc -l
```

### Import Script: `import_scraped_data.py`

```python
#!/usr/bin/env python3
"""
Import scraped JSON files from GCS download into MongoDB
"""

import json
import os
from pymongo import MongoClient
from datetime import datetime
from pathlib import Path

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"
SCRAPED_DATA_DIR = os.path.expanduser("~/scraped_property_data")

def import_data():
    """Import all JSON files into MongoDB"""
    
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    # Find all JSON files
    json_files = list(Path(SCRAPED_DATA_DIR).rglob("*.json"))
    print(f"Found {len(json_files):,} JSON files to import\n")
    
    successful = 0
    failed = 0
    
    for i, json_file in enumerate(json_files, 1):
        try:
            # Load JSON
            with open(json_file, 'r') as f:
                property_data = json.load(f)
            
            # Get metadata
            collection_name = property_data.get('collection')
            doc_id = property_data.get('doc_id')
            
            if not collection_name or not doc_id:
                print(f"Skipping {json_file}: missing collection or doc_id")
                failed += 1
                continue
            
            # Update MongoDB document
            from bson.objectid import ObjectId
            collection = db[collection_name]
            
            result = collection.update_one(
                {'_id': ObjectId(doc_id)},
                {
                    '$set': {
                        'domain_data': property_data,
                        'domain_scraped_at': datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                successful += 1
            else:
                failed += 1
            
            # Progress
            if i % 1000 == 0:
                print(f"Progress: {i:,}/{len(json_files):,} | Success: {successful:,} | Failed: {failed:,}")
        
        except Exception as e:
            print(f"Error importing {json_file}: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Import Complete")
    print(f"{'='*70}")
    print(f"Total files: {len(json_files):,}")
    print(f"Successful: {successful:,}")
    print(f"Failed: {failed:,}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    import_data()
```

### Run Import

```bash
# Make executable
chmod +x import_scraped_data.py

# Run import
python3 import_scraped_data.py
```

---

## Cost Breakdown

### Google Cloud Costs (One-Time Job)

| Resource | Quantity | Unit Cost | Hours | Total |
|----------|----------|-----------|-------|-------|
| e2-micro Preemptible VM | 200 | $0.0025/hr | 15 | $7.50 |
| Cloud Storage | 1 GB | $0.02/GB | - | $0.02 |
| Network Egress | 1 GB | $0.12/GB | - | $0.12 |

**Total Estimated Cost: $8-15**

### Cost Optimization Tips

1. **Use Preemptible VMs**: 60-91% cheaper than regular VMs
2. **Auto-shutdown**: Workers automatically shutdown when complete
3. **Regional Selection**: Use us-central1 or us-east1 for lowest costs
4. **Clean Up**: Delete workers and storage after import

---

## Troubleshooting

### Workers Not Starting

```bash
# Check quota limits
gcloud compute project-info describe --project=property-scraper-[UNIQUE-ID]

# Request quota increase if needed
# https://console.cloud.google.com/iam-admin/quotas
```

### Workers Timing Out

```bash
# Check worker logs
gcloud compute instances get-serial-port-output worker-000 --zone=us-central1-a

# Common issues:
# - MongoDB connection timeout (check URI and firewall)
# - ChromeDriver not found (check startup script)
# - Out of memory (increase machine type)
```

### Missing JSON Files

```bash
# Check if worker completed
gcloud compute instances describe worker-000 --zone=us-central1-a

# Check GCS for partial data
gsutil ls gs://property-scraper-data-[UNIQUE-ID]/scraped_data/worker_000/

# Rerun failed worker
gcloud compute instances start worker-000 --zone=us-central1-a
```

### Import Errors

```python
# Verify MongoDB connection
mongosh $MONGODB_URI

# Check for duplicate imports
db.runaway_bay.findOne({"domain_data": {$exists: true}})

# Count imported records
db.runaway_bay.countDocuments({"domain_data": {$exists: true}})
```

---

## Complete Workflow Summary

### Phase 1: Setup (1-2 hours)

```bash
# 1. Install gcloud SDK
# 2. Create GCP project
# 3. Create GCS bucket
# 4. Set up MongoDB Atlas or expose local MongoDB
# 5. Upload scraper code to Git repository
```

### Phase 2: Deploy (15-20 hours)

```bash
# 1. Create instance template
./create_template.sh

# 2. Launch 200 workers
./launch_workers.sh

# 3. Monitor progress
watch -n 60 ./check_progress.sh

# 4. Wait for completion (15-20 hours)
```

### Phase 3: Import (1-2 hours)

```bash
# 1. Download JSON files from GCS
gsutil -m rsync -r gs://BUCKET/scraped_data/ ~/scraped_property_data/

# 2. Import to MongoDB
python3 import_scraped_data.py

# 3. Verify import
mongosh --eval "db.runaway_bay.countDocuments({domain_data: {\$exists: true}})"

# 4. Clean up GCP resources
gcloud compute instances delete worker-* --zone=us-central1-a --quiet
gsutil -m rm -r gs://BUCKET/scraped_data/
```

---

## Final Checklist

- [ ] Google Cloud SDK installed and authenticated
- [ ] GCP project created and billing enabled
- [ ] GCS bucket created
- [ ] MongoDB accessible (Atlas or local with public IP)
- [ ] Scraper code pushed to Git repository
- [ ] Instance template created
- [ ] 200 workers launched
- [ ] Monitor progress (15-20 hours)
- [ ] Workers auto-shutdown on completion
- [ ] JSON files downloaded from GCS
- [ ] Data imported to local MongoDB
- [ ] Verify import successful
- [ ] Clean up GCP resources (delete workers, bucket)
- [ ] Check final cost in GCP console

---

## Support and Resources

- **Google Cloud Documentation**: https://cloud.google.com/docs
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas
- **Selenium Documentation**: https://selenium-python.readthedocs.io/

---

## Notes

- Preemptible VMs can be terminated by Google (rare for <24hr jobs)
- Rate limit: 3 seconds between requests to Domain.com.au
- Expected runtime: 300k addresses ÷ 200 workers ÷ 3 sec = ~15 hours
- JSON files are stored in GCS for 30 days (delete after import)
- Workers auto-shutdown to save costs

**Last Updated:** 2025-01-05
