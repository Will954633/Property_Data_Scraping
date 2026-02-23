#!/usr/bin/env python3
"""
Enrich Gold Coast Addresses with Postcodes
Matches addresses to postcodes using geographic coordinates
"""

import csv
import sys
from pymongo import MongoClient
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"
POSTCODE_CSV = "/Users/projects/Documents/Fetcha_Addresses/Australian_Postcodes/geocoded_postcode_file_pc004_05112025.csv"


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r


def load_postcodes():
    """Load postcode data from CSV"""
    postcodes = []
    
    print("Loading postcode data...")
    
    with open(POSTCODE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Only process QLD postcodes with coordinates
            if row.get('State') == 'QLD' and row.get('Longitude') and row.get('Latitude'):
                try:
                    postcodes.append({
                        'postcode': row['Pcode'],
                        'locality': row['Locality'],
                        'longitude': float(row['Longitude']),
                        'latitude': float(row['Latitude']),
                        'category': row.get('Category', '')
                    })
                except ValueError:
                    continue
    
    # Filter for delivery areas only (not PO boxes)
    postcodes = [p for p in postcodes if 'Delivery Area' in p.get('category', '')]
    
    print(f"✓ Loaded {len(postcodes):,} QLD postcodes with coordinates\n")
    
    return postcodes


def find_nearest_postcode(lat, lon, postcodes, max_distance_km=5.0):
    """
    Find the nearest postcode to given coordinates
    Returns (postcode, distance_km) or (None, None) if none within max_distance
    """
    if not lat or not lon:
        return None, None
    
    nearest_postcode = None
    nearest_distance = float('inf')
    
    for pc_data in postcodes:
        distance = haversine_distance(lat, lon, pc_data['latitude'], pc_data['longitude'])
        
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_postcode = pc_data['postcode']
    
    # Only return if within reasonable distance (5km)
    if nearest_distance <= max_distance_km:
        return nearest_postcode, nearest_distance
    
    return None, nearest_distance


def enrich_postcodes():
    """Main enrichment function"""
    
    print(f"\n{'='*80}")
    print("Postcode Enrichment")
    print(f"{'='*80}\n")
    
    # Connect to MongoDB
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB\n")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        sys.exit(1)
    
    db = client[DATABASE_NAME]
    
    # Load postcodes
    postcodes = load_postcodes()
    
    if not postcodes:
        print("✗ No postcodes loaded")
        sys.exit(1)
    
    # Statistics
    stats = {
        'total_addresses': 0,
        'with_coordinates': 0,
        'postcodes_added': 0,
        'already_had_postcode': 0,
        'no_match_found': 0,
        'missing_coordinates': 0
    }
    
    # Get all collections
    collections = db.list_collection_names()
    print(f"Processing {len(collections)} suburb collections...\n")
    
    for i, collection_name in enumerate(collections, 1):
        collection = db[collection_name]
        
        # Get all documents
        docs = collection.find({})
        
        for doc in docs:
            stats['total_addresses'] += 1
            
            # Check if already has postcode
            if doc.get('POSTCODE'):
                stats['already_had_postcode'] += 1
                continue
            
            # Get coordinates
            lat = doc.get('LATITUDE')
            lon = doc.get('LONGITUDE')
            
            if not lat or not lon:
                stats['missing_coordinates'] += 1
                continue
            
            stats['with_coordinates'] += 1
            
            # Find nearest postcode
            postcode, distance = find_nearest_postcode(lat, lon, postcodes)
            
            if postcode:
                # Update document
                result = collection.update_one(
                    {'_id': doc['_id']},
                    {
                        '$set': {
                            'POSTCODE': postcode,
                            'postcode_distance_km': round(distance, 3),
                            'postcode_enriched_at': datetime.now()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    stats['postcodes_added'] += 1
            else:
                stats['no_match_found'] += 1
        
        # Progress update
        if i % 10 == 0 or i == len(collections):
            print(f"  [{i}/{len(collections)}] {collection_name.replace('_', ' ').title()}: "
                  f"+{stats['postcodes_added']:,} postcodes")
    
    # Summary
    print(f"\n{'='*80}")
    print("Enrichment Complete")
    print(f"{'='*80}")
    print(f"Total addresses:          {stats['total_addresses']:,}")
    print(f"Already had postcode:     {stats['already_had_postcode']:,}")
    print(f"With coordinates:         {stats['with_coordinates']:,}")
    print(f"Postcodes added:          {stats['postcodes_added']:,}")
    print(f"No match found:           {stats['no_match_found']:,}")
    print(f"Missing coordinates:      {stats['missing_coordinates']:,}")
    print(f"{'='*80}\n")
    
    # Show examples
    print("Sample Enriched Addresses:")
    print(f"{'='*80}\n")
    
    for collection_name in collections[:3]:
        collection = db[collection_name]
        
        sample = collection.find_one({'POSTCODE': {'$exists': True, '$ne': None}})
        if sample:
            address = f"{sample.get('STREET_NO_1', '')} {sample.get('STREET_NAME', '')} {sample.get('STREET_TYPE', '')}"
            print(f"{address.strip()}")
            print(f"  Suburb: {sample.get('LOCALITY')}")
            print(f"  Postcode: {sample.get('POSTCODE')}")
            print(f"  Coordinates: {sample.get('LATITUDE')}, {sample.get('LONGITUDE')}")
            print(f"  Match Distance: {sample.get('postcode_distance_km')} km")
            print()
    
    client.close()
    print("✓ Postcode enrichment complete\n")


if __name__ == "__main__":
    try:
        enrich_postcodes()
    except KeyboardInterrupt:
        print("\n\n✗ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
