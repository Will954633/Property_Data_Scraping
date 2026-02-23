#!/usr/bin/env python3
"""
Gold Coast Postcode Enrichment Script
Enriches Gold Coast addresses in MongoDB with postcode data from Australian Postcodes CSV.
Uses MongoDB best practices for stable, resumable updates.
"""

import sys
import csv
import json
import os
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, BulkWriteError, AutoReconnect
from datetime import datetime

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"
POSTCODE_CSV = "/Users/projects/Documents/Fetcha_Addresses/Australian_Postcodes/geocoded_postcode_file_pc004_05112025.csv"
PROGRESS_FILE = "03_Gold_Coast/postcode_enrichment_progress.json"

# OPTIMIZED SETTINGS
BATCH_SIZE = 100              # Smaller batches for updates
BATCH_DELAY = 0.1             # Slightly longer delay for updates
CHECKPOINT_DELAY = 2.0        # Pause at checkpoints


def load_progress():
    """Load progress from file if it exists."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Warning: Could not load progress file: {e}")
            return None
    return None


def save_progress(progress):
    """Save progress to file."""
    try:
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        print(f"⚠ Warning: Could not save progress: {e}")


def connect_to_mongodb():
    """Establish connection to MongoDB with extended timeouts."""
    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=30000,
            socketTimeoutMS=60000,
            connectTimeoutMS=30000,
            maxPoolSize=50
        )
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB at {MONGODB_URI}")
        return client
    except ConnectionFailure as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)


def load_postcode_mapping():
    """Load postcode data from CSV and create locality-to-postcode mapping."""
    print(f"\n✓ Loading postcode data from: {POSTCODE_CSV}")
    
    postcode_map = {}
    qld_count = 0
    
    try:
        with open(POSTCODE_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only process QLD postcodes
                if row['State'] == 'QLD':
                    locality = row['Locality'].upper()
                    postcode = row['Pcode']
                    
                    # Store postcode info
                    postcode_map[locality] = {
                        'postcode': postcode,
                        'category': row['Category'],
                        'comments': row['Comments']
                    }
                    qld_count += 1
        
        print(f"✓ Loaded {qld_count:,} QLD postcodes")
        return postcode_map
        
    except FileNotFoundError:
        print(f"✗ Error: Postcode CSV file not found: {POSTCODE_CSV}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error loading postcode data: {e}")
        sys.exit(1)


def enrich_postcodes():
    """Main enrichment function."""
    start_time = datetime.now()
    print(f"\n{'='*70}")
    print("Gold Coast Postcode Enrichment - Optimized")
    print(f"{'='*70}\n")
    
    # Load existing progress
    existing_progress = load_progress()
    completed_collections = set(existing_progress.get('completed_collections', [])) if existing_progress else set()
    
    if existing_progress and completed_collections:
        print(f"✓ Found existing progress:")
        print(f"  Completed collections: {len(completed_collections)}")
        response = input("\nResume from last checkpoint? (y/n): ")
        if response.lower() != 'y':
            print("✓ Starting fresh enrichment\n")
            completed_collections = set()
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    
    # Load postcode mapping
    postcode_map = load_postcode_mapping()
    
    # Get all collections
    all_collections = db.list_collection_names()
    print(f"\n✓ Found {len(all_collections)} collections in database")
    
    # Filter to collections that need processing
    collections_to_process = [c for c in all_collections if c not in completed_collections]
    
    if not collections_to_process:
        print("\n✓ All collections already enriched!")
        return
    
    print(f"✓ Collections to process: {len(collections_to_process)}")
    print(f"\n📊 Enrichment Settings:")
    print(f"  Batch Size: {BATCH_SIZE}")
    print(f"  Batch Delay: {BATCH_DELAY}s")
    print(f"  Checkpoint Delay: {CHECKPOINT_DELAY}s")
    print(f"\nProcessing collections...\n")
    
    # Statistics
    stats = {
        'total_collections': len(all_collections),
        'processed_collections': 0,
        'total_updated': 0,
        'total_skipped': 0,
        'no_postcode_match': []
    }
    
    try:
        for idx, collection_name in enumerate(collections_to_process, 1):
            collection = db[collection_name]
            
            # Get sample document to determine locality
            sample_doc = collection.find_one()
            if not sample_doc:
                print(f"[{idx}/{len(collections_to_process)}] {collection_name:30s} SKIPPED (empty)")
                completed_collections.add(collection_name)
                continue
            
            locality = sample_doc.get('LOCALITY', '').upper()
            
            # Check if we have postcode data for this locality
            if locality not in postcode_map:
                print(f"[{idx}/{len(collections_to_process)}] {collection_name:30s} NO POSTCODE DATA")
                stats['no_postcode_match'].append(locality)
                completed_collections.add(collection_name)
                continue
            
            postcode_info = postcode_map[locality]
            doc_count = collection.count_documents({})
            
            print(f"[{idx}/{len(collections_to_process)}] {collection_name:30s} ({doc_count:6,} docs) → {postcode_info['postcode']}")
            
            # Update documents in batches
            updated = 0
            cursor = collection.find({})
            batch_updates = []
            
            for doc in cursor:
                # Prepare update
                batch_updates.append({
                    '_id': doc['_id'],
                    'POSTCODE': postcode_info['postcode'],
                    'POSTCODE_CATEGORY': postcode_info['category']
                })
                
                # Execute batch update
                if len(batch_updates) >= BATCH_SIZE:
                    try:
                        # Use bulk write for efficiency
                        from pymongo import UpdateOne
                        operations = [
                            UpdateOne(
                                {'_id': update['_id']},
                                {'$set': {
                                    'POSTCODE': update['POSTCODE'],
                                    'POSTCODE_CATEGORY': update['POSTCODE_CATEGORY']
                                }}
                            )
                            for update in batch_updates
                        ]
                        result = collection.bulk_write(operations, ordered=False)
                        updated += result.modified_count
                        batch_updates = []
                        
                        # Give MongoDB breathing room
                        time.sleep(BATCH_DELAY)
                        
                    except BulkWriteError as e:
                        updated += e.details.get('nModified', 0)
                        batch_updates = []
                    except AutoReconnect as e:
                        print(f"\n⚠ Connection lost: {e}")
                        save_progress({
                            'completed_collections': list(completed_collections),
                            'last_collection': collection_name,
                            'total_updated': stats['total_updated']
                        })
                        print("✓ Progress saved. Please restart the script to resume.")
                        sys.exit(1)
            
            # Process remaining batch
            if batch_updates:
                try:
                    from pymongo import UpdateOne
                    operations = [
                        UpdateOne(
                            {'_id': update['_id']},
                            {'$set': {
                                'POSTCODE': update['POSTCODE'],
                                'POSTCODE_CATEGORY': update['POSTCODE_CATEGORY']
                            }}
                        )
                        for update in batch_updates
                    ]
                    result = collection.bulk_write(operations, ordered=False)
                    updated += result.modified_count
                except BulkWriteError as e:
                    updated += e.details.get('nModified', 0)
            
            stats['total_updated'] += updated
            stats['processed_collections'] += 1
            completed_collections.add(collection_name)
            
            # Save progress periodically
            if idx % 10 == 0:
                save_progress({
                    'completed_collections': list(completed_collections),
                    'last_collection': collection_name,
                    'total_updated': stats['total_updated']
                })
                print(f"  💾 Progress saved ({stats['processed_collections']} collections)")
                time.sleep(CHECKPOINT_DELAY)
        
        # Final progress save
        save_progress({
            'completed_collections': list(completed_collections),
            'total_updated': stats['total_updated'],
            'completed': True
        })
        
    except KeyboardInterrupt:
        print(f"\n\n⚠ Enrichment interrupted by user")
        save_progress({
            'completed_collections': list(completed_collections),
            'total_updated': stats['total_updated']
        })
        print("✓ Progress saved. Run the script again to resume.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error during enrichment: {e}")
        import traceback
        traceback.print_exc()
        save_progress({
            'completed_collections': list(completed_collections),
            'total_updated': stats['total_updated']
        })
        sys.exit(1)
    
    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*70}")
    print("Enrichment Summary")
    print(f"{'='*70}\n")
    print(f"Total collections:        {stats['total_collections']}")
    print(f"Collections processed:    {stats['processed_collections']}")
    print(f"Total documents updated:  {stats['total_updated']:,}")
    print(f"Duration:                 {duration}")
    
    if stats['no_postcode_match']:
        print(f"\n⚠ Localities without postcode match ({len(stats['no_postcode_match'])}):")
        for locality in sorted(set(stats['no_postcode_match'])):
            print(f"  - {locality}")
    
    print(f"\n{'='*70}")
    print("✅ Enrichment completed successfully!")
    print(f"{'='*70}\n")
    
    # Verify enrichment
    print("Verifying enrichment...")
    sample_collections = ['biggera_waters', 'surfers_paradise', 'southport']
    for coll_name in sample_collections:
        if coll_name in all_collections:
            doc = db[coll_name].find_one()
            if doc:
                postcode = doc.get('POSTCODE', 'NOT SET')
                print(f"  {coll_name:30s} → POSTCODE: {postcode}")
    
    print(f"\n✓ Progress file saved for reference: {PROGRESS_FILE}\n")


if __name__ == "__main__":
    try:
        enrich_postcodes()
    except KeyboardInterrupt:
        print("\n\n✗ Enrichment interrupted by user")
        sys.exit(1)
