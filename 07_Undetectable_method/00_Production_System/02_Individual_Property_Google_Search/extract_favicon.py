#!/usr/bin/env python3
"""
Extract and crop the favicon from favicon_reference.png
Creates a small template image of just the favicon
"""

import cv2
import numpy as np
from PIL import Image

def extract_favicon(input_path, output_path):
    """Extract the red favicon from the larger screenshot"""
    
    print(f"Loading image: {input_path}")
    img = cv2.imread(input_path)
    
    if img is None:
        print(f"✗ Could not load image")
        return False
    
    print(f"Image size: {img.shape[:2]} (height x width)")
    
    # Convert to RGB for color detection
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Define red color range (for the favicon)
    # The favicon has a distinctive red color
    lower_red = np.array([180, 50, 50], dtype=np.uint8)
    upper_red = np.array([255, 150, 150], dtype=np.uint8)
    
    # Create mask for red pixels
    mask = cv2.inRange(img_rgb, lower_red, upper_red)
    
    # Find contours of red regions
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("✗ No red regions found")
        return False
    
    print(f"Found {len(contours)} red regions")
    
    # Find the largest contour (should be the favicon)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get bounding box
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    print(f"\nLargest red region:")
    print(f"  Position: ({x}, {y})")
    print(f"  Size: {w}x{h} pixels")
    
    # Add small padding
    padding = 2
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(img.shape[1] - x, w + 2 * padding)
    h = min(img.shape[0] - y, h + 2 * padding)
    
    # Crop the favicon
    favicon = img[y:y+h, x:x+w]
    
    # Save the cropped favicon
    cv2.imwrite(output_path, favicon)
    
    print(f"\n✓ Favicon extracted and saved")
    print(f"  Output: {output_path}")
    print(f"  Size: {w}x{h} pixels")
    
    return True


if __name__ == "__main__":
    success = extract_favicon("favicon_reference.png", "favicon_small.png")
    
    if success:
        print("\n" + "=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print("\nSmall favicon template created: favicon_small.png")
        print("This can now be used for accurate template matching")
        print("\n" + "=" * 70 + "\n")
    else:
        print("\n✗ Failed to extract favicon")
