#!/usr/bin/env python3
"""
Debug which text each red pixel is closest to
"""

import sys
import numpy as np
from PIL import Image
import pytesseract
import math

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def debug_pixel_owner(screenshot_path, favicon_path):
    """Show which text each red pixel is closest to"""
    
    # Extract red color
    img = Image.open(favicon_path).convert('RGB')
    pixels = np.array(img)
    pixels_flat = pixels.reshape(-1, 3)
    red_pixels_array = pixels_flat[(pixels_flat[:, 0] > pixels_flat[:, 1]) & 
                              (pixels_flat[:, 0] > pixels_flat[:, 2])]
    target_color = tuple(np.mean(red_pixels_array, axis=0).astype(int))
    
    # Find red pixels
    img = Image.open(screenshot_path).convert('RGB')
    pixels = np.array(img)
    
    COLOR_TOLERANCE = 30
    r_diff = np.abs(pixels[:, :, 0] - target_color[0])
    g_diff = np.abs(pixels[:, :, 1] - target_color[1])
    b_diff = np.abs(pixels[:, :, 2] - target_color[2])
    
    matches = (r_diff <= COLOR_TOLERANCE) & (g_diff <= COLOR_TOLERANCE) & (b_diff <= COLOR_TOLERANCE)
    y_coords, x_coords = np.where(matches)
    red_pixels = list(zip(x_coords, y_coords))
    
    # Run OCR  
    img = Image.open(screenshot_path)
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    texts_of_interest = []
    n_boxes = len(ocr_data['text'])
    
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if text and ('realestate' in text.lower() or 'property' in text.lower()):
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            
            texts_of_interest.append({
                'text': text,
                'center_x': x + w // 2,
                'center_y': y + h // 2
            })
    
    # Analyze pixel at (507, 375)
    target_pixel = (507, 375)
    
    print("=" * 70)
    print(f"ANALYZING PIXEL AT {target_pixel}")
    print("=" * 70)
    print("\nDistances to all relevant text:")
    
    distances = []
    for text_match in texts_of_interest:
        center = (text_match['center_x'], text_match['center_y'])
        dist = calculate_distance(target_pixel, center)
        distances.append({
            'text': text_match['text'],
            'center': center,
            'distance': dist
        })
    
    # Sort by distance
    distances.sort(key=lambda x: x['distance'])
    
    for i, d in enumerate(distances[:10], 1):
        print(f"{i}. '{d['text']}' at {d['center']} - {d['distance']:.1f}px away")
    
    print("\n" + "=" * 70)
    print("CONCLUSION:")
    print("=" * 70)
    closest = distances[0]
    print(f"Pixel {target_pixel} is CLOSEST to: '{closest['text']}' ({closest['distance']:.1f}px)")
    
    if 'property' in closest['text'].lower() and 'realestate' not in closest['text'].lower():
        print("\n⚠️  THIS IS THE PROBLEM!")
        print("The red pixel we're clicking is closest to PROPERTY.COM.AU text!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: venv/bin/python debug_red_pixel_owner.py <screenshot> <favicon>")
        sys.exit(1)
    
    debug_pixel_owner(sys.argv[1], sys.argv[2])
