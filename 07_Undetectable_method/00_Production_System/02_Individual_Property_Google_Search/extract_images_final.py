#!/usr/bin/env python3
"""
Final working version - Extract images and floor plans from realestate.com.au HTML
"""

import json
import re

def extract_all_images(html_file):
    """Extract all property images and floor plans from HTML"""
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print(f"Analyzing {html_file}...\n")
    
    # Extract all image URLs from i2.au.reastatic.net (realestate.com.au CDN)
    # Pattern matches full HTTPS URLs to images
    url_patterns = [
        r'https://i2\.au\.reastatic\.net/[^\s\"\'\)]+\.(?:jpg|jpeg|png|webp)',
        r'https://rimgau\.reastatic\.net/[^\s\"\'\)]+\.(?:jpg|jpeg|png|webp)',
    ]
    
    all_urls = set()
    
    for pattern in url_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            print(f"✓ Pattern '{pattern[:50]}...': {len(matches)} matches")
            all_urls.update(matches)
    
    if not all_urls:
        print("✗ No image URLs found")
        return None, None
    
    print(f"\n✓ Total unique image URLs found: {len(all_urls)}")
    
    # Categorize images
    property_images = []
    floor_plans = []
    
    for url in sorted(all_urls):
        url_lower = url.lower()
        
        # Identify floor plans by URL patterns
        is_floorplan = any(keyword in url_lower for keyword in [
            'floorplan', 'floor-plan', 'floor_plan', 'floorplans'
        ])
        
        if is_floorplan:
            floor_plans.append({"url": url, "type": "floorplan"})
        else:
            property_images.append({"url": url, "type": "property_image"})
    
    return property_images, floor_plans

if __name__ == "__main__":
    import sys
    
    html_file = "batch_results/html/property_1_20251113_211854.html"
    
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    
    property_images, floor_plans = extract_all_images(html_file)
    
    if property_images is not None or floor_plans is not None:
        print(f"\n{'=' * 80}")
        print("EXTRACTION COMPLETE")
        print(f"{'=' * 80}")
        print(f"Property images: {len(property_images)}")
        print(f"Floor plans: {len(floor_plans)}")
        
        # Show samples
        if property_images:
            print(f"\nSample property image URLs:")
            for img in property_images[:5]:
                print(f"  • {img['url']}")
        
        if floor_plans:
            print(f"\nFloor plan URLs:")
            for fp in floor_plans:
                print(f"  • {fp['url']}")
        
        # Save results
        output = {
            "total_images": len(property_images) + len(floor_plans),
            "property_images_count": len(property_images),
            "floor_plans_count": len(floor_plans),
            "property_images": property_images,
            "floor_plans": floor_plans
        }
        
        with open("batch_results/extracted_images.json", 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved to batch_results/extracted_images.json")
    else:
        print("\n✗ Could not extract image data")
