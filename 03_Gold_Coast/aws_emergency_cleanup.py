#!/usr/bin/env python3
"""
AWS Emergency Cleanup Script
Terminates all EC2 and Lightsail instances related to scraper workers
"""

import boto3
import sys
from botocore.exceptions import ClientError, NoCredentialsError

# Regions where instances were deployed
REGIONS = ['us-east-1', 'us-west-2', 'eu-west-1']

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS credentials configured")
        print(f"  Account: {identity['Account']}")
        print(f"  User: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("✗ AWS credentials not configured")
        print("\nPlease run: aws configure")
        return False
    except Exception as e:
        print(f"✗ Error checking credentials: {e}")
        return False

def check_ec2_instances(region):
    """Check for EC2 instances in a region"""
    try:
        ec2 = boto3.client('ec2', region_name=region)
        
        # Find all non-terminated instances
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running', 'pending', 'stopping', 'stopped']}
            ]
        )
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                name = 'unnamed'
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
                
                instances.append({
                    'id': instance['InstanceId'],
                    'name': name,
                    'state': instance['State']['Name'],
                    'type': instance['InstanceType']
                })
        
        return instances
    except ClientError as e:
        print(f"  Error checking EC2: {e}")
        return []

def terminate_ec2_instances(region, instances):
    """Terminate EC2 instances"""
    if not instances:
        return 0
    
    try:
        ec2 = boto3.client('ec2', region_name=region)
        instance_ids = [i['id'] for i in instances]
        
        print(f"  Terminating {len(instance_ids)} EC2 instance(s)...")
        response = ec2.terminate_instances(InstanceIds=instance_ids)
        
        terminated = 0
        for instance in response['TerminatingInstances']:
            print(f"    ✓ {instance['InstanceId']} - {instance['CurrentState']['Name']}")
            terminated += 1
        
        return terminated
    except ClientError as e:
        print(f"  ✗ Error terminating instances: {e}")
        return 0

def check_lightsail_instances(region):
    """Check for Lightsail instances in a region"""
    try:
        lightsail = boto3.client('lightsail', region_name=region)
        response = lightsail.get_instances()
        
        instances = []
        for instance in response.get('instances', []):
            instances.append({
                'name': instance['name'],
                'state': instance['state']['name'],
                'bundle': instance['bundleId']
            })
        
        return instances
    except ClientError as e:
        print(f"  Error checking Lightsail: {e}")
        return []

def delete_lightsail_instances(region, instances):
    """Delete Lightsail instances"""
    if not instances:
        return 0
    
    try:
        lightsail = boto3.client('lightsail', region_name=region)
        
        deleted = 0
        for instance in instances:
            try:
                print(f"  Deleting: {instance['name']}...")
                lightsail.delete_instance(instanceName=instance['name'])
                print(f"    ✓ {instance['name']} deleted")
                deleted += 1
            except ClientError as e:
                print(f"    ✗ Failed to delete {instance['name']}: {e}")
        
        return deleted
    except ClientError as e:
        print(f"  ✗ Error deleting instances: {e}")
        return 0

def main():
    print("=" * 60)
    print("AWS EMERGENCY CLEANUP")
    print("=" * 60)
    print()
    
    # Check credentials
    if not check_aws_credentials():
        sys.exit(1)
    
    print()
    print("This script will:")
    print("1. Check for EC2 instances in all regions")
    print("2. Check for Lightsail instances in all regions")
    print("3. Terminate/delete all found instances")
    print()
    
    # First, scan all regions
    print("=" * 60)
    print("SCANNING FOR RESOURCES")
    print("=" * 60)
    print()
    
    all_ec2 = {}
    all_lightsail = {}
    
    for region in REGIONS:
        print(f"Region: {region}")
        print("-" * 60)
        
        # Check EC2
        ec2_instances = check_ec2_instances(region)
        if ec2_instances:
            print(f"  ⚠️  Found {len(ec2_instances)} EC2 instance(s):")
            for inst in ec2_instances:
                print(f"    - {inst['id']} ({inst['name']}) - {inst['state']} - {inst['type']}")
            all_ec2[region] = ec2_instances
        else:
            print(f"  ✓ No EC2 instances")
        
        # Check Lightsail
        ls_instances = check_lightsail_instances(region)
        if ls_instances:
            print(f"  ⚠️  Found {len(ls_instances)} Lightsail instance(s):")
            for inst in ls_instances:
                print(f"    - {inst['name']} - {inst['state']} - {inst['bundle']}")
            all_lightsail[region] = ls_instances
        else:
            print(f"  ✓ No Lightsail instances")
        
        print()
    
    # Summary
    total_ec2 = sum(len(instances) for instances in all_ec2.values())
    total_lightsail = sum(len(instances) for instances in all_lightsail.values())
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total EC2 Instances: {total_ec2}")
    print(f"Total Lightsail Instances: {total_lightsail}")
    print()
    
    if total_ec2 == 0 and total_lightsail == 0:
        print("✅ No AWS resources found - you're not being charged!")
        return
    
    # Confirm cleanup
    print("⚠️  WARNING: This will terminate/delete all found instances!")
    print()
    response = input("Type 'DELETE' to proceed with cleanup: ")
    
    if response != 'DELETE':
        print("Cleanup cancelled.")
        return
    
    print()
    print("=" * 60)
    print("CLEANING UP RESOURCES")
    print("=" * 60)
    print()
    
    total_terminated = 0
    total_deleted = 0
    
    # Terminate EC2 instances
    for region, instances in all_ec2.items():
        print(f"Region: {region} - EC2")
        print("-" * 60)
        terminated = terminate_ec2_instances(region, instances)
        total_terminated += terminated
        print()
    
    # Delete Lightsail instances
    for region, instances in all_lightsail.items():
        print(f"Region: {region} - Lightsail")
        print("-" * 60)
        deleted = delete_lightsail_instances(region, instances)
        total_deleted += deleted
        print()
    
    print("=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print()
    print(f"✓ EC2 Instances Terminated: {total_terminated}")
    print(f"✓ Lightsail Instances Deleted: {total_deleted}")
    print()
    print("Note: It may take a few minutes for instances to fully terminate.")
    print("AWS will stop charging once instances enter 'shutting-down' state.")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCleanup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
