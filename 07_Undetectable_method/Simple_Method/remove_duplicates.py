#!/usr/bin/env python3
"""
MongoDB Duplicate Remover
Finds and removes duplicate property entries, keeping the most recently updated version
"""

from pymongo import MongoClient
from datetime import datetime
import sys
from collections import defaultdict

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "properties_for_sale"


def remove_duplicates(dry_run=True):
    """Find and remove duplicate properties by address"""
    try:
        print("="*80)
        print("MONGODB DUPLICATE REMOVER")
        print("="*80)
        print(f"\nDatabase: {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        if dry_run:
            print(f"\nMode: DRY RUN (no changes will be made)")
        else:
            print(f"\nMode: LIVE (duplicates will be removed)")
        
        # Connect
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Get all documents
        print(f"\n→ Scanning for duplicates...")
        docs = list(collection.find())
        
        if not docs:
            print(f"\n✓ No properties in database")
            client.close()
            return 0
        
        print(f"  Total documents: {len(docs)}")
        
        # Group by address (handle both string and dict formats)
        address_groups = defaultdict(list)
        for doc in docs:
            address_field = doc.get('address', '')
            
            # Handle address as dict (e.g., {'full': '...', 'suburb': '...', 'state': '...'})
            if isinstance(address_field, dict):
                address = address_field.get('full', '').strip().lower()
            # Handle address as string
            elif isinstance(address_field, str):
                address = address_field.strip().lower()
            else:
                address = ''
            
            if address:
                address_groups[address].append(doc)
        
        # Find duplicates
        duplicates_found = []
        for address, docs_list in address_groups.items():
            if len(docs_list) > 1:
                duplicates_found.append((address, docs_list))
        
        if not duplicates_found:
            print(f"\n✓ No duplicates found!")
            client.close()
            return 0
        
        # Process duplicates
        print(f"\n{'─'*80}")
        print(f"DUPLICATES FOUND: {len(duplicates_found)} addresses")
        print(f"{'─'*80}")
        
        total_to_remove = 0
        removal_plan = []
        
        for address, docs_list in duplicates_found:
            # Sort by last_updated (most recent first)
            sorted_docs = sorted(
                docs_list,
                key=lambda x: x.get('last_updated', datetime.min),
                reverse=True
            )
            
            # Keep the first (most recent), remove the rest
            keep_doc = sorted_docs[0]
            remove_docs = sorted_docs[1:]
            
            print(f"\n  Address: {address}")
            print(f"  Duplicates: {len(docs_list)}")
            print(f"  ✓ Keeping:  {keep_doc.get('_id')} (updated: {keep_doc.get('last_updated', 'N/A')})")
            
            for doc in remove_docs:
                print(f"  ✗ Removing: {doc.get('_id')} (updated: {doc.get('last_updated', 'N/A')})")
                removal_plan.append(doc['_id'])
                total_to_remove += 1
        
        print(f"\n{'─'*80}")
        print(f"SUMMARY")
        print(f"{'─'*80}")
        print(f"  Duplicate addresses: {len(duplicates_found)}")
        print(f"  Total documents to remove: {total_to_remove}")
        
        # Remove duplicates if not dry run
        if not dry_run and total_to_remove > 0:
            print(f"\n→ Removing {total_to_remove} duplicate documents...")
            result = collection.delete_many({'_id': {'$in': removal_plan}})
            print(f"  ✓ Removed {result.deleted_count} documents")
            
            # Verify
            remaining = collection.count_documents({})
            print(f"  ✓ Remaining documents: {remaining}")
        elif dry_run and total_to_remove > 0:
            print(f"\n⚠ DRY RUN mode - no changes made")
            print(f"  Run with --remove flag to actually remove duplicates")
        
        print(f"\n{'='*80}\n")
        
        client.close()
        return total_to_remove
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return -1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove duplicate properties from MongoDB")
    parser.add_argument('--remove', action='store_true', 
                       help='Actually remove duplicates (default is dry-run)')
    args = parser.parse_args()
    
    dry_run = not args.remove
    
    count = remove_duplicates(dry_run=dry_run)
    
    if count < 0:
        sys.exit(1)
    elif count == 0:
        sys.exit(0)
    else:
        sys.exit(0 if not dry_run else 2)  # Exit code 2 for dry-run with duplicates found
