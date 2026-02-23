#!/usr/bin/env python3
"""
Complete Color-Based Workflow
1. Opens Chrome and searches for address on Google
2. Takes screenshot of results
3. Uses color detection + OCR to find realestate.com.au favicon
4. Clicks on the favicon using native mouse control
5. Opens the realestate.com.au property page
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

# Target domain to click
TARGET_DOMAIN = "realestate.com.au"

# Configuration
INITIAL_LOAD_DELAY = 5  # Time to wait after search
SCREENSHOT_DIR = "screenshots"
FAVICON_PATH = "favicon_reference.png"

# Color detection settings
COLOR_TOLERANCE = 30
PROXIMITY_THRESHOLD = 300

# Fallback coordinates
FALLBACK_COORDINATES = {
    1: {"x": 400, "y": 250},
    2: {"x": 400, "y": 400},
    3: {"x": 400, "y": 550},
}


def run_applescript(script):
    """Execute AppleScript command"""
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()


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
    """Take screenshot of Chrome window"""
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
    """Open Chrome, search for address, and take screenshot"""
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
    print(f"✓ Pressed Enter - Google search initiated")
    print(f"→ Waiting {INITIAL_LOAD_DELAY} seconds for page to load...")
    time.sleep(INITIAL_LOAD_DELAY)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"google_search_{timestamp}.png"
    filepath = os.path.join(screenshot_dir, filename)
    
    print(f"→ Taking screenshot...")
    bring_chrome_to_front()
    time.sleep(0.5)
    take_screenshot(filepath)
    print(f"✓ Screenshot saved: {filename}")
    
    return filepath


def extract_dominant_red_color(favicon_path):
    """Extract the dominant red color from the favicon image"""
    print(f"→ Analyzing favicon: {favicon_path}")
    
    img = Image.open(favicon_path).convert('RGB')
    pixels = np.array(img)
    pixels_flat = pixels.reshape(-1, 3)
    
    red_pixels = pixels_flat[(pixels_flat[:, 0] > pixels_flat[:, 1]) & 
                              (pixels_flat[:, 0] > pixels_flat[:, 2])]
    
    if len(red_pixels) == 0:
        return None
    
    target_color = tuple(np.mean(red_pixels, axis=0).astype(int))
    print(f"✓ Target red color: RGB{target_color}")
    return target_color


def find_matching_pixels(screenshot_path, target_color, tolerance):
    """Find all pixels in screenshot that match the target color"""
    print(f"→ Searching for matching red pixels...")
    
    img = Image.open(screenshot_path).convert('RGB')
    pixels = np.array(img)
    
    r_diff = np.abs(pixels[:, :, 0] - target_color[0])
    g_diff = np.abs(pixels[:, :, 1] - target_color[1])
    b_diff = np.abs(pixels[:, :, 2] - target_color[2])
    
    matches = (r_diff <= tolerance) & (g_diff <= tolerance) & (b_diff <= tolerance)
    y_coords, x_coords = np.where(matches)
    matching_coords = list(zip(x_coords, y_coords))
    
    print(f"✓ Found {len(matching_coords)} matching red pixels")
    return matching_coords


def run_tesseract_ocr(image_path):
    """Run Tesseract OCR on image"""
    print(f"→ Running OCR...")
    
    img = Image.open(image_path)
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    results = []
    n_boxes = len(ocr_data['text'])
    
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if text:
            conf = int(ocr_data['conf'][i])
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            
            results.append({
                'text': text,
                'confidence': conf,
                'center_x': x + w // 2,
                'center_y': y + h // 2
            })
    
    print(f"✓ OCR completed: Found {len(results)} text elements")
    return results


def find_text_in_ocr(ocr_results, search_text, exclude_text=None):
    """Find specific text in OCR results, optionally excluding certain text"""
    matches = []
    for item in ocr_results:
        text_lower = item['text'].lower()
        # Must contain the search text
        if search_text.lower() in text_lower:
            # If exclusion specified, skip if it contains that text
            if exclude_text and exclude_text.lower() in text_lower:
                continue
            matches.append(item)
    return matches


def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def find_best_red_pixel(red_pixels, domain_matches, exclude_matches, threshold):
    """Find the red pixel closest to realestate.com.au URL that is also far from property text"""
    print(f"→ Finding red pixel for realestate.com.au...")
    
    if not domain_matches:
        print("✗ No domain matches found")
        return None
    
    # MUST find the actual URL (with https or www), not just text containing "realestate"
    url_matches = [m for m in domain_matches if 'https' in m['text'].lower() or 'www' in m['text'].lower()]
    
    if not url_matches:
        print("✗ No realestate.com.au URL found in OCR")
        return None
    
    # Use the first URL match
    url_matches_sorted = sorted(url_matches, key=lambda x: x['center_y'])
    primary_domain = url_matches_sorted[0]
    domain_center = (primary_domain['center_x'], primary_domain['center_y'])
    
    print(f"  Target URL: '{primary_domain['text']}' at {domain_center}")
    
    # Find red pixels close to this URL
    valid_pixels = []
    for red_pixel in red_pixels:
        dist_to_url = calculate_distance(red_pixel, domain_center)
        
        # Must be reasonably close to the URL
        if dist_to_url <= threshold:
            # Check it's NOT closer to any "property" text
            too_close_to_property = False
            if exclude_matches:
                for exclude in exclude_matches:
                    exclude_center = (exclude['center_x'], exclude['center_y'])
                    dist_to_property = calculate_distance(red_pixel, exclude_center)
                    # Reject if closer to property than to realestate URL
                    if dist_to_property < dist_to_url:
                        too_close_to_property = True
                        break
            
            if not too_close_to_property:
                valid_pixels.append({
                    'pixel': red_pixel,
                    'dist': dist_to_url
                })
    
    if valid_pixels:
        # Get the closest valid pixel
        best = min(valid_pixels, key=lambda x: x['dist'])
        print(f"✓ Valid red pixel found")
        print(f"  Coordinates: {best['pixel']}")
        print(f"  Distance to URL: {best['dist']:.1f}px")
        return best['pixel']
    
    print(f"✗ No valid red pixels found (all too close to 'property' text)")
    return None


def click_with_cliclick(x, y):
    """Use cliclick to move mouse and click"""
    print(f"→ Moving mouse to ({x}, {y})...")
    subprocess.run(['cliclick', f'm:{x},{y}'])
    time.sleep(0.3)
    
    print(f"→ Clicking...")
    subprocess.run(['cliclick', 'c:.'])
    
    print(f"✓ Click executed")
    time.sleep(2)  # Wait for page to load
    return True


def main():
    """Main workflow"""
    print("\n" + "=" * 70)
    print("COMPLETE COLOR-BASED WORKFLOW")
    print("=" * 70)
    print(f"\nAddress: {SEARCH_ADDRESS}")
    print(f"Target domain: {TARGET_DOMAIN}")
    print("\nSteps:")
    print("  1. Open Chrome and search for address")
    print("  2. Take screenshot")
    print("  3. Extract red color from favicon")
    print("  4. Find matching red pixels")
    print("  5. Run OCR to find domain")
    print("  6. Validate proximity")
    print("  7. Click on validated pixel")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    
    # Step 1-2: Search and screenshot
    print("\n→ STEP 1-2: Opening Chrome and searching...")
    screenshot_path = open_chrome_and_search(SEARCH_ADDRESS, SCREENSHOT_DIR)
    
    # Step 3: Extract favicon color
    print("\n→ STEP 3: Analyzing favicon color...")
    try:
        target_color = extract_dominant_red_color(FAVICON_PATH)
        if not target_color:
            raise Exception("Could not extract red color")
    except Exception as e:
        print(f"✗ Favicon analysis failed: {e}")
        print("→ Using fallback method...")
        click_x, click_y = FALLBACK_COORDINATES[1]['x'], FALLBACK_COORDINATES[1]['y']
        method = "Fallback"
        click_with_cliclick(click_x, click_y)
        return
    
    # Step 4: Find red pixels
    print("\n→ STEP 4: Finding matching red pixels...")
    try:
        red_pixels = find_matching_pixels(screenshot_path, target_color, COLOR_TOLERANCE)
        if len(red_pixels) == 0:
            raise Exception("No matching pixels")
    except Exception as e:
        print(f"✗ Color matching failed: {e}")
        click_x, click_y = FALLBACK_COORDINATES[1]['x'], FALLBACK_COORDINATES[1]['y']
        method = "Fallback"
        click_with_cliclick(click_x, click_y)
        return
    
    # Step 5: OCR
    print("\n→ STEP 5: Running OCR...")
    try:
        ocr_results = run_tesseract_ocr(screenshot_path)
        
        # Search for "realestate" specifically
        domain_matches = find_text_in_ocr(ocr_results, "realestate")
        print(f"✓ Found {len(domain_matches)} matches for 'realestate'")
        
        # Also find "property" to exclude those areas
        exclude_matches = find_text_in_ocr(ocr_results, "property")
        print(f"✓ Found {len(exclude_matches)} matches for 'property' (to avoid)")
        
        if len(domain_matches) == 0:
            print("✗ No realestate.com.au matches found")
            raise Exception("No valid domain matches")
    except Exception as e:
        print(f"✗ OCR failed: {e}")
        click_x, click_y = FALLBACK_COORDINATES[1]['x'], FALLBACK_COORDINATES[1]['y']
        method = "Fallback"
        click_with_cliclick(click_x, click_y)
        return
    
    # Step 6-7: Find and click
    print("\n→ STEP 6: Finding best pixel...")
    best_pixel = find_best_red_pixel(red_pixels, domain_matches, exclude_matches, PROXIMITY_THRESHOLD)
    
    if best_pixel:
        click_x, click_y = best_pixel
        method = "Color + OCR + Proximity"
    else:
        print("→ Using fallback coordinates...")
        click_x, click_y = FALLBACK_COORDINATES[1]['x'], FALLBACK_COORDINATES[1]['y']
        method = "Fallback"
    
    print(f"\n→ STEP 7: Clicking (Method: {method})...")
    click_with_cliclick(click_x, click_y)
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 70)
    print("✅ WORKFLOW COMPLETED!")
    print("=" * 70)
    print(f"\nMethod: {method}")
    print(f"Click coordinates: ({click_x}, {click_y})")
    print(f"Screenshot: {os.path.abspath(screenshot_path)}")
    print(f"Total time: {duration}")
    print(f"\nRealestate.com.au page should now be loading in Chrome!")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
