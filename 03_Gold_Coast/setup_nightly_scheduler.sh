#!/bin/bash
set -e

echo "=========================================="
echo "Setup Nightly Scheduler (launchd - macOS)"
echo "=========================================="

# Configuration
WORKER_SCRIPT_DIR="$PWD"
PLIST_NAME="com.goldcoast.nightly.scraper"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
START_SCRIPT="$WORKER_SCRIPT_DIR/start_50_local_workers.sh"
STOP_SCRIPT="$WORKER_SCRIPT_DIR/stop_local_workers.sh"

# Schedule: 10 PM every night (22:00)
SCHEDULE_HOUR=22
SCHEDULE_MINUTE=0

echo ""
echo "Configuration:"
echo "  Worker directory:    $WORKER_SCRIPT_DIR"
echo "  Start script:        $START_SCRIPT"
echo "  Schedule:            ${SCHEDULE_HOUR}:$(printf '%02d' $SCHEDULE_MINUTE) daily"
echo "  LaunchAgent plist:   $PLIST_PATH"
echo ""

# Validate scripts exist
if [ ! -f "$START_SCRIPT" ]; then
    echo "✗ Error: Start script not found: $START_SCRIPT"
    exit 1
fi

# Create stop script if it doesn't exist
if [ ! -f "$STOP_SCRIPT" ]; then
    echo "Creating stop script..."
    cat > "$STOP_SCRIPT" << 'EOF'
#!/bin/bash
echo "Stopping all local workers..."
pkill -f "python3.*domain_scraper_multi_suburb_mongodb.py"
echo "✓ Workers stopped"
EOF
    chmod +x "$STOP_SCRIPT"
    echo "✓ Created: $STOP_SCRIPT"
fi

# Make scripts executable
chmod +x "$START_SCRIPT"
chmod +x "$STOP_SCRIPT"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create plist file
echo "Creating LaunchAgent plist..."
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${START_SCRIPT}</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${SCHEDULE_HOUR}</integer>
        <key>Minute</key>
        <integer>${SCHEDULE_MINUTE}</integer>
    </dict>
    
    <key>WorkingDirectory</key>
    <string>${WORKER_SCRIPT_DIR}</string>
    
    <key>StandardOutPath</key>
    <string>${WORKER_SCRIPT_DIR}/nightly_scheduler.log</string>
    
    <key>StandardErrorPath</key>
    <string>${WORKER_SCRIPT_DIR}/nightly_scheduler_error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>MONGODB_URI</key>
        <string>mongodb://127.0.0.1:27017/</string>
    </dict>
</dict>
</plist>
EOF

echo "✓ Created: $PLIST_PATH"

# Load the LaunchAgent
echo ""
echo "Loading LaunchAgent..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

if [ $? -eq 0 ]; then
    echo "✓ LaunchAgent loaded successfully"
else
    echo "✗ Failed to load LaunchAgent"
    exit 1
fi

# Verify
echo ""
echo "Verifying LaunchAgent..."
launchctl list | grep "$PLIST_NAME" > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ LaunchAgent is registered"
else
    echo "✗ LaunchAgent not found in launchctl list"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ Nightly Scheduler Configured"
echo "=========================================="
echo ""
echo "Schedule Details:"
echo "  Run time:           ${SCHEDULE_HOUR}:$(printf '%02d' $SCHEDULE_MINUTE) daily"
echo "  Workers:            50 parallel workers"
echo "  Log file:           nightly_scheduler.log"
echo "  Error log:          nightly_scheduler_error.log"
echo ""
echo "Management Commands:"
echo "  Check status:       launchctl list | grep $PLIST_NAME"
echo "  View schedule:      cat $PLIST_PATH"
echo "  Stop scheduler:     launchctl unload $PLIST_PATH"
echo "  Start scheduler:    launchctl load $PLIST_PATH"
echo "  Manual test:        ./start_50_local_workers.sh"
echo ""
echo "Notes:"
echo "  - Scheduler will run every night at ${SCHEDULE_HOUR}:$(printf '%02d' $SCHEDULE_MINUTE)"
echo "  - Workers will process all remaining unscraped addresses"
echo "  - Each worker logs to local_worker_logs/worker_N.log"
echo "  - MongoDB must be running for scheduler to work"
echo ""
