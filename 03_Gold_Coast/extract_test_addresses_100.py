#!/usr/bin/env python3
"""
Extract 100 diverse test addresses from MongoDB for GCS deployment testing
"""

import json
import re
from pymongo import MongoClient
import random

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
    
    # Get collections
    collections = db.list_collection_names()
    if not collections:
        print("No collections found in Gold_Coast database")
        return
    
    print(f"Found {len(collections)} suburb collections")
    
    # Select 10 diverse suburbs for testing
    # Prioritize larger suburbs for variety
    collection_sizes = [(col, db[col].count_documents({})) for col in collections]
    collection_sizes.sort(key=lambda x: x[1], reverse=True)
    
    # Take top 10 suburbs by size
    selected_suburbs = [col for col, _ in collection_sizes[:10]]
    
    print(f"\nSelected suburbs for testing:")
    for suburb in selected_suburbs:
        count = db[suburb].count_documents({})
        print(f"  - {suburb}: {count:,} addresses")
    
    # Extract 10 addresses from each suburb (total 100)
    test_addresses = []
    addresses_per_suburb = 10
    
    for suburb in selected_suburbs:
        collection = db[suburb]
        
        # Get total documents
        total_docs = collection.count_documents({})
        
        # Sample addresses randomly from the collection
        # Skip a random amount to get variety
        skip_amount = random.randint(0, max(0, total_docs - 200))
        
        docs = list(collection.find({}).skip(skip_amount).limit(20))
        
        suburb_addresses = []
        for doc in docs:
            address = build_address_from_doc(doc)
            if address:
                suburb_addresses.append({
                    'address_pid': doc.get('ADDRESS_PID'),
                    'address': address,
                    'suburb': doc.get('LOCALITY'),
                    'doc_id': str(doc.get('_id')),
                    'collection': suburb,
                    'unit_type': doc.get('UNIT_TYPE'),
                    'postcode': doc.get('POSTCODE')
                })
                
                if len(suburb_addresses) >= addresses_per_suburb:
                    break
        
        test_addresses.extend(suburb_addresses)
        print(f"  ✓ Extracted {len(suburb_addresses)} from {suburb}")
    
    # Save to JSON file
    output_file = 'test_addresses_100.json'
    with open(output_file, 'w') as f:
        json.dump(test_addresses, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Extracted {len(test_addresses)} test addresses")
    print(f"✓ Saved to: {output_file}")
    print(f"{'='*70}\n")
    
    # Display statistics
    print("Address Statistics:")
    print("=" * 70)
    
    # Count by suburb
    suburb_counts = {}
    unit_count = 0
    house_count = 0
    
    for addr in test_addresses:
        suburb = addr['suburb']
        suburb_counts[suburb] = suburb_counts.get(suburb, 0) + 1
        
        if addr.get('unit_type'):
            unit_count += 1
        else:
            house_count += 1
    
    print(f"Total Addresses:  {len(test_addresses)}")
    print(f"Houses:           {house_count} ({house_count/len(test_addresses)*100:.1f}%)")
    print(f"Units/Apartments: {unit_count} ({unit_count/len(test_addresses)*100:.1f}%)")
    print(f"\nAddresses by Suburb:")
    for suburb, count in sorted(suburb_counts.items()):
        print(f"  {suburb:25s}: {count:2d}")
    
    print("=" * 70)
    
    # Display sample addresses
    print("\nSample Addresses (first 10):")
    print("=" * 70)
    for i, addr in enumerate(test_addresses[:10], 1):
        prop_type = "Unit" if addr.get('unit_type') else "House"
        print(f"{i:2d}. [{prop_type:5s}] {addr['address']}")
    print("=" * 70)

if __name__ == "__main__":
    main()
