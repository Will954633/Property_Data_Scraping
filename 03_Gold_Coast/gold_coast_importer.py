#!/usr/bin/env python3
"""
Gold Coast Address Importer
Imports all Gold Coast addresses from Queensland property data into MongoDB.
Creates one collection per suburb with documents for each address.
"""

import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, BulkWriteError
from datetime import datetime
import re

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"
DATA_FILE = "/Users/projects/Documents/Fetcha_Addresses/QLD/DP_PROP_LOCATION_INDEX_QLD_20251103.txt"
FILTER_AUTHORITY = "GOLD COAST CITY"
BATCH_SIZE = 1000

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


def connect_to_mongodb():
    """Establish connection to MongoDB."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
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
    """Main import function."""
    start_time = datetime.now()
    print(f"\n{'='*70}")
    print("Gold Coast Address Importer")
    print(f"{'='*70}\n")
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    
    # Drop existing database if it exists (clean start)
    print(f"✓ Using database: {DATABASE_NAME}")
    if DATABASE_NAME in client.list_database_names():
        print(f"  Dropping existing database...")
        client.drop_database(DATABASE_NAME)
    
    # Statistics
    stats = {
        'total_processed': 0,
        'total_imported': 0,
        'suburbs': {},
        'errors': 0
    }
    
    # Batches per suburb
    suburb_batches = {}
    
    print(f"\n✓ Reading data from: {DATA_FILE}")
    print(f"✓ Filtering for: {FILTER_AUTHORITY}")
    print(f"\nProcessing addresses...\n")
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            # Skip header line
            header = f.readline()
            
            # Process each line
            for line_num, line in enumerate(f, start=2):
                stats['total_processed'] += 1
                
                # Progress indicator
                if stats['total_processed'] % 10000 == 0:
                    print(f"  Processed: {stats['total_processed']:,} lines | "
                          f"Imported: {stats['total_imported']:,} addresses | "
                          f"Suburbs: {len(stats['suburbs'])}")
                
                # Parse the line
                document = parse_line(line)
                if not document:
                    stats['errors'] += 1
                    continue
                
                # Filter for Gold Coast City
                if document.get('LOCAL_AUTHORITY') != FILTER_AUTHORITY:
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
                        collection.insert_many(suburb_batches[collection_name], ordered=False)
                        stats['total_imported'] += len(suburb_batches[collection_name])
                        suburb_batches[collection_name] = []
                    except BulkWriteError as e:
                        stats['errors'] += len(e.details.get('writeErrors', []))
                        stats['total_imported'] += e.details.get('nInserted', 0)
                        suburb_batches[collection_name] = []
        
        # Insert remaining batches
        print("\n✓ Inserting remaining batches...")
        for collection_name, batch in suburb_batches.items():
            if batch:
                try:
                    collection = db[collection_name]
                    collection.insert_many(batch, ordered=False)
                    stats['total_imported'] += len(batch)
                except BulkWriteError as e:
                    stats['errors'] += len(e.details.get('writeErrors', []))
                    stats['total_imported'] += e.details.get('nInserted', 0)
        
    except FileNotFoundError:
        print(f"\n✗ Error: Data file not found: {DATA_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*70}")
    print("Import Summary")
    print(f"{'='*70}\n")
    print(f"Total lines processed:    {stats['total_processed']:,}")
    print(f"Total addresses imported: {stats['total_imported']:,}")
    print(f"Total suburbs:            {len(stats['suburbs'])}")
    print(f"Errors encountered:       {stats['errors']}")
    print(f"Duration:                 {duration}")
    print(f"\nDatabase: {DATABASE_NAME}")
    print(f"Collections created:      {len(suburb_batches)}")
    
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
    
    print(f"\n{'='*70}")
    print("✓ Import completed successfully!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        import_addresses()
    except KeyboardInterrupt:
        print("\n\n✗ Import interrupted by user")
        sys.exit(1)
