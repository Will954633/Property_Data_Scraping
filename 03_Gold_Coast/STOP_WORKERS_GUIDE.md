# Guide: How to Stop All Worker Processes

## Quick Summary

The `start_50_local_workers.sh` script starts 50 Python worker processes that run `domain_scraper_multi_suburb_mongodb.py`. These processes run in the background and can be difficult to track down.

## ✅ **RECOMMENDED: Use the Comprehensive Cleanup Script**

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast
./stop_all_workers_comprehensive.sh
```

This script will:
- ✓ Find all running worker processes
- ✓ Attempt graceful shutdown (SIGTERM)
- ✓ Force kill if necessary (SIGKILL)
- ✓ Check multiple locations and script types
- ✓ Provide detailed status reports
- ✓ Verify all processes are stopped

---

## Manual Commands (If Script Doesn't Work)

### 1. **Find Running Worker Processes**

```bash
# Method 1: Find domain_scraper processes
pgrep -f "domain_scraper" -l

# Method 2: Find all Python processes with domain
ps aux | grep python | grep domain | grep -v grep

# Method 3: Find specific script
ps aux | grep "domain_scraper_multi_suburb_mongodb.py" | grep -v grep
```

### 2. **Kill All Worker Processes (One Command)**

```bash
# Kill all domain_scraper processes (recommended from start_50_local_workers.sh)
pkill -f "python3.*domain_scraper_multi_suburb_mongodb.py"

# If that doesn't work, use force kill:
pkill -9 -f "python3.*domain_scraper_multi_suburb_mongodb.py"
```

### 3. **Kill by Process ID (if you have specific PIDs)**

```bash
# Find PIDs first
pgrep -f "domain_scraper_multi_suburb_mongodb.py"

# Then kill them (replace PID1 PID2 with actual process IDs)
kill PID1 PID2 PID3 ...

# Or force kill:
kill -9 PID1 PID2 PID3 ...
```

### 4. **Kill ALL Related Scraper Processes**

```bash
# Multi-suburb scraper
pkill -f "domain_scraper_multi_suburb_mongodb.py"

# Robina scraper
pkill -f "domain_scraper_robina_mongodb.py"

# GCS scrapers
pkill -f "domain_scraper_gcs.py"
pkill -f "domain_scraper_gcs_json.py"

# Generic domain scraper
pkill -f "domain_scraper.py"
```

---

## Verification Commands

### Check if any processes are still running:

```bash
# Quick check
pgrep -f "domain_scraper" | wc -l

# Detailed check
ps aux | grep domain_scraper | grep -v grep
```

If the output is `0` or empty, all processes are stopped! ✅

---

## Troubleshooting

### Problem: Processes won't stop

**Solution 1: Use force kill**
```bash
pkill -9 -f "domain_scraper"
```

**Solution 2: Kill by user**
```bash
# Kill all Python processes for your user (BE CAREFUL!)
killall -9 python3
```

**Solution 3: Find parent shell processes**
```bash
# Sometimes the starting script shell is still running
ps aux | grep "start_50_local_workers" | grep -v grep
# Kill the parent shell
kill -9 <PID_of_shell_script>
```

### Problem: Processes running in other terminal sessions

If you started the workers in another terminal/screen/tmux session:

1. **Screen sessions:**
   ```bash
   screen -ls
   screen -r <session_name>
   # Then Ctrl+C to stop processes
   ```

2. **Tmux sessions:**
   ```bash
   tmux ls
   tmux attach -t <session_name>
   # Then Ctrl+C to stop processes
   ```

3. **Background jobs in another terminal:**
   - Open that terminal
   - Run: `jobs -l`
   - Kill jobs: `kill %1 %2 %3` (job numbers)

### Problem: Processes appear to be in multiple locations

The processes themselves only run from where you started the script, but you may have:
- Multiple log files in `local_worker_logs/`
- Processes with different working directories
- Leftover PID files

**The solution stays the same:** Kill by process name pattern!

```bash
pkill -f "domain_scraper_multi_suburb_mongodb.py"
```

---

## Prevention: How to Properly Stop Workers in the Future

### Option 1: Keep track of PIDs when starting

Modify the start script to save PIDs:
```bash
echo $WORKER_PID >> worker_pids.txt
```

Then stop them all at once:
```bash
cat worker_pids.txt | xargs kill
rm worker_pids.txt
```

### Option 2: Use process groups

Start workers in a process group and kill the whole group.

### Option 3: Run in a screen/tmux session

This makes it easy to attach and stop all workers with Ctrl+C.

---

## Related Scripts

- **Start workers:** `./start_50_local_workers.sh`
- **Monitor workers:** `./monitor_local_workers.sh`
- **Stop workers:** `./stop_all_workers_comprehensive.sh` ✅
- **Stop multi-suburb:** `./start_50_multisuburb_workers.sh` (similar pattern)
- **Stop Robina workers:** `./start_20_robina_workers.sh` (similar pattern)

---

## Quick Reference Card

```bash
# CHECK STATUS
pgrep -f "domain_scraper" -l

# STOP ALL (RECOMMENDED)
./stop_all_workers_comprehensive.sh

# STOP ALL (MANUAL)
pkill -f "domain_scraper_multi_suburb_mongodb.py"

# FORCE STOP ALL
pkill -9 -f "domain_scraper_multi_suburb_mongodb.py"

# VERIFY STOPPED
pgrep -f "domain_scraper" | wc -l  # Should return 0
```

---

## Summary

✅ **No processes found?** You're all clear! The workers have already stopped or were never running.

✅ **Processes stopped?** Great! You can verify with `pgrep -f "domain_scraper"` to confirm.

❌ **Still having issues?** Check:
1. Other terminal sessions
2. Screen/tmux sessions  
3. Different user accounts
4. Try `sudo pkill -9 -f "domain_scraper"` (last resort)

---

**Created:** 2025-01-07  
**Location:** `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/`
