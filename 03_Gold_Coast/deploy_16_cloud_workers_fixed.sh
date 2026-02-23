#!/bin/bash
set -e

echo "=========================================="
echo "FIXED: 16 Google Cloud Workers Deployment"
echo "Using --break-system-packages for pip"
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

# Step 5: MongoDB URI
echo ""
echo "Step 5: MongoDB Configuration"
read -p "Enter MongoDB URI (or press Enter for local): " MONGODB_URI
if [ -z "$MONGODB_URI" ]; then
    MONGODB_URI="mongodb://127.0.0.1:27017/"
fi
echo "  Using: ${MONGODB_URI:0:30}..."

# Step 6: Launch cloud workers with FIXED startup script
echo ""
echo "Step 6: Launching $CLOUD_WORKERS cloud workers with FIXED startup script..."
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
            --metadata-from-file=startup-script=startup_script_hybrid_cloud_fixed.sh \
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
echo "✓ FIXED Workers Deployed!"
echo "=========================================="
echo ""
echo "Cloud Deployment Summary:"
echo "  Workers: $CLOUD_WORKERS (IDs 0-15)"
echo "  Regions: 2 (us-central1-a, us-east1-b)"
echo "  Bucket: gs://$BUCKET_NAME"
echo "  Fix Applied: --break-system-packages flag"
echo ""
echo "Monitor progress:"
echo "  ./monitor_hybrid.sh"
echo ""
echo "Check worker logs (wait 2-3 minutes after deployment):"
echo "  gcloud compute instances get-serial-port-output property-scraper-hybrid-0 --zone=us-central1-a 2>/dev/null | tail -50"
echo ""
echo "=========================================="
