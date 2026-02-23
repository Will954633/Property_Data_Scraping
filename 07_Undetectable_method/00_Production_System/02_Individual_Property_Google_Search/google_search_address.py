#!/usr/bin/env python3
"""
Google Search Address Script
Opens Google Chrome and searches for a property address using the URL bar
Based on methodology from multi_session_runner.py
"""

import subprocess
import time
import os
from datetime import datetime

# Address to search
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"

# Configuration
INITIAL_LOAD_DELAY = 5  # Time to wait after search is submitted for page to fully load
SCREENSHOT_DIR = "screenshots"


def run_applescript(script):
    """Execute AppleScript command"""
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()


def open_chrome_and_search(address, screenshot_dir):
    """
    Open Chrome and search for address in URL bar
    When you type an address in Chrome's URL bar and press Enter, it automatically performs a Google search
    """
    # Create screenshot directory
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Construct Google search URL (Chrome will handle this when typing in address bar)
    # We'll use AppleScript to activate Chrome, create a new window, and type in the address bar
    script = f'''
    tell application "Google Chrome"
        activate
        make new window
        set URL of active tab of front window to "about:blank"
    end tell
    '''
    run_applescript(script)
    print(f"✓ Opened Chrome")
    time.sleep(1)
    
    # Focus on the address bar (Command+L)
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    
    # Type the address
    type_text(address)
    print(f"✓ Typed address: {address}")
    time.sleep(0.5)
    
    # Press Enter to search
    press_enter()
    print(f"✓ Pressed Enter - Google search initiated")
    print(f"→ Waiting {INITIAL_LOAD_DELAY} seconds for page to load...")
    time.sleep(INITIAL_LOAD_DELAY)
    
    # Take screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"google_search_{timestamp}.png"
    filepath = os.path.join(screenshot_dir, filename)
    
    print(f"→ Taking screenshot...")
    bring_chrome_to_front()
    time.sleep(0.5)
    take_screenshot(filepath)
    print(f"✓ Screenshot saved: {filename}")
    
    return filepath


def bring_chrome_to_front():
    """Bring Chrome to foreground"""
    script = '''
    tell application "Google Chrome"
        activate
    end tell
    '''
    run_applescript(script)


def focus_address_bar():
    """Focus Chrome address bar using Command+L"""
    script = '''
    tell application "System Events"
        keystroke "l" using command down
    end tell
    '''
    run_applescript(script)


def type_text(text):
    """Type text using System Events"""
    script = f'''
    tell application "System Events"
        keystroke "{text}"
    end tell
    '''
    run_applescript(script)


def press_enter():
    """Press Enter key"""
    script = '''
    tell application "System Events"
        key code 36
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
    if result:
        bounds = [int(x.strip()) for x in result.split(',')]
        return bounds
    return None


def take_screenshot(filepath):
    """Take screenshot of Chrome window using native macOS screencapture"""
    bounds = get_chrome_window_bounds()
    
    if bounds:
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1
        subprocess.run(['screencapture', '-x', '-R', f'{x1},{y1},{width},{height}', filepath])
    else:
        # Fallback to full screen if bounds not available
        subprocess.run(['screencapture', '-x', filepath])
    
    return filepath


def main():
    """Main function - opens Chrome and searches for address"""
    print("\n" + "=" * 70)
    print("GOOGLE SEARCH ADDRESS SCRIPT")
    print("INDIVIDUAL PROPERTY SEARCH METHOD")
    print("=" * 70)
    print(f"\nAddress to search: {SEARCH_ADDRESS}")
    print(f"Screenshot directory: {SCREENSHOT_DIR}/")
    print(f"\nMethod:")
    print("  1. Open Google Chrome")
    print("  2. Focus on URL/address bar")
    print("  3. Type the address")
    print("  4. Press Enter (triggers Google search)")
    print("  5. Wait for page to load")
    print("  6. Take screenshot using native macOS screencapture")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    
    # Perform the search
    print("\n→ Starting search process...")
    screenshot_path = open_chrome_and_search(SEARCH_ADDRESS, SCREENSHOT_DIR)
    
    if screenshot_path:
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("✅ SEARCH COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nAddress searched: {SEARCH_ADDRESS}")
        print(f"Screenshot saved: {os.path.abspath(screenshot_path)}")
        print(f"Time taken: {duration}")
        print(f"\nThe Google search results are displayed in Chrome.")
        print("\n" + "=" * 70 + "\n")
    else:
        print("\n❌ Search failed!")


if __name__ == "__main__":
    main()
