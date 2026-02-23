# SikuliX Integration Guide

## Overview

This guide explains how to use SikuliX for visual recognition to reliably click on realestate.com.au links in Google search results. SikuliX provides accurate, pixel-perfect visual matching that works consistently across different screen configurations.

## What is SikuliX?

SikuliX is a powerful visual automation tool that:
- Uses image recognition to find elements on screen
- Performs native mouse clicks (100% undetectable)
- Works independently of browser automation
- Provides highly accurate matching with confidence thresholds

## Installation

### Prerequisites

1. **Java** (Already installed - OpenJDK 23.0.2)
2. **SikuliX JAR** (Already downloaded and configured)

### Files Setup

The following files have been configured:

```
07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/
├── sikulix.jar                          # SikuliX IDE JAR file (82MB)
├── favicon_small.png                    # Template image to find
├── sikuli_clicker.sikuli/              # Sikuli script directory
│   ├── sikuli_clicker.py               # Jython script executed by SikuliX
│   └── favicon_small.png               # Copy of template in script dir
└── sikulix_workflow.py                  # Python wrapper for complete workflow
```

## Usage

### Quick Start

Run the complete workflow:

```bash
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search
python3 sikulix_workflow.py
```

### What It Does

1. **Opens Chrome** and creates a new window
2. **Searches Google** for the specified address
3. **Waits** for results to load (5 seconds)
4. **Runs SikuliX** to find the favicon image on screen
5. **Clicks** on the matching favicon with pixel-perfect accuracy

### Expected Output

```
======================================================================
SIKULIX COMPLETE WORKFLOW
======================================================================

Address: 279 Ron Penhaligon Way, Robina
Method: SikuliX visual recognition
Favicon: favicon_small.png

======================================================================

→ STEP 1: Opening Chrome and searching...
→ Opening Chrome...
✓ Chrome opened
→ Focusing address bar...
→ Typing address: 279 Ron Penhaligon Way, Robina
→ Pressing Enter...
✓ Search initiated

→ Waiting for page to stabilize...

→ STEP 2: Running SikuliX to find and click favicon...
→ Starting SikuliX visual recognition...
→ Running SikuliX...
  JAR: sikulix.jar
  Script: sikuli_clicker.sikuli
  Image: favicon_small.png

--- SikuliX Output ---
======================================================================
SIKULIX VISUAL RECOGNITION
======================================================================
Looking for: favicon_small.png
======================================================================
Searching for favicon on screen...
✓ Favicon found!
  Location: M[487,424 36x35]@S(0)[0,0 1920x1080]
  Confidence: 0.99
Clicking on favicon...
✓ Click successful!
--- End Output ---

✓ SikuliX execution successful!

======================================================================
✅ WORKFLOW COMPLETE!
======================================================================
Method: SikuliX Visual Recognition
Result: Successfully clicked on realestate.com.au link
Duration: 0:00:15.234567

======================================================================
```

## Configuration

### Change Search Address

Edit `sikulix_workflow.py`:

```python
SEARCH_ADDRESS = "Your Property Address Here"
```

### Adjust Wait Times

```python
INITIAL_LOAD_DELAY = 5  # Time to wait after search (seconds)
```

### Change Confidence Threshold

Edit `sikuli_clicker.sikuli/sikuli_clicker.py`:

```python
# Lower value = more lenient matching (may match similar images)
# Higher value = stricter matching (requires exact match)
match = exists(Pattern(favicon_image).similar(0.7), 10)
#                                              ^^^
#                                           0.0 to 1.0
```

**Recommended values:**
- **0.7** (default) - Good balance for favicons
- **0.8-0.9** - Very strict, best for unique images
- **0.5-0.6** - More lenient, use if having trouble finding

### Change Search Timeout

```python
match = exists(Pattern(favicon_image).similar(0.7), 10)
#                                                    ^^
#                                                 seconds
```

## How SikuliX Works

### Visual Recognition Process

