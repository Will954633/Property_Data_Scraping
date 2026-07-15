#!/usr/bin/env python3
"""
Analyze HTML for Listing Date Data
Last Updated: 31/01/2026, 10:50 am (Brisbane Time)

PURPOSE:
Deep dive into HTML to find listing date data in JSON structures
"""

import json
import re
from bs4 import BeautifulSoup

def extract_json_from_html(html_file):
    """Extract all JSON structures from HTML"""
    print("="*80)
    print("ANALYZING HTML FOR LISTING DATE DATA")
    print("="*80)
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Look for __APOLLO_STATE__
    print("\n1. Searching for __APOLLO_STATE__...")
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and '__APOLLO_STATE__' in script.string:
            print("   ✓ Found __APOLLO_STATE__!")
            # Extract the JSON
            match = re.search(r'__APOLLO_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
            if match:
                try:
                    apollo_data = json.loads(match.group(1))
                    print(f"   ✓ Parsed JSON with {len(apollo_data)} keys")
                    
                    # Search for date-related fields
                    print("\n   Searching for date-related fields...")
                    search_terms = ['date', 'listed', 'first', 'days', 'market', 'created', 'published']
                    
                    for key, value in apollo_data.items():
                        if isinstance(value, dict):
                            for field, field_value in value.items():
                                field_lower = str(field).lower()
                                if any(term in field_lower for term in search_terms):
                                    print(f"\n   📅 Found: {key}.{field}")
                                    print(f"      Value: {field_value}")
                    
                    # Save full apollo state for inspection
                    with open('apollo_state_analysis.json', 'w') as f:
                        json.dump(apollo_data, f, indent=2)
                    print("\n   ✓ Saved full data to apollo_state_analysis.json")
                    
                except Exception as e:
                    print(f"   ✗ Error parsing JSON: {e}")
    
    # 2. Look for other JSON structures
    print("\n2. Searching for other JSON structures...")
    for script in scripts:
        if script.string and script.get('type') == 'application/ld+json':
            print("   ✓ Found application/ld+json!")
            try:
                ld_json = json.loads(script.string)
                print(f"   Type: {ld_json.get('@type', 'Unknown')}")
                
                # Look for date fields
                for key, value in ld_json.items():
                    if 'date' in key.lower() or 'published' in key.lower():
                        print(f"   📅 {key}: {value}")
                
                # Save for inspection
                with open('ld_json_analysis.json', 'w') as f:
                    json.dump(ld_json, f, indent=2)
                print("   ✓ Saved to ld_json_analysis.json")
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
    
    # 3. Search for date patterns in all text
    print("\n3. Searching for date patterns in page text...")
    page_text = soup.get_text()
    
    # Look for various date patterns
    patterns = [
        (r'listed.*?(\d{1,2}\s+\w+\s+\d{4})', 'Listed with full date'),
        (r'listed.*?(\d{1,2}\s+\w+)', 'Listed with day/month'),
        (r'(\d+)\s+days?\s+(?:on|ago)', 'Days on market'),
        (r'datePublished["\']?\s*:\s*["\']([^"\']+)', 'datePublished field'),
        (r'firstListed["\']?\s*:\s*["\']([^"\']+)', 'firstListed field'),
        (r'listedDate["\']?\s*:\s*["\']([^"\']+)', 'listedDate field'),
    ]
    
    for pattern, description in patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            print(f"\n   📅 {description}:")
            for match in matches[:5]:  # Show first 5 matches
                print(f"      {match}")
    
    # 4. Search raw HTML for date fields
    print("\n4. Searching raw HTML for date-related JSON fields...")
    date_patterns = [
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'"firstListed"\s*:\s*"([^"]+)"',
        r'"listedDate"\s*:\s*"([^"]+)"',
        r'"dateListed"\s*:\s*"([^"]+)"',
        r'"listingDate"\s*:\s*"([^"]+)"',
        r'"createdAt"\s*:\s*"([^"]+)"',
        r'"publishedAt"\s*:\s*"([^"]+)"',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, html)
        if matches:
            field_name = pattern.split('"')[1]
            print(f"\n   📅 Found {field_name}:")
            for match in matches[:3]:
                print(f"      {match}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nFiles created:")
    print("  - apollo_state_analysis.json (if found)")
    print("  - ld_json_analysis.json (if found)")
    print("\nCheck these files for the listing date data!")

if __name__ == "__main__":
    extract_json_from_html('test_property_page.html')
