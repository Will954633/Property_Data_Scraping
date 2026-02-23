#!/usr/bin/env python3
"""Quick database check - just list databases and collections"""

from pymongo import MongoClient

COSMOS_CONNECTION_STRING = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"

print("Connecting to Azure Cosmos DB...")
client = MongoClient(COSMOS_CONNECTION_STRING, serverSelectionTimeoutMS=30000)

print("\nDatabases:")
for db_name in client.list_database_names():
    print(f"  - {db_name}")
    db = client[db_name]
    collections = db.list_collection_names()
    print(f"    Collections ({len(collections)}): {', '.join(collections[:10])}")
    if len(collections) > 10:
        print(f"    ... and {len(collections) - 10} more")
    
    # Quick count
    total = 0
    for coll_name in collections:
        try:
            count = db[coll_name].count_documents({})
            total += count
        except:
            pass
    print(f"    Total documents: ~{total}")

client.close()
print("\nDone!")
