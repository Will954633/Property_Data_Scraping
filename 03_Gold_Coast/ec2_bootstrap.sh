#!/bin/bash
# Simple EC2 bootstrap - downloads and runs real startup script from GCS
set -e

# Install minimal tools
apt-get update -qq
apt-get install -y wget python3

# Download and run actual startup script from GCS
wget -q -O /tmp/startup.sh https://storage.googleapis.com/property-scraper-production-data-477306/code/ec2_worker_startup.sh
chmod +x /tmp/startup.sh
bash /tmp/startup.sh
