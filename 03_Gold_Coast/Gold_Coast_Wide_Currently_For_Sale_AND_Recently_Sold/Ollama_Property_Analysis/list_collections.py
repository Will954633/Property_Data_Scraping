 #!/usr/bin/env python3
# Last Edit: 31/01/2026, Friday, 7:53 pm (Brisbane Time)
"""
List all collections in the Gold_Coast_Currently_For_Sale database.
"""
from pymongo import MongoClient
from config import MONGODB_URI, DATABASE_NAME

def main():
    print("=" * 80)
    print("MONGODB COLLECTIONS LISTING")
    print("=" * 80)
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    print(f"\nDatabase: {DATABASE_NAME}")
    
    # List all collections
    collections = db.list_collection_names()
    
    print(f"\nFound {len(collections)} collections:\n")
    
    for i, coll_name in enumerate(sorted(collections), 1):
        count = db[coll_name].count_documents({})
        print(f"{i:2d}. {coll_name:30s} - {count:,} documents")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("\nUpdate config.py with the correct COLLECTION_NAME.")
    print("Look for collections that match your target suburbs:")
    print("  - robina")
    print("  - mudgeeraba")
    print("  - varsity lakes")
    print("  - reedy creek")
    print("  - burleigh waters")
    print("  - merimac")
    print("  - warongary")
    
    client.close()

if __name__ == "__main__":
    main()
