#!/usr/bin/env python3
"""
Extract 5 test addresses from MongoDB for GCS deployment testing
"""

import json
import re
from pymongo import MongoClient

def build_address_from_doc(doc):
    """Build full address from MongoDB document"""
    parts = []
    
    # Unit/Villa prefix
    if doc.get('UNIT_TYPE') and doc.get('UNIT_NUMBER'):
        unit_type = str(doc['UNIT_TYPE']).upper()
        unit_num = str(doc['UNIT_NUMBER'])
        parts.append(f"{unit_type} {unit_num}/")
    
    # Street number
    if doc.get('STREET_NO_1'):
        parts.append(str(doc['STREET_NO_1']))
    
    # Street name and type
    if doc.get('STREET_NAME'):
        street_part = str(doc['STREET_NAME'])
        if doc.get('STREET_TYPE'):
            street_part += f" {doc['STREET_TYPE']}"
        parts.append(street_part)
    
    # Locality, state, postcode
    if doc.get('LOCALITY'):
        locality = str(doc['LOCALITY'])
        locality_part = f"{locality} QLD"
        if doc.get('POSTCODE'):
            locality_part += f" {doc['POSTCODE']}"
        parts.append(locality_part)
    
    if not parts:
        return None
    
    address = ' '.join(parts)
    address = re.sub(r'\s*/\s*', '/', address)
    address = re.sub(r'/\s+', '/', address)
    
    return address

def main():
    # Connect to MongoDB
    client = MongoClient('mongodb://127.0.0.1:27017/')
    db = client['Gold_Coast']
    
    # Get first collection
    collections = db.list_collection_names()
    if not collections:
        print("No collections found in Gold_Coast database")
        return
    
    print(f"Found {len(collections)} collections")
    collection = db[collections[0]]
    print(f"Using collection: {collections[0]}")
    
    # Get 5 addresses
    test_addresses = []
    docs = list(collection.find({}).limit(10))  # Get 10 to ensure we get 5 valid ones
    
    for doc in docs:
        address = build_address_from_doc(doc)
        if address:
            test_addresses.append({
                'address_pid': doc.get('ADDRESS_PID'),
                'address': address,
                'suburb': doc.get('LOCALITY'),
                'doc_id': str(doc.get('_id')),
                'collection': collections[0]
            })
            
            if len(test_addresses) >= 5:
                break
    
    # Save to JSON file
    output_file = 'test_addresses_5.json'
    with open(output_file, 'w') as f:
        json.dump(test_addresses, f, indent=2)
    
    print(f"\n✓ Extracted {len(test_addresses)} test addresses")
    print(f"✓ Saved to: {output_file}\n")
    
    # Display addresses
    print("Test Addresses:")
    print("=" * 70)
    for i, addr in enumerate(test_addresses, 1):
        print(f"{i}. {addr['address']}")
    print("=" * 70)

if __name__ == "__main__":
    main()
