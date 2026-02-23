#!/usr/bin/env python3
"""
Clear MongoDB Collections for Specific Suburbs
Last Updated: 31/01/2026, 11:02 am (Brisbane Time)

PURPOSE:
Clear specific suburb collections from Gold_Coast_Currently_For_Sale database
to allow fresh scraping with new functionality.

USAGE:
python3 clear_collections.py --suburbs robina varsity_lakes
python3 clear_collections.py --suburbs robina  # Single suburb
python3 clear_collections.py --all  # Clear all collections (use with caution!)
"""

import os
import argparse
from pymongo import MongoClient
from datetime import datetime

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
DATABASE_NAME = 'Gold_Coast_Currently_For_Sale'


def clear_collections(suburb_names: list, confirm: bool = True):
    """Clear specified collections from MongoDB"""
    
    print("\n" + "=" * 80)
    print("MONGODB COLLECTION CLEANER")
    print("=" * 80)
    print(f"\nDatabase: {DATABASE_NAME}")
    print(f"Collections to clear: {', '.join(suburb_names)}")
    print("=" * 80)
    
    # Connect to MongoDB
    print(f"\n→ Connecting to MongoDB...")
    try:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        mongo_client.admin.command('ping')
        print(f"  ✓ MongoDB connected")
    except Exception as e:
        print(f"  ✗ MongoDB connection failed: {e}")
        return 1
    
    db = mongo_client[DATABASE_NAME]
    
    # Get current document counts
    print(f"\n→ Current document counts:")
    collection_stats = {}
    for suburb in suburb_names:
        collection = db[suburb]
        count = collection.count_documents({})
        collection_stats[suburb] = count
        print(f"  {suburb}: {count} documents")
    
    # Confirmation
    if confirm:
        total_docs = sum(collection_stats.values())
        print(f"\n⚠️  WARNING: This will delete {total_docs} documents from {len(suburb_names)} collection(s)!")
        response = input("Type 'YES' to confirm deletion: ")
        
        if response != 'YES':
            print("\n✗ Operation cancelled")
            mongo_client.close()
            return 0
    
    # Clear collections
    print(f"\n→ Clearing collections...")
    cleared_stats = {}
    
    for suburb in suburb_names:
        try:
            collection = db[suburb]
            result = collection.delete_many({})
            cleared_stats[suburb] = result.deleted_count
            print(f"  ✓ {suburb}: Deleted {result.deleted_count} documents")
        except Exception as e:
            print(f"  ✗ {suburb}: Error - {e}")
            cleared_stats[suburb] = 0
    
    # Verify collections are empty
    print(f"\n→ Verifying collections are empty...")
    all_clear = True
    for suburb in suburb_names:
        collection = db[suburb]
        count = collection.count_documents({})
        if count == 0:
            print(f"  ✓ {suburb}: Empty (0 documents)")
        else:
            print(f"  ⚠ {suburb}: Still has {count} documents!")
            all_clear = False
    
    # Summary
    print(f"\n{'='*80}")
    print("CLEARING COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 SUMMARY:")
    total_cleared = sum(cleared_stats.values())
    print(f"  Collections cleared: {len(suburb_names)}")
    print(f"  Total documents deleted: {total_cleared}")
    print(f"  Status: {'✅ All collections empty' if all_clear else '⚠️ Some collections not empty'}")
    print(f"\n{'='*80}\n")
    
    mongo_client.close()
    return 0


def list_all_collections():
    """List all collections in the database"""
    print("\n" + "=" * 80)
    print("AVAILABLE COLLECTIONS")
    print("=" * 80)
    
    try:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        mongo_client.admin.command('ping')
        db = mongo_client[DATABASE_NAME]
        
        collections = db.list_collection_names()
        
        if not collections:
            print("\nNo collections found in database")
        else:
            print(f"\nDatabase: {DATABASE_NAME}")
            print(f"Total collections: {len(collections)}\n")
            
            for collection_name in sorted(collections):
                collection = db[collection_name]
                count = collection.count_documents({})
                print(f"  {collection_name}: {count} documents")
        
        print(f"\n{'='*80}\n")
        mongo_client.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Clear MongoDB collections for specific suburbs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 clear_collections.py --suburbs robina varsity_lakes
  python3 clear_collections.py --suburbs robina
  python3 clear_collections.py --list
  python3 clear_collections.py --all --no-confirm
        """
    )
    
    parser.add_argument('--suburbs', nargs='+', help='Suburb collection names to clear (e.g., robina varsity_lakes)')
    parser.add_argument('--all', action='store_true', help='Clear ALL collections (use with caution!)')
    parser.add_argument('--list', action='store_true', help='List all available collections')
    parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # List collections
    if args.list:
        list_all_collections()
        return 0
    
    # Determine which collections to clear
    if args.all:
        # Get all collections
        try:
            mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
            db = mongo_client[DATABASE_NAME]
            suburb_names = db.list_collection_names()
            mongo_client.close()
            
            if not suburb_names:
                print("\n✗ No collections found in database")
                return 0
                
        except Exception as e:
            print(f"\n✗ Error connecting to MongoDB: {e}")
            return 1
    
    elif args.suburbs:
        suburb_names = args.suburbs
    
    else:
        parser.print_help()
        return 0
    
    # Clear collections
    return clear_collections(suburb_names, confirm=not args.no_confirm)


if __name__ == "__main__":
    exit(main())
