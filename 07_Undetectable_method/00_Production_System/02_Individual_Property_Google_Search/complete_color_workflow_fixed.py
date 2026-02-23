#!/usr/bin/env python3
"""
Complete Color-Based Workflow - FIXED
Uses X-coordinate filtering to ensure we click on favicon to the LEFT of realestate URL
"""

import subprocess
import time
import os
import sys
import numpy as np
from datetime import datetime
from PIL import Image
import pytesseract
import math

# Address to search
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"

# Configuration
INITIAL_LOAD_DELAY = 5
SCREENSHOT_DIR = "screenshots"
FAVICON_PATH = "favicon_reference.png"
COLOR_TOLERANCE = 30


def run_applescript(script):
    """Execute AppleScript command"""
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
    print(f"✓ Screenshot saved")
    
    return filepath


def extract_red_color(favicon_path):
    img = Image.open(favicon_path).convert('RGB')
    pixels = np.array(img)
    pixels_flat = pixels.reshape(-1, 3)
    red_pixels = pixels_flat[(pixels_flat[:, 0] > pixels_flat[:, 1]) & 
                              (pixels_flat[:, 0] > pixels_flat[:, 2])]
    if len(red_pixels) == 0:
        return None
    return tuple(np.mean(red_pixels, axis=0).astype(int))


def find_red_pixels(screenshot_path, target_color, tolerance):
    img = Image.open(screenshot_path).convert('RGB')
    pixels = np.array(img)
    
    r_diff = np.abs(pixels[:, :, 0] - target_color[0])
    g_diff = np.abs(pixels[:, :, 1] - target_color[1])
    b_diff = np.abs(pixels[:, :, 2] - target_color[2])
    
    matches = (r_diff <= tolerance) & (g_diff <= tolerance) & (b_diff <= tolerance)
    y_coords, x_coords = np.where(matches)
    return list(zip(x_coords, y_coords))


def run_ocr(image_path):
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
                'center_y': y + h // 2
            })
    return results


def find_realestate_url(ocr_results):
    """Find the actual https://www.realestate.com.au URL (not property.com.au)"""
    urls = []
    for item in ocr_results:
        text_lower = item['text'].lower()
        # Must be a URL AND contain realestate AND NOT contain "property"
        if ('https' in text_lower or 'www' in text_lower) and 'realestate' in text_lower and 'property' not in text_lower:
            urls.append(item)
    
    if urls:
        # Return topmost match
        urls.sort(key=lambda x: x['center_y'])
        return urls[0]
    return None


def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def find_favicon_pixel(red_pixels, url_text_coords):
    """Find red pixel that is to the LEFT of and close to the URL"""
    url_x, url_y = url_text_coords['center_x'], url_text_coords['center_y']
    
    print(f"  Looking for red pixels LEFT of X={url_x}, near Y={url_y}")
    
    # Filter: pixels must be to the LEFT of URL (favicons appear before text)
    # and within reasonable Y distance
    candidates = []
    for pixel in red_pixels:
        px, py = pixel
        
        # Must be to the LEFT (smaller X) and similar Y coordinate
        if px < url_x and abs(py - url_y) < 50:  # Within 50px vertically
            dist = calculate_distance(pixel, (url_x, url_y))
            candidates.append({
                'pixel': pixel,
                'dist': dist
            })
    
    if candidates:
        # Return closest
        best = min(candidates, key=lambda x: x['dist'])
        print(f"✓ Found favicon pixel to LEFT of URL")
        print(f"  Pixel: {best['pixel']}")
        print(f"  Distance: {best['dist']:.1f}px")
        return best['pixel']
    
    print(f"✗ No red pixels found to LEFT of URL")
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
    print("FIXED: FAVICON-AWARE WORKFLOW")
    print("=" * 70)
    print(f"\nAddress: {SEARCH_ADDRESS}")
    print("Method: Find red pixel to the LEFT of realestate.com.au URL")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    
    # Step 1: Search
    print("\n→ Opening Chrome and searching...")
    screenshot_path = open_chrome_and_search(SEARCH_ADDRESS, SCREENSHOT_DIR)
    
    # Step 2: Extract color
    print("\n→ Analyzing favicon color...")
    target_color = extract_red_color(FAVICON_PATH)
    if not target_color:
        print("✗ Failed")
        return
    print(f"✓ Red color: RGB{target_color}")
    
    # Step 3: Find red pixels
    print("\n→ Finding red pixels...")
    red_pixels = find_red_pixels(screenshot_path, target_color, COLOR_TOLERANCE)
    print(f"✓ Found {len(red_pixels)} red pixels")
    
    # Step 4: OCR
    print("\n→ Running OCR...")
    ocr_results = run_ocr(screenshot_path)
    print(f"✓ Found {len(ocr_results)} text elements")
    
    # Step 5: Find realestate.com.au URL
    print("\n→ Finding realestate.com.au URL...")
    url_match = find_realestate_url(ocr_results)
    
    if not url_match:
        print("✗ No realestate.com.au URL found")
        return
    
    print(f"✓ Found URL: '{url_match['text']}' at ({url_match['center_x']}, {url_match['center_y']})")
    
    # Step 6: Find favicon pixel (to the LEFT of URL)
    print("\n→ Finding favicon pixel...")
    favicon_pixel = find_favicon_pixel(red_pixels, url_match)
    
    if not favicon_pixel:
        print("✗ No favicon pixel found")
        return
    
    # Step 7: Click
    print("\n→ Clicking on favicon...")
    click_x, click_y = favicon_pixel
    click(click_x, click_y)
    
    duration = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("✅ SUCCESS!")
    print("=" * 70)
    print(f"Clicked: ({click_x}, {click_y})")
    print(f"Time: {duration}")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
