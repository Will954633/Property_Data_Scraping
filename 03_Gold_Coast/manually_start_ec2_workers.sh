#!/bin/bash
# Manually start workers via SSH (bypasses user-data issue)

set -e

GCS_KEY_B64=$(base64 -i aws-gcs-key.json | tr -d '\n')
TOTAL_WORKERS=60

echo "======================================"
echo "MANUALLY STARTING EC2 WORKERS VIA SSH"
echo "======================================"
echo ""

# Get list of running instances with their IPs and Worker IDs
INSTANCES=$(aws ec2 describe-instances \
    --region us-east-1 \
    --filters 'Name=tag:WorkerID,Values=*' 'Name=instance-state-name,Values=running' \
    --query 'Reservations[*].Instances[*].[Tags[?Key==`WorkerID`].Value|[0],PublicIpAddress,InstanceId]' \
    --output text | grep -E "^(2[6-9]|3[0-9]|4[01])")

echo "Found EC2 instances to start:"
echo "$INSTANCES" | while read worker_id ip instance_id; do
    echo "  Worker $worker_id: $ip ($instance_id)"
done
echo ""

# Start each worker
echo "$INSTANCES" | while read worker_id ip instance_id; do
    echo "Starting worker $worker_id on $ip..."
    
    ssh -i scraper-setup-key.pem \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=5 \
        ubuntu@$ip \
        "sudo su -c 'export WORKER_ID=${worker_id} && export TOTAL_WORKERS=${TOTAL_WORKERS} && export GCS_KEY_B64=\"${GCS_KEY_B64}\" && nohup bash /opt/scraper/run_worker.sh > /tmp/worker.log 2>&1 &' && echo \"  ✓ Worker ${worker_id} started\"" 2>&1 || echo "  ✗ Worker ${worker_id} failed to start"
    
    sleep 1
done

echo ""
echo "✓ All workers started!"
echo ""
echo "Wait 10-15 minutes, then check for output:"
echo "  gsutil ls gs://property-scraper-production-data-477306/scraped_data/ | grep worker_0"
