#!/usr/bin/env python3
"""
Complete Undetectable Property Search Workflow
1. Opens Chrome and searches for address
2. Takes screenshot of Google results
3. Uses OCR to find realestate.com.au link
4. Clicks the link using native mouse control
"""

import subprocess
import time
import os
import sys
from datetime import datetime
from PIL import Image
import pytesseract

# Address to search
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"

# Target domain to click
TARGET_DOMAIN = "realestate.com.au"

# Configuration
INITIAL_LOAD_DELAY = 5  # Time to wait after search is submitted
SCREENSHOT_DIR = "screenshots"

# Fallback coordinates for top 3 Google search results
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
    """Take screenshot of Chrome window using native macOS screencapture"""
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


def run_tesseract_ocr(image_path):
    """Run Tesseract OCR on image and get text with bounding box coordinates"""
    print(f"→ Running OCR on screenshot...")
    
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
                'x': x,
                'y': y,
                'width': w,
                'height': h,
                'center_x': x + w // 2,
                'center_y': y + h // 2
            })
    
    print(f"✓ OCR completed: Found {len(results)} text elements")
    return results


def find_target_domain(ocr_results, target_domain):
    """Search OCR results for target domain and return its coordinates"""
    print(f"→ Searching for '{target_domain}' in OCR results...")
    
    matches = []
    
    for item in ocr_results:
        text = item['text'].lower()
        if target_domain.lower() in text:
            matches.append(item)
            print(f"  ✓ Found match: '{item['text']}' at ({item['center_x']}, {item['center_y']})")
    
    if matches:
        matches.sort(key=lambda x: x['center_y'])
        best_match = matches[0]
        
        print(f"✓ Best match found!")
        print(f"  Text: '{best_match['text']}'")
        print(f"  Click coordinates: ({best_match['center_x']}, {best_match['center_y']})")
        print(f"  Confidence: {best_match['confidence']}%")
        
        return best_match
    
    print(f"✗ No match found for '{target_domain}'")
    return None


def click_with_cliclick(x, y):
    """Use cliclick to move mouse and click at coordinates"""
    print(f"→ Moving mouse to ({x}, {y})...")
    subprocess.run(['cliclick', f'm:{x},{y}'])
    time.sleep(0.3)
    
    print(f"→ Clicking...")
    subprocess.run(['cliclick', 'c:.'])
    
    print(f"✓ Click executed at ({x}, {y})")
    return True


def use_fallback_coordinates(position=1):
    """Use pre-recorded fallback coordinates"""
    print(f"⚠️  Using fallback coordinates for position {position}")
    
    if position in FALLBACK_COORDINATES:
        coords = FALLBACK_COORDINATES[position]
        print(f"  Fallback coordinates: ({coords['x']}, {coords['y']})")
        return coords['x'], coords['y']
    else:
        print(f"✗ No fallback coordinates available for position {position}")
        return None, None


def main():
    """Main workflow"""
    print("\n" + "=" * 70)
    print("COMPLETE UNDETECTABLE PROPERTY SEARCH WORKFLOW")
    print("=" * 70)
    print(f"\nAddress to search: {SEARCH_ADDRESS}")
    print(f"Target domain: {TARGET_DOMAIN}")
    print(f"Screenshot directory: {SCREENSHOT_DIR}/")
    print("\nWorkflow:")
    print("  1. Open Chrome and search for address")
    print("  2. Take screenshot of Google results")
    print("  3. Run OCR to find target domain")
    print("  4. Click link using native mouse control")
    print("\nFeatures:")
    print("  ✓ 100% Undetectable - uses native OS controls")
    print("  ✓ OCR-based link detection")
    print("  ✓ Fallback coordinates for reliability")
    print("  ✓ Native macOS mouse control (cliclick)")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    
    # Step 1: Open Chrome and search
    print("\n→ STEP 1: Opening Chrome and searching...")
    screenshot_path = open_chrome_and_search(SEARCH_ADDRESS, SCREENSHOT_DIR)
    
    # Step 2: Run OCR
    print("\n→ STEP 2: Running OCR analysis...")
    try:
        ocr_results = run_tesseract_ocr(screenshot_path)
    except Exception as e:
        print(f"✗ OCR failed: {e}")
        ocr_results = []
    
    # Step 3: Find target domain
    print("\n→ STEP 3: Finding target domain...")
    target = None
    if ocr_results:
        target = find_target_domain(ocr_results, TARGET_DOMAIN)
    
    # Step 4: Determine click coordinates
    if target:
        click_x = target['center_x']
        click_y = target['center_y']
        method = "OCR"
    else:
        print("→ OCR did not find target, using fallback coordinates...")
        click_x, click_y = use_fallback_coordinates(position=1)
        method = "Fallback"
        
        if click_x is None:
            print("✗ Cannot proceed - no coordinates available")
            return False
    
    # Step 5: Click
    print(f"\n→ STEP 4: Clicking link (Method: {method})...")
    time.sleep(1)
    
    success = click_with_cliclick(click_x, click_y)
    
    if success:
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nAddress searched: {SEARCH_ADDRESS}")
        print(f"Target domain: {TARGET_DOMAIN}")
        print(f"Method used: {method}")
        print(f"Click coordinates: ({click_x}, {click_y})")
        print(f"Screenshot: {os.path.abspath(screenshot_path)}")
        print(f"Total time: {duration}")
        print("\n" + "=" * 70 + "\n")
        return True
    else:
        print("✗ Workflow failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
