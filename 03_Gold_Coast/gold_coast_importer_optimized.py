#!/usr/bin/env python3
"""
Gold Coast Address Importer - Optimized Version
Incorporates MongoDB import best practices for stable, resumable imports.
Creates one collection per suburb with documents for each address.

Based on lessons from importing 7M+ Australian addresses.
"""

import sys
import json
import os
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, BulkWriteError, AutoReconnect
from datetime import datetime
import re

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"
DATA_FILE = "/Users/projects/Documents/Fetcha_Addresses/QLD/DP_PROP_LOCATION_INDEX_QLD_20251103.txt"
FILTER_AUTHORITY = "GOLD COAST CITY"
PROGRESS_FILE = "03_Gold_Coast/import_progress.json"

# OPTIMIZED SETTINGS for ~331K records
# Based on best practices: 100K-1M records
BATCH_SIZE = 250              # Moderate batch size
BATCH_DELAY = 0.05            # Small delay between batches
SAVE_INTERVAL = 5000          # Save progress every 5k records
CHECKPOINT_DELAY = 2.0        # Pause at checkpoints

# Field names from the data file
FIELD_NAMES = [
    "ADDRESS_PID", "PLAN", "LOT", "LOTPLAN_STATUS", "ADDRESS_STATUS", 
    "ADDRESS_STANDARD", "UNIT_TYPE", "UNIT_NUMBER", "UNIT_SUFFIX", 
    "PROPERTY_NAME", "STREET_NO_1", "STREET_NO_1_SUFFIX", "STREET_NO_2", 
    "STREET_NO_2_SUFFIX", "STREET_NAME", "STREET_TYPE", "STREET_SUFFIX", 
    "LOCALITY", "LOCAL_AUTHORITY", "LGA_CODE", "LATITUDE", "LONGITUDE", 
    "GEOCODE_TYPE", "DATUM"
]


def sanitize_collection_name(name):
    """
    Sanitize suburb name to create valid MongoDB collection name.
    MongoDB collection names cannot contain: $ / \\ . " * < > : | ?
    """
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^\w]', '_', name)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Convert to lowercase for consistency
    return sanitized.lower()


def parse_line(line):
    """Parse a pipe-delimited line into a dictionary."""
    values = line.strip().split('|')
    if len(values) != len(FIELD_NAMES):
        return None
    
    # Create document with all fields
    document = {}
    for i, field_name in enumerate(FIELD_NAMES):
        value = values[i].strip()
        
        # Convert numeric fields to appropriate types
        if field_name in ["LATITUDE", "LONGITUDE"]:
            try:
                document[field_name] = float(value) if value else None
            except ValueError:
                document[field_name] = None
        elif field_name in ["ADDRESS_PID", "LGA_CODE"]:
            try:
                document[field_name] = int(value) if value else None
            except ValueError:
                # Some ADDRESS_PIDs might be negative or non-numeric
                document[field_name] = value if value else None
        else:
            # Keep as string
            document[field_name] = value if value else None
    
    return document


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
        # Ensure directory exists
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        print(f"⚠ Warning: Could not save progress: {e}")


def connect_to_mongodb():
    """Establish connection to MongoDB with extended timeouts."""
    try:
        # Extended timeouts for stability under load
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=30000,   # 30s
            socketTimeoutMS=60000,             # 60s  
            connectTimeoutMS=30000,            # 30s
            maxPoolSize=50                     # Adequate pool size
        )
        # Test connection
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB at {MONGODB_URI}")
        return client
    except ConnectionFailure as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        print("\nPlease ensure MongoDB is running:")
        print("  - Check if mongod is running: ps aux | grep mongod")
        print("  - Start MongoDB if needed: brew services start mongodb-community")
        sys.exit(1)


