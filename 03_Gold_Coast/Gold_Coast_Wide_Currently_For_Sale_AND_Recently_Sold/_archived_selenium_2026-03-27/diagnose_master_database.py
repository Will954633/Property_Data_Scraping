#!/usr/bin/env python3
"""
Diagnose Master Database Structure
Last Updated: 03/02/2026, 7:29 pm (Brisbane Time)

PURPOSE:
Find out what databases and collections actually exist,
and what address fields are available.
"""

from pymongo import MongoClient
import os

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')

# Connect to MongoDB
client = MongoClient(MONGODB_URI)

print("=" * 80)
print("MONGODB DATABASE AND COLLECTION ANALYSIS")
print("=" * 80)

# List all databases
print("\n1. ALL DATABASES:")
for db_name in client.list_database_names():
    if db_name not in ['admin', 'config', 'local']:
        print(f"   - {db_name}")

# Check Gold_Coast_Currently_For_Sale database
print("\n2. Gold_Coast_Currently_For_Sale DATABASE:")
for_sale_db = client['Gold_Coast_Currently_For_Sale']
collections = for_sale_db.list_collection_names()
print(f"   Total collections: {len(collections)}")
print(f"   Sample collections: {collections[:5]}")

# Check mermaid_waters collection
mermaid_waters = for_sale_db['mermaid_waters']
count = mermaid_waters.count_documents({})
print(f"\n   mermaid_waters collection: {count} documents")

if count > 0:
    sample = mermaid_waters.find_one({})
    print(f"   Sample document fields:")
    for key in sorted(sample.keys()):
        if 'address' in key.lower() or 'suburb' in key.lower():
            print(f"     - {key}: {sample.get(key)}")

# Check if Gold_Coast database exists
print("\n3. CHECKING FOR MASTER DATABASE:")
if 'Gold_Coast' in client.list_database_names():
    print("   ✓ Gold_Coast database EXISTS")
    master_db = client['Gold_Coast']
    master_collections = master_db.list_collection_names()
    print(f"   Collections in Gold_Coast: {len(master_collections)}")
    print(f"   Sample collections: {master_collections[:10]}")
    
    # Check for Mermaid Waters collection
    if 'Mermaid Waters' in master_collections:
        print(f"\n   ✓ 'Mermaid Waters' collection EXISTS")
        mw_master = master_db['Mermaid Waters']
        master_count = mw_master.count_documents({})
        print(f"   Documents: {master_count}")
        
        if master_count > 0:
            master_sample = mw_master.find_one({})
            print(f"   Sample master document fields:")
            for key in sorted(master_sample.keys()):
                if 'address' in key.lower():
                    print(f"     - {key}: {master_sample.get(key)}")
    else:
        print(f"\n   ✗ 'Mermaid Waters' collection NOT FOUND")
        print(f"   Available collections with 'mermaid' or 'Mermaid':")
        for coll in master_collections:
            if 'mermaid' in coll.lower():
                print(f"     - {coll}")
else:
    print("   ✗ Gold_Coast database DOES NOT EXIST")
    print("\n   Databases that might be the master:")
    for db_name in client.list_database_names():
        if 'gold' in db_name.lower() and db_name != 'Gold_Coast_Currently_For_Sale':
            print(f"     - {db_name}")

# Check Gold_Coast_Recently_Sold
print("\n4. Gold_Coast_Recently_Sold COLLECTION:")
sold_collection = for_sale_db['Gold_Coast_Recently_Sold']
sold_count = sold_collection.count_documents({})
print(f"   Documents: {sold_count}")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("\nThe script is trying to update master records in:")
print("  Database: 'Gold_Coast'")
print("  Collection: 'Mermaid Waters' (or other suburb names with spaces/capitals)")
print("\nBut this database/collection may not exist!")
print("The script should either:")
print("  1. Skip master database updates if it doesn't exist")
print("  2. Use a different database/collection name")
print("  3. Create the master database structure if needed")
print("=" * 80 + "\n")

client.close()
