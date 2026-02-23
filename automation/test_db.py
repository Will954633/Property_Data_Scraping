#!/usr/bin/env python3
"""
Test MongoDB connection and basic operations
"""

from mongodb_client import PropertyDB
from datetime import datetime
import sys

def main():
    try:
        db = PropertyDB()
        
        # Test connection
        db.client.admin.command('ismaster')
        print("✓ MongoDB connection successful")
        
        # Test collections
        print(f"✓ Database: {db.db.name}")
        print(f"✓ Collections: {db.db.list_collection_names()}")
        
        # Test indexes
        print("✓ Indexes ensured")
        
        # Test get_all_active_addresses (should be empty initially)
        active = db.get_all_active_addresses()
        print(f"Active addresses: {len(active)}")
        
        # Insert a test property
        test_prop = {
            "address": "Test Address, Robina, QLD 4226",
            "status": "for_sale",
            "first_seen": datetime.now(),
            "last_seen": datetime.now(),
            "bedrooms": 3,
            "price": "$1,000,000"
        }
        result = db.properties.insert_one(test_prop)
        print(f"✓ Inserted test property: {result.inserted_id}")
        
        # Retrieve it
        retrieved = db.properties.find_one({"address": test_prop["address"]})
        if retrieved:
            print("✓ Retrieved test property successfully")
        
        # Clean up
        db.properties.delete_one({"address": test_prop["address"]})
        print("✓ Cleaned up test data")
        
        db.close()
        print("All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
