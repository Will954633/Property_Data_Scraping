#!/bin/bash

echo "=========================================="
echo "Quick Start - GCP Test Deployment"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "⚠ gcloud not found in PATH"
    echo ""
    echo "The gcloud SDK installation should be complete."
    echo "Please run: exec -l $SHELL"
    echo "Then run this script again."
    exit 1
fi

echo "✓ gcloud found"
echo ""

# Check authentication
echo "Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo ""
    echo "Please authenticate with Google Cloud:"
    echo ""
    gcloud auth login
    gcloud auth application-default login
else
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)
    echo "✓ Authenticated as: $ACCOUNT"
fi

echo ""
echo "Setting project to: property-data-scraping-477306"
gcloud config set project property-data-scraping-477306

echo ""
echo "=========================================="
echo "Ready to deploy!"
echo "=========================================="
echo ""
echo "Running deployment script..."
echo ""

# Run the deployment
./deploy_test_gcp.sh

echo ""
echo "=========================================="
echo "Deployment initiated!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Monitor VM logs (wait ~3-4 minutes for completion):"
echo "   gcloud compute instances get-serial-port-output property-scraper-test --zone=us-central1-a"
echo ""
echo "2. Check for results in GCS:"
echo "   gsutil ls -r gs://property-scraper-test-data-477306/test_data/"
echo ""
echo "3. Download results:"
echo "   mkdir -p test_results"
echo "   gsutil -m cp -r gs://property-scraper-test-data-477306/test_data/ ./test_results/"
echo ""
echo "4. View a sample:"
echo "   cat test_results/test_data/biggera_waters/*.json | python3 -m json.tool | head -50"
echo ""
echo "See GCP_TEST_README.md for full documentation"
echo ""
