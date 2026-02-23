#!/usr/bin/env python3
"""
Check Floor Plan Data Migration Status
Last Edit: 16/02/2026, 5:29 PM (Sunday) — Brisbane Time

Description: Audits what floor plan data exists in Azure Cosmos DB
and identifies what needs to be migrated from local sources.

Edit History:
- 16/02/2026 5:29 PM: Initial creation
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Azure Cosmos DB connection
COSMOS_CONNECTION_STRING = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"

def check_database(db_name, description):
    """Check a database for floor plan enrichment data"""
    print(f"\n{'='*80}")
    print(f"Checking: {db_name} ({description})")
    print(f"{'='*80}")
    
    try:
        client = MongoClient(COSMOS_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # List all collections
        collections = db.list_collection_names()
        print(f"\nFound {len(collections)} collections")
        
        stats = {
            'total_properties': 0,
            'with_floor_plan_analysis': 0,
            'with_building_condition': 0,
            'with_building_age': 0,
            'with_parking': 0,
            'with_outdoor_entertainment': 0,
            'with_renovation_status': 0,
            'with_north_facing': 0,
            'with_busy_road': 0,
            'with_corner_block': 0,
            'collections': {}
        }
        
        for collection_name in collections:
            collection = db[collection_name]
            total = collection.count_documents({})
            
            if total == 0:
                continue
                
            # Count enrichment fields
            floor_plan = collection.count_documents({'floor_plan_analysis': {'$exists': True}})
            building_condition = collection.count_documents({'building_condition': {'$exists': True}})
            building_age = collection.count_documents({'building_age': {'$exists': True}})
            parking = collection.count_documents({'parking': {'$exists': True}})
            outdoor = collection.count_documents({'outdoor_entertainment': {'$exists': True}})
            renovation = collection.count_documents({'renovation_status': {'$exists': True}})
            north_facing = collection.count_documents({'north_facing': {'$exists': True}})
            busy_road = collection.count_documents({'busy_road': {'$exists': True}})
            corner_block = collection.count_documents({'corner_block': {'$exists': True}})
            
            stats['total_properties'] += total
            stats['with_floor_plan_analysis'] += floor_plan
            stats['with_building_condition'] += building_condition
            stats['with_building_age'] += building_age
            stats['with_parking'] += parking
            stats['with_outdoor_entertainment'] += outdoor
            stats['with_renovation_status'] += renovation
            stats['with_north_facing'] += north_facing
            stats['with_busy_road'] += busy_road
            stats['with_corner_block'] += corner_block
            
            stats['collections'][collection_name] = {
                'total': total,
                'floor_plan': floor_plan,
                'building_condition': building_condition,
                'building_age': building_age,
                'parking': parking,
                'outdoor': outdoor,
                'renovation': renovation,
                'north_facing': north_facing,
                'busy_road': busy_road,
                'corner_block': corner_block
            }
            
            print(f"\n  {collection_name}:")
            print(f"    Total properties: {total}")
            print(f"    Floor plan analysis: {floor_plan} ({floor_plan/total*100:.1f}%)")
            print(f"    Building condition: {building_condition} ({building_condition/total*100:.1f}%)")
            print(f"    Building age: {building_age} ({building_age/total*100:.1f}%)")
            print(f"    Parking: {parking} ({parking/total*100:.1f}%)")
            print(f"    Outdoor entertainment: {outdoor} ({outdoor/total*100:.1f}%)")
            print(f"    Renovation status: {renovation} ({renovation/total*100:.1f}%)")
            print(f"    North facing: {north_facing} ({north_facing/total*100:.1f}%)")
            print(f"    Busy road: {busy_road} ({busy_road/total*100:.1f}%)")
            print(f"    Corner block: {corner_block} ({corner_block/total*100:.1f}%)")
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"SUMMARY: {db_name}")
        print(f"{'='*80}")
        print(f"Total properties: {stats['total_properties']}")
        print(f"With floor plan analysis: {stats['with_floor_plan_analysis']} ({stats['with_floor_plan_analysis']/stats['total_properties']*100:.1f}%)")
        print(f"With building condition: {stats['with_building_condition']} ({stats['with_building_condition']/stats['total_properties']*100:.1f}%)")
        print(f"With building age: {stats['with_building_age']} ({stats['with_building_age']/stats['total_properties']*100:.1f}%)")
        print(f"With parking: {stats['with_parking']} ({stats['with_parking']/stats['total_properties']*100:.1f}%)")
        print(f"With outdoor entertainment: {stats['with_outdoor_entertainment']} ({stats['with_outdoor_entertainment']/stats['total_properties']*100:.1f}%)")
        print(f"With renovation status: {stats['with_renovation_status']} ({stats['with_renovation_status']/stats['total_properties']*100:.1f}%)")
        print(f"With north facing: {stats['with_north_facing']} ({stats['with_north_facing']/stats['total_properties']*100:.1f}%)")
        print(f"With busy road: {stats['with_busy_road']} ({stats['with_busy_road']/stats['total_properties']*100:.1f}%)")
        print(f"With corner block: {stats['with_corner_block']} ({stats['with_corner_block']/stats['total_properties']*100:.1f}%)")
        
        client.close()
        return stats
        
    except Exception as e:
        print(f"Error checking {db_name}: {e}")
        return None

def main():
    print("="*80)
    print("FLOOR PLAN DATA MIGRATION STATUS CHECK")
    print("="*80)
    print(f"Target: Azure Cosmos DB")
    print(f"Time: 16/02/2026, 5:29 PM Brisbane Time")
    
    # Check both databases
    sold_stats = check_database('Gold_Coast_Recently_Sold', 'Sold properties - last 12 months')
    forsale_stats = check_database('Gold_Coast_Currently_For_Sale', 'Currently for sale properties')
    
    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL MIGRATION STATUS")
    print(f"{'='*80}")
    
    if sold_stats:
        print(f"\nGold_Coast_Recently_Sold:")
        print(f"  Total properties: {sold_stats['total_properties']}")
        print(f"  Missing floor plan analysis: {sold_stats['total_properties'] - sold_stats['with_floor_plan_analysis']}")
        print(f"  Missing GPT enrichment: {sold_stats['total_properties'] - sold_stats['with_building_condition']}")
    
    if forsale_stats:
        print(f"\nGold_Coast_Currently_For_Sale:")
        print(f"  Total properties: {forsale_stats['total_properties']}")
        print(f"  Missing floor plan analysis: {forsale_stats['total_properties'] - forsale_stats['with_floor_plan_analysis']}")
        print(f"  Missing GPT enrichment: {forsale_stats['total_properties'] - forsale_stats['with_building_condition']}")
    
    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print(f"{'='*80}")
    print("1. If data is missing, run migration script")
    print("2. Check local JSON files in 02_Domain_Scaping/Sold_In_Last_12_Months_8_Suburbs/property_data/")
    print("3. Run GPT enrichment on properties missing enrichment fields")
    print("4. Run Ollama floor plan analysis on properties with floor plans")

if __name__ == "__main__":
    main()
