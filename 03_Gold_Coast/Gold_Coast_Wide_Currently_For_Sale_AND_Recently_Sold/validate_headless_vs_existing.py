#!/usr/bin/env python3
"""
Validation Script: Compare Headless vs Existing Data
Last Updated: 31/01/2026, 9:31 am (Brisbane Time)

Compares properties scraped by headless scraper (Gold_Coast_Currently_For_Sale.robina)
with existing data (property_data.properties_for_sale where suburb='Robina')

Validates:
- All properties found
- Core fields match
- Image counts match
- Floor plan counts match
- Data quality
"""

import json
from datetime import datetime
from pymongo import MongoClient
from typing import Dict, List, Tuple

# MongoDB connection
MONGODB_URI = 'mongodb://127.0.0.1:27017/'
client = MongoClient(MONGODB_URI)

# Databases
existing_db = client['property_data']
headless_db = client['Gold_Coast_Currently_For_Sale']

# Collections
existing_collection = existing_db['properties_for_sale']
headless_collection = headless_db['robina']

# Fields to compare
CORE_FIELDS = [
    'address', 'street_address', 'suburb', 'postcode',
    'bedrooms', 'bathrooms', 'carspaces', 'property_type',
    'price', 'listing_url'
]

ARRAY_FIELDS = [
    'property_images', 'floor_plans', 'inspection_times', 'features'
]


def get_existing_properties() -> Dict[str, Dict]:
    """Get all Robina properties from existing system"""
    properties = {}
    cursor = existing_collection.find({'suburb': 'Robina'})
    
    for prop in cursor:
        url = prop.get('listing_url')
        if url:
            properties[url] = prop
    
    return properties


def get_headless_properties() -> Dict[str, Dict]:
    """Get all properties from headless scraper"""
    properties = {}
    cursor = headless_collection.find({})
    
    for prop in cursor:
        url = prop.get('listing_url')
        if url:
            properties[url] = prop
    
    return properties


def compare_field(field: str, existing_val, headless_val) -> Tuple[bool, str]:
    """Compare a single field value"""
    if existing_val == headless_val:
        return True, "✓ Match"
    
    # Handle None vs empty string
    if (existing_val is None or existing_val == '') and (headless_val is None or headless_val == ''):
        return True, "✓ Match (both empty)"
    
    # Handle numeric comparisons
    if isinstance(existing_val, (int, float)) and isinstance(headless_val, (int, float)):
        if existing_val == headless_val:
            return True, "✓ Match"
    
    return False, f"✗ Mismatch: '{existing_val}' vs '{headless_val}'"


def validate_property(url: str, existing: Dict, headless: Dict) -> Dict:
    """Validate a single property"""
    result = {
        'url': url,
        'address': existing.get('address', 'Unknown'),
        'core_fields': {},
        'array_fields': {},
        'all_match': True
    }
    
    # Compare core fields
    for field in CORE_FIELDS:
        existing_val = existing.get(field)
        headless_val = headless.get(field)
        
        match, message = compare_field(field, existing_val, headless_val)
        result['core_fields'][field] = {
            'match': match,
            'message': message,
            'existing': existing_val,
            'headless': headless_val
        }
        
        if not match:
            result['all_match'] = False
    
    # Compare array fields (counts)
    for field in ARRAY_FIELDS:
        existing_arr = existing.get(field, [])
        headless_arr = headless.get(field, [])
        
        existing_count = len(existing_arr) if isinstance(existing_arr, list) else 0
        headless_count = len(headless_arr) if isinstance(headless_arr, list) else 0
        
        match = existing_count == headless_count
        result['array_fields'][field] = {
            'match': match,
            'existing_count': existing_count,
            'headless_count': headless_count,
            'message': f"✓ {existing_count} items" if match else f"✗ {existing_count} vs {headless_count}"
        }
        
        if not match:
            result['all_match'] = False
    
    return result


