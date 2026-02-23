#!/bin/bash

# Simple Screenshot Scraper Runner
# This script makes it easy to run the screenshot scraper

echo "=================================="
echo "Simple Screenshot Scraper"
echo "=================================="
echo ""

# Check if Chrome is running with remote debugging
if ! lsof -i :9222 > /dev/null 2>&1; then
    echo "⚠️  Chrome is not running with remote debugging enabled!"
    echo ""
    echo "Please run this command in a new terminal first:"
    echo "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222"
    echo ""
    echo "Make sure you're logged into Google in that Chrome browser."
    echo ""
    read -p "Press Enter once Chrome is running with remote debugging..."
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed"
    exit 1
fi

# Check if selenium is installed
if ! python3 -c "import selenium" 2>/dev/null; then
    echo "Installing selenium..."
    pip3 install selenium
fi

# Run the script
echo ""
echo "Starting screenshot scraper..."
echo ""
python3 simple_screenshot_scraper.py
