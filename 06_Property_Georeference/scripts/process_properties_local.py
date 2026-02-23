#!/usr/bin/env python3
"""
Process all properties using local POI database
Calculate distances without making API calls
"""

import os
import sys
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from distance_calculator import DistanceCalculator

# Load environment variables
load_dotenv()

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
MONGODB_POI_DATABASE = os.getenv('MONGODB_POI_DATABASE', 'Gold_Coast_POIs')
MONGODB_PROPERTY_DATABASE = os.getenv('MONGODB_PROPERTY_DATABASE', 'Gold_Coast')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_closest_pois(poi_collection, property_lat, property_lon, poi_type, max_count=5):
    """Find closest POIs from local database"""
    
    # Query MongoDB using geospatial index
    nearby_pois = poi_collection.find({
        'poi_type': poi_type,
        'coordinates': {
            '$near': {
                '$geometry': {
                    'type': 'Point',
                    'coordinates': [property_lon, property_lat]
                },
                '$maxDistance': 10000  # 10km
            }
        }
    }).limit(20)
    
    # Calculate exact distances
    poi_distances = []
    for poi in nearby_pois:
        distance_km = DistanceCalculator.haversine_distance(
            property_lat, property_lon,
            poi['latitude'], poi['longitude']
        )
        
        poi_distances.append({
            'name': poi['name'],
            'place_id': poi['place_id'],
            'distance_meters': int(distance_km * 1000),
            'distance_km': distance_km,
            'coordinates': {
                'latitude': poi['latitude'],
                'longitude': poi['longitude']
            },
            'rating': poi.get('rating'),
            'user_ratings_total': poi.get('user_ratings_total', 0)
        })
    
    # Sort and return closest N
    poi_distances.sort(key=lambda x: x['distance_km'])
    return poi_distances[:max_count]

def calculate_summary_stats(distances):
    """Calculate summary statistics from distance data"""
    def get_closest(category_list):
        if isinstance(category_list, list) and len(category_list) > 0:
            return category_list[0]['distance_km']
        elif isinstance(category_list, dict):
            return category_list['distance_km']
        return None
    
    summary = {
        'closest_primary_school_km': get_closest(distances.get('primary_schools', [])),
        'closest_secondary_school_km': get_closest(distances.get('secondary_schools', [])),
        'closest_childcare_km': get_closest(distances.get('childcare_centers', [])),
        'closest_supermarket_km': get_closest(distances.get('supermarkets', [])),
        'closest_beach_km': get_closest(distances.get('beaches', [])),
        'closest_hospital_km': get_closest(distances.get('hospitals', [])),
        'airport_distance_km': distances['airport']['distance_km']
    }
    
    # Count amenities within distance thresholds
    all_pois = []
    for category, pois in distances.items():
        if isinstance(pois, list):
            all_pois.extend(pois)
    
    summary['total_amenities_within_1km'] = len([p for p in all_pois if p['distance_km'] <= 1])
    summary['total_amenities_within_2km'] = len([p for p in all_pois if p['distance_km'] <= 2])
    summary['total_amenities_within_5km'] = len([p for p in all_pois if p['distance_km'] <= 5])
    
    return summary

def process_property(property_data, poi_collection, property_collection):
    """Process single property using local POI database"""
    lat = property_data['latitude']
    lon = property_data['longitude']
    
    logger.info(f"Processing: {property_data['address']}")
    
    # Find closest POIs for each category
    distances = {}
    
    poi_categories = {
        'primary_schools': 'primary_school',
        'secondary_schools': 'secondary_school',
        'childcare_centers': 'childcare',
        'supermarkets': 'supermarket',
        'shopping_malls': 'shopping_mall',
        'hospitals': 'hospital',
        'medical_centers': 'medical_center',
        'parks': 'park',
        'pharmacies': 'pharmacy',
        'public_transport': 'public_transport'
    }
    
    for field_name, poi_type in poi_categories.items():
        max_results = 5 if 'school' in field_name or field_name == 'childcare_centers' else 3
        distances[field_name] = find_closest_pois(
            poi_collection, lat, lon, poi_type, max_results
        )
    
    # Add hardcoded locations
    distances['airport'] = DistanceCalculator.distance_to_airport(lat, lon)
    distances['beaches'] = DistanceCalculator.distances_to_beaches(lat, lon)
    
    # Calculate summary stats
    summary_stats = calculate_summary_stats(distances)
    
    # Build georeference data
    georeference_data = {
        'last_updated': datetime.now(),
        'coordinates': {'latitude': lat, 'longitude': lon},
        'distances': distances,
        'summary_stats': summary_stats,
        'calculation_method': 'local_poi_database'
    }
    
    # Update property
    property_collection.update_one(
        {'_id': property_data['_id']},
        {'$set': {'georeference_data': georeference_data}}
    )
    
    logger.info(f"✓ Completed: {property_data['address']}")

