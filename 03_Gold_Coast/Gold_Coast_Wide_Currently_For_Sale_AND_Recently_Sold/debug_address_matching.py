#!/usr/bin/env python3
"""
Debug Address Matching Issue
Last Updated: 03/02/2026, 7:27 pm (Brisbane Time)

PURPOSE:
Debug why monitor_sold_properties.py cannot find master records.
Check address format differences between collections.
"""

from pymongo import MongoClient
import os

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')

# Connect to MongoDB
client = MongoClient(MONGODB_URI)

# Check a property from For Sale collection
for_sale_db = client['Gold_Coast_Currently_For_Sale']
mermaid_waters_collection = for_sale_db['mermaid_waters']

print("=" * 80)
print("CHECKING ADDRESS FORMATS")
print("=" * 80)

# Get a sample property from for sale collection
sample_property = mermaid_waters_collection.find_one({})
if sample_property:
    print("\n1. FOR SALE COLLECTION (mermaid_waters):")
    print(f"   address field: {sample_property.get('address')}")
    print(f"   complete_address field: {sample_property.get('complete_address')}")
    print(f"   All address-related fields:")
    for key in sample_property.keys():
        if 'address' in key.lower():
            print(f"     - {key}: {sample_property.get(key)}")

# Check master database
master_db = client['Gold_Coast']
master_mermaid_waters = master_db['Mermaid Waters']

print("\n2. MASTER DATABASE (Mermaid Waters):")
sample_master = master_mermaid_waters.find_one({})
if sample_master:
    print(f"   complete_address field: {sample_master.get('complete_address')}")
    print(f"   All address-related fields:")
    for key in sample_master.keys():
        if 'address' in key.lower():
            print(f"     - {key}: {sample_master.get(key)}")

# Try to find specific addresses mentioned in error
print("\n3. SEARCHING FOR SPECIFIC ADDRESSES:")

test_addresses = [
    "3 8 Jodie Court Mermaid, Waters, QLD 4218",
    "19 111 123 Markeri Street Mermaid, Waters, QLD 4218"
]

for test_addr in test_addresses:
    print(f"\n   Looking for: {test_addr}")
    
    # Search in for sale collection
    for_sale_match = mermaid_waters_collection.find_one({"address": test_addr})
    if for_sale_match:
        print(f"   ✓ Found in FOR SALE collection")
        print(f"     address: {for_sale_match.get('address')}")
        print(f"     complete_address: {for_sale_match.get('complete_address')}")
    else:
        print(f"   ✗ NOT found in FOR SALE collection")
        # Try partial match
        partial = mermaid_waters_collection.find_one({"address": {"$regex": "Jodie Court" if "Jodie" in test_addr else "Markeri Street"}})
        if partial:
            print(f"     But found similar: {partial.get('address')}")
    
    # Search in master collection
    master_match = master_mermaid_waters.find_one({"complete_address": test_addr})
    if master_match:
        print(f"   ✓ Found in MASTER collection")
        print(f"     complete_address: {master_match.get('complete_address')}")
    else:
        print(f"   ✗ NOT found in MASTER collection")
        # Try partial match
        partial = master_mermaid_waters.find_one({"complete_address": {"$regex": "Jodie Court" if "Jodie" in test_addr else "Markeri Street"}})
        if partial:
            print(f"     But found similar: {partial.get('complete_address')}")

print("\n4. COLLECTION NAME COMPARISON:")
print(f"   For Sale collection name: 'mermaid_waters'")
print(f"   Master collection name: 'Mermaid Waters'")
print(f"   Script uses suburb_name: {sample_property.get('suburb') if sample_property else 'N/A'}")

print("\n" + "=" * 80)

client.close()
