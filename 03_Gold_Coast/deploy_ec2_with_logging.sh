#!/bin/bash
# Deploy EC2 Workers with Full Logging
set -e

echo "======================================"
echo "DEPLOYING 34 EC2 WORKERS WITH LOGGING"
echo "======================================"

TOTAL_WORKERS=60
BUCKET="property-scraper-production-data-477306"
GCS_KEY_B64=$(base64 -i aws-gcs-key.json | tr -d '\n')

AMI_US_EAST_1="ami-0c7217cdde317cfec"

deploy_worker() {
    local worker_id=$1
    local region=$2
    local ami=$3
    
    # User-data with comprehensive logging
    local userdata="#!/bin/bash
exec > >(tee /var/log/user-data.log)
exec 2>&1
set -ex

echo '=== Starting worker ${worker_id} setup ==='
date

export WORKER_ID=${worker_id}
export TOTAL_WORKERS=${TOTAL_WORKERS}
export GCS_KEY_B64='${GCS_KEY_B64}'

echo '=== Installing wget ==='
apt-get update -qq
apt-get install -y wget

echo '=== Downloading startup script ===' 
wget -v -O /tmp/run.sh https://storage.googleapis.com/${BUCKET}/code/ec2_worker_startup.sh

echo '=== Making executable ==='
chmod +x /tmp/run.sh

echo '=== Running startup script ==='
bash /tmp/run.sh

echo '=== Completed ==='
date"
    
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

echo "Deploying test worker 26 to us-east-1..."
deploy_worker 26 "us-east-1" "$AMI_US_EAST_1"

echo ""
echo "✓ Test worker deployed!"
echo ""
echo "Wait 5 minutes, then check logs:"
echo "  aws ec2 get-console-output --instance-id \$(aws ec2 describe-instances --region us-east-1 --filters 'Name=tag:WorkerID,Values=26' --query 'Reservations[0].Instances[0].InstanceId' --output text) --region us-east-1 --output text | tail -100"
