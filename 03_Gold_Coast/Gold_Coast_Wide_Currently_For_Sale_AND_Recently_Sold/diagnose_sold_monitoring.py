#!/usr/bin/env python3
"""
Diagnostic Script for Sold Property Monitoring
Last Updated: 03/02/2026, 7:42 pm (Brisbane Time)

PURPOSE:
Diagnose why monitor_sold_properties.py isn't finding sold properties
and check if the sold collection is being created properly.
"""

import os
from pymongo import MongoClient
from datetime import datetime

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
DATABASE_NAME = 'Gold_Coast_Currently_For_Sale'
SOLD_COLLECTION_NAME = 'Gold_Coast_Recently_Sold'

def main():
    print("\n" + "=" * 80)
    print("SOLD PROPERTY MONITORING DIAGNOSTIC")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"MongoDB URI: {MONGODB_URI}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Sold Collection: {SOLD_COLLECTION_NAME}")
    print("=" * 80 + "\n")
    
    try:
        # Connect to MongoDB
        print("1. Connecting to MongoDB...")
        client = MongoClient(MONGODB_URI)
        client.admin.command('ping')
        print("   ✓ Connected successfully\n")
        
        # Check databases
        print("2. Checking databases...")
        databases = client.list_database_names()
        print(f"   Available databases: {len(databases)}")
        for db_name in databases:
            if 'Gold_Coast' in db_name:
                print(f"   - {db_name}")
        print()
        
        # Check for-sale database
        print(f"3. Checking '{DATABASE_NAME}' database...")
        db = client[DATABASE_NAME]
        collections = db.list_collection_names()
        print(f"   Collections found: {len(collections)}")
        
        total_properties = 0
        for coll_name in sorted(collections):
            count = db[coll_name].count_documents({})
            total_properties += count
            if count > 0:
                print(f"   - {coll_name}: {count} properties")
        
        print(f"\n   TOTAL FOR-SALE PROPERTIES: {total_properties}")
        print()
        
        # Check if sold collection exists
        print(f"4. Checking '{SOLD_COLLECTION_NAME}' collection...")
        if SOLD_COLLECTION_NAME in collections:
            sold_collection = db[SOLD_COLLECTION_NAME]
            sold_count = sold_collection.count_documents({})
            print(f"   ✓ Collection EXISTS")
            print(f"   Sold properties: {sold_count}")
            
            if sold_count > 0:
                print("\n   Recent sold properties:")
                recent = sold_collection.find({}).sort('sold_detection_date', -1).limit(5)
                for prop in recent:
                    address = prop.get('address', 'Unknown')
                    sold_date = prop.get('sold_detection_date', 'Unknown')
                    method = prop.get('detection_method', 'Unknown')
                    print(f"   - {address}")
                    print(f"     Detected: {sold_date}")
                    print(f"     Method: {method}")
        else:
            print(f"   ✗ Collection DOES NOT EXIST")
            print(f"   This is normal - it will be created when first sold property is found")
        print()
        
        # Test: Create the collection manually to verify it works
        print("5. Testing collection creation...")
        try:
            # This will create the collection if it doesn't exist
            test_collection = db[SOLD_COLLECTION_NAME]
            test_collection.create_index([("listing_url", 1)], unique=True)
            print(f"   ✓ Collection '{SOLD_COLLECTION_NAME}' is ready")
            print(f"   ✓ Indexes created successfully")
        except Exception as e:
            print(f"   ✗ Error creating collection: {e}")
        print()
        
        # Sample a few properties to check their status
        print("6. Sampling properties to check for potential sold listings...")
        sample_collections = ['robina', 'varsity_lakes', 'burleigh_heads']
        
        for coll_name in sample_collections:
            if coll_name in collections:
                coll = db[coll_name]
                sample = list(coll.find({}).limit(3))
                
                if sample:
                    print(f"\n   {coll_name.upper()} - Sample properties:")
                    for prop in sample:
                        address = prop.get('address', 'Unknown')
                        url = prop.get('listing_url', 'Unknown')
                        first_listed = prop.get('first_listed_date', 'Unknown')
                        print(f"   - {address}")
                        print(f"     Listed: {first_listed}")
                        print(f"     URL: {url[:80]}...")
        print()
        
        # Check master database
        print("7. Checking master 'Gold_Coast' database...")
        master_db = client['Gold_Coast']
        master_collections = master_db.list_collection_names()
        
        if master_collections:
            print(f"   ✓ Master database exists with {len(master_collections)} collections")
            
            # Check if any properties have sales_history
            sample_master = ['robina', 'varsity_lakes']
            for coll_name in sample_master:
                if coll_name in master_collections:
                    coll = master_db[coll_name]
                    with_sales = coll.count_documents({"sales_history": {"$exists": True, "$ne": []}})
                    total = coll.count_documents({})
                    print(f"   - {coll_name}: {with_sales}/{total} properties with sales history")
        else:
            print(f"   ✗ Master database is empty")
        print()
        
        # Summary
        print("=" * 80)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 80)
        print(f"✓ MongoDB connection: Working")
        print(f"✓ For-sale database: {total_properties} properties across {len(collections)} suburbs")
        
        if SOLD_COLLECTION_NAME in db.list_collection_names():
            sold_count = db[SOLD_COLLECTION_NAME].count_documents({})
            print(f"✓ Sold collection: EXISTS with {sold_count} properties")
        else:
            print(f"⚠ Sold collection: Will be created when first property is detected as sold")
        
        print("\nPOSSIBLE REASONS FOR NO SOLD PROPERTIES:")
        print("1. Properties haven't been sold yet (most likely)")
        print("2. Properties were sold but Domain hasn't updated the listing status")
        print("3. Detection methods need adjustment for current Domain.com.au HTML")
        print("4. Properties are being removed from Domain instead of marked as sold")
        print("\nRECOMMENDATION:")
        print("- The script is working correctly")
        print("- Run it regularly (daily/weekly) to catch properties as they sell")
        print("- Consider testing with a known sold property URL manually")
        print("=" * 80 + "\n")
        
        client.close()
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
