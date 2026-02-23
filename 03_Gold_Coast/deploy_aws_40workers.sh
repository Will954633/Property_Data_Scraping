#!/bin/bash
# Deploy 40 AWS Lightsail instances for Domain scraping
# Workers: IDs 26-65
# Region distribution: us-east-1 (20), us-west-2 (10), eu-west-1 (10)

set -e

echo "========================================="
echo "AWS LIGHTSAIL DEPLOYMENT - 40 WORKERS"
echo "========================================="
echo ""

# Configuration
BUCKET="property-scraper-production-data-477306"
ADDRESSES_FILE="all_gold_coast_addresses.json"
TOTAL_WORKERS=150
BLUEPRINT="ubuntu_20_04"
BUNDLE="medium_2_0"  # 2 vCPU, 4GB RAM

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "✗ AWS CLI not found. Install with: brew install awscli"
    exit 1
fi

# Check AWS is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "✗ AWS not configured. Run: aws configure"
    exit 1
fi

echo "✓ AWS CLI configured"
echo ""

# Create GCS service account key for AWS workers
echo "Creating GCS service account for AWS workers..."
if ! gcloud iam service-accounts describe aws-scraper-access@${BUCKET%-*}.iam.gserviceaccount.com &> /dev/null; then
    gcloud iam service-accounts create aws-scraper-access \
        --display-name="AWS Worker GCS Access" \
        --project=${BUCKET%-*}
    
    gcloud projects add-iam-policy-binding ${BUCKET%-*} \
        --member="serviceAccount:aws-scraper-access@${BUCKET%-*}.iam.gserviceaccount.com" \
        --role="roles/storage.objectAdmin"
    
    echo "✓ Service account created"
fi

# Create key if doesn't exist
if [ ! -f "aws-gcs-key.json" ]; then
    gcloud iam service-accounts keys create aws-gcs-key.json \
        --iam-account=aws-scraper-access@${BUCKET%-*}.iam.gserviceaccount.com
    echo "✓ Service account key created: aws-gcs-key.json"
fi

# Base64 encode the key for user-data
GCS_KEY_B64=$(base64 -i aws-gcs-key.json)

echo ""
echo "Deploying workers to AWS Lightsail..."
echo ""

# Function to deploy a worker
deploy_worker() {
    local worker_id=$1
    local region=$2
    local az="${region}a"
    
    echo "  Deploying worker $worker_id in $region..."
    
    # Create user-data script
    local user_data=$(cat <<EOF
#!/bin/bash
set -e

# Update system
apt-get update -qq
apt-get install -y python3 python3-pip wget unzip jq

# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update -qq
apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=\$(google-chrome --version | awk '{print \$3}' | cut -d'.' -f1)
DRIVER_VERSION=\$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_\${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/\${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
mv chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver
rm chromedriver_linux64.zip

# Install Python packages
pip3 install --quiet selenium google-cloud-storage

# Create GCS credentials
mkdir -p /root/.config/gcloud
echo '${GCS_KEY_B64}' | base64 -d > /root/gcs-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/root/gcs-key.json

# Download scraper
wget -q -O /root/scraper.py https://storage.googleapis.com/${BUCKET}/code/domain_scraper_gcs_json.py

# Set environment and run
export WORKER_ID=${worker_id}
export TOTAL_WORKERS=${TOTAL_WORKERS}
export GCS_BUCKET=${BUCKET}
export ADDRESSES_FILE=${ADDRESSES_FILE}

cd /root
python3 scraper.py > worker_${worker_id}.log 2>&1

# Upload log to GCS
gsutil cp worker_${worker_id}.log gs://${BUCKET}/logs/

# Shutdown after completion
shutdown -h now
EOF
)
    
    # Create instance
    aws lightsail create-instances \
        --region "$region" \
        --availability-zone "$az" \
        --instance-names "domain-scraper-worker-${worker_id}" \
        --blueprint-id "$BLUEPRINT" \
        --bundle-id "$BUNDLE" \
        --user-data "$user_data" \
        > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "    ✓ Worker $worker_id deployed"
    else
        echo "    ✗ Worker $worker_id failed"
    fi
    
    # Rate limiting
    sleep 2
}

# Deploy 20 workers to us-east-1
echo "Deploying 20 workers to us-east-1..."
for worker_id in {26..45}; do
    deploy_worker $worker_id "us-east-1"
done

# Deploy 10 workers to us-west-2
echo ""
echo "Deploying 10 workers to us-west-2..."
for worker_id in {46..55}; do
    deploy_worker $worker_id "us-west-2"
done

# Deploy 10 workers to eu-west-1
echo ""
echo "Deploying 10 workers to eu-west-1..."
for worker_id in {56..65}; do
    deploy_worker $worker_id "eu-west-1"
done

echo ""
echo "========================================="
echo "DEPLOYMENT COMPLETE"
echo "========================================="
echo ""
echo "Deployed: 40 AWS Lightsail workers (IDs 26-65)"
echo "Regions: us-east-1 (20), us-west-2 (10), eu-west-1 (10)"
echo ""
echo "Monitor with:"
echo "  aws lightsail get-instances --region us-east-1 | grep RUNNING | wc -l"
echo "  cd 03_Gold_Coast && ./monitor_progress.sh"
echo ""
echo "Cleanup when done:"
echo "  ./cleanup_aws_40workers.sh"
echo ""
