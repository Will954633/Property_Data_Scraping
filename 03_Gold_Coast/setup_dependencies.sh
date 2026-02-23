#!/bin/bash
set -e

echo "=========================================="
echo "Installing Dependencies for Local Workers"
echo "=========================================="

echo ""
echo "Checking Python 3..."
python3 --version || {
    echo "✗ Python 3 not found. Please install Python 3."
    exit 1
}
echo "✓ Python 3 found"

echo ""
echo "Installing Python packages..."
pip3 install --upgrade pymongo selenium google-cloud-storage

echo ""
echo "Checking MongoDB..."
if command -v mongosh &> /dev/null; then
    echo "✓ MongoDB CLI (mongosh) found"
elif command -v mongo &> /dev/null; then
    echo "✓ MongoDB CLI (mongo) found"
else
    echo "⚠ MongoDB CLI not found"
    echo "Install with: brew install mongodb-community"
    echo "Start with: brew services start mongodb-community"
fi

# Test MongoDB connection
python3 << 'PYTHON_TEST'
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://127.0.0.1:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✓ MongoDB connection successful")
    client.close()
except Exception as e:
    print(f"⚠ MongoDB connection failed: {e}")
    print("Make sure MongoDB is running:")
    print("  brew services start mongodb-community")
PYTHON_TEST

echo ""
echo "Checking ChromeDriver..."
if command -v chromedriver &> /dev/null; then
    echo "✓ ChromeDriver found: $(which chromedriver)"
else
    echo "⚠ ChromeDriver not found"
    echo "Install with: brew install chromedriver"
    echo "Or download from: https://chromedriver.chromium.org/"
fi

echo ""
echo "Checking gcloud CLI..."
if command -v gcloud &> /dev/null; then
    echo "✓ gcloud CLI found"
    echo "Current project: $(gcloud config get-value project 2>/dev/null || echo 'Not set')"
else
    echo "⚠ gcloud CLI not found (only needed for GCS import)"
    echo "Install with: brew install --cask google-cloud-sdk"
fi

echo ""
echo "=========================================="
echo "✓ Dependency Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Ensure MongoDB is running: brew services start mongodb-community"
echo "  2. Test MongoDB: mongosh --eval 'db.adminCommand({ping:1})'"
echo "  3. Continue with migration: python3 download_gcs_to_mongodb.py"
echo ""
