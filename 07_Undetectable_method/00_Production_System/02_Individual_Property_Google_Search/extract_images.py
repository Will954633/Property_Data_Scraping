#!/usr/bin/env python3
"""
Extract images and floor plans from realestate.com.au HTML
"""

import json
import re

def extract_photos_from_html(html_file):
    """Extract all photos and floor plans from HTML"""
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print(f"Analyzing {html_file}...\n")
    
    # Method 1: Try to find photos in ArgonautExchange or similar data structures
    # Pattern: look for "photos": [{...}] structures
    
    # First, find the large JSON object (usually ArgonautExchange or similar)
    patterns_to_try = [
        r'window\.ArgonautExchange\s*=\s*({.*?});?\s*</script>',
        r'window\.ARGONAUT\s*=\s*({.*?});?\s*</script>',
        r'window\.pageData\s*=\s*({.*?});?\s*</script>',
    ]
    
    photos_data = None
    
    for pattern in patterns_to_try:
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            print(f"✓ Found data with pattern: {pattern[:50]}...")
            for match_text in matches:
                # Now search within this JSON for photos
                # Look for "photos": [ array ] or "images": [ array ]
                photo_pattern = r'"photos"\s*:\s*(\[[^\]]*?\{[^\}]*?"fullUrl"[^\]]*?\])'
                photo_matches = re.findall(photo_pattern, match_text, re.DOTALL)
                
                if photo_matches:
                    print(f"  ✓ Found {len(photo_matches)} photo arrays")
                    # Try to parse the first one
                    for pm in photo_matches:
                        try:
                            # This might have truncated data, so let's try to extract it better
                            # Find the complete array by looking for matching brackets
                            start_idx = match_text.find('"photos":')
                            if start_idx != -1:
                                # Find the opening [
                                bracket_start = match_text.find('[', start_idx)
                                if bracket_start != -1:
                                    # Now find matching ]
                                    depth = 0
                                    i = bracket_start
                                    while i < len(match_text):
                                        if match_text[i] == '[':
                                            depth += 1
                                        elif match_text[i] == ']':
                                            depth -= 1
                                            if depth == 0:
                                                # Found matching bracket! 
                                                photos_json = match_text[bracket_start:i+1]
                                                try:
                                                    photos_data = json.loads(photos_json)
                                                    print(f"  ✓✓✓ Successfully parsed {len(photos_data)} photos!")
                                                    return photos_data
                                                except json.JSONDecodeError as e:
                                                    print(f"  ✗ JSON parse error: {e}")
                                                    print(f"  Sample: {photos_json[:200]}...")
                                                break
                                        i += 1
                        except Exception as e:
                            print(f"  ✗ Error extracting photos: {e}")
    
    # Method 2: Look directly in the HTML without parsing the full JSON
    print("\n→ Method 2: Direct regex search in HTML...")
    
    # Look for patterns like "fullUrl":"https://..."
    direct_pattern = r'"photos"\s*:\s*\[((?:\{[^}]*?"fullUrl"[^}]*?\}(?:,\s*)?)+)\]'
    direct_matches = re.findall(direct_pattern, html, re.DOTALL)
    
    if direct_matches:
        print(f"  Found {len(direct_matches)} potential photo arrays")
        for i, dm in enumerate(direct_matches[:3], 1):
            # Try to parse this as JSON array
            try:
                json_str = '[' + dm + ']'
                photos_data = json.loads(json_str)
                print(f"  ✓ Array {i}: Successfully parsed {len(photos_data)} photos!")
                return photos_data
            except:
                pass
    
    # Method 3: Extract individual photo objects
    print("\n→ Method 3: Extract individual photo URLs...")
    
    # Find all fullUrl entries
    url_pattern = r'"fullUrl"\s*:\s*"(https://[^"]+)"'
    urls = re.findall(url_pattern, html)
    
    if urls:
        print(f"  Found {len(urls)} image URLs")
        # Create simplified photo objects
        photos_data = [{"fullUrl": url} for url in urls if '.jpg' in url or '.png' in url or '.webp' in url]
        print(f"  ✓ Created {len(photos_data)} photo objects")
        return photos_data
    
    return None

def categorize_images(photos_data):
    """Separate property images from floor plans"""
    
    property_images = []
    floor_plans = []
    
    for photo in photos_data:
        url = photo.get('fullUrl', photo.get('url', ''))
        
        # Check if it's a floor plan based on URL or metadata
        is_floorplan = False
        
        # Check URL for floor plan indicators
        if url and ('floorplan' in url.lower() or 'floor-plan' in url.lower() or 'floor_plan' in url.lower()):
            is_floorplan = True
        
        # Check other fields
        for key, value in photo.items():
            if isinstance(value, str):
                value_lower = value.lower()
                if 'floor' in value_lower and 'plan' in value_lower:
                    is_floorplan = True
                    break
        
        if is_floorplan:
            floor_plans.append(photo)
        else:
            property_images.append(photo)
    
    return property_images, floor_plans

if __name__ == "__main__":
    import sys
    
    html_file = "batch_results/html/property_1_20251113_211854.html"
    
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    
    photos_data = extract_photos_from_html(html_file)
    
    if photos_data:
        print(f"\n{'=' * 80}")
        print("SUCCESS! EXTRACTED IMAGE DATA")
        print(f"{'=' * 80}")
        print(f"Total images: {len(photos_data)}")
        
        # Categorize
        property_images, floor_plans = categorize_images(photos_data)
        
        print(f"\nProperty images: {len(property_images)}")
        print(f"Floor plans: {len(floor_plans)}")
        
        # Show samples
        if property_images:
            print(f"\nSample property image URLs:")
            for img in property_images[:3]:
                print(f"  • {img.get('fullUrl', img.get('url', 'N/A'))[:100]}...")
        
        if floor_plans:
            print(f"\nFloor plan URLs:")
            for fp in floor_plans:
                print(f"  • {fp.get('fullUrl', fp.get('url', 'N/A'))}")
        
        # Save results
        output = {
            "total_images": len(photos_data),
            "property_images_count": len(property_images),
            "floor_plans_count": len(floor_plans),
            "property_images": property_images,
            "floor_plans": floor_plans
        }
        
        with open("batch_results/extracted_images.json", 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved to batch_results/extracted_images.json")
    else:
        print("\n✗ Could not extract photo data")
