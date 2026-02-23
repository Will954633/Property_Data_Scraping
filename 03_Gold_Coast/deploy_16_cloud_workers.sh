#!/bin/bash
set -e

echo "=========================================="
echo "Hybrid Deployment - 16 Google Cloud Workers"
echo "Part 1 of 2: Cloud Workers (IDs 0-15)"
echo "=========================================="

# Configuration
PROJECT_ID="property-data-scraping-477306"
BUCKET_NAME="property-scraper-production-data-477306"
INSTANCE_BASE="property-scraper-hybrid"
TOTAL_WORKERS=26  # Total across cloud AND local
CLOUD_WORKERS=16

echo ""
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  GCS Bucket: $BUCKET_NAME"
echo "  Total Workers (cloud+local): $TOTAL_WORKERS"
echo "  Cloud Workers: $CLOUD_WORKERS"
echo "  Cloud Worker IDs: 0-15"
echo "  Local Worker IDs: 16-25 (you'll start separately)"
echo ""

# Regions (8 workers each to stay within per-region quota)
REGIONS=(
    "us-central1-a:8"
    "us-east1-b:8"
)

echo "Cloud Worker Distribution:"
for REGION_INFO in "${REGIONS[@]}"; do
    REGION=$(echo $REGION_INFO | cut -d: -f1)
    COUNT=$(echo $REGION_INFO | cut -d: -f2)
    echo "  - $REGION: $COUNT workers"
done
echo ""

# Step 1: Set active project
echo "Step 1: Setting active GCP project..."
gcloud config set project $PROJECT_ID

# Step 2: Enable APIs
echo ""
echo "Step 2: Enabling GCP APIs..."
gcloud services enable compute.googleapis.com storage.googleapis.com

# Step 3: Verify GCS bucket
echo ""
echo "Step 3: Verifying GCS bucket..."
if gsutil ls -b gs://$BUCKET_NAME 2>/dev/null; then
    echo "  ✓ Bucket exists: gs://$BUCKET_NAME"
else
    gsutil mb -l us-central1 gs://$BUCKET_NAME
    echo "  ✓ Created bucket: gs://$BUCKET_NAME"
fi

# Step 4: Upload scraper code
echo ""
echo "Step 4: Uploading scraper to GCS..."
gsutil cp domain_scraper_gcs.py gs://$BUCKET_NAME/domain_scraper_gcs.py
gsutil cp requirements_gcs.txt gs://$BUCKET_NAME/requirements_gcs.txt
echo "  ✓ Uploaded"

# Step 5: Create startup script
echo ""
echo "Step 5: Creating startup script..."

cat > startup_script_hybrid_cloud.sh << 'STARTUP_SCRIPT'
#!/bin/bash
set -e
exec > >(tee -a /var/log/startup-script.log)
exec 2>&1

echo "=========================================="
echo "Hybrid Cloud Worker Starting"
echo "Time: $(date)"
echo "=========================================="

export WORKER_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/worker-id" -H "Metadata-Flavor: Google")
export TOTAL_WORKERS=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/total-workers" -H "Metadata-Flavor: Google")
export GCS_BUCKET=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-bucket" -H "Metadata-Flavor: Google")
export MONGODB_URI=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-uri" -H "Metadata-Flavor: Google")

echo "Worker Configuration:"
echo "  Worker ID: $WORKER_ID (Cloud worker)"
echo "  Total Workers: $TOTAL_WORKERS (includes 10 local workers)"
echo "  GCS Bucket: $GCS_BUCKET"
echo ""

echo "Installing dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip chromium chromium-driver > /dev/null
pip3 install --quiet pymongo selenium google-cloud-storage

echo "Downloading scraper..."
mkdir -p /root/scraper && cd /root/scraper
gsutil cp gs://$GCS_BUCKET/domain_scraper_gcs.py ./

echo "Starting scraper..."
python3 domain_scraper_gcs.py

echo "Worker complete - shutting down"
sudo shutdown -h now
STARTUP_SCRIPT

echo "  ✓ Startup script created"

# Step 6: MongoDB URI
echo ""
echo "Step 6: MongoDB Configuration"
read -p "Enter MongoDB URI (or press Enter for local): " MONGODB_URI
if [ -z "$MONGODB_URI" ]; then
    MONGODB_URI="mongodb://127.0.0.1:27017/"
fi
echo "  Using: ${MONGODB_URI:0:30}..."

# Step 7: Launch cloud workers
echo ""
echo "Step 7: Launching $CLOUD_WORKERS cloud workers..."
echo ""

WORKER_ID=0
for REGION_INFO in "${REGIONS[@]}"; do
    ZONE=$(echo $REGION_INFO | cut -d: -f1)
    COUNT=$(echo $REGION_INFO | cut -d: -f2)
    
    echo "Deploying $COUNT workers in $ZONE..."
    
    for ((i=0; i<COUNT; i++)); do
        INSTANCE_NAME="${INSTANCE_BASE}-${WORKER_ID}"
        echo "  Launching worker $WORKER_ID: $INSTANCE_NAME"
        
        gcloud compute instances create $INSTANCE_NAME \
            --zone=$ZONE \
            --machine-type=e2-medium \
            --image-family=debian-12 \
            --image-project=debian-cloud \
            --boot-disk-size=20GB \
            --metadata=worker-id=$WORKER_ID,total-workers=$TOTAL_WORKERS,gcs-bucket=$BUCKET_NAME,mongodb-uri="$MONGODB_URI" \
            --metadata-from-file=startup-script=startup_script_hybrid_cloud.sh \
            --scopes=https://www.googleapis.com/auth/cloud-platform \
            --quiet 2>&1 | grep -v "WARNING" &
        
        ((WORKER_ID++))
        
        if [ $((WORKER_ID % 4)) -eq 0 ]; then
            wait
            sleep 1
        fi
    done
    
    wait
    echo "  ✓ $COUNT workers deployed in $ZONE"
    echo ""
done

wait

echo ""
echo "=========================================="
echo "✓ Cloud Workers Deployed!"
echo "=========================================="
echo ""
echo "Cloud Deployment Summary:"
echo "  Workers: $CLOUD_WORKERS (IDs 0-15)"
echo "  Regions: 2 (us-central1-a, us-east1-b)"
echo "  CPUs Used: 32 / 32 (max quota)"
echo "  Bucket: gs://$BUCKET_NAME"
echo ""
echo "Next Step: Start 10 local workers"
echo "  ./start_10_local_workers.sh"
echo ""
echo "Monitor progress:"
echo "  ./monitor_hybrid.sh"
echo ""
echo "=========================================="
