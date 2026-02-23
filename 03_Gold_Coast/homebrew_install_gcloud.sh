#!/bin/bash

echo "=========================================="
echo "Installing gcloud SDK via Homebrew"
echo "=========================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found"
    echo ""
    echo "Please install Homebrew first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✓ Homebrew found"
echo ""

# Install gcloud SDK
echo "Installing Google Cloud SDK..."
brew install --cask google-cloud-sdk

echo ""
echo "✓ gcloud SDK installed!"
echo ""

# Verify installation
if command -v gcloud &> /dev/null; then
    echo "✓ gcloud command is available"
    gcloud --version
    echo ""
    
    echo "=========================================="
    echo "Ready to Deploy!"
    echo "=========================================="
    echo ""
    echo "Run: ./quick_start_test.sh"
    echo ""
else
    echo "⚠ gcloud not found in PATH"
    echo ""
    echo "Try reloading your shell:"
    echo "  exec -l $SHELL"
    echo ""
    echo "Or manually source:"
    echo "  source /opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc"
fi
