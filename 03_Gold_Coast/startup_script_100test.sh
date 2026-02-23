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
