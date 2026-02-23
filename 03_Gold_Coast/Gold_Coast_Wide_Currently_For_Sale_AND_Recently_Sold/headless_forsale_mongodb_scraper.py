#!/usr/bin/env python3
"""
Headless For-Sale Property Scraper with MongoDB Integration
Last Updated: 31/01/2026, 9:50 am (Brisbane Time)

PHASE 2 IMPLEMENTATION:
- Scrapes for-sale properties in headless mode
- Writes to Gold_Coast_Currently_For_Sale database
- One collection per suburb (e.g., 'robina')
- Tracks changes in history.<field> arrays
- Matches existing properties_for_sale structure

AGENT EXTRACTION UPDATE (31/01/2026):
- Captures multiple agents from carousel rotation (10-12 second intervals)
- Waits 24 seconds total to capture all agents (3 snapshots)
- Extracts agency name and all agent names
- Stores as agent_names (array) and agent_name (comma-separated string)

Based on:
- property_detail_scraper_forsale_headless.py (headless scraping)
- Existing properties_for_sale collection structure
- Fields_Orchestrator change tracking pattern
"""

import time
import os
import json
import sys
from datetime import datetime
from typing import Dict, Optional, List
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium webdriver-manager pymongo")
    exit(1)

# Import the HTML parser from the existing production system
sys.path.append('../../07_Undetectable_method/Simple_Method/../00_Production_System/02_Individual_Property_Google_Search')
try:
    from html_parser import parse_listing_html, clean_property_data
except ImportError:
    print("ERROR: html_parser not found!")
    print("Make sure the path to html_parser.py is correct")
    exit(1)

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
DATABASE_NAME = 'Gold_Coast_Currently_For_Sale'
PAGE_LOAD_WAIT = 5
BETWEEN_PROPERTY_DELAY = 2

# Monitored fields for change tracking
MONITORED_FIELDS = ['price', 'inspection_times', 'agents_description']


