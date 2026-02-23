#!/usr/bin/env python3
"""
Analyze HTML to extract image URLs and floor plans
"""

import json
import re
from bs4 import BeautifulSoup

def analyze_html_for_images(html_file):
    """Analyze HTML to find all image URLs and identify floor plans"""
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print(f"Analyzing {html_file}...")
    print(f"HTML size: {len(html):,} chars\n")
    
    # Look for lightbox/gallery data structures
    print("=" * 80)
    print("SEARCHING FOR IMAGE DATA STRUCTURES")
    print("=" * 80)
    
    # 1. Check for JSON-LD script tags
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    print(f"\n1. Found {len(json_ld_scripts)} JSON-LD script tags")
    for i, script in enumerate(json_ld_scripts[:3], 1):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if 'image' in data or 'photo' in data:
                    print(f"   Script {i} has image/photo data")
                    print(f"   Keys: {list(data.keys())[:10]}")
        except:
            pass
    
    # 2. Check for script tags with window object assignments
    all_scripts = soup.find_all('script')
    print(f"\n2. Checking {len(all_scripts)} script tags for window object data...")
    
    image_data_found = False
    for script in all_scripts:
        if script.string:
            # Look for lightbox or gallery data
            if 'lightbox' in script.string.lower() or 'gallery' in script.string.lower():
                print(f"\n   ✓ Found script with 'lightbox' or 'gallery' text")
                # Extract a sample
                sample = script.string[:500]
                print(f"   Sample: {sample}...")
                image_data_found = True
                
            # Look for photo/image arrays
            if 'photos' in script.string or 'images' in script.string:
                if '[{' in script.string or '[{"' in script.string:
                    print(f"\n   ✓ Found script with photo/image array")
                    # Try to extract JSON data
                    json_matches = re.findall(r'(?:photos|images)\s*[:=]\s*(\[.*?\])', script.string, re.DOTALL)
                    if json_matches:
                        print(f"   Found {len(json_matches)} potential image arrays")
                        for j, match in enumerate(json_matches[:2], 1):
                            try:
                                # Try to parse as JSON
                                data = json.loads(match)
                                if isinstance(data, list) and len(data) > 0:
                                    print(f"   Array {j}: {len(data)} items")
                                    if isinstance(data[0], dict):
                                        print(f"   Sample keys: {list(data[0].keys())[:10]}")
                                        if 'url' in data[0] or 'src' in data[0]:
                                            print(f"   ✓✓✓ FOUND IMAGE URL STRUCTURE!")
                                            image_data_found = True
                            except:
                                pass
    
    # 3. Look for specific window assignments (common patterns on realestate.com.au)
    print(f"\n3. Looking for window.ARGONAUT or similar data structures...")
    window_patterns = [
        r'window\.ARGONAUT[^=]*=\s*(\{.*?\});',
        r'window\.ArgonautExperiments[^=]*=\s*(\{.*?\});',
        r'window\.pageData[^=]*=\s*(\{.*?\});',
        r'window\.listingPhotos[^=]*=\s*(\[.*?\]);',
    ]
    
    for pattern in window_patterns:
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            print(f"   Found {len(matches)} matches for pattern: {pattern[:40]}...")
            for match in matches[:1]:
                try:
                    # Try to see if it contains image data
                    if 'photo' in match.lower() or 'image' in match.lower():
                        print(f"   ✓ Contains photo/image references")
                        print(f"   Size: {len(match):,} chars")
                except:
                    pass
    
    # 4. Look for <img> tags with data attributes
    print(f"\n4. Analyzing <img> tags...")
    img_tags = soup.find_all('img')
    print(f"   Found {len(img_tags)} <img> tags")
    
    # Sample first few img tags
    for i, img in enumerate(img_tags[:5], 1):
        attrs = img.attrs
        print(f"   Img {i}: {list(attrs.keys())[:10]}")
        if 'src' in attrs:
            src = attrs['src']
            if 'realestate' in src or 'cloudinary' in src or 'imgix' in src:
                print(f"      src: {src[:100]}...")
    
    # 5. Look for data-testid or class names related to gallery
    print(f"\n5. Looking for gallery/lightbox elements...")
    gallery_elements = soup.find_all(attrs={'data-testid': re.compile(r'gallery|photo|image', re.I)})
    print(f"   Found {len(gallery_elements)} elements with gallery/photo/image data-testid")
    
    lightbox_elements = soup.find_all(class_=re.compile(r'lightbox|gallery|carousel', re.I))
    print(f"   Found {len(lightbox_elements)} elements with lightbox/gallery/carousel class")
    
    # 6. Specific search for floor plan indicators
    print(f"\n" + "=" * 80)
    print("SEARCHING FOR FLOOR PLAN INDICATORS")
    print("=" * 80)
    
    floorplan_patterns = [
        r'floor.*plan',
        r'floorplan',
        r'plan.*floor',
    ]
    
    for pattern in floorplan_patterns:
        # Search in HTML text
        matches = re.finditer(pattern, html, re.IGNORECASE)
        match_list = list(matches)
        if match_list:
            print(f"\n   Pattern '{pattern}': {len(match_list)} matches")
            # Show context around first match
            if match_list:
                pos = match_list[0].start()
                context = html[max(0, pos-100):min(len(html), pos+100)]
                print(f"   Context: ...{context}...")
    
    # Look for elements with floor plan in their attributes
    floorplan_elements = soup.find_all(attrs={
        'data-testid': re.compile(r'floor.*plan', re.I)
    })
    print(f"\n   Found {len(floorplan_elements)} elements with floor plan data-testid")
    
    floorplan_class = soup.find_all(class_=re.compile(r'floor.*plan', re.I))
    print(f"   Found {len(floorplan_class)} elements with floor plan class")
    
    # 7. Try to extract actual structured data
    print(f"\n" + "=" * 80)
    print("ATTEMPTING TO EXTRACT STRUCTURED IMAGE DATA")
    print("=" * 80)
    
    # Look for the most common pattern: window.ARGONAUT object
    argonaut_match = re.search(r'window\.ARGONAUT\s*=\s*(\{.*?\n\s*\});', html, re.DOTALL)
    if argonaut_match:
        print("\n✓ Found window.ARGONAUT object")
        try:
            # This might be too large, so let's look for specific keys
            argonaut_text = argonaut_match.group(1)
            
            # Look for photos/images array within ARGONAUT
            photos_match = re.search(r'"photos"\s*:\s*(\[.*?\])', argonaut_text, re.DOTALL)
            if photos_match:
                print("   ✓ Found 'photos' array in ARGONAUT")
                try:
                    photos_data = json.loads(photos_match.group(1))
                    print(f"   Photos array has {len(photos_data)} items")
                    if photos_data and isinstance(photos_data[0], dict):
                        print(f"   Sample photo keys: {list(photos_data[0].keys())}")
                        print(f"   Sample photo: {json.dumps(photos_data[0], indent=2)[:500]}")
                        return photos_data
                except Exception as e:
                    print(f"   Error parsing photos array: {e}")
        except Exception as e:
            print(f"   Error analyzing ARGONAUT: {e}")
    
    return None

