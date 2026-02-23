#!/bin/bash
set -e
exec > >(tee -a /var/log/startup-script.log)
exec 2>&1

echo "=========================================="
echo "JSON Cloud Worker Starting (FIXED)"
echo "Time: $(date)"
echo "=========================================="

export WORKER_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/worker-id" -H "Metadata-Flavor: Google")
export TOTAL_WORKERS=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/total-workers" -H "Metadata-Flavor: Google")
export GCS_BUCKET=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-bucket" -H "Metadata-Flavor: Google")
export ADDRESSES_FILE="all_gold_coast_addresses.json"

echo "Worker Configuration:"
echo "  Worker ID: $WORKER_ID"
echo "  Total Workers: $TOTAL_WORKERS"
echo "  GCS Bucket: $GCS_BUCKET"
echo "  Addresses File: $ADDRESSES_FILE"
echo ""

echo "Installing dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip chromium chromium-driver > /dev/null

echo "Installing Python packages (with --break-system-packages flag)..."
pip3 install --break-system-packages --quiet selenium google-cloud-storage

echo "Downloading JSON scraper..."
mkdir -p /root/scraper && cd /root/scraper
gsutil cp gs://$GCS_BUCKET/domain_scraper_gcs_json.py ./

echo "Starting JSON scraper..."
python3 domain_scraper_gcs_json.py

echo "Worker complete - shutting down"
sudo shutdown -h now