1. **Template Loading**: Loads `favicon_small.png` as the search template
2. **Screen Scanning**: SikuliX scans the entire screen pixel-by-pixel
3. **Pattern Matching**: Compares each screen region with the template
4. **Confidence Scoring**: Calculates similarity score (0.0 to 1.0)
5. **Match Selection**: Returns location of best match above threshold
6. **Click Action**: Moves mouse to center and clicks

### Key SikuliX Functions

```python
# Find image on screen with confidence threshold
match = exists(Pattern("image.png").similar(0.7), timeout)

# Click on matched location
click(match)

# Highlight match (visual feedback, 1 second)
match.highlight(1)

# Get match details
print(match.getScore())  # Confidence score
print(match)             # Location and dimensions
```

## Troubleshooting

### SikuliX Not Finding Image

#### 1. Check Image Quality

```bash
# Verify favicon image exists and is readable
ls -lh favicon_small.png
open favicon_small.png
```

The template should be:
- Clear and not blurred
- Exactly cropped (no extra whitespace)
- Same resolution as what appears on screen

#### 2. Lower Confidence Threshold

Edit `sikuli_clicker.sikuli/sikuli_clicker.py`:

```python
match = exists(Pattern(favicon_image).similar(0.6), 10)  # Try 0.6 instead of 0.7
```

#### 3. Check Screen Resolution

SikuliX works best when the template image matches the on-screen size. If using a different resolution:

```bash
# Take a new screenshot and crop the favicon
screencapture -x screenshot.png
# Then crop the favicon from the screenshot
```

#### 4. Enable Debug Mode

Run SikuliX with debug output:

```bash
java -jar sikulix.jar -d 3 -r sikuli_clicker.sikuli -- favicon_small.png
```

This creates `SikuliLog.txt` with detailed matching information.

### Permission Issues on macOS

SikuliX needs accessibility permissions:

1. **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Accessibility**
3. Add **Terminal** or **iTerm** or **Visual Studio Code**
4. Restart the terminal/application

### Java Errors

If you get Java-related errors:

```bash
# Verify Java version
java -version

# Should show OpenJDK 23.0.2 or similar

# If Java not found, install via Homebrew:
brew install openjdk
```

### Click Offset Issues

If SikuliX finds the image but clicks in wrong location, the match is working correctly. SikuliX clicks the center of the matched region. If this seems off:

1. Verify the template image is correctly cropped
2. Check if there's UI scaling/zoom that might affect coordinates
3. Try highlighting to see where SikuliX found the match:

```python
match.highlight(5)  # Show match for 5 seconds before clicking
```

## Manual Testing

### Test SikuliX Alone

Just run the SikuliX script without the workflow:

```bash
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search

# First, open Chrome and do a Google search manually
# Then run SikuliX:
java -jar sikulix.jar -r sikuli_clicker.sikuli -- favicon_small.png
```

### Test With Different Images

You can test SikuliX with any image:

```bash
# Screenshot something on your screen
screencapture -x test_template.png

# Crop it to just the element you want to find
# Then test:
java -jar sikulix.jar -r sikuli_clicker.sikuli -- test_template.png
```

## Advanced Usage

### Find Multiple Matches

Modify `sikuli_clicker.sikuli/sikuli_clicker.py` to find all matches:

```python
# Find all matches instead of just first
matches = findAll(Pattern(favicon_image).similar(0.7))

for match in matches:
    print("Match at: " + str(match))
    print("Confidence: " + str(match.getScore()))
```

### Click Different Result

To click the 2nd or 3rd result:

```python
matches = list(findAll(Pattern(favicon_image).similar(0.7)))

# Sort by Y coordinate (top to bottom)
matches_sorted = sorted(matches, key=lambda m: m.y)

# Click second result
if len(matches_sorted) >= 2:
    click(matches_sorted[1])  # 0=first, 1=second, 2=third
```

### Add Delay Before Click

```python
match = exists(Pattern(favicon_image).similar(0.7), 10)
if match:
    match.highlight(2)  # Highlight for 2 seconds
    wait(1)             # Wait 1 second
    click(match)        # Then click
```

### Region-Based Search

To search only part of the screen (faster):

