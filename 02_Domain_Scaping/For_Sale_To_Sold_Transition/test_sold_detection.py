#!/usr/bin/env python3
"""
Test script to verify sold property detection
Tests with the example URL: https://www.domain.com.au/81-cheltenham-drive-robina-qld-4226-2020360375
"""

from pymongo import MongoClient
from sold_property_monitor import SoldPropertyMonitor
import json

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"

# Test property data
TEST_PROPERTY = {
    "address": "81 Cheltenham Drive, Robina, QLD 4226",
    "listing_url": "https://www.domain.com.au/81-cheltenham-drive-robina-qld-4226-2020360375",
    "price": "For testing purposes",
    "bedrooms": 0,
    "bathrooms": 0,
    "property_type": "Test Property",
    "test_property": True  # Flag to identify test data
}

def main():
    print("="*80)
    print("SOLD PROPERTY DETECTION TEST")
    print("="*80)
    print()
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    for_sale = db["properties_for_sale"]
    sold = db["properties_sold"]
    
    # Clean up any previous test data
    print("1. Cleaning up any previous test data...")
    for_sale.delete_many({"test_property": True})
    sold.delete_many({"test_property": True})
    print("   ✓ Cleanup complete")
    print()
    
    # Insert test property into for_sale collection
    print("2. Inserting test property into properties_for_sale...")
    print(f"   Address: {TEST_PROPERTY['address']}")
    print(f"   URL: {TEST_PROPERTY['listing_url']}")
    result = for_sale.insert_one(TEST_PROPERTY)
    print(f"   ✓ Inserted with ID: {result.inserted_id}")
    print()
    
    # Run the monitor
    print("3. Running sold property monitor...")
    print("-" * 80)
    monitor = SoldPropertyMonitor(mongodb_uri=MONGODB_URI, db_name=DATABASE_NAME)
    
    # Get the test property from DB
    test_prop = for_sale.find_one({"test_property": True})
    if not test_prop:
        print("   ✗ Error: Test property not found in database!")
        return
    
    # Monitor this specific property
    was_sold = monitor.monitor_property(test_prop)
    monitor.close()
    print("-" * 80)
    print()
    
    # Check results
    print("4. Checking results...")
    
    # Check if property was removed from for_sale
    still_for_sale = for_sale.find_one({"test_property": True})
    
    # Check if property was moved to sold
    now_sold = sold.find_one({"test_property": True})
    
    print()
    print("="*80)
    print("TEST RESULTS")
    print("="*80)
    
    if was_sold:
        print("✅ Property detected as SOLD")
    else:
        print("❌ Property NOT detected as sold")
    
    if still_for_sale is None:
        print("✅ Property removed from properties_for_sale collection")
    else:
        print("❌ Property still in properties_for_sale collection")
    
    if now_sold:
        print("✅ Property found in properties_sold collection")
        print()
        print("SOLD PROPERTY DETAILS:")
        print("-" * 80)
        print(f"Address:          {now_sold.get('address')}")
        print(f"Listing URL:      {now_sold.get('listing_url')}")
        print(f"Sold Status:      {now_sold.get('sold_status')}")
        print(f"Sold Date:        {now_sold.get('sold_date')}")
        print(f"Sold Date Text:   {now_sold.get('sold_date_text')}")
        print(f"Sale Price:       {now_sold.get('sale_price')}")
        print(f"Detection Date:   {now_sold.get('sold_detection_date')}")
        print(f"Original Price:   {now_sold.get('price')}")
        print("-" * 80)
    else:
        print("❌ Property NOT found in properties_sold collection")
    
    print()
    
    # Determine overall test result
    if was_sold and still_for_sale is None and now_sold:
        print("🎉 TEST PASSED - All checks successful!")
        success = True
    else:
        print("⚠️  TEST FAILED - Some checks did not pass")
        success = False
    
    print("="*80)
    print()
    
    # Clean up test data
    print("5. Cleaning up test data...")
    for_sale.delete_many({"test_property": True})
    sold.delete_many({"test_property": True})
    print("   ✓ Test data removed")
    print()
    
    client.close()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
