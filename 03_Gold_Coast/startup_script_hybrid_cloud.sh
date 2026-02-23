#!/bin/bash
set -e
exec > >(tee -a /var/log/startup-script.log)
exec 2>&1

echo "=========================================="
echo "Hybrid Cloud Worker Starting"
echo "Time: $(date)"
echo "=========================================="

export WORKER_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/worker-id" -H "Metadata-Flavor: Google")
export TOTAL_WORKERS=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/total-workers" -H "Metadata-Flavor: Google")
export GCS_BUCKET=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-bucket" -H "Metadata-Flavor: Google")
export MONGODB_URI=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-uri" -H "Metadata-Flavor: Google")

echo "Worker Configuration:"
echo "  Worker ID: $WORKER_ID (Cloud worker)"
echo "  Total Workers: $TOTAL_WORKERS (includes 10 local workers)"
echo "  GCS Bucket: $GCS_BUCKET"
echo ""

echo "Installing dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip chromium chromium-driver > /dev/null
pip3 install --quiet pymongo selenium google-cloud-storage

echo "Downloading scraper..."
mkdir -p /root/scraper && cd /root/scraper
gsutil cp gs://$GCS_BUCKET/domain_scraper_gcs.py ./

echo "Starting scraper..."
python3 domain_scraper_gcs.py

echo "Worker complete - shutting down"
sudo shutdown -h now
