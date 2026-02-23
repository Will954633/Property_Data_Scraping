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

# Download scraper code from GCS
echo ""
echo "Downloading scraper code from GCS..."
mkdir -p /root/scraper
cd /root/scraper

gsutil cp gs://$GCS_BUCKET/domain_scraper_gcs.py ./

echo "  ✓ Files downloaded"

# Run the scraper
echo ""
echo "=========================================="
echo "Starting scraper..."
echo "=========================================="
python3 domain_scraper_gcs.py

# Shutdown after completion
echo ""
echo "=========================================="
echo "Worker complete - shutting down"
echo "=========================================="
sudo shutdown -h now
