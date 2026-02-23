# Fast gcloud SDK Installation (Homebrew)

The script installation got stuck. Here's a much faster way using Homebrew:

## Option 1: Install via Homebrew (FASTEST - Recommended)

```bash
# Install gcloud SDK with Homebrew (takes 1-2 minutes)
brew install --cask google-cloud-sdk

# Verify installation
gcloud --version

# Initialize
gcloud init
```

## Option 2: Manual Download (Alternative)

If you prefer to download manually:

**For macOS ARM (M1/M2/M3):**
1. Download: https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz

**For macOS Intel:**
1. Download: https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-x86_64.tar.gz

**Install manually:**
```bash
# Extract
tar -xzf ~/Downloads/google-cloud-cli-darwin-*.tar.gz -C ~

# Run install script
~/google-cloud-sdk/install.sh

# Reload shell
exec -l $SHELL

# Initialize
gcloud init
```

## Option 3: Quick Install Script

I've created a script that uses Homebrew:

```bash
cd 03_Gold_Coast
./homebrew_install_gcloud.sh
```

## After Installation

Once gcloud is installed, run the deployment:

```bash
cd 03_Gold_Coast
./quick_start_test.sh
```

This will:
1. Authenticate with Google Cloud
2. Deploy test VM
3. Scrape 5 addresses
4. Save results to GCS
5. Auto-shutdown VM

**Time: 3-5 minutes | Cost: ~$0.03**