def main():
    """Main validation"""
    print("\n" + "="*80)
    print("VALIDATION: Headless vs Existing Data (Robina)")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nExisting DB: property_data.properties_for_sale (suburb='Robina')")
    print(f"Headless DB: Gold_Coast_Currently_For_Sale.robina")
    print("="*80)
    
    # Get properties
    print("\n→ Loading existing properties...")
    existing_props = get_existing_properties()
    print(f"  ✓ Found {len(existing_props)} properties")
    
    print("\n→ Loading headless properties...")
    headless_props = get_headless_properties()
    print(f"  ✓ Found {len(headless_props)} properties")
    
    # Check coverage
    print("\n" + "="*80)
    print("COVERAGE ANALYSIS")
    print("="*80)
    
    existing_urls = set(existing_props.keys())
    headless_urls = set(headless_props.keys())
    
    missing_in_headless = existing_urls - headless_urls
    extra_in_headless = headless_urls - existing_urls
    common_urls = existing_urls & headless_urls
    
    print(f"\nTotal in existing:  {len(existing_urls)}")
    print(f"Total in headless:  {len(headless_urls)}")
    print(f"Common properties:  {len(common_urls)}")
    print(f"Missing in headless: {len(missing_in_headless)}")
    print(f"Extra in headless:   {len(extra_in_headless)}")
    
    if missing_in_headless:
        print(f"\n⚠ Missing properties:")
        for url in list(missing_in_headless)[:5]:
            print(f"  - {existing_props[url].get('address', url)}")
        if len(missing_in_headless) > 5:
            print(f"  ... and {len(missing_in_headless) - 5} more")
    
    # Validate common properties
    print("\n" + "="*80)
    print("FIELD VALIDATION")
    print("="*80)
    
    validation_results = []
    perfect_matches = 0
    
    for url in sorted(common_urls):
        result = validate_property(url, existing_props[url], headless_props[url])
        validation_results.append(result)
        
        if result['all_match']:
            perfect_matches += 1
    
    # Summary
    print(f"\nValidated {len(validation_results)} properties")
    print(f"Perfect matches: {perfect_matches} ({perfect_matches/len(validation_results)*100:.1f}%)")
    print(f"With differences: {len(validation_results) - perfect_matches}")
    
    # Show mismatches
    mismatches = [r for r in validation_results if not r['all_match']]
    
    if mismatches:
        print(f"\n" + "="*80)
        print(f"PROPERTIES WITH DIFFERENCES ({len(mismatches)})")
        print("="*80)
        
        for result in mismatches[:5]:  # Show first 5
            print(f"\n{result['address']}")
            print(f"URL: {result['url']}")
            
            # Show core field mismatches
            core_mismatches = {k: v for k, v in result['core_fields'].items() if not v['match']}
            if core_mismatches:
                print(f"  Core fields:")
                for field, data in core_mismatches.items():
                    print(f"    {field}: {data['message']}")
            
            # Show array field mismatches
            array_mismatches = {k: v for k, v in result['array_fields'].items() if not v['match']}
            if array_mismatches:
                print(f"  Array fields:")
                for field, data in array_mismatches.items():
                    print(f"    {field}: {data['message']}")
        
        if len(mismatches) > 5:
            print(f"\n... and {len(mismatches) - 5} more properties with differences")
    
    # Save detailed report
    report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'existing_count': len(existing_urls),
            'headless_count': len(headless_urls),
            'common_count': len(common_urls),
            'missing_in_headless': len(missing_in_headless),
            'extra_in_headless': len(extra_in_headless),
            'perfect_matches': perfect_matches,
            'with_differences': len(validation_results) - perfect_matches
        },
        'missing_urls': list(missing_in_headless),
        'extra_urls': list(extra_in_headless),
        'validation_results': validation_results
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n" + "="*80)
    print(f"REPORT SAVED: {report_file}")
    print("="*80)
    
    # Final verdict
    print(f"\n" + "="*80)
    print("VALIDATION RESULT")
    print("="*80)
    
    if perfect_matches == len(validation_results) and len(missing_in_headless) == 0:
        print("\n✅ PERFECT MATCH!")
        print("   All properties found and all fields match.")
    elif perfect_matches / len(validation_results) > 0.95:
        print("\n✅ EXCELLENT MATCH!")
        print(f"   {perfect_matches/len(validation_results)*100:.1f}% of properties match perfectly.")
    elif perfect_matches / len(validation_results) > 0.80:
        print("\n⚠ GOOD MATCH")
        print(f"   {perfect_matches/len(validation_results)*100:.1f}% of properties match.")
        print("   Some differences found - review report for details.")
    else:
        print("\n⚠ SIGNIFICANT DIFFERENCES")
        print(f"   Only {perfect_matches/len(validation_results)*100:.1f}% of properties match.")
        print("   Review report for details.")
    
    print("\n" + "="*80 + "\n")
    
    client.close()


if __name__ == "__main__":
    main()
