#!/usr/bin/env python3
"""
Import Scraped JSON Files to MongoDB
Downloads JSON files from Google Cloud Storage and imports them into local MongoDB
"""

import json
import os
import sys
from pymongo import MongoClient
from datetime import datetime
from pathlib import Path
from bson.objectid import ObjectId

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"
SCRAPED_DATA_DIR = os.path.expanduser("~/scraped_property_data")


def import_data():
    """Import all JSON files into MongoDB"""
    
    print(f"\n{'='*70}")
    print("Import Scraped Data to MongoDB")
    print(f"{'='*70}\n")
    
    # Connect to MongoDB
    print(f"Connecting to MongoDB...")
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB at {MONGODB_URI}")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        sys.exit(1)
    
    db = client[DATABASE_NAME]
    
    # Find all JSON files
    print(f"\nScanning directory: {SCRAPED_DATA_DIR}")
    json_files = list(Path(SCRAPED_DATA_DIR).rglob("*.json"))
    print(f"Found {len(json_files):,} JSON files to import\n")
    
    if not json_files:
        print("No JSON files found. Please download data from GCS first:")
        print(f"  gsutil -m rsync -r gs://BUCKET/scraped_data/ {SCRAPED_DATA_DIR}/")
        sys.exit(1)
    
    # Import files
    successful = 0
    failed = 0
    skipped = 0
    
    start_time = datetime.now()
    
    for i, json_file in enumerate(json_files, 1):
        try:
            # Load JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                property_data = json.load(f)
            
            # Get metadata
            collection_name = property_data.get('collection')
            doc_id = property_data.get('doc_id')
            
            if not collection_name or not doc_id:
                print(f"[{i}/{len(json_files)}] ⚠ Skipping {json_file.name}: missing collection or doc_id")
                skipped += 1
                continue
            
            # Update MongoDB document
            collection = db[collection_name]
            
            result = collection.update_one(
                {'_id': ObjectId(doc_id)},
                {
                    '$set': {
                        'domain_data': property_data,
                        'domain_scraped_at': datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                successful += 1
            else:
                # Document might already have data or not exist
                if result.matched_count == 0:
                    print(f"[{i}/{len(json_files)}] ⚠ Document not found: {doc_id}")
                    failed += 1
                else:
                    # Document exists but wasn't modified (already had data)
                    successful += 1
            
            # Progress update
            if i % 100 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (len(json_files) - i) / rate if rate > 0 else 0
                
                print(f"[{i}/{len(json_files)}] {i/len(json_files)*100:.1f}% | "
                      f"Success: {successful:,} | Failed: {failed:,} | Skipped: {skipped:,} | "
                      f"Rate: {rate:.1f} files/sec | ETA: {remaining:.0f}s")
        
        except json.JSONDecodeError:
            print(f"[{i}/{len(json_files)}] ✗ Invalid JSON: {json_file}")
            failed += 1
        except Exception as e:
            print(f"[{i}/{len(json_files)}] ✗ Error: {json_file}: {e}")
            failed += 1
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*70}")
    print(f"Import Complete")
    print(f"{'='*70}")
    print(f"Total files:     {len(json_files):,}")
    print(f"Successful:      {successful:,} ({successful/len(json_files)*100:.1f}%)")
    print(f"Failed:          {failed:,} ({failed/len(json_files)*100:.1f}%)")
    print(f"Skipped:         {skipped:,} ({skipped/len(json_files)*100:.1f}%)")
    print(f"Duration:        {duration}")
    print(f"Rate:            {len(json_files) / duration.total_seconds():.1f} files/second")
    print(f"{'='*70}\n")
    
    # Verification
    print("Verification:")
    collections = db.list_collection_names()
    total_with_data = 0
    
    for collection_name in collections:
        count = db[collection_name].count_documents({'domain_data': {'$exists': True}})
        total_with_data += count
    
    print(f"Total documents with domain_data: {total_with_data:,}")
    print(f"Across {len(collections)} suburb collections\n")
    
    client.close()


if __name__ == "__main__":
    try:
        import_data()
    except KeyboardInterrupt:
        print("\n\n✗ Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
