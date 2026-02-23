#!/usr/bin/env python3
"""
PyAutoGUI Visual Recognition - SikuliX Alternative
Uses PyAutoGUI to find and click favicon images (like SikuliX but pure Python)
"""

import subprocess
import time
import os
import sys
import pyautogui
from datetime import datetime

# Address to search
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"

# Configuration
INITIAL_LOAD_DELAY = 5
SCREENSHOT_DIR = "screenshots"
FAVICON_TEMPLATE = "favicon_small.png"
CONFIDENCE = 0.7  # Matching confidence (0.0 to 1.0)


def run_applescript(script):
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()


def bring_chrome_to_front():
    script = '''
    tell application "Google Chrome"
        activate
    end tell
    '''
    run_applescript(script)


def focus_address_bar():
    script = '''
    tell application "System Events"
        keystroke "l" using command down
    end tell
    '''
    run_applescript(script)


def type_text(text):
    script = f'''
    tell application "System Events"
        keystroke "{text}"
    end tell
    '''
    run_applescript(script)


def press_enter():
    script = '''
    tell application "System Events"
        key code 36
    end tell
    '''
    run_applescript(script)


def open_chrome_and_search(address):
    """Open Chrome and search for address"""
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
    
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(address)
    print(f"✓ Typed address: {address}")
    time.sleep(0.5)
    press_enter()
    print(f"✓ Pressed Enter")
    time.sleep(INITIAL_LOAD_DELAY)


def find_and_click_favicon(template_path, confidence=0.7):
    """
    Use PyAutoGUI to find favicon on screen and click it
    This is the SikuliX-like functionality!
    """
    print(f"→ Looking for favicon image: {template_path}")
    print(f"  Confidence threshold: {confidence}")
    
    try:
        # PyAutoGUI's locateOnScreen() - similar to SikuliX's find()
        location = pyautogui.locateOnScreen(template_path, confidence=confidence)
        
        if location is None:
            print(f"✗ Favicon not found on screen")
            
            # Try with lower confidence
            print(f"→ Retrying with lower confidence (0.6)...")
            location = pyautogui.locateOnScreen(template_path, confidence=0.6)
            
            if location is None:
                print(f"✗ Still not found")
                return False
        
        # Get center point of the match
        center_x, center_y = pyautogui.center(location)
        
        print(f"✓ Favicon found!")
        print(f"  Location: {location}")
        print(f"  Center: ({center_x}, {center_y})")
        
        # Move mouse and click (similar to SikuliX's click())
        print(f"→ Moving mouse to ({center_x}, {center_y})...")
        pyautogui.moveTo(center_x, center_y, duration=0.3)
        
        print(f"→ Clicking...")
        pyautogui.click()
        
        print(f"✓ Clicked on favicon!")
        time.sleep(2)
        
        return True
        
    except pyautogui.ImageNotFoundException:
        print(f"✗ PyAutoGUI could not find the image")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("\n" + "=" * 70)
    print("PYAUTOGUI VISUAL RECOGNITION - SIKULIX ALTERNATIVE")
    print("=" * 70)
    print(f"\nAddress: {SEARCH_ADDRESS}")
    print(f"Method: PyAutoGUI image recognition (like SikuliX)")
    print(f"Template: {FAVICON_TEMPLATE}")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    
    # Check if favicon template exists
    if not os.path.exists(FAVICON_TEMPLATE):
        print(f"\n✗ Error: Template image not found: {FAVICON_TEMPLATE}")
        sys.exit(1)
    
    # Step 1: Search
    print("\n→ STEP 1: Opening Chrome and searching...")
    open_chrome_and_search(SEARCH_ADDRESS)
    
    # Give Chrome a moment to settle
    print("\n→ Waiting for page to stabilize...")
    time.sleep(2)
    
    # Step 2: Find and click using PyAutoGUI (SikuliX-like)
    print("\n→ STEP 2: Finding favicon using PyAutoGUI (like SikuliX)...")
    success = find_and_click_favicon(FAVICON_TEMPLATE, CONFIDENCE)
    
    if not success:
        print("\n✗ Failed to find and click favicon")
        sys.exit(1)
    
    duration = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print(f"Method: PyAutoGUI Visual Recognition (SikuliX Alternative)")
    print(f"Time: {duration}")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
