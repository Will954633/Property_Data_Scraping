#!/bin/bash

# Ray White Robina Property Scraper - Quick Start Script

echo "========================================"
echo "Ray White Robina Property Scraper"
echo "========================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if required packages are installed
echo "Checking dependencies..."
if ! python3 -c "import selenium" 2>/dev/null; then
    echo "📦 Installing required packages..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "✓ All dependencies installed"
echo ""

# Run the scraper
echo "🚀 Starting Ray White Robina scraper..."
echo "   (This may take several minutes depending on the number of properties)"
echo ""

python3 ray_white_scraper.py

# Check if scraping was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ Scraping completed successfully!"
    echo "========================================"
    echo ""
    echo "📁 Output files created in current directory:"
    echo "   - ray_white_properties_*.json (property data)"
    echo "   - ray_white_scraper_*.log (execution log)"
    echo ""
else
    echo ""
    echo "========================================"
    echo "❌ Scraping failed!"
    echo "========================================"
    echo ""
    echo "Check the log file for details"
    exit 1
fi