class HeadlessForSaleMongoDBScraper:
    """Headless scraper with MongoDB integration and change tracking"""
    
    def __init__(self, suburb: str):
        """Initialize scraper for specific suburb"""
        self.suburb = suburb.lower()
        self.driver = None
        
        # MongoDB connection
        print(f"→ Connecting to MongoDB...")
        self.mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        self.db = self.mongo_client[DATABASE_NAME]
        self.collection = self.db[self.suburb]
        
        # Test connection
        try:
            self.mongo_client.admin.command('ping')
            print(f"  ✓ MongoDB connected")
            print(f"  ✓ Database: {DATABASE_NAME}")
            print(f"  ✓ Collection: {self.suburb}")
        except Exception as e:
            raise Exception(f"MongoDB connection failed: {e}")
        
        # Create indexes
        self.create_indexes()
        
        # Setup headless browser
        self.setup_driver()
    
    def create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            # Unique index on listing_url
            self.collection.create_index([("listing_url", ASCENDING)], unique=True)
            # Index on address for lookups
            self.collection.create_index([("address", ASCENDING)])
            # Index on last_updated for change monitoring
            self.collection.create_index([("last_updated", ASCENDING)])
            print(f"  ✓ Indexes created/verified")
        except Exception as e:
            print(f"  ⚠ Index creation warning: {e}")
    
    def setup_driver(self):
        """Setup headless Chrome WebDriver"""
        print("→ Setting up headless Chrome WebDriver...")
        
        chrome_options = Options()
        # HEADLESS MODE
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Anti-detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("  ✓ Headless Chrome ready")
        except Exception as e:
            raise Exception(f"Failed to create WebDriver: {e}")
    
    def extract_address_from_url(self, url: str) -> str:
        """Extract property address from Domain.com.au URL"""
        import re
        
        path = url.replace('https://www.domain.com.au/', '').replace('http://www.domain.com.au/', '')
        path = re.sub(r'-\d{7,10}$', '', path)
        parts = path.split('-')
        
        suburb_idx = -1
        for i, part in enumerate(parts):
            if part in ['qld', 'nsw', 'vic', 'sa', 'wa', 'tas', 'nt', 'act']:
                suburb_idx = i - 1
                break
        
        if suburb_idx > 0:
            street_parts = parts[:suburb_idx]
            street_address = ' '.join(street_parts).title()
            suburb = parts[suburb_idx].title()
            state = parts[suburb_idx + 1].upper() if suburb_idx + 1 < len(parts) else ''
            postcode = parts[suburb_idx + 2] if suburb_idx + 2 < len(parts) else ''
            full_address = f"{street_address}, {suburb}, {state} {postcode}"
            return full_address
        
        return ' '.join(parts).title()
    
    def scrape_property(self, url: str) -> Optional[Dict]:
        """Scrape single property using headless browser"""
        try:
            print(f"→ Loading: {url}")
            self.driver.get(url)
            time.sleep(PAGE_LOAD_WAIT)
            
            # Verify page loaded
            current_url = self.driver.current_url
            if not current_url or 'domain.com.au' not in current_url:
                print(f"  ✗ Page load failed")
                return None
            
            # Extract HTML multiple times to capture agent carousel
            # Domain rotates between agents every 10-12 seconds
            print(f"  → Capturing agent data (waiting for carousel rotation)...")
            all_agents = set()
            agency = None
            
            # Capture HTML at different intervals to get all agents
            for i in range(3):  # Check 3 times over 24 seconds
                html = self.driver.page_source
                if html and len(html) > 100:
                    # Quick parse to extract just agent info
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract agency (should be consistent)
                    if not agency:
                        agency_elem = soup.find(attrs={'data-testid': 'listing-details__agent-details-agency-name'})
                        if agency_elem:
                            agency = agency_elem.get_text(strip=True)
                    
                    # Extract agent names from current view
                    agent_detail_sections = soup.find_all(attrs={'data-testid': 'listing-details__agent-details'})
                    for section in agent_detail_sections:
                        agent_name_elem = section.find(attrs={'data-testid': 'listing-details__agent-details-agent-name'})
                        if agent_name_elem:
                            name = agent_name_elem.get_text(strip=True)
                            if name:
                                all_agents.add(name)
                
                # Wait for carousel to rotate (except on last iteration)
                if i < 2:
                    time.sleep(12)  # Wait 12 seconds for carousel rotation
            
            print(f"  ✓ Found {len(all_agents)} agent(s): {', '.join(all_agents)}")
            if agency:
                print(f"  ✓ Agency: {agency}")
            
            # Now get the full HTML for complete property data
            html = self.driver.page_source
            if not html or len(html) < 100:
                print(f"  ✗ HTML too small")
                return None
            
            print(f"  ✓ HTML extracted ({len(html):,} chars)")
            
            # Parse HTML
            address = self.extract_address_from_url(url)
            property_data = parse_listing_html(html, address)
            property_data = clean_property_data(property_data)
            
            # Override agent data with our carousel-captured data
            if all_agents:
                agent_list = sorted(list(all_agents))  # Sort for consistency
                property_data['agent_names'] = agent_list
                property_data['agent_name'] = ', '.join(agent_list)
            if agency:
                property_data['agency'] = agency
            
            if not property_data:
                print(f"  ✗ No data extracted")
                return None
            
            # Add required fields
            property_data['listing_url'] = url
            property_data['scrape_mode'] = 'headless'
            property_data['extraction_method'] = 'HTML'
            property_data['extraction_date'] = datetime.now().isoformat()
            property_data['source'] = 'headless_forsale_scraper'
            
            # Enrichment fields (set to defaults, enrichment done separately)
            property_data['enriched'] = False
            property_data['enrichment_attempted'] = False
            property_data['enrichment_retry_count'] = 0
            property_data['enrichment_error'] = None
            property_data['enrichment_data'] = None
            property_data['last_enriched'] = None
            property_data['image_analysis'] = []
            
            print(f"  ✓ Data extracted: {property_data.get('bedrooms')}bed, {property_data.get('bathrooms')}bath, {len(property_data.get('property_images', []))} images")
            
            return property_data
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
    
    def detect_changes(self, existing_doc: Dict, new_data: Dict) -> Dict:
        """Detect changes in monitored fields and build history entries"""
        changes = {}
        now = datetime.now()
        
        for field in MONITORED_FIELDS:
            old_value = existing_doc.get(field)
            new_value = new_data.get(field)
            
            # Check if value changed
            if old_value != new_value:
                # Get existing history or create new
                history_key = f'history.{field}'
                existing_history = existing_doc.get('history', {}).get(field, [])
                
                # Append new entry
                new_entry = {
                    'value': new_value,
                    'recorded_at': now
                }
                existing_history.append(new_entry)
                
                changes[history_key] = existing_history
                print(f"  📊 Change detected in {field}")
        
        return changes
    
    def save_to_mongodb(self, property_data: Dict) -> bool:
        """Save or update property in MongoDB with change tracking"""
        try:
            listing_url = property_data['listing_url']
            
            # Check if property exists
            existing_doc = self.collection.find_one({'listing_url': listing_url})
            
            if existing_doc:
                # Property exists - update with change tracking
                print(f"  → Updating existing property...")
                
                # Detect changes
                changes = self.detect_changes(existing_doc, property_data)
                
                # Build update document
                update_doc = {
                    '$set': {
                        **property_data,
                        'last_updated': datetime.now(),
                    }
                }
                
                # Add change history if any changes detected
                if changes:
                    update_doc['$set'].update(changes)
                    update_doc['$set']['last_change_detected'] = datetime.now()
                    update_doc['$inc'] = {'change_count': len(changes)}
                
                # Preserve first_seen
                if 'first_seen' in existing_doc:
                    update_doc['$setOnInsert'] = {'first_seen': existing_doc['first_seen']}
                
                result = self.collection.update_one(
                    {'listing_url': listing_url},
                    update_doc
                )
                
                if result.modified_count > 0:
                    print(f"  ✓ Updated in MongoDB ({len(changes)} changes)")
                    return True
                else:
                    print(f"  ✓ No changes detected")
                    return True
            
            else:
                # New property - insert
                print(f"  → Inserting new property...")
                
                # Add timestamps
                property_data['first_seen'] = datetime.now()
                property_data['last_updated'] = datetime.now()
                property_data['change_count'] = 0
                
                # Initialize history arrays
                property_data['history'] = {}
                for field in MONITORED_FIELDS:
                    if field in property_data and property_data[field]:
                        property_data['history'][field] = [{
                            'value': property_data[field],
                            'recorded_at': datetime.now()
                        }]
                
                result = self.collection.insert_one(property_data)
                
                if result.inserted_id:
                    print(f"  ✓ Inserted into MongoDB")
                    return True
                else:
                    print(f"  ✗ Insert failed")
                    return False
        
        except DuplicateKeyError:
            print(f"  ⚠ Duplicate key - property already exists")
            return False
        except Exception as e:
            print(f"  ✗ MongoDB error: {e}")
            return False
    
    def process_property_url(self, url: str, index: int, total: int) -> bool:
        """Process single property: scrape and save to MongoDB"""
        print(f"\n{'='*80}")
        print(f"Property {index}/{total} (HEADLESS + MONGODB)")
        print(f"{'='*80}")
        
        start_time = datetime.now()
        
        # Scrape property
        property_data = self.scrape_property(url)
        
        if not property_data:
            print(f"  ✗ Scraping failed")
            return False
        
        # Save to MongoDB
        success = self.save_to_mongodb(property_data)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"  ⏱ Duration: {duration:.1f}s")
        
        return success
    
    def close(self):
        """Close browser and MongoDB connection"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")
        
        if self.mongo_client:
            self.mongo_client.close()
            print("✓ MongoDB connection closed")


def load_urls_from_file(filepath: str) -> List[str]:
    """Load property listing URLs from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if 'urls' in data:
        return data['urls']
    elif 'all_listing_urls' in data:
        return data['all_listing_urls']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unknown JSON format")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Headless for-sale scraper with MongoDB integration")
    parser.add_argument('--suburb', required=True, help='Suburb name (e.g., robina)')
    parser.add_argument('--input', required=True, help='Input JSON file with property URLs')
    parser.add_argument('--limit', type=int, help='Limit number of properties (for testing)')
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("HEADLESS FOR-SALE SCRAPER WITH MONGODB INTEGRATION")
    print("=" * 80)
    print(f"\nSuburb: {args.suburb}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Collection: {args.suburb.lower()}")
    print(f"Mode: Headless Chrome + Change Tracking")
    print("=" * 80)
    
    # Load URLs
    if not os.path.exists(args.input):
        print(f"\n✗ Input file not found: {args.input}")
        return 1
    
    print(f"\n→ Loading property URLs from: {args.input}")
    urls = load_urls_from_file(args.input)
    
    if args.limit:
        urls = urls[:args.limit]
        print(f"  ✓ Loaded {len(urls)} URLs (limited)")
    else:
        print(f"  ✓ Loaded {len(urls)} URLs")
    
    # Initialize scraper
    scraper = None
    try:
        scraper = HeadlessForSaleMongoDBScraper(args.suburb)
        
        print(f"\n{'='*80}")
        print("Starting property scraping...")
        print(f"{'='*80}\n")
        
        # Process each property
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            if scraper.process_property_url(url, i, len(urls)):
                successful += 1
            else:
                failed += 1
            
            # Delay between properties
            if i < len(urls):
                print(f"\n→ Waiting {BETWEEN_PROPERTY_DELAY}s...")
                time.sleep(BETWEEN_PROPERTY_DELAY)
        
        # Summary
        print(f"\n{'='*80}")
        print("SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"\n📊 SUMMARY:")
        print(f"  Suburb:       {args.suburb}")
        print(f"  Total:        {len(urls)}")
        print(f"  Successful:   {successful}")
        print(f"  Failed:       {failed}")
        print(f"  Success rate: {(successful/len(urls)*100):.1f}%")
        print(f"\n💾 MongoDB:")
        print(f"  Database:    {DATABASE_NAME}")
        print(f"  Collection:  {args.suburb.lower()}")
        print(f"  Documents:   {scraper.collection.count_documents({})}")
        
        print(f"\n✅ PHASE 2 COMPLETE: MongoDB integration working")
        print(f"{'='*80}\n")
        
        return 0
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"FATAL ERROR")
        print(f"{'='*80}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    exit(main())
