#!/bin/bash
#
# Setup macOS Permissions for Property Scraping Automation
# Grants necessary permissions for Chrome automation, mouse control, screenshots
#

echo "======================================================================"
echo "PROPERTY SCRAPING PERMISSIONS SETUP"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Install required CLI tools (cliclick)"
echo "  2. Guide you through granting macOS permissions"
echo "  3. Verify permissions"
echo ""
echo "Required permissions:"
echo "  • Accessibility (for mouse control and AppleScript)"
echo "  • Screen Recording (for screenshots)"
echo ""
echo "======================================================================"
echo ""

# Step 1: Install cliclick if not present
if ! command -v cliclick &> /dev/null; then
    echo "→ Installing cliclick via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "✗ Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    brew install cliclick
    echo "✓ cliclick installed"
else
    echo "✓ cliclick already installed"
fi

# Step 2: Check and guide Accessibility permissions
echo ""
echo "STEP 2: ACCESSIBILITY PERMISSIONS"
echo "----------------------------------------------------------------------"
echo ""
echo "Open System Settings > Privacy & Security > Accessibility"
echo ""
echo "Add these applications (click + and select):"
echo "  • Terminal.app (or your terminal)"
echo "  • Google Chrome.app"
echo "  • Python (if prompted)"
echo ""
echo "Enable the checkboxes for:"
echo "  • Terminal"
echo "  • Google Chrome"
echo ""
read -p "Press Enter after granting Accessibility permissions..."

# Step 3: Check and guide Screen Recording permissions
echo ""
echo "STEP 3: SCREEN RECORDING PERMISSIONS"
echo "----------------------------------------------------------------------"
echo ""
echo "Open System Settings > Privacy & Security > Screen Recording"
echo ""
echo "Add these applications (click + and select):"
echo "  • Terminal.app"
echo "  • Google Chrome.app"
echo ""
echo "Enable the checkboxes for:"
echo "  • Terminal"
echo "  • Google Chrome"
echo ""
read -p "Press Enter after granting Screen Recording permissions..."

# Step 4: Verify permissions with test
echo ""
echo "STEP 4: TESTING PERMISSIONS"
echo "----------------------------------------------------------------------"
echo ""

# Test AppleScript (Chrome control)
echo "→ Testing AppleScript (Chrome activation)..."
osascript -e 'tell application "Google Chrome" to activate' 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ AppleScript test passed"
else
    echo "⚠ AppleScript test failed - check Accessibility permissions"
fi

# Test cliclick (mouse movement)
echo "→ Testing cliclick (mouse movement)..."
cliclick m:100,100 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Cliclick test passed"
else
    echo "⚠ Cliclick test failed - check Accessibility permissions"
fi

# Test screencapture
echo "→ Testing screencapture..."
screencapture -x /tmp/test_perm.png 2>/dev/null
if [ -f /tmp/test_perm.png ]; then
    rm /tmp/test_perm.png
    echo "✓ Screencapture test passed"
else
    echo "⚠ Screencapture test failed - check Screen Recording permissions"
fi

echo ""
echo "======================================================================"
echo "PERMISSIONS SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Run: python automation/setup_cron.sh"
echo "  2. Run initial population: python automation/daily_scraper.py"
echo "  3. Monitor logs in automation/logs/"
echo ""
echo "If tests failed, restart your Mac and grant permissions again."
echo "Some permissions require restart to take effect."
echo ""
echo "======================================================================"
