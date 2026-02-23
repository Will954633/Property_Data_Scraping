#!/usr/bin/env python3
"""
Off-Market Properties Remover
Identifies and removes properties from MongoDB that are not currently for sale
(properties without active listing URLs)
"""

from pymongo import MongoClient
from datetime import datetime
import sys

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "properties_for_sale"


def remove_offmarket_properties(dry_run=True):
    """Remove properties that don't have listing URLs (not for sale)"""
    try:
        print("="*80)
        print("OFF-MARKET PROPERTIES REMOVER")
        print("="*80)
        print(f"\nDatabase: {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        if dry_run:
            print(f"\nMode: DRY RUN (no changes will be made)")
        else:
            print(f"\nMode: LIVE (off-market properties will be removed)")
        
        # Connect
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Find properties without listing URLs
        print(f"\n→ Scanning for off-market properties...")
        
        # Query for properties that either:
        # 1. Don't have enrichment_data field
        # 2. Have enrichment_data but no listing_url
        # 3. Have listing_url but it's null/empty
        
        offmarket_queries = [
            # No enrichment data at all
            {"enrichment_data": {"$exists": False}},
            # Enrichment data exists but no listing_url field
            {"enrichment_data": {"$exists": True}, "enrichment_data.listing_url": {"$exists": False}},
            # Has listing_url but it's null
            {"enrichment_data.listing_url": None},
            # Has listing_url but it's empty string
            {"enrichment_data.listing_url": ""}
        ]
        
        offmarket_properties = []
        offmarket_ids = set()
        
        for query in offmarket_queries:
            props = list(collection.find(query))
            for prop in props:
                if prop['_id'] not in offmarket_ids:
                    offmarket_properties.append(prop)
                    offmarket_ids.add(prop['_id'])
        
        if not offmarket_properties:
            print(f"\n✓ No off-market properties found")
            print(f"  All properties in database have active listings")
            client.close()
            return 0
        
        # Display off-market properties
        print(f"\n{'─'*80}")
        print(f"OFF-MARKET PROPERTIES FOUND: {len(offmarket_properties)}")
        print(f"{'─'*80}\n")
        
        for i, prop in enumerate(offmarket_properties, 1):
            address = prop.get('address', 'N/A')
            first_seen = prop.get('first_seen', 'N/A')
            enriched = prop.get('enriched', False)
            
            if isinstance(first_seen, datetime):
                first_seen = first_seen.strftime("%Y-%m-%d")
            
            print(f"  {i}. {address}")
            print(f"     First seen: {first_seen}")
            print(f"     Enriched: {enriched}")
            print(f"     Status: No active listing found")
        
        print(f"\n{'─'*80}")
        print(f"SUMMARY")
        print(f"{'─'*80}")
        print(f"  Total off-market properties: {len(offmarket_properties)}")
        
        # Remove if not dry run
        if not dry_run and len(offmarket_properties) > 0:
            print(f"\n→ Removing {len(offmarket_properties)} off-market properties...")
            
            removal_ids = [prop['_id'] for prop in offmarket_properties]
            result = collection.delete_many({'_id': {'$in': removal_ids}})
            
            print(f"  ✓ Removed {result.deleted_count} properties")
            
            # Verify
            remaining = collection.count_documents({})
            print(f"  ✓ Remaining properties: {remaining}")
        
        elif dry_run and len(offmarket_properties) > 0:
            print(f"\n⚠ DRY RUN mode - no changes made")
            print(f"  Run with --remove flag to actually remove off-market properties")
        
        print(f"\n{'='*80}\n")
        
        client.close()
        return len(offmarket_properties)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return -1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove off-market properties from MongoDB")
    parser.add_argument('--remove', action='store_true',
                       help='Actually remove off-market properties (default is dry-run)')
    args = parser.parse_args()
    
    dry_run = not args.remove
    
    count = remove_offmarket_properties(dry_run=dry_run)
    
    if count < 0:
        sys.exit(1)
    elif count == 0:
        sys.exit(0)
    else:
        sys.exit(0 if not dry_run else 2)  # Exit code 2 for dry-run with properties found
