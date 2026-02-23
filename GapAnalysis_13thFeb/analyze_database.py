#!/usr/bin/env python3
"""
Database Analysis Script
Last Edit: 13/02/2026, 11:25 AM (Thursday) — Brisbane Time

Description: Analyzes the Gold_Coast_Recently_Sold database to understand current data structure,
collections, sample documents, and field coverage for gap analysis.
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
from collections import defaultdict

# Connection string
CONNECTION_STRING = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"

def analyze_database():
    """Analyze the database structure and contents"""
    
    print("=" * 80)
    print("DATABASE ANALYSIS REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%d/%m/%Y, %I:%M %p')} (Brisbane Time)")
    print(f"Database: Gold_Coast_Recently_Sold")
    print("=" * 80)
    print()
    
    try:
        # Connect to MongoDB
        client = MongoClient(CONNECTION_STRING)
        db = client['Gold_Coast_Recently_Sold']
        
        # Get all collections
        collections = db.list_collection_names()
        print(f"📊 TOTAL COLLECTIONS: {len(collections)}")
        print()
        
        # Analyze each collection
        collection_stats = []
        
        for coll_name in sorted(collections):
            collection = db[coll_name]
            count = collection.count_documents({})
            
            if count > 0:
                # Get sample document
                sample = collection.find_one()
                
                # Get all unique fields across documents
                pipeline = [
                    {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
                    {"$unwind": "$arrayofkeyvalue"},
                    {"$group": {"_id": None, "allkeys": {"$addToSet": "$arrayofkeyvalue.k"}}}
                ]
                
                try:
                    result = list(collection.aggregate(pipeline, allowDiskUse=True))
                    all_fields = result[0]['allkeys'] if result else []
                except:
                    # Fallback: just use sample document fields
                    all_fields = list(sample.keys()) if sample else []
                
                # Check for sold date range
                sold_dates = []
                if 'dateSold' in all_fields:
                    try:
                        oldest = collection.find_one(sort=[('dateSold', 1)])
                        newest = collection.find_one(sort=[('dateSold', -1)])
                        if oldest and newest:
                            sold_dates = [oldest.get('dateSold'), newest.get('dateSold')]
                    except:
                        pass
                
                collection_stats.append({
                    'name': coll_name,
                    'count': count,
                    'fields': all_fields,
                    'sample': sample,
                    'sold_dates': sold_dates
                })
        
        # Print collection summaries
        print("=" * 80)
        print("COLLECTION SUMMARIES")
        print("=" * 80)
        print()
        
        total_properties = 0
        for stat in collection_stats:
            print(f"📁 Collection: {stat['name']}")
            print(f"   Documents: {stat['count']:,}")
            print(f"   Fields: {len(stat['fields'])}")
            
            if stat['sold_dates']:
                print(f"   Date Range: {stat['sold_dates'][0]} to {stat['sold_dates'][1]}")
            
            total_properties += stat['count']
            print()
        
        print(f"🏠 TOTAL PROPERTIES: {total_properties:,}")
        print()
        
        # Analyze field coverage
        print("=" * 80)
        print("FIELD COVERAGE ANALYSIS")
        print("=" * 80)
        print()
        
        # Required fields from requirements
        required_fields = {
            'Room dimensions': ['bedrooms', 'bathrooms', 'rooms', 'floorplan_analysis'],
            'Lot size': ['landArea', 'lotSize'],
            'Floor area': ['floorArea', 'buildingArea'],
            'Waterfront': ['waterfront', 'features'],
            'Special views': ['views', 'features'],
            'Corner lot': ['cornerLot', 'features'],
            'Busy road': ['busyRoad', 'features'],
            'Days on market': ['daysOnMarket', 'dateListed', 'dateSold'],
            'Sale method': ['saleMethod', 'auctionDate'],
            'North facing': ['northFacing', 'aspect'],
            'Proximity to amenities': ['nearbyAmenities', 'location'],
            'Building age': ['yearBuilt', 'buildingAge'],
            'Building condition': ['condition', 'photo_analysis'],
            'Renovation status': ['renovation', 'features'],
            'Garage/Carport': ['parking', 'carSpaces', 'garageSpaces'],
            'Pool': ['pool', 'features'],
            'Outdoor entertainment': ['outdoor', 'features', 'photo_analysis'],
            'Air conditioning': ['airConditioning', 'features'],
            'Home office': ['homeOffice', 'study', 'features'],
            'Ensuite': ['ensuite', 'bathrooms'],
            'Walk-in wardrobe': ['walkInWardrobe', 'features'],
            'High ceilings': ['highCeilings', 'features'],
            'Quality of features': ['features', 'photo_analysis']
        }
        
        # Check field presence across all collections
        field_coverage = {}
        for req_name, possible_fields in required_fields.items():
            found_in = []
            for stat in collection_stats:
                for field in possible_fields:
                    if field in stat['fields']:
                        found_in.append(stat['name'])
                        break
            
            coverage_pct = (len(found_in) / len(collection_stats) * 100) if collection_stats else 0
            field_coverage[req_name] = {
                'found_in': found_in,
                'coverage': coverage_pct,
                'possible_fields': possible_fields
            }
        
        # Print coverage
        for req_name, coverage in sorted(field_coverage.items()):
            status = "✅" if coverage['coverage'] > 0 else "❌"
            print(f"{status} {req_name}")
            print(f"   Coverage: {coverage['coverage']:.1f}% of collections")
            print(f"   Looking for: {', '.join(coverage['possible_fields'])}")
            if coverage['found_in']:
                print(f"   Found in: {', '.join(coverage['found_in'][:3])}")
            print()
        
        # Sample document analysis
        print("=" * 80)
        print("SAMPLE DOCUMENT STRUCTURE")
        print("=" * 80)
        print()
        
        if collection_stats:
            sample_coll = collection_stats[0]
            print(f"Collection: {sample_coll['name']}")
            print(f"Available fields ({len(sample_coll['fields'])}):")
            print()
            
            for field in sorted(sample_coll['fields']):
                if field != '_id':
                    sample_value = sample_coll['sample'].get(field)
                    value_type = type(sample_value).__name__
                    
                    # Truncate long values
                    if isinstance(sample_value, (list, dict)):
                        display_value = f"{value_type} (length: {len(sample_value)})"
                    elif isinstance(sample_value, str) and len(sample_value) > 50:
                        display_value = f"{sample_value[:50]}..."
                    else:
                        display_value = str(sample_value)
                    
                    print(f"  • {field}: {display_value}")
            print()
        
        # Save detailed report to JSON
        report = {
            'generated': datetime.now().isoformat(),
            'database': 'Gold_Coast_Recently_Sold',
            'total_collections': len(collections),
            'total_properties': total_properties,
            'collections': [
                {
                    'name': stat['name'],
                    'count': stat['count'],
                    'fields': stat['fields'],
                    'date_range': stat['sold_dates']
                }
                for stat in collection_stats
            ],
            'field_coverage': field_coverage
        }
        
        with open('/Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb/database_analysis.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print("=" * 80)
        print("✅ Analysis complete!")
        print("📄 Detailed report saved to: database_analysis.json")
        print("=" * 80)
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_database()
