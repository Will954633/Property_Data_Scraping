#!/usr/bin/env python3
"""
Migrate Floor Plan Data from Local MongoDB to Azure Cosmos DB
Last Edit: 16/02/2026, 5:34 PM (Sunday) — Brisbane Time

Description: Migrates enriched floor plan data from local MongoDB to Azure Cosmos DB.
The enrichment script wrote to local MongoDB instead of Azure, so we need to copy the data.

Edit History:
- 16/02/2026 5:34 PM: Initial creation
"""

from pymongo import MongoClient
from tqdm import tqdm

# Connection strings
LOCAL_MONGODB = "mongodb://localhost:27017/"
AZURE_COSMOS = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"

DATABASE_NAME = "Gold_Coast_Recently_Sold"

# Enrichment fields to migrate
ENRICHMENT_FIELDS = [
    'building_condition',
    'building_age',
    'busy_road',
    'corner_block',
    'parking',
    'outdoor_entertainment',
    'renovation_status',
    'north_facing'
]

def migrate_enrichment_data():
    """Migrate enrichment data from local MongoDB to Azure Cosmos DB"""
    
    print("="*80)
    print("FLOOR PLAN DATA MIGRATION: Local MongoDB → Azure Cosmos DB")
    print("="*80)
    
    # Connect to both databases
    print("\n1. Connecting to databases...")
    local_client = MongoClient(LOCAL_MONGODB, serverSelectionTimeoutMS=5000)
    azure_client = MongoClient(AZURE_COSMOS, serverSelectionTimeoutMS=30000)
    
    local_db = local_client[DATABASE_NAME]
    azure_db = azure_client[DATABASE_NAME]
    
    print(f"   ✓ Connected to local MongoDB")
    print(f"   ✓ Connected to Azure Cosmos DB")
    
    # Get collections
    collections = local_db.list_collection_names()
    print(f"\n2. Found {len(collections)} collections in local database")
    
    total_migrated = 0
    total_properties = 0
    
    for collection_name in collections:
        local_coll = local_db[collection_name]
        azure_coll = azure_db[collection_name]
        
        # Find properties with enrichment data in local
        query = {'$or': [{field: {'$exists': True}} for field in ENRICHMENT_FIELDS]}
        enriched_properties = list(local_coll.find(query))
        
        if not enriched_properties:
            continue
        
        print(f"\n   {collection_name}: {len(enriched_properties)} properties with enrichment")
        total_properties += len(enriched_properties)
        
        # Migrate each property
        for prop in tqdm(enriched_properties, desc=f"   Migrating {collection_name}"):
            # Extract enrichment fields
            enrichment_data = {}
            for field in ENRICHMENT_FIELDS:
                if field in prop:
                    enrichment_data[field] = prop[field]
            
            if not enrichment_data:
                continue
            
            # Update in Azure
            result = azure_coll.update_one(
                {'_id': prop['_id']},
                {'$set': enrichment_data}
            )
            
            if result.modified_count > 0 or result.matched_count > 0:
                total_migrated += 1
    
    print(f"\n{'='*80}")
    print(f"MIGRATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total properties with enrichment: {total_properties}")
    print(f"Total properties migrated: {total_migrated}")
    print(f"\nEnrichment fields migrated:")
    for field in ENRICHMENT_FIELDS:
        print(f"  - {field}")
    
    local_client.close()
    azure_client.close()

if __name__ == "__main__":
    try:
        migrate_enrichment_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
