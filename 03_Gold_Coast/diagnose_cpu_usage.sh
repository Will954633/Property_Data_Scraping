#!/bin/bash

echo "============================================"
echo "CPU Usage Diagnostic Report"
echo "============================================"
echo "Generated at: $(date)"
echo ""

echo "1. OVERALL CPU USAGE"
echo "--------------------------------------------"
top -l 1 | grep "CPU usage"
echo ""

echo "2. TOP 20 PROCESSES BY CPU USAGE"
echo "--------------------------------------------"
ps aux | sort -k3 -r -n | head -20
echo ""

echo "3. ALL PYTHON PROCESSES"
echo "--------------------------------------------"
ps aux | grep -i python | grep -v grep
echo ""

echo "4. ALL DOMAIN SCRAPER PROCESSES"
echo "--------------------------------------------"
pgrep -f "domain" -a
echo ""

echo "5. CHROME/BROWSER PROCESSES (can consume high CPU)"
echo "--------------------------------------------"
ps aux | grep -E "Chrome|Safari|Firefox" | grep -v grep | head -10
echo ""

echo "6. NODE PROCESSES"
echo "--------------------------------------------"
ps aux | grep node | grep -v grep
echo ""

echo "7. PROCESS COUNT BY NAME"
echo "--------------------------------------------"
ps aux | awk '{print $11}' | sort | uniq -c | sort -rn | head -20
echo ""

echo "8. MEMORY USAGE"
echo "--------------------------------------------"
top -l 1 | grep PhysMem
echo ""

echo "9. LOAD AVERAGE"
echo "--------------------------------------------"
uptime
echo ""

echo "10. CHECK FOR RUNAWAY PROCESSES"
echo "--------------------------------------------"
echo "Processes using > 50% CPU:"
ps aux | awk '$3 > 50.0 {print $2, $3, $11}'
echo ""

echo "11. CHECK FOR SELENIUM/CHROMEDRIVER"
echo "--------------------------------------------"
ps aux | grep -E "selenium|chromedriver|geckodriver" | grep -v grep
echo ""

echo "12. CHECK FOR MONGODB PROCESSES"
echo "--------------------------------------------"
ps aux | grep -E "mongo|mongod" | grep -v grep
echo ""

echo "============================================"
echo "Diagnostic Complete"
echo "============================================"
