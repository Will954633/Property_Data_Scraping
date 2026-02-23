#!/bin/bash
# Ensure we use bash, not zsh
set -e

echo "=========================================="
echo "Multi-Region Deployment - 100 Workers"
echo "Property Scraper - No Quota Approval Needed"
echo "=========================================="

# Configuration
PROJECT_ID="property-data-scraping-477306"
BUCKET_NAME="property-scraper-production-data-477306"
INSTANCE_BASE="property-scraper-prod"
TOTAL_WORKERS=100

echo ""
echo "Strategy: Deploy across multiple regions to bypass single-region quota limits"
echo ""
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  GCS Bucket: $BUCKET_NAME"
echo "  Total Workers: $TOTAL_WORKERS"
echo ""

# Define regions and worker allocation (simple arrays for compatibility)
REGIONS=(
    "us-central1-a:8"
    "us-east1-b:8"
    "us-east4-c:8"
    "us-west1-b:8"
    "us-west2-c:8"
    "us-west3-c:8"
    "us-west4-b:8"
    "europe-west1-b:8"
    "europe-west2-c:8"
    "europe-west4-a:8"
    "europe-north1-a:8"
    "asia-east1-a:8"
    "asia-east2-a:4"
)

echo "Regions to use:"
TOTAL_ALLOCATED=0
for REGION_INFO in "${REGIONS[@]}"; do
    REGION=$(echo $REGION_INFO | cut -d: -f1)
    COUNT=$(echo $REGION_INFO | cut -d: -f2)
    echo "  - $REGION: $COUNT workers"
    TOTAL_ALLOCATED=$((TOTAL_ALLOCATED + COUNT))
done
echo ""

if [ $TOTAL_ALLOCATED -lt $TOTAL_WORKERS ]; then
    echo "WARNING: Only allocating $TOTAL_ALLOCATED workers (requested $TOTAL_WORKERS)"
    echo "Add more regions if needed"
fi

echo "Total workers to deploy: $TOTAL_ALLOCATED"
echo ""

# Step 1: Set active project
echo "Step 1: Setting active GCP project..."
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo ""
echo "Step 2: Enabling required GCP APIs..."
gcloud services enable compute.googleapis.com storage.googleapis.com

# Step 3: Create GCS bucket for production data
echo ""
echo "Step 3: Creating GCS bucket for production data..."
if gsutil ls -b gs://$BUCKET_NAME 2>/dev/null; then
    echo "  ✓ Bucket exists: gs://$BUCKET_NAME"
else
    gsutil mb -l us-central1 gs://$BUCKET_NAME
    echo "  ✓ Created bucket: gs://$BUCKET_NAME"
fi

# Step 4: Upload scraper code
echo ""
echo "Step 4: Uploading scraper code to GCS..."
gsutil cp domain_scraper_gcs.py gs://$BUCKET_NAME/domain_scraper_gcs.py
gsutil cp requirements_gcs.txt gs://$BUCKET_NAME/requirements_gcs.txt
echo "  ✓ Scraper code uploaded"

# Step 5: Create startup script
echo ""
echo "Step 5: Creating startup script..."

cat > startup_script_production.sh << 'STARTUP_SCRIPT'
#!/bin/bash
set -e

# Log everything
exec > >(tee -a /var/log/startup-script.log)
exec 2>&1

echo "=========================================="
echo "Property Scraper Worker Starting"
echo "Time: $(date)"
echo "=========================================="

# Get worker configuration from metadata
export WORKER_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/worker-id" -H "Metadata-Flavor: Google")
export TOTAL_WORKERS=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/total-workers" -H "Metadata-Flavor: Google")
export GCS_BUCKET=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-bucket" -H "Metadata-Flavor: Google")
export MONGODB_URI=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-uri" -H "Metadata-Flavor: Google")

echo "Worker Configuration:"
echo "  Worker ID: $WORKER_ID"
echo "  Total Workers: $TOTAL_WORKERS"
echo "  GCS Bucket: $GCS_BUCKET"
echo ""

# Install system dependencies
echo "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip chromium chromium-driver wget curl unzip > /dev/null

echo "  ✓ System dependencies installed"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install --quiet pymongo selenium google-cloud-storage

echo "  ✓ Python dependencies installed"

# Download scraper code from GCS
echo ""
echo "Downloading scraper code from GCS..."
mkdir -p /root/scraper
cd /root/scraper

