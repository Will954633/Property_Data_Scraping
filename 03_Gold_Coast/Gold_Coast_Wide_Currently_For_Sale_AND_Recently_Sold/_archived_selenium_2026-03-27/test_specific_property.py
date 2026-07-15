#!/usr/bin/env python3
"""
Test Specific Property from MongoDB
Last Updated: 31/01/2026, 10:57 am (Brisbane Time)
"""

import time
import re
from datetime import datetime
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bson.objectid import ObjectId

# MongoDB connection
MONGODB_URI = 'mongodb://127.0.0.1:27017/'
DATABASE_NAME = 'Gold_Coast_Currently_For_Sale'

def setup_driver():
    """Setup headless Chrome"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_date_listed(html):
    """Extract dateListed from HTML"""
    pattern = r'"dateListed"\s*:\s*"([^"]+)"'
    match = re.search(pattern, html)
    if match:
        timestamp = match.group(1)
        try:
            listed_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00').split('.')[0])
            days_on_market = (datetime.now() - listed_date).days
            return {
                'timestamp': timestamp,
                'date': listed_date.strftime('%d %B %Y'),
                'days': days_on_market
            }
        except:
            return None
    return None

print("="*80)
print("TESTING SPECIFIC PROPERTY FROM MONGODB")
print("="*80)

# Connect to MongoDB
print("\n→ Connecting to MongoDB...")
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# Find the property
object_id = ObjectId("697d4bf8a059217e06bfe589")
print(f"→ Looking for property with _id: {object_id}")

# Search all collections
for collection_name in db.list_collection_names():
    collection = db[collection_name]
    property_doc = collection.find_one({'_id': object_id})
    
    if property_doc:
        print(f"  ✓ Found in collection: {collection_name}")
        
        listing_url = property_doc.get('listing_url')
        address = property_doc.get('address', 'Unknown')
        
        print(f"\n📍 Property Details:")
        print(f"  Address: {address}")
        print(f"  URL: {listing_url}")
        
        if listing_url:
            # Test extraction
            driver = setup_driver()
            try:
                print(f"\n→ Loading property page...")
                driver.get(listing_url)
                time.sleep(5)
                
                html = driver.page_source
                
                print(f"→ Extracting dateListed...")
                result = extract_date_listed(html)
                
                if result:
                    print(f"\n{'='*80}")
                    print("✅ SUCCESS - Found dateListed!")
                    print(f"{'='*80}")
                    print(f"\n📅 Listing Data:")
                    print(f"  Timestamp: {result['timestamp']}")
                    print(f"  Date Listed: {result['date']}")
                    print(f"  Days on Market: {result['days']} days")
                    print(f"\n{'='*80}")
                else:
                    print("\n⚠️ Could not extract dateListed from this property")
                    
            finally:
                driver.quit()
                print("\n✓ Browser closed")
        
        break
else:
    print(f"  ✗ Property not found in any collection")

client.close()
