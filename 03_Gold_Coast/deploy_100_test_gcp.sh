#!/bin/bash
set -e

echo "=========================================="
echo "Google Cloud 100-Address Test Deployment"
echo "Property Scraper - 30 Workers"
echo "=========================================="

# Configuration
PROJECT_ID="property-data-scraping-477306"
BUCKET_NAME="property-scraper-test-data-477306"
ZONE="us-central1-a"
INSTANCE_BASE="property-scraper-100test"
TOTAL_WORKERS=30

echo ""
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  GCS Bucket: $BUCKET_NAME"
echo "  Zone: $ZONE"
echo "  Total Workers: $TOTAL_WORKERS"
echo "  Instance Names: ${INSTANCE_BASE}-0 to ${INSTANCE_BASE}-$((TOTAL_WORKERS-1))"
echo ""

# Step 1: Set active project
echo "Step 1: Setting active GCP project..."
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo ""
echo "Step 2: Enabling required GCP APIs..."
gcloud services enable compute.googleapis.com storage.googleapis.com

# Step 3: Create/verify GCS bucket
echo ""
echo "Step 3: Verifying GCS bucket..."
if gsutil ls -b gs://$BUCKET_NAME 2>/dev/null; then
    echo "  ✓ Bucket exists: gs://$BUCKET_NAME"
else
    gsutil mb -l us-central1 gs://$BUCKET_NAME
    echo "  ✓ Created bucket: gs://$BUCKET_NAME"
fi

# Step 4: Upload test addresses to GCS
echo ""
echo "Step 4: Uploading test addresses to GCS..."
gsutil cp test_addresses_100.json gs://$BUCKET_NAME/test_addresses_100.json
echo "  ✓ Test addresses uploaded"

# Step 5: Upload scraper code to GCS
echo ""
echo "Step 5: Uploading scraper code to GCS..."
gsutil cp domain_scraper_gcs.py gs://$BUCKET_NAME/domain_scraper_gcs.py
gsutil cp requirements_gcs.txt gs://$BUCKET_NAME/requirements_gcs.txt
echo "  ✓ Scraper code uploaded"

# Step 6: Create startup script for workers
echo ""
echo "Step 6: Creating startup script..."

cat > startup_script_100test.sh << 'STARTUP_SCRIPT'
#!/bin/bash
set -e

# Log everything
exec > >(tee -a /var/log/startup-script.log)
exec 2>&1

echo "=========================================="
echo "Property Scraper Worker Starting"
echo "Time: $(date)"
echo "=========================================="

# Get worker configuration from metadata
export WORKER_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/worker-id" -H "Metadata-Flavor: Google")
export TOTAL_WORKERS=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/total-workers" -H "Metadata-Flavor: Google")
export GCS_BUCKET=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-bucket" -H "Metadata-Flavor: Google")
export MONGODB_URI=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-uri" -H "Metadata-Flavor: Google")

echo "Worker Configuration:"
echo "  Worker ID: $WORKER_ID"
echo "  Total Workers: $TOTAL_WORKERS"
echo "  GCS Bucket: $GCS_BUCKET"
echo ""

# Install system dependencies
echo "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip chromium chromium-driver wget curl unzip > /dev/null

echo "  ✓ System dependencies installed"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install --quiet pymongo selenium google-cloud-storage

echo "  ✓ Python dependencies installed"

# Download scraper code and test addresses from GCS
echo ""
echo "Downloading files from GCS..."
mkdir -p /root/scraper
cd /root/scraper

gsutil cp gs://$GCS_BUCKET/domain_scraper_gcs.py ./
gsutil cp gs://$GCS_BUCKET/test_addresses_100.json ./

echo "  ✓ Files downloaded"

# Create test scraper that uses pre-loaded addresses
echo ""
echo "Creating test scraper wrapper..."

cat > test_scraper_worker.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
import json
import os
import sys
from domain_scraper_gcs import DomainScraperGCS

