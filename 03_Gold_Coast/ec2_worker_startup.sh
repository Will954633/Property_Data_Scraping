#!/bin/bash
# EC2 Worker Startup Script
# Environment variables must be set: WORKER_ID, TOTAL_WORKERS, GCS_KEY_B64

set -e

echo "Starting worker ${WORKER_ID} of ${TOTAL_WORKERS}"

# Install dependencies
apt-get update -qq
apt-get install -y python3 python3-pip wget unzip gnupg curl

# Install Chrome (Ubuntu 22.04 compatible)
mkdir -p /etc/apt/keyrings
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update -qq
apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
mv chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver
rm chromedriver_linux64.zip

# Install Python packages
pip3 install --quiet selenium google-cloud-storage

# Set up GCS credentials
mkdir -p /root/.config/gcloud
echo "${GCS_KEY_B64}" | base64 -d > /root/gcs-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/root/gcs-key.json

# Download scraper
wget -q -O /root/scraper.py https://storage.googleapis.com/property-scraper-production-data-477306/code/domain_scraper_gcs_json.py

# Set environment for scraper
export GCS_BUCKET=property-scraper-production-data-477306
export ADDRESSES_FILE=all_gold_coast_addresses.json

# Run scraper
cd /root
python3 scraper.py > worker_${WORKER_ID}.log 2>&1

# Upload log
python3 -c "from google.cloud import storage; storage.Client().bucket('property-scraper-production-data-477306').blob('logs/worker_${WORKER_ID}.log').upload_from_filename('worker_${WORKER_ID}.log')"

# Shutdown
shutdown -h now