def get_qualifying_properties(property_db):
    """Get all properties that match criteria"""
    twelve_months_ago = datetime.now() - timedelta(days=365)
    
    all_properties = []
    collections = [col for col in property_db.list_collection_names() 
                   if not col.startswith('system')]
    
    for col_name in collections:
        collection = property_db[col_name]
        
        # Query for qualifying properties
        query = {
            'complete_address': {'$exists': True},
            'LATITUDE': {'$exists': True},
            'LONGITUDE': {'$exists': True},
            'scraped_data.property_timeline.0': {'$exists': True},
            'georeference_data': {'$exists': False}  # Not yet processed
        }
        
        docs = list(collection.find(query))
        
        for doc in docs:
            address = doc.get('complete_address', '')
            
            # Check if house (no slash)
            if '/' in address:
                continue
            
            # Check for recent sale
            timeline = doc.get('scraped_data', {}).get('property_timeline', [])
            has_recent_sale = False
            
            for entry in timeline:
                if entry.get('category') == 'Sale' and entry.get('is_sold'):
                    date_str = entry.get('date')
                    if date_str:
                        try:
                            sale_date = datetime.strptime(date_str, '%Y-%m-%d')
                            if sale_date >= twelve_months_ago:
                                has_recent_sale = True
                                break
                        except:
                            pass
            
            if has_recent_sale:
                all_properties.append({
                    'collection': col_name,
                    '_id': doc['_id'],
                    'address': address,
                    'latitude': doc['LATITUDE'],
                    'longitude': doc['LONGITUDE']
                })
    
    return all_properties

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("PROCESSING PROPERTIES WITH LOCAL POI DATABASE")
    logger.info("="*80)
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    poi_db = client[MONGODB_POI_DATABASE]
    property_db = client[MONGODB_PROPERTY_DATABASE]
    poi_collection = poi_db['pois']
    
    logger.info(f"\nPOI Database: {MONGODB_POI_DATABASE}")
    logger.info(f"Property Database: {MONGODB_PROPERTY_DATABASE}")
    
    # Verify POI database exists
    poi_count = poi_collection.count_documents({})
    if poi_count == 0:
        logger.error("POI database is empty! Run build_poi_database.py first.")
        return
    
    logger.info(f"POI database loaded: {poi_count:,} POIs")
    
    # Get qualifying properties
    logger.info("\nFinding qualifying properties...")
    properties = get_qualifying_properties(property_db)
    total = len(properties)
    
    logger.info(f"Found {total:,} properties to process")
    logger.info("Cost: $0 (using local database)\n")
    
    if total == 0:
        logger.info("No properties to process!")
        return
    
    # Process all properties
    success_count = 0
    fail_count = 0
    
    for i, prop in enumerate(properties, 1):
        try:
            collection = property_db[prop['collection']]
            process_property(prop, poi_collection, collection)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to process {prop['address']}: {e}")
            fail_count += 1
        
        if i % 100 == 0:
            logger.info(f"\nProgress: {i}/{total} ({i/total*100:.1f}%)")
            logger.info(f"Success: {success_count}, Failed: {fail_count}")
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*80)
    logger.info(f"Total processed: {total:,}")
    logger.info(f"Successful: {success_count:,} ({success_count/total*100:.1f}%)")
    logger.info(f"Failed: {fail_count:,} ({fail_count/total*100:.1f}%)")
    logger.info("="*80)

if __name__ == '__main__':
    main()
