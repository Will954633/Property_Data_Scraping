#!/usr/bin/env python3
"""
Debug OCR Results - Show all text matches with coordinates
"""

import sys
from PIL import Image
import pytesseract

def debug_ocr(screenshot_path):
    """Show all OCR results that contain 'realestate' or 'property'"""
    print(f"\nAnalyzing: {screenshot_path}\n")
    
    img = Image.open(screenshot_path)
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    results = []
    n_boxes = len(ocr_data['text'])
    
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if text:
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Check if contains realestate or property
            if 'realestate' in text.lower() or 'property' in text.lower():
                results.append({
                    'text': text,
                    'center_x': center_x,
                    'center_y': center_y,
                    'y': y
                })
    
    # Sort by Y coordinate (top to bottom)
    results.sort(key=lambda x: x['y'])
    
    print("=" * 70)
    print("TEXT CONTAINING 'realestate' OR 'property'")
    print("=" * 70)
    print(f"{'Text':<40} {'Center X':<10} {'Center Y':<10}")
    print("-" * 70)
    
    for r in results:
        print(f"{r['text']:<40} {r['center_x']:<10} {r['center_y']:<10}")
    
    print("\n" + "=" * 70)
    print("ANALYSIS:")
    print("=" * 70)
    
    # Find just realestate
    realestate_only = [r for r in results if 'realestate' in r['text'].lower() and 'property' not in r['text'].lower()]
    property_only = [r for r in results if 'property' in r['text'].lower() and 'realestate' not in r['text'].lower()]
    
    print(f"\nMatches with 'realestate' (not 'property'): {len(realestate_only)}")
    for r in realestate_only:
        print(f"  - {r['text']} at Y={r['center_y']}")
    
    print(f"\nMatches with 'property' (not 'realestate'): {len(property_only)}")
    for r in property_only:
        print(f"  - {r['text']} at Y={r['center_y']}")
    
    if realestate_only and property_only:
        first_realestate_y = realestate_only[0]['center_y']
        first_property_y = property_only[0]['center_y']
        
        print(f"\nFirst 'realestate' appears at Y={first_realestate_y}")
        print(f"First 'property' appears at Y={first_property_y}")
        
        if first_property_y < first_realestate_y:
            print("\n⚠️  WARNING: property.com.au appears ABOVE realestate.com.au on the page!")
            print("This explains why clicking near 'realestate' text clicks property.com.au")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: venv/bin/python debug_ocr.py <screenshot_path>")
        sys.exit(1)
    
    debug_ocr(sys.argv[1])
