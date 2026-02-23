#!/usr/bin/env python3
"""
Test Update Script - Updates 10 Properties and Reviews Results
Last Updated: 30/01/2026, 8:11 pm (Brisbane Time)

This script:
1. Selects 10 properties with existing scraped_data
2. Backs up their current state
3. Updates them with fresh Domain data
4. Compares before/after to verify updates worked correctly
"""

import json
import os
from datetime import datetime
from pymongo import MongoClient
from update_gold_coast_database import GoldCoastDatabaseUpdater

def main():
    print("="*70)
    print("TEST UPDATE - 10 PROPERTIES")
    print("="*70)
    print()
    
    # Connect to MongoDB
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
    db = client['Gold_Coast']
    
    print("Step 1: Finding 10 properties with existing scraped_data...")
    print("-" * 70)
    
    # Find 10 properties with scraped_data
    test_properties = []
    for collection_name in db.list_collection_names():
        if collection_name == 'system.indexes':
            continue
        
        collection = db[collection_name]
        docs = list(collection.find(
            {'scraped_data': {'$exists': True}},
            {'scraped_data.address': 1, 'scraped_data.valuation': 1, 'scraped_data.rental_estimate': 1}
        ).limit(10 - len(test_properties)))
        
        for doc in docs:
            test_properties.append({
                'collection': collection_name,
                'mongo_id': doc['_id'],
                'address': doc.get('scraped_data', {}).get('address', 'Unknown')
            })
        
        if len(test_properties) >= 10:
            break
    
    if len(test_properties) < 10:
        print(f"⚠ Warning: Only found {len(test_properties)} properties with scraped_data")
    
    print(f"✓ Found {len(test_properties)} properties to test:\n")
    for i, prop in enumerate(test_properties, 1):
        print(f"  {i}. [{prop['collection']}] {prop['address']}")
    
    print()
    print("Step 2: Backing up current state...")
    print("-" * 70)
    
    # Backup current state
    backup = []
    for prop in test_properties:
        collection = db[prop['collection']]
        doc = collection.find_one({'_id': prop['mongo_id']})
        backup.append({
            'collection': prop['collection'],
            'mongo_id': prop['mongo_id'],
            'address': prop['address'],
            'before': doc.get('scraped_data', {})
        })
    
    # Save backup to file
    backup_file = f"test_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w') as f:
        json.dump(backup, f, indent=2, default=str)
    
    print(f"✓ Backed up to: {backup_file}\n")
    
    print("Step 3: Running update on 10 properties...")
    print("-" * 70)
    print()
    
    # Create updater instance
    updater = GoldCoastDatabaseUpdater()
    updater.setup_driver()
    
    # Update each property
    results = []
    for i, prop in enumerate(test_properties, 1):
        print(f"[{i}/{len(test_properties)}] Updating: {prop['address']}")
        
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
        results.append({
            'address': prop['address'],
            'success': success
        })
        print()
    
    # Close driver
    updater.driver.quit()
    client.close()
    
    print()
    print("="*70)
    print("STEP 4: REVIEWING RESULTS")
    print("="*70)
    print()
    
    # Reconnect to get fresh data
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
    db = client['Gold_Coast']
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"Update Summary:")
    print(f"  Successful: {successful}/{len(results)}")
    print(f"  Failed:     {failed}/{len(results)}")
    print()
    
    print("="*70)
    print("DETAILED COMPARISON - BEFORE vs AFTER")
    print("="*70)
    print()
    
    for i, backup_item in enumerate(backup, 1):
        print(f"\n{'='*70}")
        print(f"PROPERTY {i}: {backup_item['address']}")
        print(f"Collection: {backup_item['collection']}")
        print(f"{'='*70}\n")
        
        # Get updated document
        collection = db[backup_item['collection']]
        after_doc = collection.find_one({'_id': backup_item['mongo_id']})
        after_data = after_doc.get('scraped_data', {})
        before_data = backup_item['before']
        
        # Compare valuation
        print("📊 VALUATION:")
        print("-" * 70)
        before_val = before_data.get('valuation', {})
        after_val = after_data.get('valuation', {})
        
        print(f"  BEFORE: Low=${before_val.get('low', 'N/A'):,} Mid=${before_val.get('mid', 'N/A'):,} High=${before_val.get('high', 'N/A'):,}")
        print(f"  AFTER:  Low=${after_val.get('low', 'N/A'):,} Mid=${after_val.get('mid', 'N/A'):,} High=${after_val.get('high', 'N/A'):,}")
        
        val_history = after_data.get('valuation_history', [])
        if val_history:
            print(f"  ✓ HISTORY: {len(val_history)} entries")
            for j, entry in enumerate(val_history, 1):
                print(f"    {j}. Mid=${entry.get('mid', 'N/A'):,} @ {entry.get('recorded_at', 'N/A')}")
        else:
            print(f"  ⚠ NO HISTORY (valuation unchanged or first update)")
        
        print()
        
        # Compare rental estimate
        print("🏠 RENTAL ESTIMATE:")
        print("-" * 70)
        before_rent = before_data.get('rental_estimate', {})
        after_rent = after_data.get('rental_estimate', {})
        
        print(f"  BEFORE: ${before_rent.get('weekly_rent', 'N/A')}/week, {before_rent.get('yield', 'N/A')}% yield")
        print(f"  AFTER:  ${after_rent.get('weekly_rent', 'N/A')}/week, {after_rent.get('yield', 'N/A')}% yield")
        
        rent_history = after_data.get('rental_estimate_history', [])
        if rent_history:
            print(f"  ✓ HISTORY: {len(rent_history)} entries")
            for j, entry in enumerate(rent_history, 1):
                print(f"    {j}. ${entry.get('weekly_rent', 'N/A')}/week @ {entry.get('recorded_at', 'N/A')}")
        else:
            print(f"  ⚠ NO HISTORY (rental unchanged or first update)")
        
        print()
        
        # Compare timeline
        print("📅 TIMELINE:")
        print("-" * 70)
        before_timeline = before_data.get('property_timeline', [])
        after_timeline = after_data.get('property_timeline', [])
        
        print(f"  BEFORE: {len(before_timeline)} events")
        print(f"  AFTER:  {len(after_timeline)} events")
        if len(after_timeline) > 0:
            print(f"  ✓ REPLACED with fresh timeline")
            print(f"    Latest event: {after_timeline[0].get('type', 'N/A')} - {after_timeline[0].get('date', 'N/A')}")
        
        print()
        
        # Compare images
        print("🖼️  IMAGES:")
        print("-" * 70)
        before_images = before_data.get('images', [])
        after_images = after_data.get('images', [])
        
        print(f"  BEFORE: {len(before_images)} images")
        print(f"  AFTER:  {len(after_images)} images")
        if len(after_images) > 0:
            print(f"  ✓ REPLACED with fresh images")
        
        print()
        
        # Check updated_at timestamp
        if 'updated_at' in after_doc:
            print(f"✅ Document updated_at: {after_doc['updated_at']}")
        else:
            print(f"⚠ No updated_at timestamp found")
    
    print()
    print("="*70)
    print("TEST COMPLETE")
    print("="*70)
    print()
    print(f"Backup saved to: {backup_file}")
    print(f"Total properties tested: {len(test_properties)}")
    print(f"Successful updates: {successful}")
    print(f"Failed updates: {failed}")
    print()
    
    if successful == len(test_properties):
        print("✅ ALL TESTS PASSED - Update system working correctly!")
    elif successful > 0:
        print("⚠ PARTIAL SUCCESS - Some updates worked, review failures above")
    else:
        print("❌ ALL TESTS FAILED - Review errors above")
    
    print()
    client.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