```python
# Define region: Region(x, y, width, height)
search_region = Region(0, 200, 800, 600)

# Search only in this region
match = search_region.exists(Pattern(favicon_image).similar(0.7), 10)
```

## Integration with Other Scripts

### Use in Complete Workflow

The `sikulix_workflow.py` already integrates with the search workflow. To use in other scripts:

```python
import subprocess

def click_with_sikulix(image_path):
    """Use SikuliX to find and click an image"""
    cmd = [
        'java', '-jar', 'sikulix.jar',
        '-r', 'sikuli_clicker.sikuli',
        '--', image_path
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0
```

### Use in Multi-Address Runner

Integrate into `multi_address_runner.py`:

```python
from sikulix_workflow import run_sikulix, open_chrome_and_search

for address in addresses:
    open_chrome_and_search(address)
    time.sleep(5)
    
    success = run_sikulix('favicon_small.png')
    if success:
        # Continue with property scraping
        pass
```

## Performance

### Typical Execution Times

- Chrome open + search: ~6 seconds
- SikuliX image recognition: ~2-3 seconds
- Click execution: ~1 second
- **Total: ~10-12 seconds**

### Optimization Tips

1. **Reduce search region** - Search only relevant screen area
2. **Lower timeout** - Don't wait full 10 seconds if can find faster
3. **Use grayscale** - Faster matching (if color not important)
4. **Pre-position windows** - Consistent window positions = faster

## Why SikuliX is Reliable

### Advantages over Other Methods

| Method | Accuracy | Speed | Reliability |
|--------|----------|-------|-------------|
| **SikuliX** | ⭐⭐⭐⭐⭐ Pixel-perfect | ~12s | ⭐⭐⭐⭐⭐ Excellent |
| PyAutoGUI | ⭐⭐⭐⭐ Good | ~13s | ⭐⭐⭐⭐ Good |
| OpenCV | ⭐⭐⭐⭐ Good | ~13s | ⭐⭐⭐⭐ Good |
| OCR | ⭐⭐⭐ Variable | ~12s | ⭐⭐⭐ Fair |
| Color-based | ⭐⭐ Fragile | ~11s | ⭐⭐ Poor |

### Key Benefits

1. **Mature & Proven**: Used in automation for over 10 years
2. **Accurate Matching**: Sub-pixel accuracy with confidence scores
3. **Native Actions**: Uses OS-level mouse/keyboard APIs
4. **Cross-platform**: Works on macOS, Windows, Linux
5. **Well Documented**: Extensive documentation and community support

## Files Reference

### sikulix.jar
- **Size**: 82MB
- **Version**: 2.0.5 for macOS
- **Purpose**: SikuliX IDE and runtime

### sikuli_clicker.sikuli/
Directory containing the Sikuli script (Jython code + images)

### sikuli_clicker.py
Jython script executed by SikuliX. Contains the visual recognition logic.

### sikulix_workflow.py
Python wrapper that:
1. Opens Chrome
2. Searches for address
3. Calls SikuliX to click favicon
4. Reports results

## Summary

SikuliX provides the most reliable method for clicking realestate.com.au links because:

✅ Pixel-perfect image matching
✅ Native mouse control (undetectable)
✅ Confidence threshold tuning
✅ Visual feedback (highlight matches)
✅ Mature, battle-tested software
✅ Easy to debug and troubleshoot

For production use, SikuliX is recommended over OCR, color-based, or coordinate-based methods.

## Quick Commands Reference

```bash
# Run complete workflow
python3 sikulix_workflow.py

# Test SikuliX directly
java -jar sikulix.jar -r sikuli_clicker.sikuli -- favicon_small.png

# Debug mode
java -jar sikulix.jar -d 3 -r sikuli_clicker.sikuli -- favicon_small.png

# Show help
java -jar sikulix.jar -h

# Verify Java
java -version
```

## Support

For issues or questions:
1. Check SikuliX logs in `SikuliLog.txt`
2. Review [SikuliX documentation](http://sikulix.com)
3. Test with manual screenshots first
4. Adjust confidence threshold if needed
