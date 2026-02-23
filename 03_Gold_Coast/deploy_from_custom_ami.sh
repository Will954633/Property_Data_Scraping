#!/bin/bash
# Deploy 34 Workers from Custom AMI
# AMI: ami-08fffba6cb5855561

set -e

echo "======================================"
echo "DEPLOYING FROM CUSTOM AMI"
echo "======================================"
echo ""

CUSTOM_AMI="ami-08fffba6cb5855561"
TOTAL_WORKERS=60
GCS_KEY_B64=$(base64 -i aws-gcs-key.json | tr -d '\n')

echo "Using custom AMI: $CUSTOM_AMI"
echo "Deploying 34 workers (IDs 26-59)"
echo ""

deploy_worker() {
    local worker_id=$1
    local region=$2
    local ami=$3
    
    # Simple user-data that sets env vars and runs pre-installed script
    local userdata="#!/bin/bash
export WORKER_ID=${worker_id}
export TOTAL_WORKERS=${TOTAL_WORKERS}
export GCS_KEY_B64='${GCS_KEY_B64}'
sudo -E bash /opt/scraper/run_worker.sh"
    
    aws ec2 run-instances \
        --region "$region" \
        --image-id "$ami" \
        --instance-type t3.medium \
        --instance-market-options 'MarketType=spot,SpotOptions={MaxPrice=0.05,SpotInstanceType=one-time}' \
        --user-data "$userdata" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=scraper-worker-${worker_id}},{Key=WorkerID,Value=${worker_id}}]" \
        --query 'Instances[0].InstanceId' \
        --output text > /dev/null 2>&1
    
    echo "  ✓ Worker $worker_id deployed"
    sleep 1
}

echo "Deploying 16 workers to us-east-1 (26-41)..."
for id in {26..41}; do deploy_worker $id "us-east-1" "$CUSTOM_AMI"; done

echo ""
echo "Deploying 16 workers to us-west-2 (42-57)..."
AMI_WEST=$(aws ec2 copy-image --source-region us-east-1 --source-image-id $CUSTOM_AMI --region us-west-2 --name "property-scraper-worker-copy" --query 'ImageId' --output text 2>&1 || echo $CUSTOM_AMI)
for id in {42..57}; do deploy_worker $id "us-west-2" "$AMI_WEST"; done

echo ""
echo "Deploying 2 workers to eu-west-1 (58-59)..."
AMI_EU=$(aws ec2 copy-image --source-region us-east-1 --source-image-id $CUSTOM_AMI --region eu-west-1 --name "property-scraper-worker-copy" --query 'ImageId' --output text 2>&1 || echo $CUSTOM_AMI)
for id in {58..59}; do deploy_worker $id "eu-west-1" "$AMI_EU"; done

echo ""
echo "✓ 34 workers deployed from custom AMI!"
echo ""
echo "Monitor: gsutil ls gs://property-scraper-production-data-477306/scraped_data/ | grep worker_0"
