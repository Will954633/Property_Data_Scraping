#!/usr/bin/env python3
"""
Analyze Apollo State structure from Domain.com.au to find missing data fields
"""

import json
import re
import requests
from datetime import datetime

def fetch_and_analyze(url):
    """Fetch page and analyze Apollo state"""
    print(f"Fetching: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    html = response.text
    
    # Extract __NEXT_DATA__
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', 
                      html, re.DOTALL)
    
    if not match:
        print("ERROR: No __NEXT_DATA__ found!")
        return
    
    page_data = json.loads(match.group(1))
    apollo_state = page_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})
    
    print("=" * 80)
    print("SEARCHING FOR MISSING DATA IN APOLLO STATE")
    print("=" * 80)
    
    # Find Property object
    property_obj = None
    property_key = None
    for key, value in apollo_state.items():
        if key.startswith('Property:') and value.get('__typename') == 'Property':
            property_obj = value
            property_key = key
            break
    
    if not property_obj:
        print("ERROR: No Property object found!")
        return
    
    print(f"\nFound Property: {property_key}")
    print(f"Property object keys: {list(property_obj.keys())}\n")
    
    # 1. Search for rental data
    print("\n" + "=" * 80)
    print("1. SEARCHING FOR RENTAL DATA (weekly rent, yield)")
    print("=" * 80)
    
    rental_keywords = ['rent', 'yield', 'rental', 'week']
    for key, value in apollo_state.items():
        if isinstance(value, dict):
            for k, v in value.items():
                if any(kw in k.lower() for kw in rental_keywords):
                    print(f"\n{key} -> {k}:")
                    print(f"  Value: {v}")
    
    # Check property_obj specifically
    print("\n--- In Property object directly ---")
    for k, v in property_obj.items():
        if any(kw in k.lower() for kw in rental_keywords):
            print(f"{k}: {v}")
    
    # 2. Search for property type
    print("\n" + "=" * 80)
    print("2. SEARCHING FOR PROPERTY TYPE")
    print("=" * 80)
    
    type_keywords = ['type', 'category', 'propertyType']
    for key, value in apollo_state.items():
        if isinstance(value, dict):
            for k, v in value.items():
                if any(kw in k.lower() for kw in type_keywords) and isinstance(v, str):
                    print(f"\n{key} -> {k}:")
                    print(f"  Value: {v}")
    
    # Check property_obj
    print("\n--- In Property object directly ---")
    for k, v in property_obj.items():
        if any(kw in k.lower() for kw in type_keywords):
            print(f"{k}: {v}")
    
    # 3. Search for property timeline/history
    print("\n" + "=" * 80)
    print("3. SEARCHING FOR PROPERTY TIMELINE/HISTORY")
    print("=" * 80)
    
    history_keywords = ['listing', 'history', 'sale', 'sold', 'event']
    for key, value in apollo_state.items():
        if isinstance(value, dict):
            for k, v in value.items():
                if any(kw in k.lower() for kw in history_keywords):
                    if isinstance(v, list) and len(v) > 0:
                        print(f"\n{key} -> {k}:")
                        print(f"  Type: {type(v)}, Length: {len(v)}")
                        if len(v) > 0:
                            print(f"  First item: {v[0]}")
    
    # Check property_obj listings
    print("\n--- Property listings field ---")
    if 'listings' in property_obj:
        listings = property_obj['listings']
        print(f"Type: {type(listings)}, Length: {len(listings) if isinstance(listings, list) else 'N/A'}")
        if isinstance(listings, list) and len(listings) > 0:
            print(f"First listing: {listings[0]}")
    
    # 4. Search for land size
    print("\n" + "=" * 80)
    print("4. SEARCHING FOR LAND SIZE")
    print("=" * 80)
    
    land_keywords = ['land', 'area', 'size', 'sqm', 'm2']
    for key, value in apollo_state.items():
        if isinstance(value, dict):
            for k, v in value.items():
                if any(kw in k.lower() for kw in land_keywords):
                    print(f"\n{key} -> {k}:")
                    print(f"  Value: {v}")
    
    # 5. Show all top-level Apollo state keys
    print("\n" + "=" * 80)
    print("5. ALL TOP-LEVEL APOLLO STATE KEYS")
    print("=" * 80)
    
    for key in sorted(apollo_state.keys()):
        typename = apollo_state[key].get('__typename') if isinstance(apollo_state[key], dict) else None
        print(f"  {key}" + (f" (__typename: {typename})" if typename else ""))
    
    # 6. Deep dive into specific objects that might contain the data
    print("\n" + "=" * 80)
    print("6. ANALYZING SPECIFIC OBJECTS")
    print("=" * 80)
    
    # Check for Address objects
    for key, value in apollo_state.items():
        if isinstance(value, dict) and value.get('__typename') == 'Address':
            print(f"\nAddress object: {key}")
            print(json.dumps(value, indent=2))
    
    # Check for PropertyProfile objects
    for key, value in apollo_state.items():
        if isinstance(value, dict) and ('profile' in key.lower() or 'Profile' in key):
            print(f"\nProfile-related object: {key}")
            print(json.dumps(value, indent=2))
    
    # Save full Apollo state for manual inspection
    output_file = '03_Gold_Coast/apollo_state_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(apollo_state, f, indent=2)
    print(f"\n\nFull Apollo state saved to: {output_file}")


if __name__ == "__main__":
    # Analyze the example property
    url = "https://www.domain.com.au/property-profile/11-matina-street-biggera-waters-qld-4216"
    fetch_and_analyze(url)
