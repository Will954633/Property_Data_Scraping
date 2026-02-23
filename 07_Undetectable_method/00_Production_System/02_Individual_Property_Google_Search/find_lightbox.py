#!/usr/bin/env python3
"""
Find lightbox/gallery photo data in realestate.com.au HTML
"""

import re
import json

def find_lightbox_data(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print(f"Analyzing {len(html):,} chars of HTML\n")
    
    # Strategy 1: Look for window.ARGONAUT or similar structures
    print("=" * 80)
    print("STRATEGY 1: Finding window object data")
    print("=" * 80)
    
    # Find all window.XXX = {...} assignments
    window_pattern = r'window\.([\w]+)\s*=\s*({.*?});?\s*(?:</script>|var |window\.|$)'
    window_matches = re.finditer(window_pattern, html, re.DOTALL)
    
    for match in window_matches:
        var_name = match.group(1)
        var_content = match.group(2)
        
        # Check if this contains photo/image data
        if any(keyword in var_content.lower() for keyword in['photo', 'image', 'media', 'gallery']):
            print(f"\n✓ Found: window.{var_name}")
            print(f"  Size: {len(var_content):,} chars")
            
            # Try to parse as JSON
            try:
                data = json.loads(var_content)
                # Look for photos/media arrays
                def find_photo_arrays(obj, path=""):
                    results = []
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            new_path = f"{path}.{key}" if path else key
                            if key.lower() in ['photos', 'media', 'images', 'gallery']:
                                if isinstance(value, list):
                                    results.append((new_path, value))
                            results.extend(find_photo_arrays(value, new_path))
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            results.extend(find_photo_arrays(item, f"{path}[{i}]"))
                    return results
                
                photo_arrays = find_photo_arrays(data)
                if photo_arrays:
                    for path, array in photo_arrays:
                        print(f"  → Found photo array at: {path}")
                        print(f"     Length: {len(array)}")
                        if array and isinstance(array[0], dict):
                            print(f"     Sample keys: {list(array[0].keys())[:10]}")
                            print(f"     Sample: {json.dumps(array[0], indent=6)[:300]}...")
                    return photo_arrays[0][1]  # Return first photo array
            except json.JSONDecodeError:
                print(f"  ✗ Could not parse as JSON")
    
    # Strategy 2: Search for specific JSON structures in script tags
    print("\n" + "=" * 80)
    print("STRATEGY 2: Searching script tags for photo data")
    print("=" * 80)
    
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    print(f"Found {len(scripts)} script tags")
    
    for i, script in enumerate(scripts):
        if 'photos' in script.lower() or 'media' in script.lower():
            # Try to find JSON arrays
            json_arrays = re.findall(r'\[[^\[\]]*\{[^\}]*"(?:url|mainImage|fullUrl)"[^\}]*\}[^\[\]]*\]', script, re.DOTALL)
            if json_arrays:
                print(f"\nScript {i}: Found {len(json_arrays)} potential photo arrays")
                for j, arr in enumerate(json_arrays[:2]):
                    try:
                        data = json.loads(arr)
                        if isinstance(data, list) and len(data) > 0:
                            print(f"  Array {j}: {len(data)} items")
                            if isinstance(data[0], dict):
                                print(f"  Keys: {list(data[0].keys())}")
                                return data
                    except:
                        pass
    
    return None

if __name__ == "__main__":
    html_file = "batch_results/html/property_1_20251113_212448.html"
    photos = find_lightbox_data(html_file)
    
    if photos:
        print(f"\n{'=' * 80}")
        print("SUCCESS!")
        print(f"{'=' * 80}")
        print(f"Found {len(photos)} photos in lightbox")
        
        # Show sample
        if photos:
            print(f"\nSample photo object:")
            print(json.dumps(photos[0], indent=2))
    else:
        print("\n✗ Could not find lightbox photo data")
