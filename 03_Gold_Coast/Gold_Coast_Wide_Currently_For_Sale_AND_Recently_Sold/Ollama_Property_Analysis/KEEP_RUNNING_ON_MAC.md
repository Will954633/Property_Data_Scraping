# Last Edit: 01/02/2026, Saturday, 10:19 am (Brisbane Time)
# How to Keep Floor Plan Analysis Running When Closing Mac Laptop
# Solutions for preventing sleep and keeping processes alive

# Keep Process Running When Closing Mac Laptop

## ⚠️ IMPORTANT: Default Behavior

**On macOS, closing the laptop lid will STOP your process!**

When you close the lid:
- Mac goes to sleep
- All processes pause or stop
- Python scripts stop
- Ollama server may stop
- MongoDB may stop

## Solutions

### Option 1: Use caffeinate (RECOMMENDED - Easiest)

The `caffeinate` command prevents your Mac from sleeping:

```bash
# Stop current process first (if running)
pkill -f ollama_floor_plan_analysis.py

# Restart with caffeinate to prevent sleep
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && caffeinate -i python3 ollama_floor_plan_analysis.py
```

**What this does:**
- `-i` flag prevents idle sleep
- Mac stays awake even with lid closed
- Process continues running
- You can close the lid safely

**To monitor progress** (in another terminal):
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && tail -f logs/ollama_processing.log
```

---

### Option 2: caffeinate + nohup (BEST for Long Runs)

Combines caffeinate with nohup for maximum reliability:

```bash
# Stop current process first
pkill -f ollama_floor_plan_analysis.py

# Restart with both caffeinate and nohup
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && caffeinate -i nohup python3 ollama_floor_plan_analysis.py > floor_plan_production.log 2>&1 &

# Get the process ID
echo "Process started. To check if running:"
echo "ps aux | grep ollama_floor_plan_analysis"
```

**Monitor progress:**
```bash
tail -f /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis/floor_plan_production.log
```

**Check if still running:**
```bash
ps aux | grep ollama_floor_plan_analysis | grep -v grep
```

---

### Option 3: Change System Settings

Permanently prevent sleep when lid is closed:

1. **Go to System Settings**
   - Click Apple menu > System Settings
   - Click **Battery** (or **Energy Saver** on older macOS)

2. **For MacBook on Power Adapter:**
   - Find "Prevent automatic sleeping when the display is off"
   - Turn it ON
   - Or set "Turn display off after" to Never

3. **For MacBook on Battery:**
   - Similar settings under Battery tab
   - Note: This will drain battery faster

Then run normally:
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 ollama_floor_plan_analysis.py
```

---

### Option 4: Use pmset (Advanced)

Temporarily disable sleep via command line:

```bash
# Disable sleep (requires sudo password)
sudo pmset -a disablesleep 1

# Run your process
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 ollama_floor_plan_analysis.py

# After completion, re-enable sleep
sudo pmset -a disablesleep 0
```

---

## Recommended Approach

**For the floor plan analysis (3-4 hour run):**

Use **Option 1** (caffeinate) - it's the simplest:

```bash
# 1. Stop current process if running
pkill -f ollama_floor_plan_analysis.py

# 2. Restart with caffeinate
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && caffeinate -i python3 ollama_floor_plan_analysis.py
```

**Benefits:**
- ✅ Simple one-line command
- ✅ No system settings changes needed
- ✅ Automatically stops preventing sleep when script finishes
- ✅ Safe to close laptop lid
- ✅ Can still use external monitor if needed

---

## How to Check if Process is Still Running

```bash
# Check if process is running
ps aux | grep ollama_floor_plan_analysis | grep -v grep

# If output shows a process, it's running
# If no output, process has stopped
```

---

## How to Stop the Process

If you need to stop it:

```bash
# Find the process
ps aux | grep ollama_floor_plan_analysis | grep -v grep

# Kill it
pkill -f ollama_floor_plan_analysis.py

# Or kill by PID (if you know it)
kill <PID>
```

---

## What Happens if Mac Goes to Sleep Anyway?

If your Mac goes to sleep (battery dies, forced sleep, etc.):

1. **Process will pause** - Not lost, just paused
2. **When Mac wakes up:**
   - Process may resume (if lucky)
   - Or may have terminated (more likely)

3. **To check:**
   ```bash
   ps aux | grep ollama_floor_plan_analysis
   ```

4. **If stopped, restart:**
   - The system will automatically skip already-analyzed properties
   - Just run the command again:
   ```bash
   cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && caffeinate -i python3 ollama_floor_plan_analysis.py
   ```

---

## Summary

**Problem**: Closing Mac laptop lid stops the process  
**Solution**: Use `caffeinate -i` before your python command  
**Command**: 
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && caffeinate -i python3 ollama_floor_plan_analysis.py
```

**Now you can safely close your laptop lid!** ✅

---

**Last Updated**: 01/02/2026, Saturday, 10:19 am (Brisbane Time)  
**Recommended**: Use caffeinate -i (Option 1)  
**Duration**: 3-4 hours for full analysis
