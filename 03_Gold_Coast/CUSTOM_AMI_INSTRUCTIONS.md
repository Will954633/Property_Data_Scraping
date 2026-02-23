# Custom AMI Setup Instructions for AWS EC2 Workers

## Current Status

- ✅ Base EC2 instance running: `i-0e13fdb2a6bd34348`
- ✅ Public IP: `54.91.11.29`
- ✅ SSH key created: `03_Gold_Coast/scraper-setup-key.pem`
- ✅ Security group allows SSH (port 22)
- ⏳ Waiting for SSH to become available (~2-3 more minutes)

## Step 1: SSH into Instance

Wait 2-3 minutes for instance to fully boot, then:

```bash
cd 03_Gold_Coast
ssh -i scraper-setup-key.pem ubuntu@54.91.11.29
```

If connection refused, wait another minute and retry.

## Step 2: Run Setup Script

Once connected, run these commands:

```bash
# Download setup script
wget -O /tmp/setup.sh https://storage.googleapis.com/property-scraper-production-data-477306/code/ami_setup_script.sh 2>/dev/null || curl -o /tmp/setup.sh https://raw.githubusercontent.com/.../ami_setup_script.sh

# OR paste the script manually:
cat > /tmp/setup.sh << 'ENDSCRIPT'
#!/bin/bash
set -e

echo "Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip wget unzip gnupg curl

echo "Installing Chrome..."
sudo mkdir -p /etc/apt/keyrings
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update -qq
sudo apt-get install -y google-chrome-stable

echo "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver
rm chromedriver_linux64.zip

echo "Installing Python packages..."
sudo pip3 install --quiet selenium google-cloud-storage

echo "Downloading scraper..."
sudo mkdir -p /opt/scraper
sudo wget -q -O /opt/scraper/domain_scraper_gcs_json.py https://storage.googleapis.com/property-scraper-production-data-477306/code/domain_scraper_gcs_json.py

echo "Creating launcher..."
sudo tee /opt/scraper/run_worker.sh > /dev/null <<'LAUNCHER'
#!/bin/bash
set -e
mkdir -p /root/.config/gcloud
echo "${GCS_KEY_B64}" | base64 -d > /root/gcs-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/root/gcs-key.json
export GCS_BUCKET=property-scraper-production-data-477306
export ADDRESSES_FILE=all_gold_coast_addresses.json
cd /opt/scraper
python3 domain_scraper_gcs_json.py > /var/log/worker_${WORKER_ID}.log 2>&1
python3 -c "from google.cloud import storage; storage.Client().bucket('${GCS_BUCKET}').blob('logs/worker_${WORKER_ID}.log').upload_from_filename('/var/log/worker_${WORKER_ID}.log')"
shutdown -h now
LAUNCHER

sudo chmod +x /opt/scraper/run_worker.sh

echo "✓ Setup complete!"
google-chrome --version
chromedriver --version
ENDSCRIPT

# Run setup
chmod +x /tmp/setup.sh
bash /tmp/setup.sh
```

## Step 3: Create AMI

Once setup completes successfully, **from your local machine** run:

```bash
# Create AMI from configured instance
aws ec2 create-image \
    --region us-east-1 \
    --instance-id i-0e13fdb2a6bd34348 \
    --name "property-scraper-worker-$(date +%Y%m%d-%H%M)" \
    --description "Pre-configured property scraper with Chrome, Python, and dependencies" \
    --no-reboot

# Note the AMI ID from output (ami-xxxxx)
```

## Step 4: Deploy Workers from AMI

Once AMI is created (~5-10 minutes), use this deployment script with your AMI ID.

The deployment script `deploy_from_custom_ami.sh` is being created now...

## Quick Status Check

Before proceeding, verify:
```bash
# Check if SSH works now
ssh -i 03_Gold_Coast/scraper-setup-key.pem ubuntu@54.91.11.29 'echo "SSH working!"'
```

If this works, proceed with steps above.
