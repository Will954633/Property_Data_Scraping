#!/usr/bin/env python3
"""
End-to-End Test: Scrape → Parse → Upload to MongoDB
Tests the complete workflow for sold properties
"""

import time
import os
import json
from datetime import datetime
from pymongo import MongoClient

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"ERROR: Required package not installed: {e}")
    print("Please install with:")
    print("  pip3 install selenium webdriver-manager pymongo")
    exit(1)

from html_parser_sold import parse_sold_listing_html, clean_property_data, is_within_6_months
from bs4 import BeautifulSoup
import re

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "sold_last_6_months_test"  # Use test collection

# Test URL - List page to extract a property from
LIST_URL = "https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1"


def create_driver():
    """Create and configure Selenium WebDriver"""
    print("→ Setting up Chrome WebDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("  ✓ Chrome WebDriver ready")
        return driver
    except Exception as e:
        print(f"  ✗ Failed to create WebDriver: {e}")
        return None


def extract_first_property_url(driver):
    """Extract the first property URL from the list page"""
    print("→ Loading list page to find a property...")
    driver.get(LIST_URL)
    time.sleep(5)
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find property links - Domain uses data-testid for property cards
    property_links = soup.find_all('a', attrs={'data-testid': re.compile(r'listing-card-wrapper')})
    
    if not property_links:
        # Fallback: look for any links to sold property pages
        property_links = soup.find_all('a', href=re.compile(r'/\d+-[a-z-]+-qld-\d+'))
    
    if property_links:
        # Get the first property URL
        first_link = property_links[0]
        href = first_link.get('href', '')
        
        # Make it absolute if needed
        if href.startswith('/'):
            property_url = f"https://www.domain.com.au{href}"
        else:
            property_url = href
        
        # Extract address from the link text or nearby elements
        address_elem = first_link.find(attrs={'data-testid': 'address-line1'})
        if address_elem:
            address = address_elem.get_text(strip=True)
        else:
            # Try to extract from URL
            match = re.search(r'/(\d+-.+?-qld-\d+)', href)
            if match:
                address = match.group(1).replace('-', ' ').title()
            else:
                address = "Unknown Address"
        
        print(f"  ✓ Found property: {address}")
        print(f"  ✓ URL: {property_url}")
        
        return property_url, address
    else:
        print("  ✗ No property links found on list page")
        return None, None


def setup_mongodb():
    """Setup MongoDB connection and test collection"""
    print("\n→ Connecting to MongoDB...")
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        print("  ✓ MongoDB connected")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Clear test collection
        collection.delete_many({})
        print(f"  ✓ Test collection '{COLLECTION_NAME}' cleared")
        
        # Create indexes
        collection.create_index("address", unique=True)
        collection.create_index("sale_date")
        print("  ✓ Indexes created")
        
        return client, collection
    except Exception as e:
        print(f"  ✗ MongoDB connection failed: {e}")
        print("  ℹ Make sure MongoDB is running: mongod")
        return None, None


def upload_to_mongodb(collection, property_data):
    """Upload property data to MongoDB"""
    print("\n→ Uploading to MongoDB...")
    
    try:
        # Add metadata
        insert_doc = {
            **property_data,
            "first_seen": datetime.now(),
            "last_updated": datetime.now(),
            "source": "end_to_end_test"
        }
        
        # Insert
        result = collection.insert_one(insert_doc)
        print(f"  ✓ Inserted with ID: {result.inserted_id}")
        
        return True
    except Exception as e:
        print(f"  ✗ Upload failed: {e}")
        return False


def verify_in_mongodb(collection, address):
    """Verify property exists in MongoDB"""
    print("\n→ Verifying data in MongoDB...")
    
    try:
        doc = collection.find_one({"address": address})
        
        if doc:
            print(f"  ✓ Property found in database")
            print(f"\n  📋 Database Record:")
            print(f"    Address: {doc.get('address')}")
            print(f"    Sale Date: {doc.get('sale_date')}")
            print(f"    Sale Price: {doc.get('sale_price')}")
            print(f"    Property Type: {doc.get('property_type')}")
            print(f"    Bedrooms: {doc.get('bedrooms')}")
            print(f"    Bathrooms: {doc.get('bathrooms')}")
            print(f"    Car Spaces: {doc.get('carspaces')}")
            print(f"    First Seen: {doc.get('first_seen')}")
            print(f"    Source: {doc.get('source')}")
            
            # Count images
            images = doc.get('property_images', [])
            if images:
                print(f"    Property Images: {len(images)} items")
            
            return True
        else:
            print(f"  ✗ Property NOT found in database")
            return False
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        return False


def test_end_to_end():
    """Run complete end-to-end test"""
    print("\n" + "=" * 80)
    print("END-TO-END TEST: SCRAPE → PARSE → UPLOAD TO MONGODB")
    print("=" * 80)
    print(f"\nList URL: {LIST_URL}")
    print(f"MongoDB: {MONGODB_URI}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Collection: {COLLECTION_NAME} (test)")
    
    # Setup MongoDB
    mongo_client, collection = setup_mongodb()
    if not mongo_client:
        print("\n✗ Cannot proceed without MongoDB")
        return 1
    
    # Create driver
    driver = create_driver()
    if not driver:
        print("\n✗ Cannot proceed without WebDriver")
        mongo_client.close()
        return 1
    
    try:
        # STEP 1: Extract property URL from list page
        print("\n" + "=" * 80)
        print("STEP 1: EXTRACT PROPERTY URL FROM LIST PAGE")
        print("=" * 80)
        
        property_url, address = extract_first_property_url(driver)
        
        if not property_url:
            print("\n✗ Could not find a property to test")
            return 1
        
        # STEP 2: Scrape individual property page
        print("\n" + "=" * 80)
        print("STEP 2: SCRAPE INDIVIDUAL PROPERTY PAGE")
        print("=" * 80)
        
        print(f"\n→ Loading property page...")
        driver.get(property_url)
        time.sleep(5)
        
        print("→ Extracting HTML...")
        html = driver.page_source
        print(f"  ✓ Extracted {len(html):,} characters")
        
        # STEP 3: Parse property data
        print("\n" + "=" * 80)
        print("STEP 3: PARSE PROPERTY DATA")
        print("=" * 80)
        
        print("\n→ Parsing property data...")
        property_data = parse_sold_listing_html(html, address)
        property_data = clean_property_data(property_data)
        
        # Add metadata
        property_data['listing_url'] = property_url
        property_data['suburb_scraped'] = 'robina'
        
        # Validate critical fields
        critical_fields = ['sale_date', 'sale_price', 'address', 'bedrooms', 'bathrooms', 'property_type']
        missing_fields = [f for f in critical_fields if not property_data.get(f)]
        
        if missing_fields:
            print(f"  ✗ Missing critical fields: {', '.join(missing_fields)}")
            return 1
        
        print(f"  ✓ All critical fields present")
        print(f"\n  📋 Parsed Data:")
        print(f"    Address: {property_data.get('address')}")
        print(f"    Sale Date: {property_data.get('sale_date')}")
        print(f"    Sale Price: {property_data.get('sale_price')}")
        print(f"    Property Type: {property_data.get('property_type')}")
        print(f"    Bedrooms: {property_data.get('bedrooms')}")
        print(f"    Bathrooms: {property_data.get('bathrooms')}")
        
        # STEP 4: Upload to MongoDB
        print("\n" + "=" * 80)
        print("STEP 4: UPLOAD TO MONGODB")
        print("=" * 80)
        
        upload_success = upload_to_mongodb(collection, property_data)
        
        if not upload_success:
            print("\n✗ Upload failed")
            return 1
        
        # STEP 5: Verify in MongoDB
        print("\n" + "=" * 80)
        print("STEP 5: VERIFY DATA IN MONGODB")
        print("=" * 80)
        
        verify_success = verify_in_mongodb(collection, address)
        
        if not verify_success:
            print("\n✗ Verification failed")
            return 1
        
        # STEP 6: Collection statistics
        print("\n" + "=" * 80)
        print("STEP 6: COLLECTION STATISTICS")
        print("=" * 80)
        
        total_count = collection.count_documents({})
        print(f"\n  Total documents in collection: {total_count}")
        
        # Overall assessment
        print("\n" + "=" * 80)
        print("OVERALL ASSESSMENT")
        print("=" * 80)
        
        print("\n✅ END-TO-END TEST PASSED")
        print("  ✓ Property URL extracted from list page")
        print("  ✓ Property page scraped successfully")
        print("  ✓ All critical fields parsed correctly")
        print("  ✓ Data uploaded to MongoDB")
        print("  ✓ Data verified in database")
        print("\n  🎉 Complete workflow is functioning correctly!")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if driver:
            print("\n→ Closing browser...")
            driver.quit()
            print("  ✓ Browser closed")
        
        if mongo_client:
            print("→ Closing MongoDB connection...")
            mongo_client.close()
            print("  ✓ MongoDB connection closed")


if __name__ == "__main__":
    exit(test_end_to_end())
