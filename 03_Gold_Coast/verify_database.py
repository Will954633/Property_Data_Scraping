#!/usr/bin/env python3
"""
Quick verification script for Gold Coast database
"""
from pymongo import MongoClient

# Connect to database
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Gold_Coast"]

# Get collections
collections = db.list_collection_names()
print(f"\n{'='*70}")
print("Gold Coast Database Verification")
print(f"{'='*70}\n")
print(f"Total collections (suburbs): {len(collections)}")

# Count total documents
total = sum(db[col].count_documents({}) for col in collections)
print(f"Total addresses:             {total:,}")

# Show sample address
print(f"\n{'='*70}")
print("Sample Address from Surfers Paradise")
print(f"{'='*70}\n")
sample = db.surfers_paradise.find_one()
if sample:
    for key, value in sample.items():
        if key != '_id':
            print(f"  {key:20s}: {value}")

# Show collection sizes
print(f"\n{'='*70}")
print("Top 10 Suburbs by Address Count")
print(f"{'='*70}\n")
collection_counts = [(col, db[col].count_documents({})) for col in collections]
collection_counts.sort(key=lambda x: x[1], reverse=True)
for col, count in collection_counts[:10]:
    print(f"  {col:40s} {count:6,}")

print(f"\n{'='*70}\n")
