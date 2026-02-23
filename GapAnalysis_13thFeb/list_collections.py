#!/usr/bin/env python3
"""
List all collections in Gold_Coast_Recently_Sold database
"""

import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("COSMOS_CONNECTION_STRING")
DATABASE_NAME = "Gold_Coast_Recently_Sold"

def list_collections():
    """List all collections and their document counts"""
    print("=" * 80)
    print("LISTING COLLECTIONS IN DATABASE")
    print("=" * 80)
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        
        print(f"\n✅ Connected to Azure Cosmos DB")
        print(f"   Database: {DATABASE_NAME}\n")
        
        # Get all collection names
        collections = db.list_collection_names()
        
        print(f"📊 Found {len(collections)} collections:\n")
        
        total_docs = 0
        for coll_name in sorted(collections):
            collection = db[coll_name]
            count = collection.count_documents({})
            total_docs += count
            print(f"   • {coll_name}: {count} documents")
            
            # Sample one document to see structure
            if count > 0:
                sample = collection.find_one()
                if sample:
                    print(f"      Sample fields: {list(sample.keys())[:10]}")
        
        print(f"\n{'=' * 80}")
        print(f"TOTAL: {total_docs} documents across {len(collections)} collections")
        print(f"{'=' * 80}\n")
        
        client.close()
        return collections
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return []


if __name__ == "__main__":
    list_collections()
