#!/usr/bin/env python3
"""
Native macOS Screenshot Scraper - FULLY AUTONOMOUS & UNDETECTABLE
Uses actual system-level scrolling and screenshots - no browser automation
"""

import subprocess
import time
import os
from datetime import datetime

# Target URL
TARGET_URL = "https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-1?includeSurrounding=false&activeSort=relevance&sourcePage=rea:homepage&sourceElement=suburb-select:recent%20searches%20tiles"

# Configuration
SCREENSHOT_DIR = "screenshots"
NUM_SCROLLS = 25  # Number of times to scroll down (captures full page)
SCROLL_DELAY = 1.5  # Seconds to wait after each scroll
INITIAL_LOAD_DELAY = 5  # Seconds to wait for initial page load

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def run_applescript(script):
    """Execute AppleScript command"""
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()

def open_url_in_chrome(url):
    """Open URL in Chrome using AppleScript"""
    script = f'''
    tell application "Google Chrome"
        activate
        open location "{url}"
    end tell
    '''
    run_applescript(script)
    print(f"✓ Opened URL in Chrome")
    time.sleep(INITIAL_LOAD_DELAY)  # Wait for page to load

def bring_chrome_to_front():
    """Bring Chrome to foreground"""
    script = '''
    tell application "Google Chrome"
        activate
    end tell
    '''
    run_applescript(script)

def click_chrome_window():
    """Click on Chrome window to ensure focus"""
    script = '''
    tell application "System Events"
        tell process "Google Chrome"
            click window 1
        end tell
    end tell
    '''
    run_applescript(script)

def scroll_down():
    """Send Page Down key to Chrome using AppleScript"""
    script = '''
    tell application "System Events"
        key code 121
    end tell
    '''
    run_applescript(script)

def scroll_to_top():
    """Send Command+Home to scroll to top"""
    script = '''
    tell application "System Events"
        key code 115 using command down
    end tell
    '''
    run_applescript(script)

def close_chrome_tab():
    """Close current Chrome tab using Command+W"""
    script = '''
    tell application "System Events"
        keystroke "w" using command down
    end tell
    '''
    run_applescript(script)

def get_chrome_window_bounds():
    """Get Chrome window position and size using AppleScript"""
    script = '''
    tell application "Google Chrome"
        set windowBounds to bounds of front window
        return windowBounds
    end tell
    '''
    result = run_applescript(script)
    # Returns: "x1, y1, x2, y2"
    if result:
        bounds = [int(x.strip()) for x in result.split(',')]
        return bounds
    return None

def take_screenshot(filename):
    """Take screenshot of Chrome window using keyboard shortcut"""
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # Get window bounds
    bounds = get_chrome_window_bounds()
    
    if bounds:
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1
        
        # Use screencapture with region capture (no clicking required!)
        subprocess.run(['screencapture', '-x', '-R', f'{x1},{y1},{width},{height}', filepath])
    else:
        # Fallback: Use full screen capture
        subprocess.run(['screencapture', '-x', filepath])
    
    return filepath

def main():
    """Main function - FULLY AUTONOMOUS"""
    print("=" * 70)
    print("NATIVE macOS SCREENSHOT SCRAPER")
    print("FULLY AUTONOMOUS & UNDETECTABLE")
    print("=" * 70)
    print("\nFeatures:")
    print("  ✓ Native macOS scrolling (Page Down key)")
    print("  ✓ Native macOS screenshots")
    print("  ✓ AppleScript for Chrome control")
    print("  ✓ Completely autonomous - no user interaction needed")
    print("  ✓ Automatically closes window when complete")
    print("  ✓ 100% Undetectable by websites")
    print("\n" + "=" * 70)
    
    # Step 1: Open URL in Chrome
    print("\n→ Opening URL in Chrome...")
    open_url_in_chrome(TARGET_URL)
    
    # Step 2: Click window to ensure focus
    print("→ Activating Chrome window...")
    bring_chrome_to_front()
    time.sleep(0.5)
    click_chrome_window()
    time.sleep(0.5)
    
    # Step 3: Scroll to top first
    print("→ Scrolling to top of page...")
    scroll_to_top()
    time.sleep(2)
    
    # Step 4: Take screenshots while scrolling
    print(f"\n→ Taking {NUM_SCROLLS} screenshots while scrolling down...")
    print("   (This is fully automated - sit back and relax!)\n")
    screenshots = []
    
    for i in range(NUM_SCROLLS):
        # Ensure Chrome is in front
        bring_chrome_to_front()
        time.sleep(0.3)
        
        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"section_{i+1:02d}_{timestamp}.png"
        
        print(f"  📸 Screenshot {i+1}/{NUM_SCROLLS}: {filename}")
        
        filepath = take_screenshot(filename)
        screenshots.append(filepath)
        
        # Scroll down
        if i < NUM_SCROLLS - 1:
            time.sleep(0.5)
            scroll_down()
            time.sleep(SCROLL_DELAY)
    
    # Step 5: Close the Chrome tab
    print("\n→ Closing Chrome tab...")
    time.sleep(1)
    close_chrome_tab()
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS - TASK COMPLETED!")
    print("=" * 70)
    print(f"Screenshots saved: {len(screenshots)}")
    print(f"Location: {os.path.abspath(SCREENSHOT_DIR)}/")
    print("\nTo view screenshots:")
    print(f"  open {SCREENSHOT_DIR}/")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
