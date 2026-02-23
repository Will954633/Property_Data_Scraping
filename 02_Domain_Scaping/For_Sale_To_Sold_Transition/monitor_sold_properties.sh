#!/bin/bash

# Sold Property Monitor - Selenium Version
# Shell script to run sold property monitoring process
# Last Updated: 27/01/2026, 9:44 AM (Monday) - Brisbane
# - Updated to use Selenium-based version (sold_property_monitor_selenium.py)
# - Resolves bot detection issues with Domain.com.au

echo "================================================================================"
echo "SOLD PROPERTY MONITOR (SELENIUM VERSION)"
echo "================================================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  WARNING: MongoDB doesn't appear to be running!"
    echo "   Please start MongoDB before running this script."
    echo "   You can start it with: brew services start mongodb-community"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if Python script exists
if [ ! -f "sold_property_monitor_selenium.py" ]; then
    echo "❌ Error: sold_property_monitor_selenium.py not found!"
    exit 1
fi

# Default values
LIMIT=""
DELAY="2.0"
REPORT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        --delay)
            DELAY="$2"
            shift 2
            ;;
        --report)
            REPORT=true
            shift
            ;;
        --help)
            echo "Usage: ./monitor_sold_properties.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --limit N      Check only N properties (for testing)"
            echo "  --delay N      Delay between requests in seconds (default: 2.0)"
            echo "  --report       Generate sold properties report only"
            echo "  --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./monitor_sold_properties.sh                    # Monitor all properties"
            echo "  ./monitor_sold_properties.sh --limit 10         # Test with 10 properties"
            echo "  ./monitor_sold_properties.sh --delay 3          # Use 3 second delay"
            echo "  ./monitor_sold_properties.sh --report           # View sold properties report"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build the command
CMD="python3 sold_property_monitor_selenium.py --delay $DELAY $LIMIT"

if [ "$REPORT" = true ]; then
    CMD="python3 sold_property_monitor_selenium.py --report"
fi

# Display what we're doing
echo "Starting sold property monitoring..."
echo "MongoDB: mongodb://127.0.0.1:27017/"
echo "Database: property_data"
echo ""

if [ "$REPORT" = true ]; then
    echo "Generating sold properties report..."
else
    if [ -n "$LIMIT" ]; then
        echo "⚠️  TEST MODE: Checking limited number of properties"
    else
        echo "📊 Checking all properties in for_sale collection..."
    fi
    echo "Request delay: ${DELAY} seconds"
fi

echo ""
echo "================================================================================"
echo ""

# Run the monitor
$CMD

EXIT_CODE=$?

echo ""
echo "================================================================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Monitoring completed successfully"
else
    echo "❌ Monitoring ended with errors (exit code: $EXIT_CODE)"
fi

echo "================================================================================"
echo ""

exit $EXIT_CODE