class TestScraperWorker(DomainScraperGCS):
    """Test scraper that uses pre-loaded test addresses"""
    
    def get_my_addresses(self):
        """Load addresses from test file"""
        with open('test_addresses_100.json', 'r') as f:
            all_addresses = json.load(f)
        
        # Sort for consistency
        all_addresses.sort(key=lambda x: (x.get('address_pid') or 0))
        
        # Calculate this worker's slice
        total = len(all_addresses)
        per_worker = total // self.total_workers
        start_idx = self.worker_id * per_worker
        
        # Last worker gets remainder
        if self.worker_id == self.total_workers - 1:
            end_idx = total
        else:
            end_idx = start_idx + per_worker
        
        my_addresses = all_addresses[start_idx:end_idx]
        
        print(f"Total test addresses: {total:,}")
        print(f"My slice: {start_idx:,} to {end_idx:,} ({len(my_addresses):,} addresses)")
        
        return my_addresses

if __name__ == "__main__":
    try:
        scraper = TestScraperWorker()
        scraper.run()
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
PYTHON_SCRIPT

chmod +x test_scraper_worker.py

# Run the scraper
echo ""
echo "=========================================="
echo "Starting scraper..."
echo "=========================================="
python3 test_scraper_worker.py

# Shutdown after completion
echo ""
echo "=========================================="
echo "Worker complete - shutting down"
echo "=========================================="
sudo shutdown -h now
STARTUP_SCRIPT

echo "  ✓ Startup script created"

# Step 7: Get MongoDB URI
echo ""
echo "Step 7: MongoDB Configuration"
read -p "Enter MongoDB URI (or press Enter for local): " MONGODB_URI
if [ -z "$MONGODB_URI" ]; then
    MONGODB_URI="mongodb://127.0.0.1:27017/"
fi
echo "  Using: ${MONGODB_URI:0:30}..."

# Step 8: Launch worker instances
echo ""
echo "Step 8: Launching $TOTAL_WORKERS worker instances..."
echo "This may take a few moments..."
echo ""

for ((i=0; i<TOTAL_WORKERS; i++)); do
    INSTANCE_NAME="${INSTANCE_BASE}-${i}"
    
    echo "  Launching worker $i: $INSTANCE_NAME"
    
    gcloud compute instances create $INSTANCE_NAME \
        --zone=$ZONE \
        --machine-type=e2-medium \
        --image-family=debian-12 \
        --image-project=debian-cloud \
        --boot-disk-size=20GB \
        --boot-disk-type=pd-standard \
        --metadata=worker-id=$i,total-workers=$TOTAL_WORKERS,gcs-bucket=$BUCKET_NAME,mongodb-uri="$MONGODB_URI" \
        --metadata-from-file=startup-script=startup_script_100test.sh \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --tags=http-server,https-server \
        --quiet &
    
    # Launch in batches of 10 to avoid API limits
    if [ $(((i+1) % 10)) -eq 0 ]; then
        wait
        echo "    Batch of 10 launched, pausing..."
        sleep 5
    fi
done

# Wait for all background jobs
wait

echo ""
echo "=========================================="
echo "✓ All Workers Launched!"
echo "=========================================="
echo ""
echo "Deployment Summary:"
echo "  Workers: $TOTAL_WORKERS"
echo "  Instance Pattern: ${INSTANCE_BASE}-0 to ${INSTANCE_BASE}-$((TOTAL_WORKERS-1))"
echo "  Zone: $ZONE"
echo "  Bucket: gs://$BUCKET_NAME"
echo ""
echo "Workers will:"
echo "  1. Install Chrome and dependencies (~2-3 minutes)"
echo "  2. Download test addresses and scraper code"
echo "  3. Process their assigned addresses (~5-10 minutes)"
echo "  4. Save results to GCS bucket"
echo "  5. Automatically shutdown"
echo ""
echo "Estimated completion: ~10-15 minutes"
echo ""
echo "Monitor progress:"
echo "  ./monitor_100_test.sh"
echo ""
echo "Or check individual worker:"
echo "  gcloud compute instances get-serial-port-output ${INSTANCE_BASE}-0 --zone=$ZONE"
echo ""
echo "Check results in real-time:"
echo "  gsutil ls -r gs://$BUCKET_NAME/scraped_data/"
echo ""
echo "Download results (after completion):"
echo "  mkdir -p test_results_100"
echo "  gsutil -m cp -r gs://$BUCKET_NAME/scraped_data/ ./test_results_100/"
echo ""
echo "Cleanup all workers:"
echo "  ./cleanup_100_test.sh"
echo ""
echo "=========================================="
