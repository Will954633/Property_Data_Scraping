#!/bin/bash
# Startup script for cloud workers (GCS JSON version - no MongoDB)
# This script:
# 1. Installs all dependencies
# 2. Downloads the scraper from GCS
# 3. Runs the scraper with worker configuration

set -e

echo "========================================="
echo "DOMAIN SCRAPER - CLOUD WORKER STARTUP"
echo "========================================="
echo ""

# Worker configuration from metadata
WORKER_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/worker-id" -H "Metadata-Flavor: Google")
TOTAL_WORKERS=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/total-workers" -H "Metadata-Flavor: Google")
GCS_BUCKET=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-bucket" -H "Metadata-Flavor: Google")
ADDRESSES_FILE=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/addresses-file" -H "Metadata-Flavor: Google")

echo "Worker ID: $WORKER_ID"
echo "Total Workers: $TOTAL_WORKERS"
echo "GCS Bucket: $GCS_BUCKET"
echo "Addresses File: $ADDRESSES_FILE"
echo ""

# Update system
echo "Updating system packages..."
sudo apt-get update -qq

# Install Python 3 and pip
echo "Installing Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install Chrome and ChromeDriver
echo "Installing Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt-get update -qq
sudo apt-get install -y google-chrome-stable

echo "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver
rm chromedriver_linux64.zip

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --quiet selenium google-cloud-storage

# Download scraper from GCS
echo "Downloading scraper from GCS..."
gsutil cp gs://${GCS_BUCKET}/code/domain_scraper_gcs_json.py /home/ubuntu/scraper.py
chmod +x /home/ubuntu/scraper.py

# Set environment variables
export WORKER_ID=$WORKER_ID
export TOTAL_WORKERS=$TOTAL_WORKERS
export GCS_BUCKET=$GCS_BUCKET
export ADDRESSES_FILE=$ADDRESSES_FILE

# Run scraper
echo ""
echo "========================================="
echo "STARTING SCRAPER"
echo "========================================="
echo ""

cd /home/ubuntu
python3 scraper.py 2>&1 | tee worker_${WORKER_ID}.log

# Upload log to GCS on completion
echo "Uploading log to GCS..."
gsutil cp worker_${WORKER_ID}.log gs://${GCS_BUCKET}/logs/

echo ""
echo "========================================="
echo "WORKER COMPLETE - SHUTTING DOWN"
echo "========================================="

# Shutdown instance after completion
sudo shutdown -h now