def import_addresses():
    """Main import function with progress tracking and error handling."""
    start_time = datetime.now()
    print(f"\n{'='*70}")
    print("Gold Coast Address Importer - Optimized")
    print(f"{'='*70}\n")
    
    # Check for resumable import
    existing_progress = load_progress()
    start_from = 0
    
    if existing_progress:
        print(f"✓ Found existing progress:")
        print(f"  Last processed: {existing_progress.get('last_processed', 0):,} lines")
        print(f"  Total imported: {existing_progress.get('total_imported', 0):,} addresses")
        response = input("\nResume from last checkpoint? (y/n): ")
        if response.lower() == 'y':
            start_from = existing_progress.get('last_processed', 0)
            print(f"✓ Resuming from line {start_from:,}\n")
        else:
            print("✓ Starting fresh import\n")
            existing_progress = None
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    
    # Drop existing database if starting fresh
    print(f"✓ Using database: {DATABASE_NAME}")
    if not existing_progress and DATABASE_NAME in client.list_database_names():
        print(f"  Dropping existing database...")
        client.drop_database(DATABASE_NAME)
    
    # Statistics
    stats = {
        'total_processed': existing_progress.get('last_processed', 0) if existing_progress else 0,
        'total_imported': existing_progress.get('total_imported', 0) if existing_progress else 0,
        'suburbs': existing_progress.get('suburbs', {}) if existing_progress else {},
        'errors': 0,
        'skipped': 0
    }
    
    # Batches per suburb
    suburb_batches = {}
    
    print(f"\n✓ Reading data from: {DATA_FILE}")
    print(f"✓ Filtering for: {FILTER_AUTHORITY}")
    print(f"\n📊 Import Settings:")
    print(f"  Batch Size: {BATCH_SIZE}")
    print(f"  Batch Delay: {BATCH_DELAY}s")
    print(f"  Save Interval: {SAVE_INTERVAL:,} records")
    print(f"  Checkpoint Delay: {CHECKPOINT_DELAY}s")
    print(f"\nProcessing addresses...\n")
    
    line_number = 0
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            # Skip header line
            header = f.readline()
            line_number = 1
            
            # Skip already processed lines if resuming
            if start_from > 1:
                print(f"⏭  Skipping to line {start_from:,}...")
                for _ in range(start_from - 1):
                    f.readline()
                    line_number += 1
            
            # Process each line
            for line in f:
                line_number += 1
                stats['total_processed'] = line_number
                
                # Progress indicator
                if (stats['total_processed'] - 1) % 10000 == 0:
                    print(f"  Processed: {stats['total_processed']:,} lines | "
                          f"Imported: {stats['total_imported']:,} addresses | "
                          f"Suburbs: {len(stats['suburbs'])} | "
                          f"Errors: {stats['errors']}")
                
                # Parse the line
                document = parse_line(line)
                if not document:
                    stats['errors'] += 1
                    continue
                
                # Filter for Gold Coast City
                if document.get('LOCAL_AUTHORITY') != FILTER_AUTHORITY:
                    stats['skipped'] += 1
                    continue
                
                # Get suburb/locality
                locality = document.get('LOCALITY')
                if not locality:
                    stats['errors'] += 1
                    continue
                
                # Track suburb
                if locality not in stats['suburbs']:
                    stats['suburbs'][locality] = 0
                stats['suburbs'][locality] += 1
                
                # Add to batch for this suburb
                collection_name = sanitize_collection_name(locality)
                if collection_name not in suburb_batches:
                    suburb_batches[collection_name] = []
                
                suburb_batches[collection_name].append(document)
                
                # Insert batch if it reaches BATCH_SIZE
                if len(suburb_batches[collection_name]) >= BATCH_SIZE:
                    try:
                        collection = db[collection_name]
                        result = collection.insert_many(
                            suburb_batches[collection_name], 
                            ordered=False
                        )
                        stats['total_imported'] += len(result.inserted_ids)
                        suburb_batches[collection_name] = []
                        
                        # CRITICAL: Small delay to give MongoDB breathing room
                        time.sleep(BATCH_DELAY)
                        
                    except BulkWriteError as e:
                        # Count partial success
                        inserted = e.details.get('nInserted', 0)
                        stats['total_imported'] += inserted
                        stats['errors'] += len(e.details.get('writeErrors', []))
                        suburb_batches[collection_name] = []
                        
                    except AutoReconnect as e:
                        print(f"\n⚠ Connection lost: {e}")
                        print(f"Saving progress at line {line_number:,}...")
                        save_progress({
                            'last_processed': line_number,
                            'total_imported': stats['total_imported'],
                            'suburbs': stats['suburbs']
                        })
                        print("✓ Progress saved. Please restart the script to resume.")
                        sys.exit(1)
                
                # Save progress checkpoint
                if (line_number % SAVE_INTERVAL == 0):
                    save_progress({
                        'last_processed': line_number,
                        'total_imported': stats['total_imported'],
                        'suburbs': stats['suburbs']
                    })
                    print(f"  💾 Progress saved at line {line_number:,}")
                    
                    # CRITICAL: Longer pause at checkpoints
                    time.sleep(CHECKPOINT_DELAY)
        
        # Insert remaining batches
        print("\n✓ Inserting remaining batches...")
        for collection_name, batch in suburb_batches.items():
            if batch:
                try:
                    collection = db[collection_name]
                    result = collection.insert_many(batch, ordered=False)
                    stats['total_imported'] += len(result.inserted_ids)
                except BulkWriteError as e:
                    # Count partial success
                    inserted = e.details.get('nInserted', 0)
                    stats['total_imported'] += inserted
                    stats['errors'] += len(e.details.get('writeErrors', []))
        
        # Final progress save
        save_progress({
            'last_processed': line_number,
            'total_imported': stats['total_imported'],
            'suburbs': stats['suburbs'],
            'completed': True
        })
        
    except FileNotFoundError:
        print(f"\n✗ Error: Data file not found: {DATA_FILE}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n⚠ Import interrupted by user at line {line_number:,}")
        save_progress({
            'last_processed': line_number,
            'total_imported': stats['total_imported'],
            'suburbs': stats['suburbs']
        })
        print("✓ Progress saved. Run the script again to resume.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error during import at line {line_number:,}: {e}")
        import traceback
        traceback.print_exc()
        save_progress({
            'last_processed': line_number,
            'total_imported': stats['total_imported'],
            'suburbs': stats['suburbs']
        })
        print("✓ Progress saved. Fix the error and run again to resume.")
        sys.exit(1)
    
    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*70}")
    print("Import Summary")
    print(f"{'='*70}\n")
    print(f"Total lines processed:    {stats['total_processed']:,}")
    print(f"Gold Coast addresses:     {stats['total_imported']:,}")
    print(f"Non-Gold Coast skipped:   {stats['skipped']:,}")
    print(f"Total suburbs:            {len(stats['suburbs'])}")
    print(f"Errors encountered:       {stats['errors']}")
    print(f"Duration:                 {duration}")
    print(f"\nDatabase: {DATABASE_NAME}")
    print(f"Collections created:      {len(db.list_collection_names())}")
    
    # Show suburb statistics (top 20)
    print(f"\n{'='*70}")
    print("Top 20 Suburbs by Address Count")
    print(f"{'='*70}\n")
    sorted_suburbs = sorted(stats['suburbs'].items(), key=lambda x: x[1], reverse=True)
    for suburb, count in sorted_suburbs[:20]:
        collection_name = sanitize_collection_name(suburb)
        print(f"  {suburb:40s} {count:6,} → {collection_name}")
    
    if len(sorted_suburbs) > 20:
        print(f"\n  ... and {len(sorted_suburbs) - 20} more suburbs")
    
    # Verify data integrity
    print(f"\n{'='*70}")
    print("Database Verification")
    print(f"{'='*70}\n")
    
    total_docs = 0
    for collection_name in db.list_collection_names():
        count = db[collection_name].count_documents({})
        total_docs += count
    
    print(f"Total documents in database: {total_docs:,}")
    print(f"Expected from import:        {stats['total_imported']:,}")
    
    if total_docs == stats['total_imported']:
        print(f"✓ Document counts match!")
    else:
        print(f"⚠ Warning: Document count mismatch!")
        print(f"  Difference: {abs(total_docs - stats['total_imported']):,}")
    
    print(f"\n{'='*70}")
    print("✅ Import completed successfully!")
    print(f"{'='*70}\n")
    
    # Clean up progress file on successful completion
    if os.path.exists(PROGRESS_FILE):
        # Keep the file but mark as completed
        print(f"✓ Progress file saved for reference: {PROGRESS_FILE}\n")


if __name__ == "__main__":
    try:
        import_addresses()
    except KeyboardInterrupt:
        print("\n\n✗ Import interrupted by user")
        sys.exit(1)