gsutil cp gs://$GCS_BUCKET/domain_scraper_gcs.py ./

echo "  ✓ Files downloaded"

# Run the scraper
echo ""
echo "=========================================="
echo "Starting scraper..."
echo "=========================================="
python3 domain_scraper_gcs.py

# Shutdown after completion
echo ""
echo "=========================================="
echo "Worker complete - shutting down"
echo "=========================================="
sudo shutdown -h now
STARTUP_SCRIPT

echo "  ✓ Startup script created"

# Step 6: Get MongoDB URI
echo ""
echo "Step 6: MongoDB Configuration"
read -p "Enter MongoDB URI (or press Enter for local): " MONGODB_URI
if [ -z "$MONGODB_URI" ]; then
    MONGODB_URI="mongodb://127.0.0.1:27017/"
fi
echo "  Using: ${MONGODB_URI:0:30}..."

# Step 7: Launch workers across all regions
echo ""
echo "Step 7: Launching $TOTAL_ALLOCATED workers across ${#REGIONS[@]} regions..."
echo "This will take several minutes..."
echo ""

WORKER_ID=0
BATCH_SIZE=5  # Launch 5 workers at a time to avoid API limits

for REGION_INFO in "${REGIONS[@]}"; do
    ZONE=$(echo $REGION_INFO | cut -d: -f1)
    WORKER_COUNT=$(echo $REGION_INFO | cut -d: -f2)
    echo "Region: $ZONE - Deploying $WORKER_COUNT workers..."
    
    for ((i=0; i<WORKER_COUNT; i++)); do
        INSTANCE_NAME="${INSTANCE_BASE}-${WORKER_ID}"
        
        echo "  Launching worker $WORKER_ID in $ZONE"
        
        gcloud compute instances create $INSTANCE_NAME \
            --zone=$ZONE \
            --machine-type=e2-medium \
            --image-family=debian-12 \
            --image-project=debian-cloud \
            --boot-disk-size=20GB \
            --boot-disk-type=pd-standard \
            --metadata=worker-id=$WORKER_ID,total-workers=$TOTAL_WORKERS,gcs-bucket=$BUCKET_NAME,mongodb-uri="$MONGODB_URI" \
            --metadata-from-file=startup-script=startup_script_production.sh \
            --scopes=https://www.googleapis.com/auth/cloud-platform \
            --tags=http-server,https-server \
            --quiet 2>&1 | grep -v "WARNING" &
        
        ((WORKER_ID++))
        
        # Batch control
        if [ $((WORKER_ID % BATCH_SIZE)) -eq 0 ]; then
            wait
            echo "    Batch of $BATCH_SIZE launched, brief pause..."
            sleep 2
        fi
    done
    
    # Wait for region batch to complete
    wait
    echo "  ✓ $WORKER_COUNT workers deployed in $ZONE"
    echo
done

# Wait for all background jobs
wait

echo ""
echo "=========================================="
echo "✓ All $WORKER_ID Workers Launched!"
echo "=========================================="
echo ""
echo "Deployment Summary:"
echo "  Workers: $WORKER_ID"
echo "  Regions: ${#REGIONS[@]}"
echo "  Instance Pattern: ${INSTANCE_BASE}-0 to ${INSTANCE_BASE}-$((WORKER_ID-1))"
echo "  Bucket: gs://$BUCKET_NAME"
echo ""
echo "Workers will:"
echo "  1. Install Chrome and dependencies (~2-3 minutes)"
echo "  2. Download scraper code from GCS"
echo "  3. Connect to MongoDB and process assigned addresses"
echo "  4. Save results to GCS bucket"
echo "  5. Automatically shutdown"
echo ""
echo "Estimated completion: ~4-5 hours with 100 workers"
echo ""
echo "Monitor progress:"
echo "  watch -n 30 'gsutil ls -r gs://$BUCKET_NAME/scraped_data/ | grep -c \".json$\"'"
echo ""
echo "Check worker status across all regions:"
echo "  gcloud compute instances list --filter='name:property-scraper-prod' --format='table(name,zone,status)'"
echo ""
echo "Download results (after completion):"
echo "  mkdir -p production_results"
echo "  gsutil -m cp -r gs://$BUCKET_NAME/scraped_data/ ./production_results/"
echo ""
echo "Cleanup all workers (after completion):"
echo "  ./cleanup_multiregion.sh"
echo ""
echo "=========================================="
