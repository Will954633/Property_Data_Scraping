#!/usr/bin/env python3
"""
Test Cadastral Data Enrichment on Single Suburb
Tests the enrichment process on one suburb before running full enrichment.
"""

import sys
import requests
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import json

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"
API_BASE_URL = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer"
TEST_SUBURB = "mudgeeraba"  # Test on Mudgeeraba first
TEST_LIMIT = 5  # Test on first 5 properties


def connect_to_mongodb():
    """Establish connection to MongoDB."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB")
        return client
    except ConnectionFailure as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)


def test_api_query(lot: str, plan: str):
    """Test a single API query."""
    print(f"\nTesting API query for LOT={lot}, PLAN={plan}...")
    
    # Query cadastral data
    where_clause = f"lot='{lot}' AND plan='{plan}'"
    params = {
        'where': where_clause,
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'false'
    }
    
    url = f"{API_BASE_URL}/4/query"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('features'):
            print(f"✓ Found {len(data['features'])} result(s)")
            attributes = data['features'][0]['attributes']
            
            # Show key fields
            print("\nKey fields returned:")
            key_fields = ['lot', 'plan', 'lotplan', 'lot_area', 'excl_area', 'tenure', 
                         'cover_typ', 'parcel_typ', 'locality']
            for field in key_fields:
                value = attributes.get(field)
                print(f"  {field}: {value}")
            
            return attributes
        else:
            print("✗ No results found")
            print(f"Response: {json.dumps(data, indent=2)}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def main():
    """Main test function."""
    print("="*70)
    print("Cadastral Data Enrichment - API Test")
    print("="*70)
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    
    # Check if test suburb exists
    if TEST_SUBURB not in db.list_collection_names():
        print(f"\n✗ Test suburb '{TEST_SUBURB}' not found in database")
        print(f"Available suburbs: {', '.join(sorted(db.list_collection_names())[:10])}...")
        sys.exit(1)
    
    collection = db[TEST_SUBURB]
    total = collection.count_documents({})
    print(f"\n✓ Found test suburb: {TEST_SUBURB} ({total:,} properties)")
    
    # Get sample properties
    print(f"\nTesting with first {TEST_LIMIT} properties...")
    
    properties = list(collection.find().limit(TEST_LIMIT))
    
    success_count = 0
    fail_count = 0
    
    for i, prop in enumerate(properties, 1):
        lot = prop.get('LOT')
        plan = prop.get('PLAN')
        address = f"{prop.get('STREET_NO_1', '')} {prop.get('STREET_NAME', '')} {prop.get('STREET_TYPE', '')}"
        
        print(f"\n{'='*70}")
        print(f"Property {i}/{TEST_LIMIT}")
        print(f"{'='*70}")
        print(f"Address: {address}")
        print(f"Lot/Plan: {lot}/{plan}")
        
        if not lot or not plan:
            print("✗ Missing lot or plan")
            fail_count += 1
            continue
        
        result = test_api_query(lot, plan)
        
        if result:
            success_count += 1
            
            # Check specific important fields
            if result.get('lot_area'):
                print(f"\n✓ SUCCESS: lot_area = {result.get('lot_area')} m²")
            else:
                print(f"\n⚠ WARNING: lot_area is null")
        else:
            fail_count += 1
    
    # Summary
    print(f"\n{'='*70}")
    print("Test Summary")
    print(f"{'='*70}")
    print(f"Properties tested:  {len(properties)}")
    print(f"Successful queries: {success_count}")
    print(f"Failed queries:     {fail_count}")
    
    if success_count > 0:
        success_rate = (success_count / len(properties)) * 100
        print(f"Success rate:       {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"\n✓ API connection working well!")
            print(f"✓ Ready to run full enrichment with: python3 enrich_cadastral_data.py")
        else:
            print(f"\n⚠ Lower success rate than expected - check API connectivity")
    else:
        print(f"\n✗ No successful API queries - check configuration")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
