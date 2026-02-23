# SikuliX Permission Fix for macOS

## Problem

SikuliX is timing out when trying to find images because it needs **Screen Recording** permission on macOS to scan the screen.

## Solution: Grant Screen Recording Permission

### Step 1: Open System Preferences

1. Click the Apple menu () → **System Preferences** (or **System Settings** on newer macOS)
2. Go to **Security & Privacy** → **Privacy** tab
3. Scroll down and select **Screen Recording** in the left sidebar

### Step 2: Grant Permission to Terminal/Java

Add these applications to the Screen Recording list:

- **Terminal** (if running from Terminal)
- **iTerm** (if using iTerm)
- **Visual Studio Code** (if running from VS Code terminal)
- **java** or **javaw** (the Java executable)

To add an application:
1. Click the lock icon 🔒 and enter your password
2. Click the **+** button
3. Navigate to the application:
   - Terminal: `/System/Applications/Utilities/Terminal.app`
   - VS Code: `/Applications/Visual Studio Code.app`
   - Java: `/usr/bin/java` or use Command+Shift+G and paste the path

4. Check the checkbox next to the application
5. **Restart the application** for changes to take effect

### Step 3: Test Again

After granting permissions and restarting your terminal:

```bash
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search
python3 sikulix_workflow.py
```

## Alternative: Use OpenCV Method Instead

Your OpenCV favicon clicker already exists and works without special permissions!

### Use This Instead (Recommended for Now)

```bash
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search
venv/bin/python opencv_favicon_clicker.py
```

The OpenCV method:
- ✅ No special permissions needed
- ✅ Already tested and working
- ✅ Similar accuracy to SikuliX
- ✅ Faster to set up

## How to Check Current Permissions

Run this command to see what has Screen Recording permission:

```bash
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT service, client FROM access WHERE service='kTCCServiceScreenCapture';" 2>/dev/null
```

Or check manually in System Preferences → Security & Privacy → Privacy → Screen Recording

## Why SikuliX Needs This Permission

SikuliX uses screen capture APIs to:
1. Take a snapshot of the entire screen
2. Search for the template image (favicon_small.png)
3. Find matching regions
4. Click on the match

Without Screen Recording permission, step 1 fails silently, causing the timeout.

## Comparison of Methods

| Method | Permission Needed | Status |
|--------|------------------|---------|
| **OpenCV** | None | ✅ Working |
| **PyAutoGUI** | Accessibility | ⚠️ Clicks wrong location |
| **SikuliX** | Screen Recording | ⚠️ Needs permission |
| **OCR** | None | ⚠️ Variable accuracy |

## Recommendation

**For immediate use:** Stick with the OpenCV method (`opencv_favicon_clicker.py`)

**For best accuracy:** Grant Screen Recording permission and use SikuliX

## Test OpenCV Method Now

```bash
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search

# Run the OpenCV version
venv/bin/python opencv_favicon_clicker.py
```

This should work immediately without any permission changes!

## Still Have Issues?

If OpenCV also has problems, try:

1. **Lower confidence threshold**:
   Edit `opencv_favicon_clicker.py` and change:
   ```python
   MATCH_THRESHOLD = 0.6  # Lower from 0.7
   ```

2. **Check favicon image**:
   ```bash
   open favicon_small.png
   ```
   Make sure it's clear and matches what appears on screen

3. **Try OCR method**:
   ```bash
   venv/bin/python complete_workflow.py
   ```

## Summary

- **Problem**: SikuliX needs Screen Recording permission
- **Quick Fix**: Use OpenCV instead (`opencv_favicon_clicker.py`)
- **Permanent Fix**: Grant Screen Recording permission to Terminal/Java
- **Best Option**: OpenCV works now, no permissions needed!
