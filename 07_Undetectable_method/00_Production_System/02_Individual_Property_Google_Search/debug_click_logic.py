#!/usr/bin/env python3
"""
Debug the click coordinate calculation to see exactly what's happening
"""

import sys
import numpy as np
from PIL import Image
import pytesseract
import math

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def debug_click(screenshot_path, favicon_path):
    """Debug exactly what pixel we're selecting and why"""
    
    # Extract red color from favicon
    img = Image.open(favicon_path).convert('RGB')
    pixels = np.array(img)
    pixels_flat = pixels.reshape(-1, 3)
    red_pixels = pixels_flat[(pixels_flat[:, 0] > pixels_flat[:, 1]) & 
                              (pixels_flat[:, 0] > pixels_flat[:, 2])]
    target_color = tuple(np.mean(red_pixels, axis=0).astype(int))
    print(f"Target red color: RGB{target_color}\n")
    
    # Find matching red pixels in screenshot
    img = Image.open(screenshot_path).convert('RGB')
    pixels = np.array(img)
    
    COLOR_TOLERANCE = 30
    r_diff = np.abs(pixels[:, :, 0] - target_color[0])
    g_diff = np.abs(pixels[:, :, 1] - target_color[1])
    b_diff = np.abs(pixels[:, :, 2] - target_color[2])
    
    matches = (r_diff <= COLOR_TOLERANCE) & (g_diff <= COLOR_TOLERANCE) & (b_diff <= COLOR_TOLERANCE)
    y_coords, x_coords = np.where(matches)
    red_pixels = list(zip(x_coords, y_coords))
    
    print(f"Found {len(red_pixels)} matching red pixels\n")
    
    # Run OCR
    img = Image.open(screenshot_path)
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    ocr_results = []
    n_boxes = len(ocr_data['text'])
    
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if text and 'realestate' in text.lower():
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            
            ocr_results.append({
                'text': text,
                'center_x': x + w // 2,
                'center_y': y + h // 2
            })
    
    print("=" * 70)
    print("REALESTATE TEXT MATCHES:")
    print("=" * 70)
    for i, match in enumerate(ocr_results, 1):
        print(f"{i}. '{match['text']}' at ({match['center_x']}, {match['center_y']})")
    
    # Sort and find URL match
    domain_matches_sorted = sorted(ocr_results, key=lambda x: x['center_y'])
    
    url_match = None
    for match in domain_matches_sorted:
        if 'https' in match['text'].lower() or 'www' in match['text'].lower():
            url_match = match
            break
    
    primary_domain = url_match if url_match else domain_matches_sorted[0]
    
    print(f"\nSelected primary target: '{primary_domain['text']}'")
    print(f"  Center: ({primary_domain['center_x']}, {primary_domain['center_y']})")
    
    # Find closest red pixel
    domain_center = (primary_domain['center_x'], primary_domain['center_y'])
    
    closest_pixel = None
    min_distance = float('inf')
    
    for red_pixel in red_pixels:
        dist = calculate_distance(red_pixel, domain_center)
        if dist < min_distance:
            min_distance = dist
            closest_pixel = red_pixel
    
    print(f"\nClosest red pixel: {closest_pixel}")
    print(f"  Distance: {min_distance:.1f}px")
    
    # Show the top 5 closest red pixels for comparison
    print("\nTop 5 closest red pixels to primary target:")
    distances = [(pixel, calculate_distance(pixel, domain_center)) for pixel in red_pixels]
    distances.sort(key=lambda x: x[1])
    
    for i, (pixel, dist) in enumerate(distances[:5], 1):
        print(f"  {i}. {pixel} - {dist:.1f}px away")
    
    print("\n" + "=" * 70)
    print("CLICK COORDINATE:")
    print("=" * 70)
    print(f"Will click at: {closest_pixel}")
    print(f"This is {min_distance:.1f}px from '{primary_domain['text']}'")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: venv/bin/python debug_click_logic.py <screenshot> <favicon>")
        sys.exit(1)
    
    debug_click(sys.argv[1], sys.argv[2])
