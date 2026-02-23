#!/usr/bin/env python3
# Last Edit: 31/01/2026, Friday, 7:51 pm (Brisbane Time)
"""
Diagnostic script to check MongoDB database structure and content.
"""
from pymongo import MongoClient
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME, TARGET_SUBURBS

def main():
    print("=" * 80)
    print("DATABASE DIAGNOSTIC")
    print("=" * 80)
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print(f"\nDatabase: {DATABASE_NAME}")
    print(f"Collection: {COLLECTION_NAME}")
    
    # Get total count
    total_count = collection.count_documents({})
    print(f"\nTotal documents in collection: {total_count}")
    
    if total_count == 0:
        print("\n⚠️  Collection is EMPTY!")
        print("You need to scrape properties first before running analysis.")
        return
    
    # Get a sample document
    print("\n" + "=" * 80)
    print("SAMPLE DOCUMENT STRUCTURE")
    print("=" * 80)
    sample = collection.find_one({})
    
    if sample:
        print("\nTop-level fields:")
        for key in sorted(sample.keys()):
            value_type = type(sample[key]).__name__
            print(f"  - {key}: {value_type}")
        
        # Check for suburb field
        print("\n" + "=" * 80)
        print("SUBURB FIELD ANALYSIS")
        print("=" * 80)
        
        suburb_fields = []
        if "suburb" in sample:
            suburb_fields.append(("suburb", sample["suburb"]))
        if "address" in sample and isinstance(sample["address"], dict):
            if "suburb" in sample["address"]:
                suburb_fields.append(("address.suburb", sample["address"]["suburb"]))
        if "property_details" in sample and isinstance(sample["property_details"], dict):
            if "suburb" in sample["property_details"]:
                suburb_fields.append(("property_details.suburb", sample["property_details"]["suburb"]))
        if "scraped_data" in sample and isinstance(sample["scraped_data"], dict):
            if "suburb" in sample["scraped_data"]:
                suburb_fields.append(("scraped_data.suburb", sample["scraped_data"]["suburb"]))
        
        if suburb_fields:
            print("\nFound suburb fields:")
            for field_path, value in suburb_fields:
                print(f"  - {field_path}: '{value}'")
        else:
            print("\n⚠️  No suburb field found in sample document!")
        
        # Check for images
        print("\n" + "=" * 80)
        print("IMAGE FIELD ANALYSIS")
        print("=" * 80)
        
        image_fields = []
        if "images" in sample:
            image_fields.append(("images", len(sample["images"]) if isinstance(sample["images"], list) else "not a list"))
        if "property_images" in sample:
            image_fields.append(("property_images", len(sample["property_images"]) if isinstance(sample["property_images"], list) else "not a list"))
        if "scraped_data" in sample and isinstance(sample["scraped_data"], dict):
            if "images" in sample["scraped_data"]:
                image_fields.append(("scraped_data.images", len(sample["scraped_data"]["images"]) if isinstance(sample["scraped_data"]["images"], list) else "not a list"))
        
        if image_fields:
            print("\nFound image fields:")
            for field_path, count in image_fields:
                print(f"  - {field_path}: {count} images")
        else:
            print("\n⚠️  No image field found in sample document!")
    
    # Count by suburb (try different field paths)
    print("\n" + "=" * 80)
    print("SUBURB COUNTS")
    print("=" * 80)
    
    for suburb in TARGET_SUBURBS:
        # Try different field paths
        queries = [
            {"suburb": suburb},
            {"suburb": suburb.title()},  # Try title case
            {"address.suburb": suburb},
            {"property_details.suburb": suburb},
            {"scraped_data.suburb": suburb}
        ]
        
        for query in queries:
            count = collection.count_documents(query)
            if count > 0:
                field = list(query.keys())[0]
                value = list(query.values())[0]
                print(f"  {field} = '{value}': {count} properties")
                break
    
    # Check for documents with images
    print("\n" + "=" * 80)
    print("DOCUMENTS WITH IMAGES")
    print("=" * 80)
    
    with_images_query = {
        "$or": [
            {"images": {"$exists": True, "$type": "array", "$ne": []}},
            {"property_images": {"$exists": True, "$type": "array", "$ne": []}},
            {"scraped_data.images": {"$exists": True, "$type": "array", "$ne": []}}
        ]
    }
    
    with_images_count = collection.count_documents(with_images_query)
    print(f"\nDocuments with images: {with_images_count}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    if total_count == 0:
        print("\n❌ Database is empty. Run the scraper first.")
    elif not suburb_fields:
        print("\n❌ No suburb field found. Check your data structure.")
    elif not image_fields:
        print("\n❌ No image fields found. Properties need images for analysis.")
    elif with_images_count == 0:
        print("\n❌ No properties have images. Scrape images first.")
    else:
        print("\n✅ Database looks good! Update config.py with the correct field paths.")
    
    client.close()

if __name__ == "__main__":
    main()
