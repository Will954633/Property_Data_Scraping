#!/usr/bin/env python3
"""
Migrate Sold Properties to Suburb-Specific Collections
Last Updated: 03/02/2026, 8:02 pm (Brisbane Time)

PURPOSE:
Reorganizes sold properties from Gold_Coast_Recently_Sold.sold_properties
into suburb-specific collections matching the for-sale database structure.

STRUCTURE:
Gold_Coast_Recently_Sold (Database)
├── robina (Collection) ← Sold properties from Robina
├── varsity_lakes (Collection) ← Sold properties from Varsity Lakes
└── ... (one collection per suburb)
"""

from pymongo import MongoClient, ASCENDING
from datetime import datetime

# Configuration
MONGODB_URI = 'mongodb://127.0.0.1:27017/'
SOLD_DATABASE = 'Gold_Coast_Recently_Sold'
OLD_COLLECTION = 'sold_properties'  # Single collection with all sold properties


def migrate_to_suburb_collections():
    """Migrate sold properties to suburb-specific collections"""
    
    print("=" * 80)
    print("MIGRATE TO SUBURB-SPECIFIC COLLECTIONS")
    print("=" * 80)
    print(f"\nConnecting to MongoDB...")
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    sold_db = client[SOLD_DATABASE]
    old_collection = sold_db[OLD_COLLECTION]
    
    print(f"✓ Connected\n")
    
    # Count existing documents
    total_count = old_collection.count_documents({})
    
    print(f"Source: {SOLD_DATABASE}.{OLD_COLLECTION}")
    print(f"  Total documents: {total_count}")
    
    if total_count == 0:
        print("\n✓ No documents to migrate")
        client.close()
        return
    
    print(f"\n{'=' * 80}")
    print("STARTING MIGRATION")
    print("=" * 80 + "\n")
    
    # Get all sold properties
    sold_properties = list(old_collection.find({}))
    
    # Group by suburb
    suburb_groups = {}
    for prop in sold_properties:
        original_suburb = prop.get('original_suburb', 'Unknown')
        collection_name = prop.get('original_collection', original_suburb.lower().replace(' ', '_'))
        
        if collection_name not in suburb_groups:
            suburb_groups[collection_name] = []
        suburb_groups[collection_name].append(prop)
    
    print(f"Found {len(suburb_groups)} suburbs with sold properties\n")
    
    migrated = 0
    skipped = 0
    errors = 0
    
    # Migrate each suburb
    for collection_name, properties in suburb_groups.items():
        print(f"\n📍 {collection_name.upper().replace('_', ' ')}")
        print(f"   Properties to migrate: {len(properties)}")
        
        # Get or create suburb collection
        suburb_collection = sold_db[collection_name]
        
        # Create indexes
        try:
            suburb_collection.create_index([("listing_url", ASCENDING)], unique=True)
            suburb_collection.create_index([("address", ASCENDING)])
            suburb_collection.create_index([("sold_detection_date", ASCENDING)])
            suburb_collection.create_index([("sold_date", ASCENDING)])
        except Exception as e:
            print(f"   ⚠ Index creation: {e}")
        
        # Migrate properties
        for prop in properties:
            try:
                listing_url = prop.get('listing_url')
                address = prop.get('address', 'Unknown')
                
                # Check if already exists
                existing = suburb_collection.find_one({"listing_url": listing_url})
                
                if existing:
                    skipped += 1
                    continue
                
                # Add migration timestamp
                prop['migrated_to_suburb_collection'] = datetime.now()
                
                # Insert into suburb collection
                suburb_collection.insert_one(prop)
                migrated += 1
                
            except Exception as e:
                print(f"   ✗ Error: {address}: {e}")
                errors += 1
        
        print(f"   ✓ Migrated: {len(properties) - skipped} properties")
    
    # Final summary
    print(f"\n{'=' * 80}")
    print("MIGRATION COMPLETE")
    print("=" * 80 + "\n")
    
    print(f"Migrated:  {migrated}")
    print(f"Skipped:   {skipped}")
    print(f"Errors:    {errors}")
    print(f"Total:     {total_count}")
    
    # Verify
    print(f"\n{'=' * 80}")
    print("VERIFICATION")
    print("=" * 80 + "\n")
    
    collections = sold_db.list_collection_names()
    suburb_collections = [c for c in collections if c != OLD_COLLECTION]
    
    total_in_suburbs = 0
    for coll_name in suburb_collections:
        count = sold_db[coll_name].count_documents({})
        if count > 0:
            total_in_suburbs += count
            print(f"  {coll_name}: {count} properties")
    
    print(f"\nTotal in suburb collections: {total_in_suburbs}")
    print(f"Original collection still has: {old_collection.count_documents({})} properties")
    
    # Cleanup instructions
    print(f"\n{'=' * 80}")
    print("CLEANUP OPTIONS")
    print("=" * 80 + "\n")
    
    print(f"After verifying the migration, you can remove the old collection:")
    print(f"  mongosh")
    print(f"  use {SOLD_DATABASE}")
    print(f"  db.{OLD_COLLECTION}.drop()")
    
    client.close()
    print("\n✓ Migration complete!\n")


if __name__ == "__main__":
    migrate_to_suburb_collections()
