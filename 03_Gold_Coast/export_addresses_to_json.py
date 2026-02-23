#!/usr/bin/env python3
"""
Export all Gold Coast property addresses from local MongoDB to JSON
Builds Domain URLs from address components (same as scraper does)
"""

import json
from pymongo import MongoClient
import sys
import re

def build_address_from_components(doc):
    """
    Build address string from MongoDB document components
    
    Examples:
    - House: "414 MARINE PARADE, BIGGERA WATERS QLD 4216"
    - Unit: "U 12/414 MARINE PARADE, BIGGERA WATERS QLD 4216"
    """
    parts = []
    
    # Unit/Villa prefix (e.g., "U 12/", "V 5/")
    if doc.get('UNIT_TYPE') and doc.get('UNIT_NUMBER'):
        unit_type = str(doc['UNIT_TYPE']).upper()
        unit_num = str(doc['UNIT_NUMBER'])
        parts.append(f"{unit_type} {unit_num}/")
    
    # Street number (e.g., "414")
    if doc.get('STREET_NO_1'):
        parts.append(str(doc['STREET_NO_1']))
    
    # Street name and type (e.g., "MARINE PARADE")
    if doc.get('STREET_NAME'):
        street_part = str(doc['STREET_NAME'])
        if doc.get('STREET_TYPE'):
            street_part += f" {doc['STREET_TYPE']}"
        parts.append(street_part)
    
    # Locality, state, and postcode (e.g., "BIGGERA WATERS QLD 4216")
    if doc.get('LOCALITY'):
        locality = str(doc['LOCALITY'])
        locality_part = f"{locality} QLD"
        
        # Add postcode if available
        if doc.get('POSTCODE'):
            locality_part += f" {doc['POSTCODE']}"
        
        parts.append(locality_part)
    
    if not parts:
        return None
    
    # Join parts with appropriate spacing
    address = ' '.join(parts)
    
    # Clean up spacing around "/"
    address = re.sub(r'\s*/\s*', '/', address)
    address = re.sub(r'/\s+', '/', address)
    
    return address

def build_domain_url(address):
    """
    Build Domain property profile URL from address
    
    Domain URL format: https://www.domain.com.au/property-profile/{slug}
    
    Rules: Domain.com.au does NOT include unit type prefix in URL
    - Remove unit type prefix (U, V, etc.) if present
    - Convert to lowercase
    - Replace spaces, commas, slashes with hyphens
    - Remove special characters
    """
    # Remove unit type prefix (e.g., "U ", "V ", etc.) at the start
    url_slug = re.sub(r'^[A-Z]\s+', '', address.upper())
    
    # Convert to lowercase
    url_slug = url_slug.lower().strip()
    
    # Replace separators with hyphens
    url_slug = re.sub(r'[,\s/]+', '-', url_slug)
    
    # Remove special characters (keep only alphanumeric and hyphens)
    url_slug = re.sub(r'[^a-z0-9\-]', '', url_slug)
    
    # Remove multiple consecutive hyphens
    url_slug = re.sub(r'-+', '-', url_slug)
    
    # Remove leading/trailing hyphens
    url_slug = url_slug.strip('-')
    
    return f"https://www.domain.com.au/property-profile/{url_slug}"

def export_addresses():
    """Export all addresses from MongoDB and build Domain URLs"""
    
    print("Connecting to local MongoDB...")
    try:
        client = MongoClient('mongodb://127.0.0.1:27017/', serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    db = client['Gold_Coast']
    
    print("\nFetching all suburb collections...")
    collections = db.list_collection_names()
    print(f"✓ Found {len(collections)} suburb collections")
    
    all_urls = []
    total_properties = 0
    
    print("\nBuilding Domain URLs from address components...")
    for collection_name in collections:
        collection = db[collection_name]
        docs = list(collection.find({}, {
            'ADDRESS_PID': 1,
            'UNIT_TYPE': 1,
            'UNIT_NUMBER': 1,
            'STREET_NO_1': 1,
            'STREET_NAME': 1,
            'STREET_TYPE': 1,
            'LOCALITY': 1,
            'POSTCODE': 1
        }))
        
        for doc in docs:
            # Build address from components
            address = build_address_from_components(doc)
            
            if address:
                # Build Domain URL from address
                url = build_domain_url(address)
                all_urls.append(url)
                total_properties += 1
        
        print(f"  {collection_name}: {len(docs):,} properties")
    
    if not all_urls:
        print("✗ No addresses found!")
        sys.exit(1)
    
    print(f"\n✓ Built {len(all_urls):,} Domain URLs from {total_properties:,} properties")
    
    # Save to JSON
    output_file = 'all_gold_coast_addresses.json'
    print(f"\nWriting to {output_file}...")
    
    with open(output_file, 'w') as f:
        json.dump(all_urls, f, indent=2)
    
    print(f"✓ Exported {len(all_urls):,} URLs to {output_file}")
    print(f"✓ File size: {len(json.dumps(all_urls)) / 1024 / 1024:.2f} MB")
    
    # Print sample
    print("\nSample URLs:")
    for url in all_urls[:5]:
        print(f"  - {url}")
    
    print(f"\n✓ Export complete!")
    print(f"\nNext step: Upload to GCS with:")
    print(f"  gsutil cp {output_file} gs://property-scraper-production-data-477306/")
    
    return output_file, len(all_urls)

if __name__ == '__main__':
    export_addresses()
