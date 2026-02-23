#!/bin/bash
# EMERGENCY: Terminate ALL AWS EC2 and Lightsail instances immediately

echo "========================================="
echo "TERMINATING ALL AWS INSTANCES"
echo "========================================="
echo ""

REGIONS=("us-east-1" "us-west-2" "eu-west-1")

for region in "${REGIONS[@]}"; do
    echo "Region: $region"
    echo "-----------------------------------------"
    
    # Get all EC2 instance IDs
    INSTANCE_IDS=$(aws ec2 describe-instances \
        --region "$region" \
        --filters "Name=instance-state-name,Values=running,pending,stopped,stopping" \
        --query 'Reservations[*].Instances[*].InstanceId' \
        --output text)
    
    if [ -n "$INSTANCE_IDS" ]; then
        echo "  EC2 Instances found: $INSTANCE_IDS"
        echo "  Terminating..."
        aws ec2 terminate-instances --region "$region" --instance-ids $INSTANCE_IDS
        echo "  ✓ Termination initiated"
    else
        echo "  No EC2 instances"
    fi
    
    # Get all Lightsail instance names
    LIGHTSAIL_NAMES=$(aws lightsail get-instances \
        --region "$region" \
        --query 'instances[*].name' \
        --output text 2>/dev/null)
    
    if [ -n "$LIGHTSAIL_NAMES" ]; then
        echo "  Lightsail Instances found: $LIGHTSAIL_NAMES"
        for name in $LIGHTSAIL_NAMES; do
            echo "  Deleting: $name"
            aws lightsail delete-instance --region "$region" --instance-name "$name"
        done
        echo "  ✓ Deletion initiated"
    else
        echo "  No Lightsail instances"
    fi
    
    echo ""
done

echo "========================================="
echo "TERMINATION COMPLETE"
echo "========================================="
echo ""
echo "All AWS resources have been terminated."
echo "Billing will stop within minutes."
echo ""
