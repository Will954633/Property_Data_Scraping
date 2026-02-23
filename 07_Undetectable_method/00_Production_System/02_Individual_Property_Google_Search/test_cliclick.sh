#!/bin/bash

# Quick test script for the cliclick solution
# This opens Chrome, performs a test search, and tries to click the result

echo "============================================================"
echo "CLICLICK TEST SCRIPT"
echo "============================================================"
echo ""
echo "This script will:"
echo "  1. Open Chrome and navigate to Google"
echo "  2. Wait for you to perform a manual search"
echo "  3. Try to click the first realestate.com.au result"
echo ""
echo "============================================================"
echo ""

# Check if cliclick is installed
if ! command -v cliclick &> /dev/null; then
    echo "❌ Error: cliclick is not installed"
    echo ""
    echo "Install it with:"
    echo "  brew install cliclick"
    echo ""
    exit 1
fi

echo "✅ cliclick is installed"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLICK_SCRIPT="$SCRIPT_DIR/click_google_result.sh"

# Check if click script exists
if [ ! -f "$CLICK_SCRIPT" ]; then
    echo "❌ Error: click_google_result.sh not found at: $CLICK_SCRIPT"
    exit 1
fi

# Check if script is executable
if [ ! -x "$CLICK_SCRIPT" ]; then
    echo "❌ Error: click_google_result.sh is not executable"
    echo ""
    echo "Run this to fix:"
    echo "  chmod +x $CLICK_SCRIPT"
    echo ""
    exit 1
fi

echo "✅ Click script is ready"
echo ""

# Open Chrome
echo "Opening Chrome with Google..."
open -a "Google Chrome" "https://www.google.com"

echo ""
echo "============================================================"
echo "MANUAL STEPS REQUIRED:"
echo "============================================================"
echo ""
echo "1. In the Chrome window that just opened:"
echo "   - Perform a Google search for a property address"
echo "   - Example: '123 Main Street, Gold Coast QLD'"
echo ""
echo "2. Wait for the search results to load completely"
echo ""
echo "3. Come back here and press ENTER when ready"
echo ""
read -p "Press ENTER when you've completed the search and results are loaded..."

echo ""
echo "============================================================"
echo "Attempting to click realestate.com.au result..."
echo "============================================================"
echo ""

# Try to click the result
"$CLICK_SCRIPT" "realestate.com.au"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "============================================================"
    echo "✅ TEST SUCCESSFUL!"
    echo "============================================================"
    echo ""
    echo "The script should have clicked the realestate.com.au result."
    echo "Check the Chrome window to verify."
    echo ""
else
    echo "============================================================"
    echo "❌ TEST FAILED"
    echo "============================================================"
    echo ""
    echo "Possible reasons:"
    echo "  - No realestate.com.au result found in search results"
    echo "  - Chrome window was not active/visible"
    echo "  - Search results were not fully loaded"
    echo ""
    echo "Try again with:"
    echo "  1. Make sure Chrome is the active window"
    echo "  2. Ensure realestate.com.au appears in the results"
    echo "  3. Try scrolling up to show the first result"
    echo ""
fi

echo "Test complete!"
