#!/usr/bin/env python3
"""
Multi-Address Runner
Tests multiple addresses to observe click behavior
Based on simple_url_clicker.py
"""

import subprocess
import time
import os
from datetime import datetime
from PIL import Image
import pytesseract

# Addresses to test
TEST_ADDRESSES = [
    "18 Mornington Terrace, Robina",
    "22 Homebush Drive, Robina",
    "6 Macedon Close, Robina",
    "33 Manly Drive, Robina",
    "3 Beaumaris Court, Robina"
]

# Configuration
INITIAL_LOAD_DELAY = 5
PAGE_LOAD_DELAY = 3  # Wait to observe result before next test
SCREENSHOT_DIR = "multi_test_screenshots"


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


def close_chrome_tab():
    """Close current tab"""
    script = '''
    tell application "System Events"
        keystroke "w" using command down
    end tell
    '''
    run_applescript(script)


def open_chrome_and_search(address, screenshot_dir, test_num):
    os.makedirs(screenshot_dir, exist_ok=True)
    
    script = f'''
    tell application "Google Chrome"
        activate
        make new window
        set URL of active tab of front window to "about:blank"
    end tell
    '''
    run_applescript(script)
    time.sleep(1)
    
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(address)
    time.sleep(0.5)
    press_enter()
    time.sleep(INITIAL_LOAD_DELAY)
    
    filename = f"test{test_num}_google_search.png"
    filepath = os.path.join(screenshot_dir, filename)
    
    bring_chrome_to_front()
    time.sleep(0.5)
    take_screenshot(filepath)
    
    return filepath


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
                'center_y': y + h // 2,
                'y': y
            })
    return results


def find_realestate_url(ocr_results):
    """Find https://www.realestate.com.au URL (exclude property.com.au)"""
    urls = []
    for item in ocr_results:
        text_lower = item['text'].lower()
        
        if 'realestate.com.au' in text_lower and 'property' not in text_lower:
            if 'https' in text_lower or 'www' in text_lower:
                urls.append(item)
    
    if urls:
        urls.sort(key=lambda x: x['y'])
        return urls[0]
    return None


def click(x, y):
    subprocess.run(['cliclick', f'm:{x},{y}'])
    time.sleep(0.3)
    subprocess.run(['cliclick', 'c:.'])
    time.sleep(PAGE_LOAD_DELAY)


def process_address(address, test_num):
    """Process one address"""
    print(f"\n{'=' * 70}")
    print(f"TEST {test_num}/{len(TEST_ADDRESSES)}: {address}")
    print(f"{'=' * 70}")
    
    # Step 1: Search
    print(f"→ Opening Chrome and searching...")
    screenshot_path = open_chrome_and_search(address, SCREENSHOT_DIR, test_num)
    print(f"  ✓ Screenshot saved")
    
    # Step 2: OCR
    print(f"→ Running OCR...")
    ocr_results = run_ocr(screenshot_path)
    print(f"  ✓ Found {len(ocr_results)} text elements")
    
    # Step 3: Find URL
    print(f"→ Finding realestate.com.au URL...")
    url_match = find_realestate_url(ocr_results)
    
    if not url_match:
        print(f"  ✗ No realestate.com.au URL found")
        close_chrome_tab()
        return {
            'address': address,
            'success': False,
            'reason': 'URL not found'
        }
    
    print(f"  ✓ Found URL at ({url_match['center_x']}, {url_match['center_y']})")
    
    # Step 4: Click
    print(f"→ Clicking...")
    click(url_match['center_x'], url_match['center_y'])
    print(f"  ✓ Clicked - observe which site opened!")
    
    # Wait for user to observe
    print(f"  → Waiting {PAGE_LOAD_DELAY} seconds for observation...")
    time.sleep(PAGE_LOAD_DELAY)
    
    # Close tab
    close_chrome_tab()
    print(f"  ✓ Closed tab")
    
    return {
        'address': address,
        'success': True,
        'click_coords': (url_match['center_x'], url_match['center_y'])
    }


def main():
    print("\n" + "=" * 70)
    print("MULTI-ADDRESS TESTER")
    print("=" * 70)
    print(f"\nAddresses to test: {len(TEST_ADDRESSES)}")
    for i, addr in enumerate(TEST_ADDRESSES, 1):
        print(f"  {i}. {addr}")
    print(f"\nYou will be able to manually observe which site it clicks on")
    print(f"Screenshot directory: {SCREENSHOT_DIR}/")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    results = []
    
    # Process each address
    for i, address in enumerate(TEST_ADDRESSES, 1):
        result = process_address(address, i)
        results.append(result)
        
        # Delay between tests (except after last one)
        if i < len(TEST_ADDRESSES):
            print(f"\n→ Waiting 2 seconds before next test...")
            time.sleep(2)
    
    # Summary
    duration = datetime.now() - start_time
    
    print("\n" + "=" * 70)
    print("TESTING COMPLETE!")
    print("=" * 70)
    print(f"\nTotal tests: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    print(f"Total time: {duration}")
    
    print(f"\nResults:")
    for i, result in enumerate(results, 1):
        status = "✓" if result['success'] else "✗"
        print(f"  {status} Test {i}: {result['address']}")
        if result['success']:
            print(f"     Clicked at: {result['click_coords']}")
        else:
            print(f"     Reason: {result['reason']}")
    
    print(f"\nScreenshots saved to: {os.path.abspath(SCREENSHOT_DIR)}/")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
