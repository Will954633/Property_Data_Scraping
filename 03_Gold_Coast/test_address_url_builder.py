#!/usr/bin/env python3
"""
Test Address URL Builder
Tests building Domain.com.au URLs from Gold Coast MongoDB addresses
"""

import re
from pymongo import MongoClient
from typing import Dict, Optional

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"


def build_address_from_components(doc: Dict) -> Optional[str]:
    """
    Build address string from MongoDB document components
    
    Examples:
    - House: "414 MARINE PARADE, BIGGERA WATERS QLD 4216"
    - Unit: "U 12/414 MARINE PARADE, BIGGERA WATERS QLD 4216"
    - Villa: "V 5/123 MAIN STREET, SURFERS PARADISE QLD 4217"
    """
    parts = []
    
    # Unit/Villa prefix (e.g., "U 12/", "V 5/")
    if doc.get('UNIT_TYPE') and doc.get('UNIT_NUMBER'):
        unit_type = doc['UNIT_TYPE'].upper()
        unit_num = str(doc['UNIT_NUMBER'])
        parts.append(f"{unit_type} {unit_num}/")
    
    # Street number (e.g., "414")
    if doc.get('STREET_NO_1'):
        parts.append(str(doc['STREET_NO_1']))
    
    # Street name and type (e.g., "MARINE PARADE")
    if doc.get('STREET_NAME'):
        street_part = doc['STREET_NAME']
        if doc.get('STREET_TYPE'):
            street_part += f" {doc['STREET_TYPE']}"
        parts.append(street_part)
    
    # Locality and state (e.g., "BIGGERA WATERS QLD 4216")
    if doc.get('LOCALITY'):
        # Determine postcode from locality (Gold Coast is 4xxx)
        # For this test, we'll use a generic 4xxx postcode
        locality = doc['LOCALITY']
        parts.append(f"{locality} QLD")
    
    if not parts:
        return None
    
    # Join parts with appropriate spacing
    address = ' '.join(parts)
    
    # Clean up spacing around "/"
    address = re.sub(r'\s*/\s*', '/', address)
    address = re.sub(r'/\s+', '/', address)
    
    return address


def build_domain_url(address: str) -> str:
    """
    Build Domain property profile URL from address
    
    Domain URL format:
    https://www.domain.com.au/property-profile/{address-slug}
    
    Rules:
    1. Convert to lowercase
    2. Replace spaces, commas, slashes with hyphens
    3. Remove multiple consecutive hyphens
    4. Remove special characters except hyphens
    5. Trim leading/trailing hyphens
    
    Examples:
    - "414 MARINE PARADE, BIGGERA WATERS QLD 4216"
      → "414-marine-parade-biggera-waters-qld-4216"
    
    - "U 12/414 MARINE PARADE, BIGGERA WATERS QLD 4216"
      → "u-12-414-marine-parade-biggera-waters-qld-4216"
    """
    # Convert to lowercase
    url_slug = address.lower().strip()
    
    # Replace separators with hyphens
    url_slug = re.sub(r'[,\s/]+', '-', url_slug)
    
    # Remove special characters (keep only alphanumeric and hyphens)
    url_slug = re.sub(r'[^a-z0-9\-]', '', url_slug)
    
    # Remove multiple consecutive hyphens
    url_slug = re.sub(r'-+', '-', url_slug)
    
    # Remove leading/trailing hyphens
    url_slug = url_slug.strip('-')
    
    return f"https://www.domain.com.au/property-profile/{url_slug}"


def test_url_builder():
    """Test URL builder with real Gold Coast addresses"""
    
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    print("="*80)
    print("Domain URL Builder Test")
    print("="*80)
    print()
    
    # Get sample addresses from different suburbs
    collections = db.list_collection_names()
    
    test_addresses = []
    
    # Sample different address types
    for collection_name in collections[:10]:  # Test first 10 suburbs
        collection = db[collection_name]
        
        # Get houses (no unit)
        house = collection.find_one({'UNIT_TYPE': None, 'STREET_NO_1': {'$ne': None}})
        if house:
            test_addresses.append((collection_name, house, 'House'))
        
        # Get units
        unit = collection.find_one({'UNIT_TYPE': 'U', 'UNIT_NUMBER': {'$ne': None}})
        if unit:
            test_addresses.append((collection_name, unit, 'Unit'))
        
        # Get villas
        villa = collection.find_one({'UNIT_TYPE': 'V', 'UNIT_NUMBER': {'$ne': None}})
        if villa:
            test_addresses.append((collection_name, villa, 'Villa'))
    
    # Test URL generation
    print(f"Testing {len(test_addresses)} addresses:\n")
    
    results = []
    
    for suburb, doc, prop_type in test_addresses:
        address = build_address_from_components(doc)
        
        if address:
            url = build_domain_url(address)
            
            results.append({
                'suburb': suburb,
                'type': prop_type,
                'address': address,
                'url': url,
                'components': {
                    'unit_type': doc.get('UNIT_TYPE'),
                    'unit_number': doc.get('UNIT_NUMBER'),
                    'street_no': doc.get('STREET_NO_1'),
                    'street_name': doc.get('STREET_NAME'),
                    'street_type': doc.get('STREET_TYPE'),
                    'locality': doc.get('LOCALITY')
                }
            })
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['type'].upper()} - {result['suburb'].replace('_', ' ').title()}")
        print(f"    Address: {result['address']}")
        print(f"    URL:     {result['url']}")
        print()
    
    print("="*80)
    print("URL Test File Generated")
    print("="*80)
    print()
    
    # Save URLs to file for manual testing
    output_file = "03_Gold_Coast/domain_urls_test.txt"
    with open(output_file, 'w') as f:
        f.write("# Domain URL Test List\n")
        f.write("# Generated from Gold_Coast MongoDB\n")
        f.write(f"# Total URLs: {len(results)}\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"# {i}. {result['type']} - {result['suburb'].replace('_', ' ').title()}\n")
            f.write(f"# Address: {result['address']}\n")
            f.write(f"{result['url']}\n\n")
    
    print(f"✓ Saved {len(results)} test URLs to: {output_file}")
    print(f"✓ You can test these URLs manually in a browser\n")
    
    # Generate summary statistics
    print("="*80)
    print("Summary")
    print("="*80)
    
    type_counts = {}
    for result in results:
        prop_type = result['type']
        type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
    
    for prop_type, count in sorted(type_counts.items()):
        print(f"{prop_type:15s}: {count} addresses")
    
    print(f"\nTotal test URLs: {len(results)}")
    print()
    
    client.close()
    
    return results


if __name__ == "__main__":
    try:
        test_url_builder()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
