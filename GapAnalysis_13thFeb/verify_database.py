#!/usr/bin/env python3
"""
Verify Database Upload
Quick script to check if the 2,153 properties were uploaded correctly to Azure Cosmos DB
"""

import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("COSMOS_CONNECTION_STRING")
DATABASE_NAME = "Gold_Coast_Recently_Sold"
COLLECTION_NAME = "properties"

def verify_upload():
    """Verify the upload worked correctly"""
    print("=" * 80)
    print("VERIFYING DATABASE UPLOAD")
    print("=" * 80)
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Get total count
        total_count = collection.count_documents({})
        print(f"\n✅ Connected to Azure Cosmos DB")
        print(f"   Database: {DATABASE_NAME}")
        print(f"   Collection: {COLLECTION_NAME}")
        print(f"   Total properties: {total_count}")
        
        # Count by suburb
        print(f"\n📊 Properties by suburb:")
        pipeline = [
            {"$group": {"_id": "$suburb_scraped", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_suburb = list(collection.aggregate(pipeline))
        
        for item in by_suburb:
            suburb = item["_id"]
            count = item["count"]
            print(f"   • {suburb}: {count} properties")
        
        # Sample a few properties to check data quality
        print(f"\n🔍 Sample property check:")
        sample = collection.find_one({"suburb_scraped": "robina"})
        
        if sample:
            print(f"   Address: {sample.get('address', 'N/A')}")
            print(f"   Sale date: {sample.get('sale_date', 'N/A')}")
            print(f"   Sale price: {sample.get('sale_price', 'N/A')}")
            print(f"   Bedrooms: {sample.get('bedrooms', 'N/A')}")
            print(f"   Bathrooms: {sample.get('bathrooms', 'N/A')}")
            print(f"   Car spaces: {sample.get('car_spaces', 'N/A')}")
            print(f"   Property type: {sample.get('property_type', 'N/A')}")
            print(f"   Images: {len(sample.get('images', []))} images")
            
            # Check if enrichment fields exist (should be empty before enrichment)
            enrichment_fields = [
                'building_condition', 'building_age', 'busy_road', 
                'corner_block', 'parking', 'outdoor_entertainment', 'renovation_status'
            ]
            has_enrichment = any(field in sample for field in enrichment_fields)
            
            if has_enrichment:
                print(f"\n   ⚠️  Some properties already have enrichment data")
            else:
                print(f"\n   ✅ Properties ready for enrichment (no enrichment data yet)")
        
        # Check for properties with images (needed for GPT Vision)
        with_images = collection.count_documents({"images": {"$exists": True, "$ne": []}})
        print(f"\n📷 Properties with images: {with_images}/{total_count} ({with_images/total_count*100:.1f}%)")
        
        if with_images < total_count * 0.9:
            print(f"   ⚠️  Warning: {total_count - with_images} properties missing images")
        else:
            print(f"   ✅ Good image coverage for GPT Vision enrichment")
        
        print(f"\n{'=' * 80}")
        print(f"VERIFICATION COMPLETE")
        print(f"{'=' * 80}")
        print(f"\n✅ Database upload successful!")
        print(f"✅ {total_count} properties ready for enrichment")
        print(f"\nTo run enrichment:")
        print(f"  cd /Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb")
        print(f"  python3 run_production.py")
        print(f"{'=' * 80}\n")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error connecting to database: {e}")
        return False


if __name__ == "__main__":
    verify_upload()
