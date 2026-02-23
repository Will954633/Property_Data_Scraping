#!/usr/bin/env python3
"""
MongoDB Status Checker for SOLD Properties Collection
Displays statistics and recent sales from the sold_last_6_months collection
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import sys

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "sold_last_6_months"


def main():
    """Check and display MongoDB collection status"""
    print("="*80)
    print("MONGODB STATUS - SOLD PROPERTIES (Last 6 Months)")
    print("="*80)
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Get total count
        total = collection.count_documents({})
        
        print(f"\n📊 COLLECTION OVERVIEW:")
        print(f"  Database: {DATABASE_NAME}")
        print(f"  Collection: {COLLECTION_NAME}")
        print(f"  Total properties: {total}")
        
        if total == 0:
            print("\n  ⚠ Collection is empty")
            print("  Run the scraper to populate data:")
            print("    ./process_sold_properties.sh")
            client.close()
            return 0
        
        # Count by suburb
        print(f"\n📍 BY SUBURB:")
        pipeline = [
            {"$group": {"_id": "$suburb_scraped", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_suburb = list(collection.aggregate(pipeline))
        for item in by_suburb:
            suburb = item["_id"] if item["_id"] else "Unknown"
            count = item["count"]
            print(f"  • {suburb}: {count} properties")
        
        # Recent sales (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent_30 = collection.count_documents({"sale_date": {"$gte": thirty_days_ago}})
        
        # Recent sales (last 60 days)
        sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        recent_60 = collection.count_documents({"sale_date": {"$gte": sixty_days_ago}})
        
        # Recent sales (last 90 days)
        ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        recent_90 = collection.count_documents({"sale_date": {"$gte": ninety_days_ago}})
        
        print(f"\n📅 RECENT SALES:")
        print(f"  Last 30 days: {recent_30} properties")
        print(f"  Last 60 days: {recent_60} properties")
        print(f"  Last 90 days: {recent_90} properties")
        
        # Get date range
        oldest = collection.find_one(sort=[("sale_date", 1)])
        newest = collection.find_one(sort=[("sale_date", -1)])
        
        if oldest and newest:
            print(f"\n📆 DATE RANGE:")
            print(f"  Oldest sale: {oldest.get('sale_date', 'N/A')}")
            print(f"  Newest sale: {newest.get('sale_date', 'N/A')}")
        
        # Count properties with/without sale dates
        with_date = collection.count_documents({"sale_date": {"$exists": True, "$ne": None}})
        without_date = total - with_date
        
        print(f"\n✓ DATA QUALITY:")
        print(f"  With sale date: {with_date} ({(with_date/total*100):.1f}%)")
        if without_date > 0:
            print(f"  Missing sale date: {without_date} ({(without_date/total*100):.1f}%)")
        
        # Show sample of most recent sales
        print(f"\n🏠 MOST RECENT SALES (Top 5):")
        recent_sales = collection.find(
            {"sale_date": {"$exists": True}},
            {"address": 1, "sale_date": 1, "sale_price": 1, "bedrooms": 1, "bathrooms": 1, "_id": 0}
        ).sort("sale_date", -1).limit(5)
        
        for i, prop in enumerate(recent_sales, 1):
            address = prop.get('address', 'N/A')
            sale_date = prop.get('sale_date', 'N/A')
            sale_price = prop.get('sale_price', 'N/A')
            beds = prop.get('bedrooms', '?')
            baths = prop.get('bathrooms', '?')
            print(f"  {i}. {address}")
            print(f"     Sold: {sale_date} | Price: {sale_price} | {beds} bed, {baths} bath")
        
        # Last updated info
        last_updated = collection.find_one(sort=[("last_updated", -1)])
        if last_updated:
            last_update_time = last_updated.get('last_updated')
            if last_update_time:
                print(f"\n🕐 LAST UPDATED:")
                print(f"  {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n{'='*80}\n")
        
        client.close()
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
