#!/usr/bin/env python3
# Last Edit: 01/02/2026, Saturday, 9:25 am (Brisbane Time)
# Show floor plan analysis result for a specific document

"""
Display the floor plan analysis result from MongoDB.
"""
import json
from pymongo import MongoClient
from bson import ObjectId

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Gold_Coast_Currently_For_Sale"]

# The document ID from the test
doc_id = ObjectId("697d7cd03eed455fdb62afd2")

# Try to find in robina collection (lowercase)
collection = db["robina"]
doc = collection.find_one({"_id": doc_id})

if not doc:
    # Try Robina with capital R
    collection = db["Robina"]
    doc = collection.find_one({"_id": doc_id})

if doc:
    print("=" * 80)
    print("PROPERTY FOUND")
    print("=" * 80)
    
    # Get address
    address = doc.get("address", "Unknown")
    if isinstance(address, dict):
        address = address.get("full_address", str(doc_id))
    
    print(f"Address: {address}")
    print(f"Document ID: {doc_id}")
    print()
    
    # Check for floor_plans field
    floor_plans = doc.get("floor_plans", [])
    print(f"Has floor_plans field: {len(floor_plans) > 0}")
    if floor_plans:
        print(f"Number of floor plans: {len(floor_plans)}")
        for idx, fp in enumerate(floor_plans):
            print(f"  Floor plan {idx + 1}: {fp[:100]}...")
    print()
    
    # Check for floor plan analysis
    if "ollama_floor_plan_analysis" in doc:
        print("=" * 80)
        print("FLOOR PLAN ANALYSIS FOUND")
        print("=" * 80)
        analysis = doc["ollama_floor_plan_analysis"]
        print(json.dumps(analysis, indent=2, default=str))
    else:
        print("=" * 80)
        print("NO FLOOR PLAN ANALYSIS FOUND")
        print("=" * 80)
        print("The ollama_floor_plan_analysis field does not exist in this document.")
        print()
        print("Available fields in document:")
        for key in sorted(doc.keys()):
            if key != "_id":
                print(f"  - {key}")
else:
    print(f"Document with ID {doc_id} not found in robina or Robina collections")

client.close()
