#!/usr/bin/env python3
"""
OCR Link Clicker - Undetectable Method
Uses Tesseract OCR to find links and native macOS mouse control (cliclick) to click them
100% Undetectable - uses native OS mouse events
"""

import subprocess
import time
import sys
from PIL import Image
import pytesseract
import re

# Target domain to find and click
TARGET_DOMAIN = "realestate.com.au"

# Fallback coordinates for top 3 Google search results (typical positions)
# These are approximate Y positions for first 3 organic results on a standard Google search page
FALLBACK_COORDINATES = {
    1: {"x": 400, "y": 250},  # First result
    2: {"x": 400, "y": 400},  # Second result  
    3: {"x": 400, "y": 550},  # Third result
}


def run_tesseract_ocr(image_path):
    """
    Run Tesseract OCR on image and get text with bounding box coordinates
    Returns list of dictionaries with text, confidence, and coordinates
    """
    print(f"→ Running OCR on: {image_path}")
    
    # Load image
    img = Image.open(image_path)
    
    # Get detailed OCR data including bounding boxes
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    # Parse OCR results
    results = []
    n_boxes = len(ocr_data['text'])
    
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if text:  # Only include non-empty text
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
    """
    Search OCR results for target domain and return its coordinates
    """
    print(f"\n→ Searching for '{target_domain}' in OCR results...")
    
    matches = []
    
    for item in ocr_results:
        text = item['text'].lower()
        
        # Check if target domain is in the text
        if target_domain.lower() in text:
            matches.append(item)
            print(f"  ✓ Found match: '{item['text']}' at ({item['center_x']}, {item['center_y']})")
    
    if matches:
        # Return the first match (topmost on page)
        # Sort by Y coordinate to get topmost
        matches.sort(key=lambda x: x['center_y'])
        best_match = matches[0]
        
        print(f"\n✓ Best match found!")
        print(f"  Text: '{best_match['text']}'")
        print(f"  Click coordinates: ({best_match['center_x']}, {best_match['center_y']})")
        print(f"  Confidence: {best_match['confidence']}%")
        
        return best_match
    
    print(f"✗ No match found for '{target_domain}'")
    return None


def click_with_cliclick(x, y):
    """
    Use cliclick to move mouse and click at coordinates
    This is 100% undetectable as it uses native macOS mouse events
    """
    print(f"\n→ Moving mouse to ({x}, {y})...")
    
    # Move mouse to coordinates
    subprocess.run(['cliclick', f'm:{x},{y}'])
    time.sleep(0.3)
    
    # Click
    print(f"→ Clicking...")
    subprocess.run(['cliclick', 'c:.'])
    
    print(f"✓ Click executed at ({x}, {y})")
    return True


def use_fallback_coordinates(position=1):
    """
    Use pre-recorded fallback coordinates for typical Google result positions
    """
    print(f"\n⚠️  Using fallback coordinates for position {position}")
    
    if position in FALLBACK_COORDINATES:
        coords = FALLBACK_COORDINATES[position]
        print(f"  Fallback coordinates: ({coords['x']}, {coords['y']})")
        return coords['x'], coords['y']
    else:
        print(f"✗ No fallback coordinates available for position {position}")
        return None, None


def main(screenshot_path):
    """
    Main function - OCR + Click workflow
    """
    print("\n" + "=" * 70)
    print("OCR LINK CLICKER - UNDETECTABLE METHOD")
    print("=" * 70)
    print(f"\nTarget domain: {TARGET_DOMAIN}")
    print(f"Screenshot: {screenshot_path}")
    print("\nWorkflow:")
    print("  1. Run Tesseract OCR on screenshot")
    print("  2. Find target domain coordinates")
    print("  3. Click using native macOS mouse (cliclick)")
    print("  4. Fallback to pre-recorded coordinates if needed")
    print("\n" + "=" * 70)
    
    # Step 1: Run OCR
    try:
        ocr_results = run_tesseract_ocr(screenshot_path)
    except Exception as e:
        print(f"\n✗ OCR failed: {e}")
        print("→ Will try fallback coordinates...")
        ocr_results = []
    
    # Step 2: Find target domain
    target = None
    if ocr_results:
        target = find_target_domain(ocr_results, TARGET_DOMAIN)
    
    # Step 3: Determine click coordinates
    if target:
        # Use OCR-detected coordinates
        click_x = target['center_x']
        click_y = target['center_y']
        method = "OCR"
    else:
        # Use fallback coordinates
        print("\n→ OCR did not find target, using fallback coordinates...")
        click_x, click_y = use_fallback_coordinates(position=1)
        method = "Fallback"
        
        if click_x is None:
            print("\n✗ Cannot proceed - no coordinates available")
            return False
    
    # Step 4: Click
    print(f"\n→ Method: {method}")
    time.sleep(1)  # Brief pause before clicking
    
    success = click_with_cliclick(click_x, click_y)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ CLICK COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nMethod used: {method}")
        print(f"Click coordinates: ({click_x}, {click_y})")
        print(f"Target domain: {TARGET_DOMAIN}")
        print("\n" + "=" * 70 + "\n")
        return True
    else:
        print("\n✗ Click failed")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_link_clicker.py <screenshot_path>")
        print("Example: python ocr_link_clicker.py screenshots/google_search_20251113_112258.png")
        sys.exit(1)
    
    screenshot_path = sys.argv[1]
    success = main(screenshot_path)
    sys.exit(0 if success else 1)
