#!/usr/bin/env python3
"""
Clear MongoDB Collection - Utility to clear properties_for_sale collection

Use this to start fresh before running a new scraping session.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from mongodb_saver import MongoDBSaver


def clear_collection():
    """Clear all properties from MongoDB collection"""
    print("\n" + "="*70)
    print("  CLEAR MONGODB COLLECTION")
    print("="*70)
    print("\n⚠️  WARNING: This will delete ALL properties from the collection!")
    print("   Database: property_data")
    print("   Collection: properties_for_sale")
    
    # Ask for confirmation
    response = input("\nAre you sure you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("\n❌ Operation cancelled")
        return
    
    try:
        with MongoDBSaver() as saver:
            # Get current count
            current_count = saver.get_property_count()
            print(f"\n📊 Current property count: {current_count}")
            
            if current_count == 0:
                print("\n✓ Collection is already empty")
                return
            
            # Clear collection
            print("\n🗑️  Clearing collection...")
            deleted_count = saver.clear_collection()
            
            print(f"\n✅ Successfully deleted {deleted_count} properties")
            print(f"📊 New property count: {saver.get_property_count()}")
            
            print("\n" + "="*70)
            print("✅ COLLECTION CLEARED")
            print("="*70)
            print("\nYou can now run fresh scraping sessions:")
            print("  python 3_replay/replay_engine.py --suburb robina --session 1")
            print("  python 3_replay/replay_engine.py --suburb mudgeeraba --session 1")
            print()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure MongoDB is running:")
        print("  brew services start mongodb-community")
        sys.exit(1)


if __name__ == "__main__":
    clear_collection()
