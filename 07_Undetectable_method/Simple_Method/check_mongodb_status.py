#!/usr/bin/env python3
"""
MongoDB Status Checker
Check the status of properties in MongoDB - how many are enriched vs unenriched
"""

from pymongo import MongoClient
from datetime import datetime
import sys

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "properties_for_sale"


def check_status():
    """Check and display MongoDB status"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Get counts
        total = collection.count_documents({})
        enriched = collection.count_documents({"enriched": True})
        unenriched = collection.count_documents({"enriched": False})
        attempted = collection.count_documents({"enrichment_attempted": True})
        failed = collection.count_documents({"enrichment_error": {"$ne": None}})
        
        print("="*80)
        print("MONGODB STATUS - PROPERTY DATA")
        print("="*80)
        print(f"\nDatabase: {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        print(f"MongoDB URI: {MONGODB_URI}")
        print(f"\n{'─'*80}")
        print("SUMMARY")
        print(f"{'─'*80}")
        print(f"  Total properties:        {total}")
        print(f"  Enriched:                {enriched}")
        print(f"  Unenriched:              {unenriched}")
        print(f"  Enrichment attempted:    {attempted}")
        print(f"  Failed enrichments:      {failed}")
        
        if total > 0:
            print(f"\n  Completion rate:         {(enriched/total*100):.1f}%")
        
        # Show some recent additions
        print(f"\n{'─'*80}")
        print("RECENT PROPERTIES (Last 5)")
        print(f"{'─'*80}")
        
        recent = collection.find().sort("first_seen", -1).limit(5)
        for i, prop in enumerate(recent, 1):
            addr = prop.get('address', 'N/A')
            enriched_status = "✓" if prop.get('enriched') else "✗"
            first_seen = prop.get('first_seen', 'N/A')
            if isinstance(first_seen, datetime):
                first_seen = first_seen.strftime("%Y-%m-%d %H:%M")
            print(f"  {i}. [{enriched_status}] {addr}")
            print(f"      Added: {first_seen}")
        
        # Show properties needing enrichment
        needs_enrichment = collection.count_documents({
            "enriched": False,
            "enrichment_attempted": {"$ne": True}
        })
        
        if needs_enrichment > 0:
            print(f"\n{'─'*80}")
            print(f"PROPERTIES NEEDING ENRICHMENT ({needs_enrichment})")
            print(f"{'─'*80}")
            
            pending = collection.find({
                "enriched": False,
                "enrichment_attempted": {"$ne": True}
            }).limit(10)
            
            for i, prop in enumerate(pending, 1):
                addr = prop.get('address', 'N/A')
                print(f"  {i}. {addr}")
            
            if needs_enrichment > 10:
                print(f"  ... and {needs_enrichment - 10} more")
        
        # Show failed enrichments
        if failed > 0:
            print(f"\n{'─'*80}")
            print(f"FAILED ENRICHMENTS ({failed})")
            print(f"{'─'*80}")
            
            failures = collection.find({
                "enrichment_error": {"$ne": None}
            }).limit(5)
            
            for i, prop in enumerate(failures, 1):
                addr = prop.get('address', 'N/A')
                error = prop.get('enrichment_error', 'Unknown error')
                retry_count = prop.get('enrichment_retry_count', 0)
                print(f"  {i}. {addr}")
                print(f"      Error: {error}")
                print(f"      Retries: {retry_count}")
        
        print(f"\n{'='*80}\n")
        
        client.close()
        return 0
        
    except Exception as e:
        print(f"\n✗ Error connecting to MongoDB: {e}\n")
        print("Make sure MongoDB is running:")
        print("  brew services start mongodb-community")
        print(f"\nOr check if MongoDB is accessible at: {MONGODB_URI}\n")
        return 1


if __name__ == "__main__":
    sys.exit(check_status())
