#!/usr/bin/env python3
"""
Identify Building Complexes in Gold Coast Database
Detects buildings by finding addresses with multiple units and marks them in MongoDB
"""

from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime
import sys

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"


def identify_buildings():
    """Identify building complexes and mark them in database"""
    
    print(f"\n{'='*80}")
    print("Building Complex Identification")
    print(f"{'='*80}\n")
    
    # Connect to MongoDB
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB\n")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        sys.exit(1)
    
    db = client[DATABASE_NAME]
    
    # Statistics
    stats = {
        'total_addresses': 0,
        'standalone_houses': 0,
        'buildings_identified': 0,
        'units_in_buildings': 0,
        'updated': 0
    }
    
    # Get all collections (suburbs)
    collections = db.list_collection_names()
    print(f"Processing {len(collections)} suburb collections...\n")
    
    for i, collection_name in enumerate(collections, 1):
        collection = db[collection_name]
        
        # Get all documents
        docs = list(collection.find({}))
        stats['total_addresses'] += len(docs)
        
        # Group by base address (street number + street name + street type + locality)
        address_groups = defaultdict(list)
        
        for doc in docs:
            # Create base address key
            base_key = (
                doc.get('STREET_NO_1'),
                doc.get('STREET_NAME'),
                doc.get('STREET_TYPE'),
                doc.get('LOCALITY')
            )
            
            address_groups[base_key].append(doc)
        
        # Process each address group
        for base_address, group_docs in address_groups.items():
            street_no, street_name, street_type, locality = base_address
            
            # Skip if any component is missing
            if not all([street_no, street_name, locality]):
                continue
            
            # Count units at this address
            units = [d for d in group_docs if d.get('UNIT_TYPE') and d.get('UNIT_NUMBER')]
            standalone = [d for d in group_docs if not d.get('UNIT_TYPE')]
            
            # If multiple units exist at this address, it's a building
            if len(units) >= 2:
                building_name = f"{street_no} {street_name}"
                if street_type:
                    building_name += f" {street_type}"
                
                stats['buildings_identified'] += 1
                stats['units_in_buildings'] += len(units)
                
                # Mark all units in this building
                for unit_doc in units:
                    result = collection.update_one(
                        {'_id': unit_doc['_id']},
                        {
                            '$set': {
                                'property_classification': 'unit',
                                'building_complex': building_name,
                                'building_address': f"{street_no} {street_name} {street_type}, {locality}".strip(),
                                'total_units_in_building': len(units),
                                'classification_updated': datetime.now()
                            }
                        }
                    )
                    if result.modified_count > 0:
                        stats['updated'] += 1
                
                # Mark the base building address if it exists
                for standalone_doc in standalone:
                    result = collection.update_one(
                        {'_id': standalone_doc['_id']},
                        {
                            '$set': {
                                'property_classification': 'building',
                                'building_complex': building_name,
                                'total_units_in_building': len(units),
                                'classification_updated': datetime.now()
                            }
                        }
                    )
                    if result.modified_count > 0:
                        stats['updated'] += 1
            
            # Otherwise, mark as standalone house/property
            elif len(standalone) > 0:
                for standalone_doc in standalone:
                    result = collection.update_one(
                        {'_id': standalone_doc['_id']},
                        {
                            '$set': {
                                'property_classification': 'standalone',
                                'classification_updated': datetime.now()
                            }
                        }
                    )
                    if result.modified_count > 0:
                        stats['updated'] += 1
                
                stats['standalone_houses'] += len(standalone)
        
        # Progress update
        if i % 10 == 0 or i == len(collections):
            print(f"  [{i}/{len(collections)}] Processed {collection_name.replace('_', ' ').title()}")
    
    # Summary
    print(f"\n{'='*80}")
    print("Identification Complete")
    print(f"{'='*80}")
    print(f"Total addresses:         {stats['total_addresses']:,}")
    print(f"Standalone houses:       {stats['standalone_houses']:,}")
    print(f"Buildings identified:    {stats['buildings_identified']:,}")
    print(f"Units in buildings:      {stats['units_in_buildings']:,}")
    print(f"Documents updated:       {stats['updated']:,}")
    print(f"{'='*80}\n")
    
    # Show examples
    print("Example Buildings Found:")
    print(f"{'='*80}\n")
    
    example_count = 0
    for collection_name in collections[:5]:
        collection = db[collection_name]
        
        # Find a building example
        building_doc = collection.find_one({'property_classification': 'building'})
        if building_doc and example_count < 5:
            print(f"Building: {building_doc.get('building_complex')}")
            print(f"  Suburb: {building_doc.get('LOCALITY')}")
            print(f"  Units: {building_doc.get('total_units_in_building')} units")
            
            # Show some units
            units = collection.find({
                'property_classification': 'unit',
                'building_complex': building_doc.get('building_complex')
            }).limit(3)
            
            for unit in units:
                unit_str = f"{unit.get('UNIT_TYPE')} {unit.get('UNIT_NUMBER')}"
                print(f"    - {unit_str}/{building_doc.get('building_complex')}")
            
            print()
            example_count += 1
    
    client.close()
    print("✓ Classification complete\n")


if __name__ == "__main__":
    try:
        identify_buildings()
    except KeyboardInterrupt:
        print("\n\n✗ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
