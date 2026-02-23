#!/bin/bash
# Deploy 180 Workers: GCP (16) + Local (10) + AWS (154)
# Maximum deployment with available resources

set -e

echo "========================================="
echo "DEPLOYING 180 WORKERS"
echo "========================================="
echo ""
echo "Distribution:"
echo "- Google Cloud: 16 workers (IDs 0-15)"
echo "- Local: 10 workers (IDs 16-25)"
echo "- AWS Lightsail: 154 workers (IDs 26-179)"
echo ""
echo "Total: 180 workers"
echo "Per worker: ~1,840 addresses"
echo "Estimated completion: 20-24 hours"
echo "Cost: ~$141 ($123 AWS + $18 GCP)"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

TOTAL_WORKERS=180
BUCKET="property-scraper-production-data-477306"
PROJECT="property-data-scraping-477306"
ADDRESSES_FILE="all_gold_coast_addresses.json"

# Create GCS service account key for AWS workers
echo ""
echo "========================================="
echo "CREATING GCS SERVICE ACCOUNT"
echo "========================================="
echo ""

if [ ! -f "aws-gcs-key.json" ]; then
    echo "Creating GCS service account for AWS workers..."
    
    # Create service account if doesn't exist
    if ! gcloud iam service-accounts describe aws-scraper-access@${PROJECT}.iam.gserviceaccount.com &> /dev/null; then
        gcloud iam service-accounts create aws-scraper-access \
            --display-name="AWS Worker GCS Access" \
            --project=${PROJECT}
        
        gcloud projects add-iam-policy-binding ${PROJECT} \
            --member="serviceAccount:aws-scraper-access@${PROJECT}.iam.gserviceaccount.com" \
            --role="roles/storage.objectAdmin"
        
        echo "✓ Service account created"
    fi
    
    # Create key
    gcloud iam service-accounts keys create aws-gcs-key.json \
        --iam-account=aws-scraper-access@${PROJECT}.iam.gserviceaccount.com
    echo "✓ Service account key created: aws-gcs-key.json"
else
    echo "✓ Using existing aws-gcs-key.json"
fi

# Base64 encode the key
GCS_KEY_B64=$(base64 -i aws-gcs-key.json | tr -d '\n')

echo ""
echo "========================================="
echo "DEPLOYING AWS WORKERS (154 total)"
echo "========================================="
echo ""

# Function to deploy AWS worker
deploy_aws_worker() {
    local worker_id=$1
    local region=$2
    local az="${region}a"
    
    # Create user-data script
    local user_data=$(cat <<EOF
#!/bin/bash
set -e
apt-get update -qq
apt-get install -y python3 python3-pip wget unzip gnupg
mkdir -p /etc/apt/keyrings
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update -qq
apt-get install -y google-chrome-stable
CHROME_VERSION=\$(google-chrome --version | awk '{print \$3}' | cut -d'.' -f1)
DRIVER_VERSION=\$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_\${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/\${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
mv chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver
rm chromedriver_linux64.zip
pip3 install --quiet selenium google-cloud-storage
mkdir -p /root/.config/gcloud
echo '${GCS_KEY_B64}' | base64 -d > /root/gcs-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/root/gcs-key.json
wget -q -O /root/scraper.py https://storage.googleapis.com/${BUCKET}/code/domain_scraper_gcs_json.py
export WORKER_ID=${worker_id}
export TOTAL_WORKERS=${TOTAL_WORKERS}
export GCS_BUCKET=${BUCKET}
export ADDRESSES_FILE=${ADDRESSES_FILE}
cd /root
python3 scraper.py > worker_${worker_id}.log 2>&1
python3 -c "from google.cloud import storage; storage.Client().bucket('${BUCKET}').blob('logs/worker_${worker_id}.log').upload_from_filename('worker_${worker_id}.log')"
shutdown -h now
EOF
)
    
    # Deploy to AWS Lightsail
    aws lightsail create-instances \
        --region "$region" \
        --availability-zone "$az" \
        --instance-names "scraper-worker-${worker_id}" \
        --blueprint-id "ubuntu_22_04" \
        --bundle-id "medium_2_0" \
        --user-data "$user_data" \
        > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "  ✓ Worker $worker_id deployed ($(($worker_id - 25))/154)"
    else
        echo "  ✗ Worker $worker_id failed"
    fi
    
    sleep 2  # Rate limiting
}

# Deploy 60 workers to us-east-1
echo "Deploying 60 workers to us-east-1 (IDs 26-85)..."
for worker_id in {26..85}; do
    deploy_aws_worker $worker_id "us-east-1"
done

# Deploy 50 workers to us-west-2
echo ""
echo "Deploying 50 workers to us-west-2 (IDs 86-135)..."
for worker_id in {86..135}; do
    deploy_aws_worker $worker_id "us-west-2"
done

# Deploy 44 workers to eu-west-1
echo ""
echo "Deploying 44 workers to eu-west-1 (IDs 136-179)..."
for worker_id in {136..179}; do
    deploy_aws_worker $worker_id "eu-west-1"
done

echo ""
echo "========================================="
echo "AWS DEPLOYMENT COMPLETE"
echo "========================================="
echo ""
echo "✓ Deployed 154 AWS workers (IDs 26-179)"
echo "  - us-east-1: 60 workers"
echo "  - us-west-2: 50 workers"
echo "  - eu-west-1: 44 workers"
echo ""
echo "Next: Deploy GCP and Local workers"
echo ""

# Instructions for GCP deployment (manual step required)
cat << 'EOFGCP'
========================================
DEPLOY GOOGLE CLOUD WORKERS (16)
========================================

Run this separately to deploy 16 GCP workers with TOTAL_WORKERS=180:

cd 03_Gold_Coast

for worker_id in {0..15}; do
    gcloud compute instances create worker-${worker_id} \
        --zone=us-central1-a \
        --machine-type=e2-medium \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=10GB \
        --metadata=worker-id=${worker_id},total-workers=180,gcs-bucket=property-scraper-production-data-477306,addresses-file=all_gold_coast_addresses.json \
        --metadata-from-file=startup-script=startup_script_production_json.sh \
        --scopes=cloud-platform &
done

wait
echo "✓ GCP workers deployed"

========================================
DEPLOY LOCAL WORKERS (10)
========================================

Run these in 10 separate terminals (or use tmux/screen):

export TOTAL_WORKERS=180
export GCS_BUCKET=property-scraper-production-data-477306
export ADDRESSES_FILE=all_gold_coast_addresses.json

# Worker 16
export WORKER_ID=16 && python3 domain_scraper_gcs_json.py > worker_logs/worker_16.log 2>&1 &

# Worker 17
export WORKER_ID=17 && python3 domain_scraper_gcs_json.py > worker_logs/worker_17.log 2>&1 &

# ... repeat for workers 18-25

========================================
MONITOR ALL 180 WORKERS
========================================

./monitor_progress.sh

EOFGCP

echo ""
echo "See instructions above for GCP and Local deployment"
echo ""
