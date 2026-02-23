#!/usr/bin/env python3
"""Check what's in local MongoDB"""

from pymongo import MongoClient

LOCAL_MONGODB = "mongodb://localhost:27017/"

print("Connecting to local MongoDB...")
client = MongoClient(LOCAL_MONGODB, serverSelectionTimeoutMS=5000)

print("\nDatabases:")
for db_name in client.list_database_names():
    if db_name in ['admin', 'config', 'local']:
        continue
    print(f"\n  {db_name}:")
    db = client[db_name]
    collections = db.list_collection_names()
    
    for coll_name in collections[:20]:  # First 20 collections
        coll = db[coll_name]
        total = coll.count_documents({})
        
        # Check for enrichment
        enriched = coll.count_documents({
            '$or': [
                {'building_condition': {'$exists': True}},
                {'floor_plan_analysis': {'$exists': True}}
            ]
        })
        
        if total > 0:
            print(f"    {coll_name}: {total} docs, {enriched} enriched ({enriched/total*100:.0f}%)")
    
    if len(collections) > 20:
        print(f"    ... and {len(collections) - 20} more collections")

client.close()
