#!/bin/bash
# Deploy 34 EC2 Workers - SIMPLE APPROACH
# Uses minimal inline user-data to avoid heredoc issues

set -e

echo "======================================"
echo "DEPLOYING 34 EC2 WORKERS"
echo "======================================"
echo ""

TOTAL_WORKERS=60
BUCKET="property-scraper-production-data-477306"
GCS_KEY_B64=$(base64 -i aws-gcs-key.json | tr -d '\n')

# AMIs for each region
AMI_US_EAST_1="ami-0c7217cdde317cfec"
AMI_US_WEST_2="ami-0aff18ec83b712f05"  
AMI_EU_WEST_1="ami-0d940f23d527c3ab1"

deploy_worker() {
    local worker_id=$1
    local region=$2
    local ami=$3
    
    # Ultra-simple user-data that just bootstraps from GCS
    local userdata="#!/bin/bash
export WORKER_ID=${worker_id}
export TOTAL_WORKERS=${TOTAL_WORKERS}
export GCS_KEY_B64='${GCS_KEY_B64}'
wget -q -O /tmp/run.sh https://storage.googleapis.com/${BUCKET}/code/ec2_worker_startup.sh
chmod +x /tmp/run.sh
bash /tmp/run.sh"
    
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
for id in {26..41}; do deploy_worker $id "us-east-1" "$AMI_US_EAST_1"; done

echo ""
echo "Deploying 16 workers to us-west-2 (42-57)..."  
for id in {42..57}; do deploy_worker $id "us-west-2" "$AMI_US_WEST_2"; done

echo ""
echo "Deploying 2 workers to eu-west-1 (58-59)..."
for id in {58..59}; do deploy_worker $id "eu-west-1" "$AMI_EU_WEST_1"; done

echo ""
echo "✓ 34 EC2 workers deployed!"
echo ""
echo "Monitor: aws ec2 describe-instances --region us-east-1 --filters 'Name=tag:WorkerID,Values=*' --query 'Reservations[*].Instances[*].[Tags[?Key==\`Name\`].Value|[0],State.Name]' --output table"
