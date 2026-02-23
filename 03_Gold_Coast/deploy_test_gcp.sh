#!/bin/bash
set -e

echo "=========================================="
echo "Google Cloud Test Deployment"
echo "Property Scraper - 5 Addresses Test"
echo "=========================================="

# Configuration
PROJECT_ID="property-data-scraping-477306"
BUCKET_NAME="property-scraper-test-data-477306"
ZONE="us-central1-a"
INSTANCE_NAME="property-scraper-test"

echo ""
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  GCS Bucket: $BUCKET_NAME"
echo "  Zone: $ZONE"
echo "  Instance: $INSTANCE_NAME"
echo ""

# Step 1: Set active project
echo "Step 1: Setting active GCP project..."
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo ""
echo "Step 2: Enabling required GCP APIs..."
gcloud services enable compute.googleapis.com storage.googleapis.com

# Step 3: Create GCS bucket
echo ""
echo "Step 3: Creating GCS bucket..."
if gsutil ls -b gs://$BUCKET_NAME 2>/dev/null; then
    echo "  Bucket already exists: gs://$BUCKET_NAME"
else
    gsutil mb -l us-central1 gs://$BUCKET_NAME
    echo "  ✓ Created bucket: gs://$BUCKET_NAME"
fi

# Step 4: Read files for metadata
echo ""
echo "Step 4: Preparing deployment files..."

# Read test addresses
TEST_ADDRESSES=$(cat test_addresses_5.json | base64)

# Read scraper code
SCRAPER_CODE=$(cat test_scraper_gcs.py | base64)

echo "  ✓ Test addresses loaded"
echo "  ✓ Scraper code loaded"

# Step 5: Create and launch VM
echo ""
echo "Step 5: Creating test VM instance..."

gcloud compute instances create $INSTANCE_NAME \
    --zone=$ZONE \
    --machine-type=e2-medium \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --metadata=^:^gcs-bucket=$BUCKET_NAME:test-addresses="$TEST_ADDRESSES":scraper-code="$SCRAPER_CODE" \
    --metadata-from-file=startup-script=gcp_startup_script.sh \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=http-server,https-server

echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "VM Instance: $INSTANCE_NAME"
echo "  Status: Starting up..."
echo "  Zone: $ZONE"
echo ""
echo "The VM will:"
echo "  1. Install Chrome and dependencies (~2-3 minutes)"
echo "  2. Run the scraper on 5 addresses (~30 seconds)"  
echo "  3. Save results to GCS bucket"
echo "  4. Automatically shutdown"
echo ""
echo "Monitor progress:"
echo "  gcloud compute instances get-serial-port-output $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "Check GCS bucket:"
echo "  gsutil ls -r gs://$BUCKET_NAME/test_data/"
echo ""
echo "Download results:"
echo "  gsutil -m cp -r gs://$BUCKET_NAME/test_data/ ./test_results/"
echo ""
echo "Cleanup (after test):"
echo "  gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet"
echo "  gsutil -m rm -r gs://$BUCKET_NAME/test_data/"
echo ""
echo "=========================================="
