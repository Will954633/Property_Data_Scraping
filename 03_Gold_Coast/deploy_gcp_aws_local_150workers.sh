#!/bin/bash
# Deploy 150 workers using Google Cloud + AWS + Local
# Distribution:
# - Google Cloud: 16 workers (IDs 0-15)
# - Local: 20 workers (IDs 16-35)
# - AWS: 114 workers (IDs 36-149)

set -e

echo "========================================="
echo "150 WORKER DEPLOYMENT"
echo "Google Cloud + AWS + Local"
echo "========================================="
echo ""

BUCKET="property-scraper-production-data-477306"
ADDRESSES_FILE="all_gold_coast_addresses.json"
TOTAL_WORKERS=150

echo "Worker Distribution:"
echo "  Google Cloud: 16 workers (IDs 0-15)"
echo "  Local:        20 workers (IDs 16-35)"
echo "  AWS:          114 workers (IDs 36-149)"
echo "  TOTAL:        150 workers"
echo ""

read -p "Ready to deploy? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Part 1: Deploy Google Cloud workers (16 workers, IDs 0-15)
echo ""
echo "========================================="
echo "PART 1: DEPLOYING GOOGLE CLOUD WORKERS"
echo "========================================="
echo ""

# Update existing GCP deployment script for TOTAL_WORKERS=150
cat > /tmp/gcp_startup_150workers.sh <<'EOFGCP'
#!/bin/bash
set -e

echo "Installing dependencies..."
apt-get update -qq
apt-get install -y python3 python3-pip wget unzip

# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update -qq
apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
mv chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver

# Install Python packages
pip3 install selenium google-cloud-storage pymongo

# Download scraper (using JSON version for consistency)
gsutil cp gs://property-scraper-production-data-477306/code/domain_scraper_gcs_json.py /root/scraper.py

# Get worker ID from metadata
WORKER_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/worker-id" -H "Metadata-Flavor: Google")

# Set environment
export WORKER_ID=$WORKER_ID
export TOTAL_WORKERS=150
export GCS_BUCKET=property-scraper-production-data-477306
export ADDRESSES_FILE=all_gold_coast_addresses.json

# Run scraper
cd /root
python3 scraper.py > worker_${WORKER_ID}.log 2>&1

# Upload log
gsutil cp worker_${WORKER_ID}.log gs://property-scraper-production-data-477306/logs/

# Shutdown
shutdown -h now
EOFGCP

# Upload startup script to GCS
gsutil cp /tmp/gcp_startup_150workers.sh gs://${BUCKET}/code/

# Deploy 16 GCP workers
for worker_id in {0..15}; do
    echo "  Deploying GCP worker-$worker_id..."
    
    gcloud compute instances create worker-$worker_id \
        --zone=us-central1-a \
        --machine-type=e2-medium \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --metadata=worker-id=$worker_id \
        --metadata-from-file=startup-script=/tmp/gcp_startup_150workers.sh \
        --scopes=cloud-platform \
        --quiet &
    
    sleep 1
done

wait
echo "✓ 16 GCP workers deployed"

