# Pure CLI Google Result Clicker Guide

## Overview

This solution uses **AppleScript + cliclick** to reliably click on Google search results. It's simple, robust, and works by:

1. Using AppleScript to execute JavaScript inside Chrome
2. JavaScript finds the Google result whose title contains your target text
3. Calculates the screen coordinates of the link
4. Uses `cliclick` to physically move the mouse and click at those coordinates

## Prerequisites

✅ **Already installed:**
- Homebrew
- cliclick (version 5.1)

## How It Works

The `click_google_result.sh` script:

1. Takes a partial title text as input
2. Runs JavaScript in Chrome's active tab to find matching result
3. Calculates the exact screen coordinates of the link
4. Uses `cliclick` to perform a physical mouse click

## Usage

### Basic Usage

```bash
./click_google_result.sh "partial title text"
```

### For Real Estate Properties

When searching for a property on Google and you want to click the realestate.com.au result:

```bash
./click_google_result.sh "realestate.com.au"
```

Or be more specific:

```bash
./click_google_result.sh "sold & rental history"
```

### Examples

1. **Click any realestate.com.au result:**
   ```bash
   ./click_google_result.sh "realestate.com.au"
   ```

2. **Click a specific type of result:**
   ```bash
   ./click_google_result.sh "property details"
   ```

3. **Click with more specific text:**
   ```bash
   ./click_google_result.sh "10 Example Street"
   ```

## Step-by-Step Workflow

1. **Open Chrome** (make sure it's the active application)

2. **Perform a Google search** for your property address
   - Example: "10 Example Street, Gold Coast QLD 4217"

3. **Wait for results to load** (make sure the search results page is fully loaded)

4. **Run the script** from terminal:
   ```bash
   cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search
   ./click_google_result.sh "realestate.com.au"
   ```

5. **Watch the magic happen:**
   - Script finds the matching result
   - Prints the coordinates: "Clicking at x,y"
   - Moves the mouse and clicks automatically

## Important Notes

### Text Matching
- The script performs **case-insensitive** matching
- It only needs a **partial match** - searches for text contained in the title
- It will click the **first matching result** it finds

### Chrome Requirements
- Chrome must be the **active application** (frontmost window)
- The search results page must be visible in the **active tab**
- Make sure the result you want to click is **visible on screen** (not scrolled off)

### Error Messages

**"Link containing 'text' not found."**
- The script couldn't find a result with that text
- Try a different/shorter search phrase
- Make sure you're on a Google search results page
- The result might be scrolled off-screen - try scrolling up

**No output/nothing happens:**
- Chrome might not be active - click on Chrome window first
- Check if you're on the right tab
- Verify the search results are loaded

### Special Characters

⚠️ **Avoid using single quotes (`'`)** in your search text, as they can interfere with the shell script.

✅ **Safe:** `"realestate.com.au"`, `"property details"`, `"123 Main St"`
❌ **Problematic:** `"owner's property"` (contains single quote)

If you must use single quotes, escape them: `"owner\'s property"`

## Advantages Over Other Methods

1. **No Image Recognition** - doesn't depend on visual elements
2. **No OCR** - doesn't need to read text from screenshots
3. **Pixel-Perfect** - calculates exact coordinates mathematically
4. **Fast** - executes instantly
5. **Reliable** - works as long as Chrome can run JavaScript
6. **Simple** - one script, no complex dependencies

## Integration with Python

You can call this script from Python:

```python
import subprocess
import os

def click_google_result(title_text):
    script_path = "07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/click_google_result.sh"
    
    try:
        result = subprocess.run(
            [script_path, title_text],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

# Usage
click_google_result("realestate.com.au")
```

## Troubleshooting

### Permission Issues
If you get a permission error, make sure the script is executable:
```bash
chmod +x click_google_result.sh
```

### Chrome Not Responding
If Chrome doesn't respond to AppleScript:
1. Quit Chrome completely
2. Reopen Chrome
3. Go to Google and perform a search
4. Try the script again

### Coordinates Are Wrong
If the click happens in the wrong place:
- Make sure Chrome is not in fullscreen mode
- Try resizing the Chrome window
- Ensure the search result is visible on screen
- The script calculates based on the element's position in the viewport

## Script Location

```
/Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/click_google_result.sh
```

## Testing

To test if the script works:

1. Open Chrome
2. Go to Google: `https://www.google.com`
3. Search for: "realestate.com.au Gold Coast"
4. Run the script:
   ```bash
   ./click_google_result.sh "realestate.com.au"
   ```

You should see the mouse move and click on the first realestate.com.au result automatically.

## Next Steps

This script can be integrated into your existing workflow to automatically click on property search results. You can:

1. Combine it with your address search script
2. Wait for the page to load after clicking
3. Continue with your data extraction process

The key advantage is that this method is **much more reliable** than trying to detect visual elements or use OCR to find click targets.
