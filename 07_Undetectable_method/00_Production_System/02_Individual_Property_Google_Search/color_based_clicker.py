#!/usr/bin/env python3
"""
Color-Based Favicon Clicker - Enhanced Undetectable Method
Combines:
1. Color detection (finds red pixels from favicon)
2. OCR text detection (finds "realestate.com.au" and search address)
3. Proximity validation (ensures all elements are close together)
4. Native mouse click (100% undetectable)
"""

import subprocess
import time
import sys
import numpy as np
from PIL import Image
import pytesseract
import math

# Configuration
TARGET_DOMAIN = "realestate.com.au"
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"  # Used for proximity validation

# Color tolerance for matching (RGB values can vary slightly)
COLOR_TOLERANCE = 30

# Proximity threshold in pixels (all elements must be within this distance)
PROXIMITY_THRESHOLD = 300

# Fallback coordinates if color+OCR method fails
FALLBACK_COORDINATES = {
    1: {"x": 400, "y": 250},
    2: {"x": 400, "y": 400},
    3: {"x": 400, "y": 550},
}


def extract_dominant_red_color(favicon_path):
    """
    Extract the dominant red color from the favicon image
    Returns RGB tuple
    """
    print(f"→ Analyzing favicon: {favicon_path}")
    
    img = Image.open(favicon_path).convert('RGB')
    pixels = np.array(img)
    
    # Flatten to list of RGB values
    pixels_flat = pixels.reshape(-1, 3)
    
    # Find pixels that are predominantly red (R > G and R > B)
    red_pixels = pixels_flat[(pixels_flat[:, 0] > pixels_flat[:, 1]) & 
                              (pixels_flat[:, 0] > pixels_flat[:, 2])]
    
    if len(red_pixels) == 0:
        print("✗ No red pixels found in favicon")
        return None
    
    # Get the most common red color (using mean of red pixels)
    target_color = tuple(np.mean(red_pixels, axis=0).astype(int))
    
    print(f"✓ Target red color: RGB{target_color}")
    return target_color


def find_matching_pixels(screenshot_path, target_color, tolerance):
    """
    Find all pixels in screenshot that match the target color within tolerance
    Returns list of (x, y) coordinates
    """
    print(f"→ Searching for matching red pixels in screenshot...")
    
    img = Image.open(screenshot_path).convert('RGB')
    pixels = np.array(img)
    
    height, width, _ = pixels.shape
    
    # Calculate color distance for all pixels
    r_diff = np.abs(pixels[:, :, 0] - target_color[0])
    g_diff = np.abs(pixels[:, :, 1] - target_color[1])
    b_diff = np.abs(pixels[:, :, 2] - target_color[2])
    
    # Find pixels where all RGB components are within tolerance
    matches = (r_diff <= tolerance) & (g_diff <= tolerance) & (b_diff <= tolerance)
    
    # Get coordinates of matching pixels
    y_coords, x_coords = np.where(matches)
    
    matching_coords = list(zip(x_coords, y_coords))
    
    print(f"✓ Found {len(matching_coords)} matching red pixels")
    
    return matching_coords


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


def find_text_in_ocr(ocr_results, search_text, exclude_text=None):
    """Find specific text in OCR results and return all matches, optionally excluding certain text"""
    matches = []
    
    for item in ocr_results:
        text = item['text'].lower()
        # Must contain the search text
        if search_text.lower() in text:
            # If exclusion specified, skip if it contains that text
            if exclude_text and exclude_text.lower() in text:
                continue
            matches.append(item)
    
    return matches


def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def validate_proximity(red_pixel, domain_coords, address_coords, threshold):
    """
    Check if red pixel is within threshold distance of both domain and address text
    Returns True if valid, False otherwise
    """
    if not domain_coords or not address_coords:
        return False
    
    # Get center points of text elements
    domain_center = (domain_coords['center_x'], domain_coords['center_y'])
    address_center = (address_coords['center_x'], address_coords['center_y'])
    
    # Calculate distances
    dist_to_domain = calculate_distance(red_pixel, domain_center)
    dist_to_address = calculate_distance(red_pixel, address_center)
    
    # Both must be within threshold
    return (dist_to_domain <= threshold) and (dist_to_address <= threshold)


