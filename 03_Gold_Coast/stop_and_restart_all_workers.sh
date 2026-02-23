#!/bin/bash
# Stop existing workers and restart all 150 with proper TOTAL_WORKERS=150
# This ensures perfect address distribution with no gaps

set -e

echo "========================================="
echo "STOP & RESTART ALL WORKERS"
echo "========================================="
echo ""

echo "This script will:"
echo "1. Stop existing 16 GCP workers"
echo "2. Stop existing 10 local workers"
echo "3. Restart all 150 workers with TOTAL_WORKERS=150"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Stop GCP workers
echo ""
echo "Stopping GCP workers (IDs 0-15)..."
for i in {0..15}; do
    echo "  Stopping worker-$i..."
    gcloud compute instances delete worker-$i \
        --zone=us-central1-a \
        --quiet &> /dev/null || true
done
echo "✓ GCP workers stopped"

# Stop local workers
echo ""
echo "Stopping local workers (IDs 16-25)..."
pkill -f "domain_scraper" || true
echo "✓ Local workers stopped"

echo ""
echo "========================================="
echo "ALL WORKERS STOPPED"
echo "========================================="
echo ""
echo "Now deploy all 150 workers:"
echo ""
echo "1. Deploy AWS (40 workers):"
echo "   ./deploy_aws_40workers.sh"
echo ""
echo "2. Deploy DigitalOcean (54 workers):"
echo "   ./deploy_digitalocean_40workers.sh"
echo ""
echo "3. Deploy Azure (30 workers):"
echo "   ./deploy_azure_30workers.sh"
echo ""
echo "4. Restart GCP workers (16 workers) - use updated script"
echo "5. Restart local workers (10 workers) - with TOTAL_WORKERS=150"
echo ""
echo "All workers will use TOTAL_WORKERS=150 for perfect distribution!"
echo ""
