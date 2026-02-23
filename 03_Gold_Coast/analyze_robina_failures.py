#!/usr/bin/env python3
"""
Analyze Robina Worker Failures
Examines MongoDB to identify failed addresses and reasons
"""

from pymongo import MongoClient
import json
from datetime import datetime

def analyze_failures():
    """Query MongoDB for failed addresses"""
    
    # Connect to MongoDB
    client = MongoClient('mongodb://127.0.0.1:27017/')
    db = client['Gold_Coast']
    collection = db['robina']
    
    print("=" * 80)
    print("ROBINA WORKER FAILURE ANALYSIS")
    print("=" * 80)
    print()
    
    # Get total counts
    total_count = collection.count_documents({})
    scraped_count = collection.count_documents({'scraped_data': {'$exists': True}})
    not_scraped_count = collection.count_documents({'scraped_data': {'$exists': False}})
    
    print(f"Total Addresses: {total_count:,}")
    print(f"Successfully Scraped: {scraped_count:,}")
    print(f"Not Yet Scraped: {not_scraped_count:,}")
    print()
    
    # Check for error fields (common patterns)
    error_patterns = [
        {'error': {'$exists': True}},
        {'scrape_error': {'$exists': True}},
        {'failed': True},
        {'status': 'failed'}
    ]
    
    all_errors = []
    for pattern in error_patterns:
        count = collection.count_documents(pattern)
        if count > 0:
            print(f"Documents matching {pattern}: {count}")
            errors = list(collection.find(pattern).limit(20))
            all_errors.extend(errors)
    
    print()
    print("=" * 80)
    print("SAMPLE FAILED ADDRESSES (5 examples)")
    print("=" * 80)
    print()
    
    if all_errors:
        # Show first 5 unique failed addresses
        for i, doc in enumerate(all_errors[:5], 1):
            print(f"\n{i}. Failed Address:")
            print(f"   Address: {doc.get('address', 'N/A')}")
            print(f"   Property ID: {doc.get('property_id', 'N/A')}")
            print(f"   URL: {doc.get('url', 'N/A')}")
            print(f"   Error: {doc.get('error', doc.get('scrape_error', 'Unknown error'))}")
            if 'last_attempt' in doc:
                print(f"   Last Attempt: {doc.get('last_attempt')}")
    else:
        print("No explicit error documents found.")
        print()
        print("This could mean:")
        print("  1. Workers are still processing (no failures yet)")
        print("  2. Failures are not being logged to MongoDB")
        print("  3. All addresses scraped successfully")
        print()
        print("Checking sample of unscraped addresses...")
        print()
        
        # Get 5 unscraped addresses as examples
        unscraped = list(collection.find(
            {'scraped_data': {'$exists': False}},
            {'address': 1, 'property_id': 1, 'url': 1, '_id': 0}
        ).limit(5))
        
        if unscraped:
            print("Sample Unscraped Addresses (may not be failures, just not processed yet):")
            for i, doc in enumerate(unscraped, 1):
                print(f"\n{i}. Unscraped Address:")
                print(f"   Address: {doc.get('address', 'N/A')}")
                print(f"   Property ID: {doc.get('property_id', 'N/A')}")
                print(f"   URL: {doc.get('url', 'N/A')}")
        else:
            print("All addresses appear to have been scraped!")
    
    # Check for addresses with incomplete data
    print()
    print("=" * 80)
    print("CHECKING FOR ADDRESSES WITH INCOMPLETE DATA")
    print("=" * 80)
    print()
    
    # Addresses that were scraped but may have missing fields
    incomplete = list(collection.find({
        'scraped_data': {'$exists': True},
        '$or': [
            {'scraped_data.property_details': {'$exists': False}},
            {'scraped_data.property_details': None},
            {'scraped_data.property_details.bedrooms': {'$exists': False}}
        ]
    }).limit(5))
    
    if incomplete:
        print(f"Found {len(incomplete)} addresses with incomplete data (showing first 5):")
        for i, doc in enumerate(incomplete, 1):
            print(f"\n{i}. Incomplete Data:")
            print(f"   Address: {doc.get('address', 'N/A')}")
            print(f"   Property ID: {doc.get('property_id', 'N/A')}")
            scraped_data = doc.get('scraped_data', {})
            print(f"   Has property_details: {'property_details' in scraped_data}")
            print(f"   Has timeline: {'timeline' in scraped_data}")
    else:
        print("No addresses found with incomplete data patterns.")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Scraping Progress: {(scraped_count/total_count*100):.2f}%")
    print(f"Completion Status: {'✓ Complete!' if not_scraped_count == 0 else f'{not_scraped_count:,} remain'}")
    print()
    
    client.close()

if __name__ == '__main__':
    try:
        analyze_failures()
    except Exception as e:
        print(f"Error analyzing failures: {e}")
        print()
        print("This could indicate:")
        print("  - MongoDB is not running")
        print("  - Connection issues")
        print("  - Database/collection doesn't exist yet")
