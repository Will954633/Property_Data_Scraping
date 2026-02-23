#!/bin/bash

# Keyboard Maestro Integration Setup Script
# This script installs all dependencies and verifies the setup

echo "=========================================="
echo "  Keyboard Maestro Integration Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}✗ Error: This script requires macOS${NC}"
    exit 1
fi

echo "Checking prerequisites..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python installed: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python not found${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Homebrew
if command -v brew &> /dev/null; then
    echo -e "${GREEN}✓ Homebrew installed${NC}"
else
    echo -e "${YELLOW}⚠ Homebrew not found${NC}"
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo ""
echo "Installing dependencies..."
echo ""

# Install Tesseract OCR
echo "Installing Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version | head -n1)
    echo -e "${GREEN}✓ Tesseract already installed: $TESSERACT_VERSION${NC}"
else
    brew install tesseract
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Tesseract installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install Tesseract${NC}"
        exit 1
    fi
fi

# Install Python packages
echo ""
echo "Installing Python packages..."
pip3 install pytesseract pillow opencv-python pymongo

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python packages installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install Python packages${NC}"
    exit 1
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x km_screenshot_processor.py
chmod +x km_ocr_extractor.py
chmod +x km_mongodb_saver.py

# Check MongoDB
echo ""
echo "Checking MongoDB..."
if command -v mongosh &> /dev/null; then
    echo -e "${GREEN}✓ MongoDB shell (mongosh) installed${NC}"
    
    # Try to connect to MongoDB
    if mongosh --eval "db.version()" mongodb://127.0.0.1:27017/ &> /dev/null; then
        echo -e "${GREEN}✓ MongoDB is running${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB is not running${NC}"
        echo "Start MongoDB with: brew services start mongodb-community"
    fi
else
    echo -e "${YELLOW}⚠ MongoDB not found${NC}"
    echo "Install MongoDB with: brew install mongodb-community"
fi

# Check Keyboard Maestro
echo ""
echo "Checking Keyboard Maestro..."
if [ -d "/Applications/Keyboard Maestro.app" ]; then
    echo -e "${GREEN}✓ Keyboard Maestro installed${NC}"
else
    echo -e "${YELLOW}⚠ Keyboard Maestro not found in /Applications/${NC}"
    echo "Move Keyboard Maestro.app to /Applications/"
fi

# Create test screenshot directories
echo ""
echo "Creating directory structure..."
cd ..
mkdir -p screenshots/{robina,mudgeeraba,varsity_lakes}
mkdir -p macros
mkdir -p logs/ocr_debug

echo -e "${GREEN}✓ Directory structure created${NC}"

# Run tests
echo ""
echo "=========================================="
echo "  Running Tests"
echo "=========================================="
echo ""

# Test OCR extractor
echo "Testing OCR extractor..."
cd scripts
python3 km_ocr_extractor.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ OCR extractor test passed${NC}"
else
    echo -e "${RED}✗ OCR extractor test failed${NC}"
fi

# Test MongoDB connection (if MongoDB is running)
if mongosh --eval "db.version()" mongodb://127.0.0.1:27017/ &> /dev/null; then
    echo "Testing MongoDB connection..."
    python3 km_mongodb_saver.py > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ MongoDB connection test passed${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB connection test warning (check if MongoDB is running)${NC}"
    fi
fi

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open Keyboard Maestro: open /Applications/Keyboard\ Maestro.app"
echo "2. Follow the Quick Start guide: cat ../QUICKSTART.md"
echo "3. Record your first macro"
echo ""
echo "For detailed instructions:"
echo "  - Quick Start: 07_Undetectable_method/5_keyboard_maestro/QUICKSTART.md"
echo "  - Full Guide: 07_Undetectable_method/KEYBOARD_MAESTRO_INTEGRATION.md"
echo ""
