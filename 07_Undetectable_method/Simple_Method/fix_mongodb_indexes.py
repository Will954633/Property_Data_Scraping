#!/usr/bin/env python3
"""
Fix MongoDB Indexes
Removes old indexes and sets up correct schema for properties_for_sale collection
"""

from pymongo import MongoClient
import sys

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "properties_for_sale"


def fix_indexes():
    """Fix MongoDB indexes - remove old ones and create new ones"""
    try:
        print("="*80)
        print("MONGODB INDEX FIX UTILITY")
        print("="*80)
        print(f"\nDatabase: {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        
        # Connect
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # List current indexes
        print(f"\n→ Current indexes:")
        indexes = collection.list_indexes()
        for idx in indexes:
            print(f"  • {idx['name']}: {idx.get('key', {})}")
        
        # Drop the problematic property_id index if it exists
        print(f"\n→ Removing old indexes...")
        try:
            collection.drop_index("property_id_1")
            print(f"  ✓ Dropped 'property_id_1' index")
        except Exception as e:
            if "index not found" in str(e).lower():
                print(f"  ℹ 'property_id_1' index doesn't exist (already removed)")
            else:
                print(f"  ⚠ Error dropping property_id_1: {e}")
        
        # Drop all indexes except _id (fresh start)
        try:
            collection.drop_indexes()
            print(f"  ✓ Dropped all custom indexes")
        except Exception as e:
            print(f"  ⚠ Error dropping indexes: {e}")
        
        # Create correct indexes for new schema
        print(f"\n→ Creating new indexes...")
        
        collection.create_index("address", unique=True)
        print(f"  ✓ Created unique index on 'address'")
        
        collection.create_index("enriched")
        print(f"  ✓ Created index on 'enriched'")
        
        collection.create_index("first_seen")
        print(f"  ✓ Created index on 'first_seen'")
        
        collection.create_index("last_updated")
        print(f"  ✓ Created index on 'last_updated'")
        
        # List final indexes
        print(f"\n→ Final indexes:")
        indexes = collection.list_indexes()
        for idx in indexes:
            print(f"  • {idx['name']}: {idx.get('key', {})}")
        
        # Get collection stats
        doc_count = collection.count_documents({})
        print(f"\n→ Collection stats:")
        print(f"  Total documents: {doc_count}")
        
        client.close()
        
        print(f"\n{'='*80}")
        print("✓ INDEX FIX COMPLETE")
        print("="*80)
        print("\nYou can now run:")
        print("  python mongodb_uploader.py")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(fix_indexes())
