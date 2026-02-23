#!/bin/bash
# EMERGENCY CLEANUP - Stop and delete ALL AWS resources
# This script will terminate EC2 instances and delete Lightsail instances

set -e

echo "========================================="
echo "AWS EMERGENCY CLEANUP"
echo "========================================="
echo ""
echo "This script will:"
echo "1. Terminate ALL EC2 instances tagged as scraper workers"
echo "2. Delete ALL Lightsail instances with 'domain-scraper' in name"
echo "3. Search across regions: us-east-1, us-west-2, eu-west-1"
echo ""
echo "⚠️  WARNING: This will STOP all running scraper workers!"
echo ""

read -p "Continue with cleanup? (yes/no): " -r
echo
if [[ ! $REPLY == "yes" ]]; then
    echo "Cancelled. Please type 'yes' to confirm."
    exit 1
fi

REGIONS=("us-east-1" "us-west-2" "eu-west-1")
TOTAL_TERMINATED=0
TOTAL_DELETED=0

echo ""
echo "========================================="
echo "STEP 1: CHECKING EC2 INSTANCES"
echo "========================================="
echo ""

for region in "${REGIONS[@]}"; do
    echo "Checking region: $region"
    echo "-----------------------------------"
    
    # Find all EC2 instances with Worker tag or scraper name
    INSTANCE_IDS=$(aws ec2 describe-instances \
        --region "$region" \
        --filters "Name=instance-state-name,Values=running,pending,stopping,stopped" \
                  "Name=tag:Worker,Values=*" \
        --query 'Reservations[*].Instances[*].[InstanceId]' \
        --output text 2>/dev/null || echo "")
    
    # Also check for instances with scraper in the name
    NAMED_INSTANCES=$(aws ec2 describe-instances \
        --region "$region" \
        --filters "Name=instance-state-name,Values=running,pending,stopping,stopped" \
                  "Name=tag:Name,Values=*scraper*" \
        --query 'Reservations[*].Instances[*].[InstanceId]' \
        --output text 2>/dev/null || echo "")
    
    # Combine and deduplicate
    ALL_INSTANCES=$(echo "$INSTANCE_IDS $NAMED_INSTANCES" | tr ' ' '\n' | sort -u | grep -v '^$' || echo "")
    
    if [ -z "$ALL_INSTANCES" ]; then
        echo "  ✓ No EC2 instances found"
    else
        INSTANCE_COUNT=$(echo "$ALL_INSTANCES" | wc -w)
        echo "  Found $INSTANCE_COUNT EC2 instance(s)"
        
        for instance_id in $ALL_INSTANCES; do
            # Get instance name
            INSTANCE_NAME=$(aws ec2 describe-instances \
                --region "$region" \
                --instance-ids "$instance_id" \
                --query 'Reservations[0].Instances[0].Tags[?Key==`Name`].Value' \
                --output text 2>/dev/null || echo "unnamed")
            
            # Get instance state
            INSTANCE_STATE=$(aws ec2 describe-instances \
                --region "$region" \
                --instance-ids "$instance_id" \
                --query 'Reservations[0].Instances[0].State.Name' \
                --output text 2>/dev/null || echo "unknown")
            
            echo "    Terminating: $instance_id ($INSTANCE_NAME) - State: $INSTANCE_STATE"
            
            # Terminate instance
            aws ec2 terminate-instances \
                --region "$region" \
                --instance-ids "$instance_id" \
                > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                echo "      ✓ Terminated"
                TOTAL_TERMINATED=$((TOTAL_TERMINATED + 1))
            else
                echo "      ✗ Failed to terminate"
            fi
        done
    fi
    echo ""
done

echo ""
echo "========================================="
echo "STEP 2: CHECKING LIGHTSAIL INSTANCES"
echo "========================================="
echo ""

for region in "${REGIONS[@]}"; do
    echo "Checking region: $region"
    echo "-----------------------------------"
    
    # Find all Lightsail instances with domain-scraper in name
    LIGHTSAIL_INSTANCES=$(aws lightsail get-instances \
        --region "$region" \
        --query 'instances[?contains(name, `domain-scraper`)].name' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$LIGHTSAIL_INSTANCES" ]; then
        echo "  ✓ No Lightsail instances found"
    else
        INSTANCE_COUNT=$(echo "$LIGHTSAIL_INSTANCES" | wc -w)
        echo "  Found $INSTANCE_COUNT Lightsail instance(s)"
        
        for instance_name in $LIGHTSAIL_INSTANCES; do
            # Get instance state
            INSTANCE_STATE=$(aws lightsail get-instance \
                --region "$region" \
                --instance-name "$instance_name" \
                --query 'instance.state.name' \
                --output text 2>/dev/null || echo "unknown")
            
            echo "    Deleting: $instance_name - State: $INSTANCE_STATE"
            
            # Delete instance
            aws lightsail delete-instance \
                --region "$region" \
                --instance-name "$instance_name" \
                > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                echo "      ✓ Deleted"
                TOTAL_DELETED=$((TOTAL_DELETED + 1))
            else
                echo "      ✗ Failed to delete"
            fi
        done
    fi
    echo ""
done

echo ""
echo "========================================="
echo "CLEANUP SUMMARY"
echo "========================================="
echo ""
echo "✓ EC2 Instances Terminated: $TOTAL_TERMINATED"
echo "✓ Lightsail Instances Deleted: $TOTAL_DELETED"
echo ""

if [ $TOTAL_TERMINATED -eq 0 ] && [ $TOTAL_DELETED -eq 0 ]; then
    echo "✓ No running instances found - you're all clear!"
    echo "  No AWS costs are being incurred."
else
    echo "✓ Cleanup complete!"
    echo ""
    echo "Note: It may take a few minutes for instances to fully terminate."
    echo "AWS will stop charging as soon as instances enter 'shutting-down' state."
fi

echo ""
echo "To verify cleanup, run:"
echo "  aws ec2 describe-instances --region us-east-1 --filters 'Name=instance-state-name,Values=running' --output table"
echo "  aws lightsail get-instances --region us-east-1 --output table"
echo ""
