# Last Edit: 01/02/2026, Saturday, 7:13 am (Brisbane Time)
# Script to check all unique suburb names in the database
# This will help identify correct spellings and multi-word suburbs

from pymongo import MongoClient
from collections import Counter
import json

# MongoDB Configuration
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "Gold_Coast_Currently_For_Sale"
COLLECTION_NAME = "properties"

def check_suburb_names():
    """Query database for all unique suburb names and their counts"""
    
    print("Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print(f"Connected to database: {DATABASE_NAME}")
    print(f"Collection: {COLLECTION_NAME}\n")
    
    # Get all unique suburbs
    print("Fetching all unique suburb names...")
    suburbs = collection.distinct("suburb")
    
    print(f"\nTotal unique suburbs found: {len(suburbs)}\n")
    print("=" * 80)
    print("ALL SUBURBS IN DATABASE (alphabetically sorted):")
    print("=" * 80)
    
    # Sort suburbs alphabetically
    sorted_suburbs = sorted([s for s in suburbs if s], key=str.lower)
    
    for i, suburb in enumerate(sorted_suburbs, 1):
        # Count properties in this suburb
        count = collection.count_documents({"suburb": suburb})
        print(f"{i:3d}. {suburb:40s} ({count:4d} properties)")
    
    print("\n" + "=" * 80)
    print("MULTI-WORD SUBURBS (need underscores for URL matching):")
    print("=" * 80)
    
    multi_word_suburbs = [s for s in sorted_suburbs if ' ' in s]
    for suburb in multi_word_suburbs:
        count = collection.count_documents({"suburb": suburb})
        url_format = suburb.replace(' ', '_')
        print(f"  Database: '{suburb}' -> URL format: '{url_format}' ({count} properties)")
    
    print("\n" + "=" * 80)
    print("TARGET SUBURBS FROM CONFIG (checking if they exist):")
    print("=" * 80)
    
    target_suburbs = [
        "robina",
        "mudgeeraba",
        "varsity lakes",
        "reedy creek",
        "burleigh waters",
        "merimac",
        "warongary"
    ]
    
    for target in target_suburbs:
        # Try exact match (case-insensitive)
        matches = [s for s in suburbs if s and s.lower() == target.lower()]
        
        if matches:
            count = collection.count_documents({"suburb": matches[0]})
            print(f"  ✓ '{target}' -> Found as '{matches[0]}' ({count} properties)")
        else:
            # Try partial match
            partial_matches = [s for s in suburbs if s and target.lower() in s.lower()]
            if partial_matches:
                print(f"  ✗ '{target}' -> NOT FOUND. Similar: {partial_matches}")
            else:
                print(f"  ✗ '{target}' -> NOT FOUND. No similar matches.")
    
    print("\n" + "=" * 80)
    print("CHECKING FOR PROPERTIES WITH IMAGES:")
    print("=" * 80)
    
    for target in target_suburbs:
        matches = [s for s in suburbs if s and s.lower() == target.lower()]
        if matches:
            suburb_name = matches[0]
            total = collection.count_documents({"suburb": suburb_name})
            with_images = collection.count_documents({
                "suburb": suburb_name,
                "images": {"$exists": True, "$ne": [], "$ne": None}
            })
            print(f"  {suburb_name:30s}: {with_images:4d}/{total:4d} have images")
    
    # Save results to JSON for reference
    results = {
        "all_suburbs": sorted_suburbs,
        "multi_word_suburbs": multi_word_suburbs,
        "target_suburbs_status": {}
    }
    
    for target in target_suburbs:
        matches = [s for s in suburbs if s and s.lower() == target.lower()]
        results["target_suburbs_status"][target] = {
            "found": len(matches) > 0,
            "actual_name": matches[0] if matches else None,
            "count": collection.count_documents({"suburb": matches[0]}) if matches else 0
        }
    
    with open("suburb_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to suburb_analysis.json")
    
    client.close()

if __name__ == "__main__":
    check_suburb_names()
