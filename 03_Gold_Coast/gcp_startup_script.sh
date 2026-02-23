#!/bin/bash
set -e

echo "=========================================="
echo "GCP VM STARTUP - Property Scraper Test"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt-get update
apt-get install -y python3-pip git wget unzip

# Install Chrome
echo "Installing Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
echo "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
echo "Chrome version: $CHROME_VERSION"
wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"
unzip -q chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver
rm -rf chromedriver-linux64.zip chromedriver-linux64

# Install Python dependencies
echo "Installing Python packages..."
pip3 install --break-system-packages selenium google-cloud-storage

# Create working directory
echo "Setting up working directory..."
mkdir -p /opt/scraper
cd /opt/scraper

# Download test files from metadata
echo "Downloading test data..."
curl -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/attributes/test-addresses" \
  | base64 -d > test_addresses_5.json

curl -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/attributes/scraper-code" \
  | base64 -d > test_scraper_gcs.py

chmod +x test_scraper_gcs.py

# Get GCS bucket from metadata
export GCS_BUCKET=$(curl -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-bucket" 2>/dev/null)

echo "GCS Bucket: $GCS_BUCKET"

# Verify files
echo "Verifying setup..."
ls -la
cat test_addresses_5.json

# Run scraper
echo "=========================================="
echo "Starting scraper..."
echo "=========================================="
python3 test_scraper_gcs.py

# Shutdown when complete (to save costs)
echo "=========================================="
echo "Test complete - shutting down VM"
echo "=========================================="
sudo shutdown -h now
