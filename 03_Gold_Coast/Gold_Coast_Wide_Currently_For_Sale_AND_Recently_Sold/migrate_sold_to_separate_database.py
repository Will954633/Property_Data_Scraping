#!/usr/bin/env python3
"""
Migrate Sold Properties to Separate Database
Last Updated: 03/02/2026, 7:58 pm (Brisbane Time)

PURPOSE:
Migrates sold properties from Gold_Coast_Currently_For_Sale.Gold_Coast_Recently_Sold
to the new separate database: Gold_Coast_Recently_Sold.sold_properties

This is a one-time migration script.
"""

from pymongo import MongoClient, ASCENDING
from datetime import datetime

# Configuration
MONGODB_URI = 'mongodb://127.0.0.1:27017/'
OLD_DATABASE = 'Gold_Coast_Currently_For_Sale'
OLD_COLLECTION = 'Gold_Coast_Recently_Sold'
NEW_DATABASE = 'Gold_Coast_Recently_Sold'
NEW_COLLECTION = 'sold_properties'


def migrate_sold_properties():
    """Migrate sold properties to separate database"""
    
    print("=" * 80)
    print("SOLD PROPERTIES MIGRATION")
    print("=" * 80)
    print(f"\nConnecting to MongoDB...")
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    
    # Get old and new collections
    old_db = client[OLD_DATABASE]
    old_collection = old_db[OLD_COLLECTION]
    
    new_db = client[NEW_DATABASE]
    new_collection = new_db[NEW_COLLECTION]
    
    print(f"✓ Connected\n")
    
    # Count existing documents
    old_count = old_collection.count_documents({})
    new_count = new_collection.count_documents({})
    
    print(f"Source: {OLD_DATABASE}.{OLD_COLLECTION}")
    print(f"  Documents: {old_count}")
    print(f"\nDestination: {NEW_DATABASE}.{NEW_COLLECTION}")
    print(f"  Documents: {new_count}")
    
    if old_count == 0:
        print("\n✓ No documents to migrate")
        client.close()
        return
    
    print(f"\n{'=' * 80}")
    print("STARTING MIGRATION")
    print("=" * 80 + "\n")
    
    # Get all sold properties
    sold_properties = list(old_collection.find({}))
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for prop in sold_properties:
        try:
            listing_url = prop.get('listing_url')
            address = prop.get('address', 'Unknown')
            
            # Check if already exists in new database
            existing = new_collection.find_one({"listing_url": listing_url})
            
            if existing:
                print(f"⚠ Skipped (already exists): {address}")
                skipped += 1
                continue
            
            # Add migration timestamp
            prop['migrated_to_separate_db'] = datetime.now()
            
            # Insert into new database
            new_collection.insert_one(prop)
            print(f"✓ Migrated: {address}")
            migrated += 1
            
        except Exception as e:
            print(f"✗ Error migrating {prop.get('address', 'Unknown')}: {e}")
            errors += 1
    
    # Create indexes on new collection
    print(f"\n{'=' * 80}")
    print("CREATING INDEXES")
    print("=" * 80 + "\n")
    
    new_collection.create_index([("listing_url", ASCENDING)], unique=True)
    new_collection.create_index([("address", ASCENDING)])
    new_collection.create_index([("sold_detection_date", ASCENDING)])
    new_collection.create_index([("sold_date", ASCENDING)])
    new_collection.create_index([("original_suburb", ASCENDING)])
    
    print("✓ Indexes created")
    
    # Final summary
    print(f"\n{'=' * 80}")
    print("MIGRATION COMPLETE")
    print("=" * 80 + "\n")
    
    print(f"Migrated:  {migrated}")
    print(f"Skipped:   {skipped}")
    print(f"Errors:    {errors}")
    print(f"Total:     {old_count}")
    
    # Verify
    final_count = new_collection.count_documents({})
    print(f"\nNew database now contains: {final_count} documents")
    
    # Ask about cleanup
    print(f"\n{'=' * 80}")
    print("CLEANUP OPTIONS")
    print("=" * 80 + "\n")
    
    print(f"The old collection still contains {old_count} documents.")
    print(f"Location: {OLD_DATABASE}.{OLD_COLLECTION}")
    print(f"\nTo remove the old collection after verifying migration:")
    print(f"  mongosh")
    print(f"  use {OLD_DATABASE}")
    print(f"  db.{OLD_COLLECTION}.drop()")
    
    client.close()
    print("\n✓ Migration complete!\n")


if __name__ == "__main__":
    migrate_sold_properties()
