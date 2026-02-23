#!/bin/bash

echo "=========================================="
echo "GPT Vision Clicker - Quick Test"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Check dependencies"
echo "2. Run the GPT vision clicker"
echo ""
echo "Press Ctrl+C to cancel, or wait 3 seconds to continue..."
sleep 3

# Navigate to script directory
cd "$(dirname "$0")"

echo ""
echo "→ Checking dependencies..."

# Check if cliclick is installed
if ! command -v cliclick &> /dev/null; then
    echo "❌ cliclick is not installed"
    echo "   Install with: brew install cliclick"
    exit 1
fi
echo "✓ cliclick is installed"

# Check if OpenAI package is installed
if ! python3 -c "import openai" 2>/dev/null; then
    echo "❌ OpenAI package is not installed"
    echo "   Install with: pip3 install --break-system-packages openai"
    exit 1
fi
echo "✓ OpenAI package is installed"

echo ""
echo "→ Running GPT vision clicker..."
echo ""

# Run the script
python3 gpt_vision_clicker.py

echo ""
echo "=========================================="
echo "Test completed!"
echo "=========================================="
