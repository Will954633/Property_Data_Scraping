#!/usr/bin/env python3
"""
Quick Test - Updates 2 Properties Only
Last Updated: 30/01/2026, 8:47 pm (Brisbane Time)

Fast test to verify the update system works correctly.
"""

import json
import os
from datetime import datetime
from pymongo import MongoClient
from update_gold_coast_database import GoldCoastDatabaseUpdater

def main():
    print("="*70)
    print("QUICK TEST - 2 PROPERTIES")
    print("="*70)
    print()
    
    # Connect to MongoDB
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
    db = client['Gold_Coast']
    
    print("Finding 2 properties with existing scraped_data...")
    
    # Find 2 properties
    test_properties = []
    for collection_name in db.list_collection_names():
        if collection_name == 'system.indexes':
            continue
        
        collection = db[collection_name]
        docs = list(collection.find(
            {'scraped_data': {'$exists': True}},
            {'scraped_data.address': 1}
        ).limit(2))
        
        for doc in docs:
            test_properties.append({
                'collection': collection_name,
                'mongo_id': doc['_id'],
                'address': doc.get('scraped_data', {}).get('address', 'Unknown')
            })
            if len(test_properties) >= 2:
                break
        
        if len(test_properties) >= 2:
            break
    
    print(f"✓ Found {len(test_properties)} properties:\n")
    for i, prop in enumerate(test_properties, 1):
        print(f"  {i}. [{prop['collection']}] {prop['address']}")
    
    print("\nBacking up current state...")
    backup = []
    for prop in test_properties:
        collection = db[prop['collection']]
        doc = collection.find_one({'_id': prop['mongo_id']})
        backup.append({
            'collection': prop['collection'],
            'mongo_id': prop['mongo_id'],
            'address': prop['address'],
            'before_valuation': doc.get('scraped_data', {}).get('valuation'),
            'before_rental': doc.get('scraped_data', {}).get('rental_estimate'),
            'before_timeline_count': len(doc.get('scraped_data', {}).get('property_timeline', [])),
            'before_images_count': len(doc.get('scraped_data', {}).get('images', []))
        })
    
    print("✓ Backup complete\n")
    print("="*70)
    print("UPDATING PROPERTIES")
    print("="*70)
    print()
    
    # Create updater
    updater = GoldCoastDatabaseUpdater()
    updater.setup_driver()
    
    # Update each property
    for i, prop in enumerate(test_properties, 1):
        print(f"\n[{i}/{len(test_properties)}] {prop['address']}")
        print("-" * 70)
        
        collection = db[prop['collection']]
        existing_doc = collection.find_one({'_id': prop['mongo_id']})
        
        prop_info = {
            'address': prop['address'],
            'suburb': prop['collection'],
            'mongo_id': prop['mongo_id'],
            'collection': prop['collection'],
            'existing_valuation': existing_doc.get('scraped_data', {}).get('valuation'),
            'existing_rental': existing_doc.get('scraped_data', {}).get('rental_estimate')
        }
        
        success = updater.update_property(prop_info, existing_doc)
        print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    updater.driver.quit()
    client.close()
    
    print("\n" + "="*70)
    print("VERIFICATION - CHECKING UPDATES")
    print("="*70)
    print()
    
    # Reconnect and verify
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
    db = client['Gold_Coast']
    
    for i, backup_item in enumerate(backup, 1):
        print(f"\nProperty {i}: {backup_item['address']}")
        print("-" * 70)
        
        collection = db[backup_item['collection']]
        after_doc = collection.find_one({'_id': backup_item['mongo_id']})
        after_data = after_doc.get('scraped_data', {})
        
        # Check valuation
        after_val = after_data.get('valuation', {})
        print(f"Valuation: ${after_val.get('mid', 'N/A'):,}")
        
        val_history = after_data.get('valuation_history', [])
        if val_history:
            print(f"  ✅ valuation_history: {len(val_history)} entries")
            for j, entry in enumerate(val_history, 1):
                print(f"     {j}. ${entry.get('mid', 'N/A'):,} @ {entry.get('recorded_at', 'N/A')[:19]}")
        else:
            print(f"  ⚠️  No valuation_history (unchanged)")
        
        # Check rental
        after_rent = after_data.get('rental_estimate', {})
        print(f"\nRental: ${after_rent.get('weekly_rent', 'N/A')}/week")
        
        rent_history = after_data.get('rental_estimate_history', [])
        if rent_history:
            print(f"  ✅ rental_estimate_history: {len(rent_history)} entries")
            for j, entry in enumerate(rent_history, 1):
                print(f"     {j}. ${entry.get('weekly_rent', 'N/A')}/week @ {entry.get('recorded_at', 'N/A')[:19]}")
        else:
            print(f"  ⚠️  No rental_estimate_history (unchanged)")
        
        # Check timeline
        after_timeline = after_data.get('property_timeline', [])
        print(f"\nTimeline: {len(after_timeline)} events")
        if len(after_timeline) != backup_item['before_timeline_count']:
            print(f"  ✅ CHANGED from {backup_item['before_timeline_count']} events")
        else:
            print(f"  ✅ REPLACED (same count)")
        
        # Check images
        after_images = after_data.get('images', [])
        print(f"Images: {len(after_images)} images")
        if len(after_images) != backup_item['before_images_count']:
            print(f"  ✅ CHANGED from {backup_item['before_images_count']} images")
        else:
            print(f"  ✅ REPLACED (same count)")
        
        # Check updated_at
        if 'updated_at' in after_doc:
            print(f"\n✅ updated_at: {after_doc['updated_at']}")
        else:
            print(f"\n⚠️  No updated_at timestamp")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    
    client.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
