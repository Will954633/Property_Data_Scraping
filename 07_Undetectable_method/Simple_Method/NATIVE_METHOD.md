# Native macOS Scrolling Method - UNDETECTABLE

This method uses **native macOS system functions** instead of browser automation like Selenium. It's completely undetectable because it simulates real user actions.

## How It Works

✓ **AppleScript** - Controls Chrome at the OS level  
✓ **System Events** - Sends real keyboard commands (Page Down key)  
✓ **screencapture** - Native macOS screenshot tool  
✓ **100% Undetectable** - Appears as real user behavior  

## Quick Start

### Step 1: Make sure Chrome is open and you're logged into Google

Just open Chrome normally and log in.

### Step 2: Run the script

```bash
cd 07_Undetectable_method/Simple_Method
python3 native_scroll_screenshot.py
```

### Step 3: Follow the prompts

The script will:
1. Open the URL in Chrome
2. Ask you to click the Chrome window
3. Automatically scroll to the top
4. Prompt you before each screenshot
5. Send real Page Down keypresses
6. Save screenshots to `screenshots/` folder

## No Dependencies Required

This script uses only **Python standard library** - no pip install needed!

- ✅ subprocess (built-in)
- ✅ time (built-in)
- ✅ os (built-in)
- ✅ datetime (built-in)

## Usage

```bash
./native_scroll_screenshot.py
```

Or:

```bash
python3 native_scroll_screenshot.py
```

## Configuration

Edit these variables at the top of `native_scroll_screenshot.py`:

```python
NUM_SCROLLS = 10        # Number of times to scroll down
SCROLL_DELAY = 2        # Seconds between scrolls
SCREENSHOT_DIR = "screenshots"  # Where to save images
```

## Why This Method is Undetectable

1. **No Selenium/WebDriver** - Websites can't detect WebDriver
2. **Real Keyboard Events** - Uses actual macOS keyboard events
3. **Native Screenshots** - Uses macOS screencapture, not browser APIs
4. **AppleScript Control** - OS-level browser control
5. **Logged-in Session** - Uses your real Chrome profile with Google login

## Screenshots

Screenshots are saved as:
- `section_01_20251211_194523.png`
- `section_02_20251211_194525.png`
- etc.

## View Screenshots

```bash
open screenshots/
```

## Tips

- **Manual Control**: The script prompts before each screenshot, giving you full control
- **Adjustable**: Change NUM_SCROLLS and SCROLL_DELAY as needed
- **Safe**: No risk of account bans - it looks like real usage
- **Reliable**: Uses stable macOS system tools

## Comparison

| Feature | Selenium Method | Native Method |
|---------|----------------|---------------|
| Detectable | ❌ Yes | ✅ No |
| Dependencies | Selenium | None |
| Setup | Complex | Simple |
| Google Login | Manual workaround | Native |
| Speed | Fast | Moderate |
| Control | Automated | Semi-manual |

## Advanced: Fully Automated Version

If you want fully automated (no prompts), you can modify the script to remove the `input()` calls. The current version includes prompts for safety and control.
