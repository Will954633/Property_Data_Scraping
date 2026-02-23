#!/bin/bash
# Deploy 54 DigitalOcean Droplets for Domain scraping
# Workers: IDs 66-119 (absorbed Railway's 14 workers)
# Region distribution: nyc1 (20), sfo3 (15), lon1 (12), sgp1 (7)

set -e

echo "========================================="
echo "DIGITALOCEAN DEPLOYMENT - 40 WORKERS"
echo "========================================="
echo ""

# Configuration
BUCKET="property-scraper-production-data-477306"
ADDRESSES_FILE="all_gold_coast_addresses.json"
TOTAL_WORKERS=150
IMAGE="ubuntu-20-04-x64"
SIZE="s-2vcpu-4gb"  # 2 vCPU, 4GB RAM
PROJECT_NAME="property-scraper-production-data-477306"

# Check doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "✗ doctl not found. Install with: brew install doctl"
    exit 1
fi

# Check doctl is configured
if ! doctl auth list &> /dev/null 2>&1; then
    echo "✗ doctl not configured. Run: doctl auth init"
    exit 1
fi

echo "✓ doctl configured"
echo ""

# Create GCS service account key for DO workers (reuse AWS key if exists)
if [ ! -f "aws-gcs-key.json" ]; then
    echo "Creating GCS service account for cloud workers..."
    if ! gcloud iam service-accounts describe aws-scraper-access@${PROJECT_NAME}.iam.gserviceaccount.com &> /dev/null; then
        gcloud iam service-accounts create aws-scraper-access \
            --display-name="Cloud Worker GCS Access" \
            --project=${PROJECT_NAME}
        
        gcloud projects add-iam-policy-binding ${PROJECT_NAME} \
            --member="serviceAccount:aws-scraper-access@${PROJECT_NAME}.iam.gserviceaccount.com" \
            --role="roles/storage.objectAdmin"
    fi
    
    gcloud iam service-accounts keys create aws-gcs-key.json \
        --iam-account=aws-scraper-access@${PROJECT_NAME}.iam.gserviceaccount.com
    echo "✓ Service account key created"
fi

# Base64 encode the key
GCS_KEY_B64=$(base64 -i aws-gcs-key.json | tr -d '\n')

echo ""
echo "Deploying workers to DigitalOcean..."
echo ""

# Function to deploy a worker
deploy_worker() {
    local worker_id=$1
    local region=$2
    
    echo "  Deploying worker $worker_id in $region..."
    
    # Create user-data script
    local user_data=$(cat <<'EOFUSER'
#!/bin/bash
set -e

# Update system
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
rm chromedriver_linux64.zip

# Install Python packages
pip3 install --quiet selenium google-cloud-storage

# Create GCS credentials
mkdir -p /root/.config/gcloud
echo 'GCS_KEY_B64_PLACEHOLDER' | base64 -d > /root/gcs-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/root/gcs-key.json

# Download scraper
wget -q -O /root/scraper.py https://storage.googleapis.com/BUCKET_PLACEHOLDER/code/domain_scraper_gcs_json.py

# Set environment and run
export WORKER_ID=WORKER_ID_PLACEHOLDER
export TOTAL_WORKERS=TOTAL_WORKERS_PLACEHOLDER
export GCS_BUCKET=BUCKET_PLACEHOLDER
export ADDRESSES_FILE=ADDRESSES_FILE_PLACEHOLDER

cd /root
python3 scraper.py > worker_WORKER_ID_PLACEHOLDER.log 2>&1

# Upload log to GCS
export GOOGLE_APPLICATION_CREDENTIALS=/root/gcs-key.json
python3 -c "from google.cloud import storage; storage.Client().bucket('BUCKET_PLACEHOLDER').blob('logs/worker_WORKER_ID_PLACEHOLDER.log').upload_from_filename('worker_WORKER_ID_PLACEHOLDER.log')"

# Shutdown after completion
shutdown -h now
EOFUSER
)
    
    # Replace placeholders
    user_data="${user_data//GCS_KEY_B64_PLACEHOLDER/$GCS_KEY_B64}"
    user_data="${user_data//BUCKET_PLACEHOLDER/$BUCKET}"
    user_data="${user_data//WORKER_ID_PLACEHOLDER/$worker_id}"
    user_data="${user_data//TOTAL_WORKERS_PLACEHOLDER/$TOTAL_WORKERS}"
    user_data="${user_data//ADDRESSES_FILE_PLACEHOLDER/$ADDRESSES_FILE}"
    
    # Create droplet
    doctl compute droplet create "scraper-worker-${worker_id}" \
        --region "$region" \
        --image "$IMAGE" \
        --size "$SIZE" \
        --user-data "$user_data" \
        --wait \
        > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "    ✓ Worker $worker_id deployed"
    else
        echo "    ✗ Worker $worker_id failed"
    fi
    
    # Rate limiting
    sleep 3
}

# Deploy 20 workers to NYC
echo "Deploying 20 workers to nyc1..."
for worker_id in {66..85}; do
    deploy_worker $worker_id "nyc1"
done

# Deploy 15 workers to SFO
echo ""
echo "Deploying 15 workers to sfo3..."
for worker_id in {86..100}; do
    deploy_worker $worker_id "sfo3"
done

# Deploy 12 workers to London
echo ""
echo "Deploying 12 workers to lon1..."
for worker_id in {101..112}; do
    deploy_worker $worker_id "lon1"
done

# Deploy 7 workers to Singapore
echo ""
echo "Deploying 7 workers to sgp1..."
for worker_id in {113..119}; do
    deploy_worker $worker_id "sgp1"
done

echo ""
echo "========================================="
echo "DEPLOYMENT COMPLETE"
echo "========================================="
echo ""
echo "Deployed: 54 DigitalOcean droplets (IDs 66-119)"
echo "Regions: nyc1 (20), sfo3 (15), lon1 (12), sgp1 (7)"
echo ""
echo "Monitor with:"
echo "  doctl compute droplet list | grep scraper-worker | wc -l  # Should show 54"
echo "  cd 03_Gold_Coast && ./monitor_progress.sh"
echo ""
echo "Cleanup when done:"
echo "  ./cleanup_digitalocean_54workers.sh"
echo ""