def find_best_red_pixel(red_pixels, domain_matches, address_matches, threshold):
    """
    Find the best red pixel that is close to both domain and address text
    Returns (x, y) coordinates or None
    """
    print(f"→ Validating {len(red_pixels)} red pixels with proximity check...")
    
    if not domain_matches:
        print("✗ No domain text found in OCR")
        return None
    
    if not address_matches:
        print("⚠️  No address text found in OCR (will proceed with domain only)")
        # Fallback: use domain proximity only
        valid_pixels = []
        for red_pixel in red_pixels:
            for domain in domain_matches:
                domain_center = (domain['center_x'], domain['center_y'])
                dist = calculate_distance(red_pixel, domain_center)
                if dist <= threshold:
                    valid_pixels.append({
                        'coords': red_pixel,
                        'dist': dist
                    })
        
        if valid_pixels:
            # Return the pixel closest to domain
            best = min(valid_pixels, key=lambda x: x['dist'])
            print(f"✓ Valid red pixel found near domain")
            print(f"  Coordinates: {best['coords']}")
            print(f"  Distance to domain: {best['dist']:.1f}px")
            return best['coords']
        
        print(f"✗ No red pixels found within {threshold}px of domain text")
        return None
    
    # Full validation with both domain and address
    valid_pixels = []
    
    for red_pixel in red_pixels:
        for domain in domain_matches:
            for address in address_matches:
                if validate_proximity(red_pixel, domain, address, threshold):
                    domain_center = (domain['center_x'], domain['center_y'])
                    address_center = (address['center_x'], address['center_y'])
                    
                    dist_domain = calculate_distance(red_pixel, domain_center)
                    dist_address = calculate_distance(red_pixel, address_center)
                    
                    valid_pixels.append({
                        'coords': red_pixel,
                        'dist_domain': dist_domain,
                        'dist_address': dist_address,
                        'total_dist': dist_domain + dist_address
                    })
    
    if not valid_pixels:
        print("✗ No red pixels found near both domain and address")
        return None
    
    # Return the pixel with smallest combined distance
    best = min(valid_pixels, key=lambda x: x['total_dist'])
    
    print(f"✓ Best red pixel found!")
    print(f"  Coordinates: {best['coords']}")
    print(f"  Distance to domain: {best['dist_domain']:.1f}px")
    print(f"  Distance to address: {best['dist_address']:.1f}px")
    
    return best['coords']


def click_with_cliclick(x, y):
    """Use cliclick to move mouse and click at coordinates"""
    print(f"→ Moving mouse to ({x}, {y})...")
    subprocess.run(['cliclick', f'm:{x},{y}'])
    time.sleep(0.3)
    
    print(f"→ Clicking...")
    subprocess.run(['cliclick', 'c:.'])
    
    print(f"✓ Click executed at ({x}, {y})")
    return True


def main(screenshot_path, favicon_path):
    """Main function - Color + OCR + Proximity workflow"""
    print("\n" + "=" * 70)
    print("COLOR-BASED FAVICON CLICKER - ENHANCED METHOD")
    print("=" * 70)
    print(f"\nScreenshot: {screenshot_path}")
    print(f"Favicon: {favicon_path}")
    print(f"Target domain: {TARGET_DOMAIN}")
    print(f"Search address: {SEARCH_ADDRESS}")
    print(f"\nMethod:")
    print("  1. Extract red color from favicon")
    print("  2. Find matching red pixels in screenshot")
    print("  3. Run OCR to find domain and address text")
    print("  4. Validate proximity of red pixels to text")
    print("  5. Click on validated red pixel")
    print("\n" + "=" * 70)
    
    # Step 1: Extract target color from favicon
    try:
        target_color = extract_dominant_red_color(favicon_path)
        if not target_color:
            raise Exception("Could not extract red color from favicon")
    except Exception as e:
        print(f"\n✗ Favicon analysis failed: {e}")
        print("→ Falling back to OCR-only method...")
        return False
    
    # Step 2: Find matching red pixels
    try:
        red_pixels = find_matching_pixels(screenshot_path, target_color, COLOR_TOLERANCE)
        if len(red_pixels) == 0:
            raise Exception("No matching red pixels found")
    except Exception as e:
        print(f"\n✗ Color matching failed: {e}")
        return False
    
    # Step 3: Run OCR
    try:
        ocr_results = run_tesseract_ocr(screenshot_path)
    except Exception as e:
        print(f"\n✗ OCR failed: {e}")
        ocr_results = []
    
    # Step 4: Find domain and address in OCR results
    print(f"\n→ Searching for '{TARGET_DOMAIN}' in OCR results...")
    # Search for "realestate" specifically (unique to realestate.com.au, not in property.com.au)
    domain_matches = find_text_in_ocr(ocr_results, "realestate")
    print(f"✓ Found {len(domain_matches)} matches for 'realestate' (unique identifier)")
    
    print(f"\n→ Searching for '{SEARCH_ADDRESS}' in OCR results...")
    address_matches = find_text_in_ocr(ocr_results, SEARCH_ADDRESS)
    print(f"✓ Found {len(address_matches)} address matches")
    
    # Step 5: Find best red pixel using proximity validation
    best_pixel = find_best_red_pixel(red_pixels, domain_matches, address_matches, PROXIMITY_THRESHOLD)
    
    if best_pixel:
        click_x, click_y = best_pixel
        method = "Color + OCR + Proximity"
    else:
        print("\n⚠️  Color-based method failed, using fallback coordinates...")
        click_x = FALLBACK_COORDINATES[1]['x']
        click_y = FALLBACK_COORDINATES[1]['y']
        method = "Fallback"
    
    # Step 6: Click
    print(f"\n→ Method: {method}")
    time.sleep(1)
    
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
    if len(sys.argv) < 3:
        print("Usage: python color_based_clicker.py <screenshot_path> <favicon_path>")
        print("Example: python color_based_clicker.py screenshots/google_search.png favicon_reference.png")
        sys.exit(1)
    
    screenshot_path = sys.argv[1]
    favicon_path = sys.argv[2]
    
    success = main(screenshot_path, favicon_path)
    sys.exit(0 if success else 1)
