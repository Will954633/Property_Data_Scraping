#!/bin/bash

echo "=========================================="
echo "Waiting for gcloud SDK Installation"
echo "=========================================="
echo ""

# Wait for installation to complete
echo "Monitoring installation progress..."
while ps aux | grep "install_google_cloud" | grep -v grep > /dev/null; do
    echo "  Installation still running... (checking every 10 seconds)"
    sleep 10
done

echo ""
echo "✓ Installation process completed!"
echo ""

# Give it a moment to finalize
sleep 5

# Check if gcloud SDK directory exists
if [ -d "$HOME/google-cloud-sdk" ]; then
    echo "✓ gcloud SDK directory found at $HOME/google-cloud-sdk"
    echo ""
    
    # Source the path
    echo "Loading gcloud into PATH..."
    source "$HOME/google-cloud-sdk/path.bash.inc"
    source "$HOME/google-cloud-sdk/completion.bash.inc"
    
    # Verify gcloud is available
    if command -v gcloud &> /dev/null; then
        echo "✓ gcloud command is now available"
        echo ""
        gcloud --version
        echo ""
        
        # Run initialization
        echo "=========================================="
        echo "Initializing Google Cloud"
        echo "=========================================="
        echo ""
        echo "This will open your browser for authentication..."
        echo ""
        
        # Initialize gcloud
        gcloud init
        
        echo ""
        echo "=========================================="
        echo "Running Test Deployment"
        echo "=========================================="
        echo ""
        
        # Run the deployment
        cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast
        ./deploy_test_gcp.sh
        
    else
        echo "⚠ gcloud not found in PATH after sourcing"
        echo ""
        echo "Manual steps required:"
        echo "1. Close and reopen your terminal"
        echo "2. Run: cd 03_Gold_Coast"
        echo "3. Run: ./quick_start_test.sh"
    fi
else
    echo "⚠ gcloud SDK directory not found"
    echo ""
    echo "Please check the installation manually"
fi

echo ""
echo "=========================================="
echo "Setup Complete"
echo "=========================================="