if __name__ == "__main__":
    import sys
    
    # Use most recent HTML file
    html_file = "batch_results/html/property_1_20251113_211854.html"
    
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    
    photos_data = analyze_html_for_images(html_file)
    
    if photos_data:
        print(f"\n{'=' * 80}")
        print("SUCCESS! EXTRACTED IMAGE DATA")
        print(f"{'=' * 80}")
        print(f"Total images: {len(photos_data)}")
        
        # Categorize images
        property_images = []
        floor_plans = []
        
        for photo in photos_data:
            # Check if it's a floor plan
            if isinstance(photo, dict):
                # Look for floor plan indicators in the photo metadata
                is_floorplan = False
                for key, value in photo.items():
                    if isinstance(value, str) and 'floor' in value.lower() and 'plan' in value.lower():
                        is_floorplan = True
                        break
                
                if is_floorplan:
                    floor_plans.append(photo)
                else:
                    property_images.append(photo)
        
        print(f"Property images: {len(property_images)}")
        print(f"Floor plans: {len(floor_plans)}")
        
        # Save to JSON
        output = {
            "total_images": len(photos_data),
            "property_images_count": len(property_images),
            "floor_plans_count": len(floor_plans),
            "property_images": property_images,
            "floor_plans": floor_plans,
            "all_photos": photos_data
        }
        
        with open("batch_results/extracted_images.json", 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Saved to batch_results/extracted_images.json")
