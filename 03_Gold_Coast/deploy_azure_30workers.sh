#!/bin/bash
# Deploy 30 Azure VMs for Domain scraping
# Workers: IDs 106-135
# Region distribution: eastus (12), westeurope (10), southeastasia (8)

set -e

echo "========================================="
echo "AZURE DEPLOYMENT - 30 WORKERS"
echo "========================================="
echo ""

# Configuration
BUCKET="property-scraper-production-data-477306"
ADDRESSES_FILE="all_gold_coast_addresses.json"
TOTAL_WORKERS=150
IMAGE="UbuntuLTS"
SIZE="Standard_B2s"  # 2 vCPU, 4GB RAM
RESOURCE_GROUP="property-scraper-rg"

# Check Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "✗ Azure CLI not found. Install with: brew install azure-cli"
    exit 1
fi

# Check Azure is configured
if ! az account show &> /dev/null 2>&1; then
    echo "✗ Azure not configured. Run: az login"
    exit 1
fi

echo "✓ Azure CLI configured"
echo ""

# Create resource group if doesn't exist
echo "Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location eastus &> /dev/null || true
echo "✓ Resource group ready"
echo ""

# Create GCS service account key (reuse if exists)
if [ ! -f "aws-gcs-key.json" ]; then
    echo "Creating GCS service account for cloud workers..."
    PROJECT_NAME="property-scraper-production-data-477306"
    
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
echo "Deploying workers to Azure..."
echo ""

# Function to deploy a worker
deploy_worker() {
    local worker_id=$1
    local region=$2
    
    echo "  Deploying worker $worker_id in $region..."
    
    # Create custom-data script
    local custom_data=$(cat <<'EOFCUSTOM'
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
EOFCUSTOM
)
    
    # Replace placeholders
    custom_data="${custom_data//GCS_KEY_B64_PLACEHOLDER/$GCS_KEY_B64}"
    custom_data="${custom_data//BUCKET_PLACEHOLDER/$BUCKET}"
    custom_data="${custom_data//WORKER_ID_PLACEHOLDER/$worker_id}"
    custom_data="${custom_data//TOTAL_WORKERS_PLACEHOLDER/$TOTAL_WORKERS}"
    custom_data="${custom_data//ADDRESSES_FILE_PLACEHOLDER/$ADDRESSES_FILE}"
    
    # Save to temp file
    echo "$custom_data" > "/tmp/custom-data-${worker_id}.sh"
    
    # Create VM
    az vm create \
        --resource-group "$RESOURCE_GROUP" \
        --name "scraper-worker-${worker_id}" \
        --location "$region" \
        --image "$IMAGE" \
        --size "$SIZE" \
        --custom-data "/tmp/custom-data-${worker_id}.sh" \
        --admin-username azureuser \
        --generate-ssh-keys \
        --no-wait \
        > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "    ✓ Worker $worker_id deployed"
    else
        echo "    ✗ Worker $worker_id failed"
    fi
    
    # Cleanup temp file
    rm -f "/tmp/custom-data-${worker_id}.sh"
    
    # Rate limiting
    sleep 2
}

# Deploy 12 workers to East US
echo "Deploying 12 workers to eastus..."
for worker_id in {106..117}; do
    deploy_worker $worker_id "eastus"
done

# Deploy 10 workers to West Europe
echo ""
echo "Deploying 10 workers to westeurope..."
for worker_id in {118..127}; do
    deploy_worker $worker_id "westeurope"
done

# Deploy 8 workers to Southeast Asia
echo ""
echo "Deploying 8 workers to southeastasia..."
for worker_id in {128..135}; do
    deploy_worker $worker_id "southeastasia"
done

echo ""
echo "Waiting for deployments to complete (this may take a few minutes)..."
sleep 60

echo ""
echo "========================================="
echo "DEPLOYMENT COMPLETE"
echo "========================================="
echo ""
echo "Deployed: 30 Azure VMs (IDs 106-135)"
echo "Regions: eastus (12), westeurope (10), southeastasia (8)"
echo ""
echo "Monitor with:"
echo "  az vm list --resource-group $RESOURCE_GROUP --query \"[?powerState=='VM running']\" | jq length"
echo "  cd 03_Gold_Coast && ./monitor_progress.sh"
echo ""
echo "Cleanup when done:"
echo "  ./cleanup_azure_30workers.sh"
echo ""
