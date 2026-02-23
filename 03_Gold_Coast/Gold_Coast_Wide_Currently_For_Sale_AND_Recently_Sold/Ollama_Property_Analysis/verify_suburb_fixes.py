# Last Edit: 01/02/2026, Saturday, 7:14 am (Brisbane Time)
# Verification script to test that suburb name fixes are working correctly
# This script checks that all target suburbs can be found in the database

from pymongo import MongoClient
from config import MONGODB_URI, DATABASE_NAME, TARGET_SUBURBS
from logger import logger

def verify_suburb_fixes():
    """Verify that all target suburbs exist in the database and have documents."""
    
    print("=" * 80)
    print("SUBURB NAME FIX VERIFICATION")
    print("=" * 80)
    print(f"\nDatabase: {DATABASE_NAME}")
    print(f"Target suburbs: {len(TARGET_SUBURBS)}\n")
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    # Get all collection names
    all_collections = db.list_collection_names()
    
    print("VERIFICATION RESULTS:")
    print("-" * 80)
    
    all_found = True
    total_properties = 0
    total_with_images = 0
    total_unprocessed = 0
    
    for suburb in TARGET_SUBURBS:
        if suburb in all_collections:
            collection = db[suburb]
            
            # Count total documents
            total = collection.count_documents({})
            
            # Count documents with images
            with_images = collection.count_documents({
                "$or": [
                    {"scraped_data.images": {"$exists": True, "$type": "array", "$ne": []}},
                    {"property_images": {"$exists": True, "$type": "array", "$ne": []}},
                    {"images": {"$exists": True, "$type": "array", "$ne": []}}
                ]
            })
            
            # Count unprocessed documents with images
            unprocessed = collection.count_documents({
                "$and": [
                    {
                        "$or": [
                            {"scraped_data.images": {"$exists": True, "$type": "array", "$ne": []}},
                            {"property_images": {"$exists": True, "$type": "array", "$ne": []}},
                            {"images": {"$exists": True, "$type": "array", "$ne": []}}
                        ]
                    },
                    {"ollama_analysis.processed": {"$ne": True}}
                ]
            })
            
            total_properties += total
            total_with_images += with_images
            total_unprocessed += unprocessed
            
            print(f"✓ {suburb:20s} - FOUND")
            print(f"    Total: {total:3d} | With images: {with_images:3d} | Unprocessed: {unprocessed:3d}")
        else:
            print(f"✗ {suburb:20s} - NOT FOUND (collection does not exist)")
            all_found = False
    
    print("-" * 80)
    print(f"\nSUMMARY:")
    print(f"  All suburbs found: {'YES ✓' if all_found else 'NO ✗'}")
    print(f"  Total properties: {total_properties}")
    print(f"  Properties with images: {total_with_images}")
    print(f"  Unprocessed properties: {total_unprocessed}")
    
    if all_found and total_unprocessed > 0:
        print(f"\n{'=' * 80}")
        print("SUCCESS! All suburb names are correct and there are properties to process.")
        print(f"{'=' * 80}")
        print(f"\nReady to run: python3 run_production.py")
    elif all_found and total_unprocessed == 0:
        print(f"\n{'=' * 80}")
        print("All suburb names are correct, but all properties have been processed.")
        print(f"{'=' * 80}")
    else:
        print(f"\n{'=' * 80}")
        print("ERROR: Some suburb names are still incorrect!")
        print(f"{'=' * 80}")
        print("\nPlease check the TARGET_SUBURBS list in config.py")
    
    client.close()

if __name__ == "__main__":
    verify_suburb_fixes()
