#!/bin/bash
# Deploy 34 EC2 Workers across 3 regions
# Distribution: us-east-1 (16), us-west-2 (16), eu-west-1 (2)
# Total system: GCP (16) + Local (10) + EC2 (34) = 60 workers

set -e

echo "========================================="
echo "DEPLOYING 34 EC2 WORKERS"
echo "========================================="
echo ""
echo "Distribution:"
echo "- Google Cloud: 16 workers (IDs 0-15)"
echo "- Local: 10 workers (IDs 16-25)"
echo "- AWS EC2: 34 workers (IDs 26-59)"
echo ""
echo "Total: 60 workers"
echo "Per worker: ~5,530 addresses"
echo "Estimated completion: 36-48 hours"
echo "Cost: ~$20 (EC2 spot instances)"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

TOTAL_WORKERS=60
BUCKET="property-scraper-production-data-477306"
PROJECT="property-data-scraping-477306"
ADDRESSES_FILE="all_gold_coast_addresses.json"

# Ensure GCS key exists
if [ ! -f "aws-gcs-key.json" ]; then
    echo "Error: aws-gcs-key.json not found. Run deploy_180_workers.sh first to create it."
    exit 1
fi

# Base64 encode the key
GCS_KEY_B64=$(base64 -i aws-gcs-key.json | tr -d '\n')

echo ""
echo "========================================="
echo "DEPLOYING EC2 WORKERS (34 total)"
echo "========================================="
echo ""

# Get Ubuntu 22.04 AMI IDs for each region
AMI_US_EAST_1="ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS
AMI_US_WEST_2="ami-0aff18ec83b712f05"  # Ubuntu 22.04 LTS
AMI_EU_WEST_1="ami-0d940f23d527c3ab1"  # Ubuntu 22.04 LTS

# Function to deploy EC2 worker
deploy_ec2_worker() {
    local worker_id=$1
    local region=$2
    local ami=$3
    
    # Create user-data script
    local user_data=$(cat <<'EOF'
#!/bin/bash
set -e
apt-get update -qq
apt-get install -y python3 python3-pip wget unzip gnupg
mkdir -p /etc/apt/keyrings
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update -qq
apt-get install -y google-chrome-stable
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
mv chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver
rm chromedriver_linux64.zip
pip3 install --quiet selenium google-cloud-storage
mkdir -p /root/.config/gcloud
echo 'GCS_KEY_B64_PLACEHOLDER' | base64 -d > /root/gcs-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/root/gcs-key.json
wget -q -O /root/scraper.py https://storage.googleapis.com/BUCKET_PLACEHOLDER/code/domain_scraper_gcs_json.py
export WORKER_ID=WORKER_ID_PLACEHOLDER
export TOTAL_WORKERS=TOTAL_WORKERS_PLACEHOLDER
export GCS_BUCKET=BUCKET_PLACEHOLDER
export ADDRESSES_FILE=ADDRESSES_FILE_PLACEHOLDER
cd /root
python3 scraper.py > worker_${WORKER_ID}.log 2>&1
python3 -c "from google.cloud import storage; storage.Client().bucket('BUCKET_PLACEHOLDER').blob('logs/worker_${WORKER_ID}.log').upload_from_filename('worker_${WORKER_ID}.log')"
shutdown -h now
EOF
)
    
    # Replace placeholders in user-data
    user_data="${user_data//GCS_KEY_B64_PLACEHOLDER/$GCS_KEY_B64}"
    user_data="${user_data//BUCKET_PLACEHOLDER/$BUCKET}"
    user_data="${user_data//WORKER_ID_PLACEHOLDER/$worker_id}"
    user_data="${user_data//TOTAL_WORKERS_PLACEHOLDER/$TOTAL_WORKERS}"
    user_data="${user_data//ADDRESSES_FILE_PLACEHOLDER/$ADDRESSES_FILE}"
    
    # Deploy spot instance
    INSTANCE_ID=$(aws ec2 run-instances \
        --region "$region" \
        --image-id "$ami" \
        --instance-type t3.medium \
        --instance-market-options 'MarketType=spot,SpotOptions={MaxPrice=0.05,SpotInstanceType=one-time}' \
        --user-data "$user_data" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=scraper-worker-${worker_id}},{Key=Worker,Value=${worker_id}}]" \
        --query 'Instances[0].InstanceId' \
        --output text 2>&1)
    
    if [[ $INSTANCE_ID == i-* ]]; then
        echo "  ✓ Worker $worker_id deployed: $INSTANCE_ID ($(($worker_id - 25))/34)"
    else
        echo "  ✗ Worker $worker_id failed: $INSTANCE_ID"
    fi
    
    sleep 1  # Rate limiting
}

# Deploy 16 workers to us-east-1
echo "Deploying 16 workers to us-east-1 (IDs 26-41)..."
for worker_id in {26..41}; do
    deploy_ec2_worker $worker_id "us-east-1" "$AMI_US_EAST_1"
done

# Deploy 16 workers to us-west-2
echo ""
echo "Deploying 16 workers to us-west-2 (IDs 42-57)..."
for worker_id in {42..57}; do
    deploy_ec2_worker $worker_id "us-west-2" "$AMI_US_WEST_2"
done

# Deploy 2 workers to eu-west-1
echo ""
echo "Deploying 2 workers to eu-west-1 (IDs 58-59)..."
for worker_id in {58..59}; do
    deploy_ec2_worker $worker_id "eu-west-1" "$AMI_EU_WEST_1"
done

echo ""
echo "========================================="
echo "EC2 DEPLOYMENT COMPLETE"
echo "========================================="
echo ""
echo "✓ Deployed 34 EC2 workers (IDs 26-59)"
echo "  - us-east-1: 16 workers"
echo "  - us-west-2: 16 workers"
echo "  - eu-west-1: 2 workers"
echo ""
echo "Total system: 60 workers"
echo "- GCP: 16 workers (0-15)"
echo "- Local: 10 workers (16-25)"
echo "- EC2: 34 workers (26-59)"
echo ""
echo "Monitor with:"
echo "  aws ec2 describe-instances --region us-east-1 --filters 'Name=tag:Worker,Values=*' --query 'Reservations[*].Instances[*].[Tags[?Key==\`Name\`].Value|[0],State.Name]' --output table"
echo ""
echo "Check GCS for output:"
echo "  gsutil ls gs://${BUCKET}/scraped_data/"
echo ""
