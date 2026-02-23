#!/bin/bash

echo "=========================================="
echo "ROBINA PRIORITY - 20 Local Workers"
echo "MongoDB Storage: Gold_Coast.robina"
echo "=========================================="

# Configuration
TOTAL_WORKERS=20
MONGODB_URI="mongodb://127.0.0.1:27017/"

echo ""
echo "Configuration:"
echo "  Total Workers: $TOTAL_WORKERS"
echo "  MongoDB URI: $MONGODB_URI"
echo "  Database: Gold_Coast"
echo "  Collection: robina (both input and output)"
echo "  Target: ROBINA addresses only"
echo "  Expected addresses: ~11,761"
echo ""

# Check dependencies
echo "Checking local dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "  ✗ python3 not found"
    exit 1
fi
echo "  ✓ python3 found"

# Check required Python packages
echo "Checking Python packages..."
if ! python3 -c "import selenium" 2>/dev/null; then
    echo "  ⚠ selenium not found, installing..."
    pip3 install selenium pymongo
else
    echo "  ✓ selenium installed"
fi

if ! python3 -c "import pymongo" 2>/dev/null; then
    echo "  ⚠ pymongo not found, installing..."
    pip3 install pymongo
else
    echo "  ✓ pymongo installed"
fi

# Check ChromeDriver
if ! command -v chromedriver &> /dev/null; then
    echo "  ⚠ ChromeDriver not found in PATH"
    echo "  Please install ChromeDriver:"
    echo "    brew install --cask chromedriver  # macOS"
    exit 1
else
    echo "  ✓ ChromeDriver found"
fi

# Check MongoDB connection
echo "Testing MongoDB connection..."
if python3 -c "from pymongo import MongoClient; client = MongoClient('$MONGODB_URI', serverSelectionTimeoutMS=5000); client.admin.command('ping'); print('  ✓ MongoDB connected')" 2>/dev/null; then
    :
else
    echo "  ✗ MongoDB connection failed"
    echo "  Please ensure MongoDB is running on localhost:27017"
    exit 1
fi

# Check for robina collection
echo "Checking Robina collection..."
ROBINA_COUNT=$(python3 -c "from pymongo import MongoClient; client = MongoClient('$MONGODB_URI'); db = client['Gold_Coast']; print(db['robina'].count_documents({}))" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "  ✓ Found $ROBINA_COUNT documents in Gold_Coast.robina"
else
    echo "  ✗ Could not access Gold_Coast.robina collection"
    exit 1
fi

echo ""
echo "=========================================="
echo "Starting 20 Local Workers for ROBINA"
echo "=========================================="
echo ""

# Create log directory
mkdir -p robina_worker_logs

# Detect Python command (prefer conda python over system python3)
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "  ✗ No Python found"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Start workers in background
for ((WORKER_ID=0; WORKER_ID<TOTAL_WORKERS; WORKER_ID++)); do
    echo "Starting Robina worker $WORKER_ID..."
    
    # Export environment variables and run in background
    (
        export WORKER_ID=$WORKER_ID
        export TOTAL_WORKERS=$TOTAL_WORKERS
        export MONGODB_URI=$MONGODB_URI
        
        $PYTHON_CMD domain_scraper_robina_mongodb.py > robina_worker_logs/worker_${WORKER_ID}.log 2>&1
    ) &
    
    WORKER_PID=$!
    echo "  Started worker $WORKER_ID (PID: $WORKER_PID)"
    
    # Small delay between worker starts
    sleep 2
done

echo ""
echo "=========================================="
echo "✓ All 20 Robina Workers Started!"
echo "=========================================="
echo ""
echo "Workers Configuration:"
echo "  Worker IDs: 0-19"
echo "  Total: 20 workers"
echo "  Running in background"
echo "  Logs: robina_worker_logs/worker_*.log"
echo ""
echo "Expected Processing:"
echo "  Addresses: ~11,761 (Robina only)"
echo "  Per worker: ~588 addresses"
echo "  Rate: ~120 addr/hour per worker"
echo "  Total time: ~5 hours"
echo ""
echo "Monitor progress:"
echo "  ./monitor_robina_workers.sh"
echo ""
echo "Watch a specific worker log:"
echo "  tail -f robina_worker_logs/worker_0.log"
echo ""
echo "Watch all workers:"
echo "  tail -f robina_worker_logs/worker_*.log"
echo ""
echo "Check running processes:"
echo "  ps aux | grep domain_scraper_robina_mongodb.py"
echo ""
echo "Stop all Robina workers:"
echo "  pkill -f domain_scraper_robina_mongodb.py"
echo ""
echo "=========================================="
echo ""
echo "⏳ Workers are now processing Robina addresses..."
echo "Data will be saved to: MongoDB Gold_Coast.robina collection"
echo ""
