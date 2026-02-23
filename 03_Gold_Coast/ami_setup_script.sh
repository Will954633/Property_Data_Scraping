#!/bin/bash
# AMI Setup Script - Install all dependencies
# Run this via SSH on the base EC2 instance

set -e

echo "========================================="
echo "PROPERTY SCRAPER AMI SETUP"
echo "========================================="
echo ""

# Update system
echo "1. Updating system..."
sudo apt-get update -qq

# Install dependencies  
echo "2. Installing dependencies..."
sudo apt-get install -y python3 python3-pip wget unzip gnupg curl

# Install Chrome (Ubuntu 22.04 compatible)
echo "3. Installing Google Chrome..."
sudo mkdir -p /etc/apt/keyrings
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update -qq
sudo apt-get install -y google-chrome-stable

# Install ChromeDriver
echo "4. Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver
rm chromedriver_linux64.zip

# Install Python packages
echo "5. Installing Python packages..."
sudo pip3 install --quiet selenium google-cloud-storage

# Download worker script
echo "6. Downloading scraper script..."
sudo mkdir -p /opt/scraper
sudo wget -q -O /opt/scraper/domain_scraper_gcs_json.py https://storage.googleapis.com/property-scraper-production-data-477306/code/domain_scraper_gcs_json.py

# Create launcher script
echo "7. Creating launcher script..."
sudo tee /opt/scraper/run_worker.sh > /dev/null <<'LAUNCHER'
#!/bin/bash
# Worker launcher - expects env vars: WORKER_ID, TOTAL_WORKERS, GCS_KEY_B64

set -e

# Setup GCS credentials
mkdir -p /root/.config/gcloud
echo "${GCS_KEY_B64}" | base64 -d > /root/gcs-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/root/gcs-key.json

# Set environment
export GCS_BUCKET=property-scraper-production-data-477306
export ADDRESSES_FILE=all_gold_coast_addresses.json

# Run scraper
cd /opt/scraper
python3 domain_scraper_gcs_json.py > /var/log/worker_${WORKER_ID}.log 2>&1

# Upload log
python3 -c "from google.cloud import storage; storage.Client().bucket('${GCS_BUCKET}').blob('logs/worker_${WORKER_ID}.log').upload_from_filename('/var/log/worker_${WORKER_ID}.log')"

# Shutdown
shutdown -h now
LAUNCHER

sudo chmod +x /opt/scraper/run_worker.sh

echo ""
echo "========================================="
echo "SETUP COMPLETE!"
echo "========================================="
echo ""
echo "Verification:"
google-chrome --version
chromedriver --version
python3 -c "import selenium; print(f'✓ Selenium {selenium.__version__}')"
python3 -c "from google.cloud import storage; print('✓ GCS client installed')"
echo ""
echo "✓ AMI is ready to be created!"
echo ""
