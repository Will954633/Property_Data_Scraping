#!/bin/bash
# Check what AWS resources are currently running

echo "========================================="
echo "AWS RESOURCE CHECK"
echo "========================================="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "✗ AWS CLI not configured or no credentials found"
    echo ""
    echo "To configure AWS CLI, run:"
    echo "  aws configure"
    echo ""
    exit 1
fi

echo "✓ AWS CLI is configured"
echo ""

REGIONS=("us-east-1" "us-west-2" "eu-west-1")

echo "========================================="
echo "CHECKING EC2 INSTANCES"
echo "========================================="
echo ""

TOTAL_EC2=0
for region in "${REGIONS[@]}"; do
    echo "Region: $region"
    echo "-----------------------------------"
    
    # Count running EC2 instances
    RUNNING=$(aws ec2 describe-instances \
        --region "$region" \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' \
        --output text 2>/dev/null | wc -l)
    
    # Count all non-terminated EC2 instances
    ALL=$(aws ec2 describe-instances \
        --region "$region" \
        --filters "Name=instance-state-name,Values=running,pending,stopping,stopped" \
        --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' \
        --output text 2>/dev/null | wc -l)
    
    if [ "$ALL" -eq 0 ]; then
        echo "  ✓ No EC2 instances"
    else
        echo "  ⚠️  Found $ALL instance(s) ($RUNNING running)"
        TOTAL_EC2=$((TOTAL_EC2 + ALL))
        
        # List them
        aws ec2 describe-instances \
            --region "$region" \
            --filters "Name=instance-state-name,Values=running,pending,stopping,stopped" \
            --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name,InstanceType]' \
            --output table 2>/dev/null
    fi
    echo ""
done

echo ""
echo "========================================="
echo "CHECKING LIGHTSAIL INSTANCES"
echo "========================================="
echo ""

TOTAL_LIGHTSAIL=0
for region in "${REGIONS[@]}"; do
    echo "Region: $region"
    echo "-----------------------------------"
    
    # Count Lightsail instances
    COUNT=$(aws lightsail get-instances \
        --region "$region" \
        --query 'instances[*].[name,state.name]' \
        --output text 2>/dev/null | wc -l)
    
    if [ "$COUNT" -eq 0 ]; then
        echo "  ✓ No Lightsail instances"
    else
        echo "  ⚠️  Found $COUNT instance(s)"
        TOTAL_LIGHTSAIL=$((TOTAL_LIGHTSAIL + COUNT))
        
        # List them
        aws lightsail get-instances \
            --region "$region" \
            --query 'instances[*].[name,state.name,bundleId]' \
            --output table 2>/dev/null
    fi
    echo ""
done

echo ""
echo "========================================="
echo "SUMMARY"
echo "========================================="
echo ""
echo "Total EC2 Instances: $TOTAL_EC2"
echo "Total Lightsail Instances: $TOTAL_LIGHTSAIL"
echo ""

if [ $TOTAL_EC2 -eq 0 ] && [ $TOTAL_LIGHTSAIL -eq 0 ]; then
    echo "✅ No AWS resources found - you're not being charged!"
else
    echo "⚠️  AWS resources are running and costing money!"
    echo ""
    echo "To clean up, run:"
    echo "  ./cleanup_all_aws_resources.sh"
fi
echo ""
