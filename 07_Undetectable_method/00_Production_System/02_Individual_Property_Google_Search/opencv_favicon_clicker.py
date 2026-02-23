#!/usr/bin/env python3
"""
OpenCV Template Matching - Visual Recognition Method
Uses OpenCV to find the exact favicon image in the screenshot
Similar to Sikuli but Python-based
"""

import subprocess
import time
import os
import sys
import cv2
import numpy as np
from datetime import datetime

# Address to search
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"

# Configuration
INITIAL_LOAD_DELAY = 5
SCREENSHOT_DIR = "screenshots"
FAVICON_TEMPLATE = "favicon_small.png"  # Small cropped favicon (36x35 pixels)
MATCH_THRESHOLD = 0.7  # Confidence threshold for template matching


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


def get_chrome_window_bounds():
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
    bounds = get_chrome_window_bounds()
    if bounds:
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1
        subprocess.run(['screencapture', '-x', '-R', f'{x1},{y1},{width},{height}', filepath])
    else:
        subprocess.run(['screencapture', '-x', filepath])
    return filepath


def open_chrome_and_search(address, screenshot_dir):
    os.makedirs(screenshot_dir, exist_ok=True)
    
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
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"google_search_{timestamp}.png"
    filepath = os.path.join(screenshot_dir, filename)
    
    bring_chrome_to_front()
    time.sleep(0.5)
    take_screenshot(filepath)
    print(f"✓ Screenshot saved")
    
    return filepath


def find_template_in_screenshot(screenshot_path, template_path, threshold):
    """
    Use OpenCV template matching to find favicon in screenshot
    Returns list of (x, y) coordinates for all matches above threshold
    """
    print(f"→ Loading images...")
    screenshot = cv2.imread(screenshot_path)
    template = cv2.imread(template_path)
    
    if screenshot is None:
        print(f"✗ Could not load screenshot: {screenshot_path}")
        return []
    
    if template is None:
        print(f"✗ Could not load template: {template_path}")
        return []
    
    print(f"  Screenshot size: {screenshot.shape[:2]}")
    print(f"  Template size: {template.shape[:2]}")
    
    # Perform template matching
    print(f"→ Performing template matching...")
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    
    # Find all matches above threshold
    locations = np.where(result >= threshold)
    matches = []
    
    h, w = template.shape[:2]
    
    for pt in zip(*locations[::-1]):  # Switch x and y
        x, y = pt
        # Calculate center of matched region
        center_x = x + w // 2
        center_y = y + h // 2
        confidence = result[y, x]
        
        matches.append({
            'x': center_x,
            'y': center_y,
            'confidence': confidence
        })
    
    print(f"✓ Found {len(matches)} matches above {threshold} confidence")
    
    return matches


def click(x, y):
    print(f"→ Clicking at ({x}, {y})...")
    subprocess.run(['cliclick', f'm:{x},{y}'])
    time.sleep(0.3)
    subprocess.run(['cliclick', 'c:.'])
    print(f"✓ Clicked")
    time.sleep(2)


def main():
    print("\n" + "=" * 70)
    print("OPENCV TEMPLATE MATCHING - VISUAL RECOGNITION")
    print("=" * 70)
    print(f"\nAddress: {SEARCH_ADDRESS}")
    print(f"Method: OpenCV template matching (like Sikuli)")
    print(f"Template: {FAVICON_TEMPLATE}")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    
    # Step 1: Search
    print("\n→ STEP 1: Opening Chrome and searching...")
    screenshot_path = open_chrome_and_search(SEARCH_ADDRESS, SCREENSHOT_DIR)
    
    # Step 2: Find favicon using template matching
    print("\n→ STEP 2: Finding favicon using OpenCV template matching...")
    matches = find_template_in_screenshot(screenshot_path, FAVICON_TEMPLATE, MATCH_THRESHOLD)
    
    if not matches:
        print("✗ No favicon matches found")
        return
    
    # Sort by Y coordinate (top to bottom) and take first match
    matches_sorted = sorted(matches, key=lambda x: x['y'])
    best_match = matches_sorted[0]
    
    print(f"\n✓ Best match (topmost):")
    print(f"  Coordinates: ({best_match['x']}, {best_match['y']})")
    print(f"  Confidence: {best_match['confidence']:.2%}")
    
    # Step 3: Click
    print("\n→ STEP 3: Clicking on matched favicon...")
    click(best_match['x'], best_match['y'])
    
    duration = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print(f"Method: OpenCV Template Matching")
    print(f"Clicked: ({best_match['x']}, {best_match['y']})")
    print(f"Confidence: {best_match['confidence']:.2%}")
    print(f"Time: {duration}")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
