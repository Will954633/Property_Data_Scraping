#!/usr/bin/env python3
"""
Build comprehensive POI database for Gold Coast region
One-time execution to collect all POIs
"""

import os
import sys
from pymongo import MongoClient
from datetime import datetime
import time
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_client import GooglePlacesClient

# Load environment variables
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
MONGODB_POI_DATABASE = os.getenv('MONGODB_POI_DATABASE', 'Gold_Coast_POIs')

# Gold Coast bounds
NORTH = -27.75
SOUTH = -28.20
WEST = 153.25
EAST = 153.55

# Grid configuration
GRID_SPACING = 0.08  # ~8km spacing
SEARCH_RADIUS = 5000  # 5km radius

# POI Categories
POI_CATEGORIES = {
    'primary_school': ['primary_school'],
    'secondary_school': ['secondary_school'],
    'childcare': ['child_care'],
    'supermarket': ['supermarket'],
    'shopping_mall': ['shopping_mall'],
    'hospital': ['hospital'],
    'medical_center': ['medical_center'],
    'park': ['park'],
    'pharmacy': ['pharmacy'],
    'public_transport': ['bus_station', 'train_station', 'light_rail_station']
}

def generate_grid_points():
    """Generate grid of search points covering Gold Coast"""
    grid_points = []
    
    lat = NORTH
    grid_row = 0
    
    while lat >= SOUTH:
        lon = WEST
        grid_col = 0
        
        while lon <= EAST:
            grid_points.append({
                'latitude': lat,
                'longitude': lon,
                'grid_cell': f"grid_{grid_row}_{grid_col}"
            })
            lon += GRID_SPACING
            grid_col += 1
        
        lat -= GRID_SPACING
        grid_row += 1
    
    return grid_points

def collect_pois_for_grid_point(api_client, grid_point, poi_collection):
    """Collect all POIs around a grid point"""
    lat = grid_point['latitude']
    lon = grid_point['longitude']
    grid_cell = grid_point['grid_cell']
    
    print(f"Collecting POIs for {grid_cell} ({lat:.4f}, {lon:.4f})")
    
    pois_collected = 0
    
    for category_name, place_types in POI_CATEGORIES.items():
        try:
            places = api_client.search_nearby(
                lat, lon, place_types, SEARCH_RADIUS, max_results=20
            )
            
            for place in places:
                # Check if POI already exists (by place_id)
                existing = poi_collection.find_one({'place_id': place['place_id']})
                
                if not existing:
                    # Add new POI
                    poi_doc = {
                        'poi_type': category_name,
                        'name': place['name'],
                        'place_id': place['place_id'],
                        'coordinates': {
                            'type': 'Point',
                            'coordinates': [
                                place['coordinates']['longitude'],
                                place['coordinates']['latitude']
                            ]
                        },
                        'latitude': place['coordinates']['latitude'],
                        'longitude': place['coordinates']['longitude'],
                        'rating': place.get('rating'),
                        'user_ratings_total': place.get('user_ratings_total', 0),
                        'last_updated': datetime.now(),
                        'discovered_in_grid': grid_cell
                    }
                    
                    poi_collection.insert_one(poi_doc)
                    pois_collected += 1
            
            # Small delay between categories
            time.sleep(0.1)
            
        except Exception as e:
            print(f"  Error collecting {category_name} for {grid_cell}: {e}")
    
    print(f"  → Collected {pois_collected} new POIs")
    return pois_collected

def main():
    """Main execution"""
    print("="*80)
    print("BUILDING GOLD COAST POI DATABASE")
    print("="*80)
    
    # Connect to MongoDB (separate POI database)
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_POI_DATABASE]
    poi_collection = db['pois']
    
    print(f"\nUsing POI database: {MONGODB_POI_DATABASE}")
    print(f"Collection: pois")
    
    # Create indexes
    print("\nCreating indexes...")
    poi_collection.create_index([('coordinates', '2dsphere')])
    poi_collection.create_index('poi_type')
    poi_collection.create_index([('poi_type', 1), ('coordinates', '2dsphere')])
    poi_collection.create_index('place_id', unique=True)
    
    # Initialize API client
    api_client = GooglePlacesClient(GOOGLE_API_KEY)
    
    # Generate grid
    grid_points = generate_grid_points()
    print(f"Generated {len(grid_points)} grid points")
    print(f"Expected API calls: ~{len(grid_points) * len(POI_CATEGORIES)} (with category grouping)")
    
    # Collect POIs
    total_pois = 0
    api_calls = 0
    
    for i, grid_point in enumerate(grid_points, 1):
        print(f"\n[{i}/{len(grid_points)}] Processing grid point...")
        
        pois = collect_pois_for_grid_point(api_client, grid_point, poi_collection)
        total_pois += pois
        api_calls += len(POI_CATEGORIES)
        
        if i % 10 == 0:
            print(f"\nProgress: {i}/{len(grid_points)} grid points")
            print(f"Total POIs collected: {total_pois}")
            print(f"API calls made: {api_calls}")
            print(f"Estimated cost so far: ${api_calls * 0.032:.2f}")
    
    # Final summary
    print("\n" + "="*80)
    print("POI DATABASE BUILD COMPLETE")
    print("="*80)
    
    # Count POIs by category
    for category in POI_CATEGORIES.keys():
        count = poi_collection.count_documents({'poi_type': category})
        print(f"{category:20s}: {count:5,} POIs")
    
    total_db_pois = poi_collection.count_documents({})
    print(f"\n{'Total POIs in database':20s}: {total_db_pois:5,}")
    print(f"API calls made: {api_calls}")
    print(f"Total cost: ${api_calls * 0.032:.2f}")
    print("="*80)

if __name__ == '__main__':
    main()
