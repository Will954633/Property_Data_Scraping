#!/usr/bin/env python3
"""
Simple URL Clicker - Foolproof Method
Clicks directly on the realestate.com.au URL text (not the favicon)
"""

import subprocess
import time
import os
import sys
import numpy as np
from datetime import datetime
from PIL import Image
import pytesseract

# Address to search
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"

# Configuration
INITIAL_LOAD_DELAY = 5
SCREENSHOT_DIR = "screenshots"


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
    print(f"→ Waiting {INITIAL_LOAD_DELAY} seconds...")
    time.sleep(INITIAL_LOAD_DELAY)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"google_search_{timestamp}.png"
    filepath = os.path.join(screenshot_dir, filename)
    
    bring_chrome_to_front()
    time.sleep(0.5)
    take_screenshot(filepath)
    print(f"✓ Screenshot saved: {filename}")
    
    return filepath


def run_ocr(image_path):
    print(f"→ Running OCR...")
    img = Image.open(image_path)
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    results = []
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        if text:
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            results.append({
                'text': text,
                'center_x': x + w // 2,
                'center_y': y + h // 2,
                'y': y
            })
    print(f"✓ Found {len(results)} text elements")
    return results


def find_realestate_url(ocr_results):
    """Find ONLY https://www.realestate.com.au URL (exclude property.com.au)"""
    urls = []
    for item in ocr_results:
        text = item['text']
        text_lower = text.lower()
        
        # Must contain www.realestate.com.au OR https://www.realestate.com.au
        # AND must NOT contain "property"
        if 'realestate.com.au' in text_lower and 'property' not in text_lower:
            if 'https' in text_lower or 'www' in text_lower:
                urls.append(item)
                print(f"  Found: '{text}' at Y={item['y']}")
    
    if urls:
        # Return topmost URL
        urls.sort(key=lambda x: x['y'])
        return urls[0]
    return None


def click(x, y):
    print(f"→ Clicking at ({x}, {y})...")
    subprocess.run(['cliclick', f'm:{x},{y}'])
    time.sleep(0.3)
    subprocess.run(['cliclick', 'c:.'])
    print(f"✓ Clicked")
    time.sleep(2)


def main():
    print("\n" + "=" * 70)
    print("SIMPLE URL CLICKER - FOOLPROOF METHOD")
    print("=" * 70)
    print(f"\nAddress: {SEARCH_ADDRESS}")
    print("Method: Click directly on realestate.com.au URL text")
    print("(No favicon detection - just click the URL itself)")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    
    # Step 1: Search
    print("\n→ STEP 1: Opening Chrome and searching...")
    screenshot_path = open_chrome_and_search(SEARCH_ADDRESS, SCREENSHOT_DIR)
    
    # Step 2: OCR
    print("\n→ STEP 2: Running OCR to find URL...")
    ocr_results = run_ocr(screenshot_path)
    
    # Step 3: Find URL
    print("\n→ STEP 3: Finding realestate.com.au URL (excluding property.com.au)...")
    url_match = find_realestate_url(ocr_results)
    
    if not url_match:
        print("✗ No realestate.com.au URL found")
        return
    
    print(f"\n✓ Target URL: '{url_match['text']}'")
    print(f"  Coordinates: ({url_match['center_x']}, {url_match['center_y']})")
    
    # Step 4: Click directly on URL text
    print("\n→ STEP 4: Clicking on URL text...")
    click(url_match['center_x'], url_match['center_y'])
    
    duration = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print(f"Method: Direct URL click (no favicon)")
    print(f"Clicked: ({url_match['center_x']}, {url_match['center_y']})")
    print(f"Time: {duration}")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
