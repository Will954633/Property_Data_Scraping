#!/bin/bash
# Quick test script for SikuliX setup

cd "$(dirname "$0")"

echo "======================================================================"
echo "SIKULIX SETUP TEST"
echo "======================================================================"
echo ""

# Check Java
echo "→ Checking Java installation..."
if command -v java &> /dev/null; then
    java -version 2>&1 | head -n 1
    echo "✓ Java is installed"
else
    echo "✗ Java not found. Please install Java first."
    exit 1
fi
echo ""

# Check SikuliX JAR
echo "→ Checking SikuliX JAR..."
if [ -f "sikulix.jar" ]; then
    SIZE=$(ls -lh sikulix.jar | awk '{print $5}')
    echo "✓ sikulix.jar found (Size: $SIZE)"
else
    echo "✗ sikulix.jar not found"
    exit 1
fi
echo ""

# Check Sikuli script
echo "→ Checking Sikuli script..."
if [ -d "sikuli_clicker.sikuli" ]; then
    echo "✓ sikuli_clicker.sikuli/ directory found"
    if [ -f "sikuli_clicker.sikuli/sikuli_clicker.py" ]; then
        echo "✓ sikuli_clicker.py found"
    else
        echo "✗ sikuli_clicker.py not found"
        exit 1
    fi
else
    echo "✗ sikuli_clicker.sikuli/ directory not found"
    exit 1
fi
echo ""

# Check favicon image
echo "→ Checking favicon images..."
if [ -f "favicon_small.png" ]; then
    echo "✓ favicon_small.png found (main directory)"
else
    echo "✗ favicon_small.png not found in main directory"
    exit 1
fi

if [ -f "sikuli_clicker.sikuli/favicon_small.png" ]; then
    echo "✓ favicon_small.png found (sikuli directory)"
else
    echo "✗ favicon_small.png not found in sikuli directory"
    exit 1
fi
echo ""

# Check Python workflow
echo "→ Checking Python workflow..."
if [ -f "sikulix_workflow.py" ]; then
    echo "✓ sikulix_workflow.py found"
else
    echo "✗ sikulix_workflow.py not found"
    exit 1
fi
echo ""

# Test SikuliX help
echo "→ Testing SikuliX execution..."
if java -jar sikulix.jar -h > /dev/null 2>&1; then
    echo "✓ SikuliX can execute"
else
    echo "✗ SikuliX execution failed"
    exit 1
fi
echo ""

echo "======================================================================"
echo "✅ ALL CHECKS PASSED!"
echo "======================================================================"
echo ""
echo "SikuliX is ready to use. To run the workflow:"
echo ""
echo "  python3 sikulix_workflow.py"
echo ""
echo "Or test SikuliX directly (after opening Chrome with a search):"
echo ""
echo "  java -jar sikulix.jar -r sikuli_clicker.sikuli -- favicon_small.png"
echo ""
echo "For full documentation, see:"
echo "  cat SIKULIX_GUIDE.md"
echo ""
echo "======================================================================"
