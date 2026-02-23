#!/bin/bash
# Last Edit: 01/02/2026, Saturday, 8:28 am (Brisbane Time)
# Script to wait for llama3.2:3b model download and then run test

echo "============================================================"
echo "WAITING FOR MODEL DOWNLOAD AND RUNNING TEST"
echo "============================================================"
echo ""

# Wait for model to be available
echo "Checking if llama3.2:3b model is available..."
while true; do
    if ollama list | grep -q "llama3.2:3b"; then
        echo "✓ Model llama3.2:3b is ready!"
        break
    fi
    echo "Waiting for model download to complete..."
    sleep 10
done

echo ""
echo "============================================================"
echo "RUNNING SINGLE PROPERTY TEST"
echo "============================================================"
echo ""

# Run the test
python3 test_photo_reorder_single.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✓ TEST COMPLETED SUCCESSFULLY!"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "1. Review the test output above"
    echo "2. Check the photo tour data in MongoDB"
    echo "3. Run full production: python3 ollama_photo_reorder.py"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "✗ TEST FAILED - CHECK ERRORS ABOVE"
    echo "============================================================"
    echo ""
fi
