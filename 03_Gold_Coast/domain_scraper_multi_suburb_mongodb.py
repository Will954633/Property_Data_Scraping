#!/usr/bin/env python3
"""
Domain Property Scraper - Multi-Suburb (MongoDB Storage)
Scraper for processing multiple Gold Coast suburbs with direct MongoDB storage
Processes top 30% of unscraped addresses across largest suburbs
"""

import json
import os
import time
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class MultiSuburbScraperMongoDB:
    """Domain scraper for multiple suburbs - saves directly to MongoDB"""
    
    @staticmethod
    def transform_timeline_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw timeline event to clean, readable format"""
        # Parse date
        event_date = event.get('eventDate')
        if event_date:
            try:
                date_obj = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d')
                month_year = date_obj.strftime('%b %Y')
            except ValueError:
                formatted_date = None
                month_year = None
        else:
            formatted_date = None
            month_year = None
        
        # Extract agency info
        agency_info = event.get('agency')
        agency_name = agency_info.get('name') if agency_info else None
        agency_url = agency_info.get('profileUrl') if agency_info else None
        
        # Build clean event
        clean_event = {
            'date': formatted_date,
            'month_year': month_year,
            'category': event.get('category'),
            'type': event.get('priceDescription'),
            'price': event.get('eventPrice'),
            'days_on_market': event.get('daysOnMarket'),
            'is_major_event': event.get('isMajorEvent'),
            'agency_name': agency_name,
            'agency_url': agency_url,
        }
        
        # Add sale metadata
        sale_metadata = event.get('saleMetadata')
        if sale_metadata:
            clean_event['is_sold'] = sale_metadata.get('isSold')
        else:
            clean_event['is_sold'] = None
        
        return clean_event
    
    def __init__(self):
        # Configuration from environment
        self.worker_id = int(os.getenv('WORKER_ID', 0))
        self.total_workers = int(os.getenv('TOTAL_WORKERS', 50))
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
        
        # Initialize MongoDB connection
        print(f"Connecting to MongoDB...")
        self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=10000)
        self.db = self.mongo_client['Gold_Coast']
        
        # Test MongoDB connection
        try:
            self.mongo_client.admin.command('ping')
            print(f"✓ MongoDB connected")
        except Exception as e:
            raise Exception(f"MongoDB connection failed: {e}")
        
        # Target only robina collection
        self.TARGET_SUBURBS = ['robina']
        print(f"✓ Targeting robina collection only")
        
        # Selenium driver
        self.driver = None
        
        print(f"\nWorker {self.worker_id}/{self.total_workers} initialized")
        print(f"MongoDB: {self.mongodb_uri.split('@')[1] if '@' in self.mongodb_uri else 'localhost'}")
        print(f"Processing: ALL suburbs ({len(self.TARGET_SUBURBS)} collections)")
        if len(self.TARGET_SUBURBS) <= 5:
            print(f"Suburbs: {', '.join(self.TARGET_SUBURBS)}")
        else:
            print(f"First 5 suburbs: {', '.join(self.TARGET_SUBURBS[:5])}...")
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Detect ChromeDriver location
        import platform
        import shutil
        
        chromedriver_path = None
        if platform.system() == 'Darwin':  # macOS
            possible_paths = [
                '/opt/homebrew/bin/chromedriver',  # ARM Mac
                '/usr/local/bin/chromedriver',      # Intel Mac
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    break
            
            if not chromedriver_path:
                chromedriver_path = shutil.which('chromedriver')
        else:  # Linux (Google Cloud)
            chromedriver_path = '/usr/bin/chromedriver'
        
        if chromedriver_path:
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.implicitly_wait(10)
        print("✓ Chrome driver initialized")
    
    def build_address_from_document(self, doc: Dict) -> Optional[str]:
        """Build address string from MongoDB document"""
        parts = []
        
        # Unit/Villa prefix
        if doc.get('UNIT_TYPE') and doc.get('UNIT_NUMBER'):
            unit_type = str(doc['UNIT_TYPE']).upper()
            unit_num = str(doc['UNIT_NUMBER'])
            parts.append(f"{unit_type} {unit_num}/")
        
        # Street number
        if doc.get('STREET_NO_1'):
            parts.append(str(doc['STREET_NO_1']))
        
        # Street name and type
        if doc.get('STREET_NAME'):
            street_part = str(doc['STREET_NAME'])
            if doc.get('STREET_TYPE'):
                street_part += f" {doc['STREET_TYPE']}"
            parts.append(street_part)
        
        # Locality, state, postcode
        if doc.get('LOCALITY'):
            locality = str(doc['LOCALITY'])
            locality_part = f"{locality} QLD"
            if doc.get('POSTCODE'):
                locality_part += f" {doc['POSTCODE']}"
            parts.append(locality_part)
        
        if not parts:
            return None
        
        address = ' '.join(parts)
        address = re.sub(r'\s*/\s*', '/', address)
        address = re.sub(r'/\s+', '/', address)
        
        return address
    
    def get_my_addresses(self) -> List[Dict]:
        """Get addresses from target suburbs assigned to this worker"""
        print(f"\nRetrieving addresses from {len(self.TARGET_SUBURBS)} target suburbs...")
        
        all_addresses = []
        
        # Collect addresses from each suburb
        for suburb in self.TARGET_SUBURBS:
            collection = self.db[suburb]
            
            # Get unscraped documents from this suburb
            docs = list(collection.find({'scraped_data': {'$exists': False}}, {
                'ADDRESS_PID': 1,
                'UNIT_TYPE': 1,
                'UNIT_NUMBER': 1,
                'STREET_NO_1': 1,
                'STREET_NAME': 1,
                'STREET_TYPE': 1,
                'LOCALITY': 1,
                'POSTCODE': 1,
                '_id': 1
            }))
            
            for doc in docs:
                address = self.build_address_from_document(doc)
                if address:
                    all_addresses.append({
                        'address_pid': doc.get('ADDRESS_PID'),
                        'address': address,
                        'suburb': suburb,
                        'doc_id': str(doc.get('_id')),
                        'mongo_id': doc.get('_id'),
                        'collection': suburb
                    })
            
            print(f"  {suburb:30s}: {len(docs):6,d} unscraped")
        
        # Sort by suburb then address_pid for consistent ordering
        all_addresses.sort(key=lambda x: (x['suburb'], x.get('address_pid') or 0))
        
        # Calculate this worker's slice
        total = len(all_addresses)
        per_worker = total // self.total_workers
        start_idx = self.worker_id * per_worker
        
        # Last worker gets remainder
        if self.worker_id == self.total_workers - 1:
            end_idx = total
        else:
            end_idx = start_idx + per_worker
        
        my_addresses = all_addresses[start_idx:end_idx]
        
        print(f"\nTotal unscraped addresses: {total:,}")
        print(f"My slice: {start_idx:,} to {end_idx:,} ({len(my_addresses):,} addresses)")
        
        # Show suburb distribution for this worker
        suburb_counts = {}
        for addr in my_addresses:
            suburb_counts[addr['suburb']] = suburb_counts.get(addr['suburb'], 0) + 1
        
        print(f"\nMy suburb distribution:")
        for suburb, count in sorted(suburb_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {suburb:30s}: {count:6,d} addresses")
        
        return my_addresses
    
    def build_domain_url(self, address: str) -> str:
        """Build Domain property profile URL from address"""
        # Remove unit type prefix
        url_slug = re.sub(r'^[A-Z]\s+', '', address.upper())
        url_slug = url_slug.lower().strip()
        url_slug = re.sub(r'[,\s/]+', '-', url_slug)
        url_slug = re.sub(r'[^a-z0-9\-]', '', url_slug)
        url_slug = re.sub(r'-+', '-', url_slug)
        url_slug = url_slug.strip('-')
        
        return f"https://www.domain.com.au/property-profile/{url_slug}"
    
    def extract_property_data(self, url: str, address: str, retry_count: int = 0, max_retries: int = 2) -> Optional[Dict]:
        """Extract property data from Domain.com.au"""
        try:
            print(f"  Accessing: {url}")
            if retry_count > 0:
                print(f"  Retry attempt {retry_count}/{max_retries}")
            
            self.driver.get(url)
            time.sleep(5)
            
            html = self.driver.page_source
            
            # Extract __NEXT_DATA__ JSON
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', 
                            html, re.DOTALL)
            
            if not match:
                print(f"  ⚠ No JSON data found")
                return None
            
            try:
                page_data = json.loads(match.group(1))
                apollo_state = page_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})
            except Exception as e:
                print(f"  ⚠ JSON parse error: {e}")
                return None
            
            # Find Property object
            property_obj = {}
            for key, value in apollo_state.items():
                if key.startswith('Property:') and value.get('__typename') == 'Property':
                    property_obj = value
                    break
            
            if not property_obj:
                print(f"  ⚠ No property object found")
                return None
            
            # Extract data
            features = property_obj.get('features', {})
            valuation = property_obj.get('valuation', {})
            
            beds = features.get('beds') or features.get('bedrooms')
            baths = features.get('baths') or features.get('bathrooms')
            parking = features.get('parking') or features.get('parkingSpaces') or features.get('carSpaces')
            prop_type = (features.get('propertyType') or features.get('type') or 
                        property_obj.get('propertyType') or property_obj.get('type'))
            land_size = (features.get('landSize') or features.get('land_size') or 
                        features.get('landArea') or features.get('sizeInSquareMetres'))
            
            # Search apollo_state for missing data
            if not beds or not baths or not prop_type or not land_size:
                for key, value in apollo_state.items():
                    if isinstance(value, dict):
                        if not beds and ('beds' in value or 'bedrooms' in value):
                            beds = value.get('beds') or value.get('bedrooms')
                        if not baths and ('baths' in value or 'bathrooms' in value):
                            baths = value.get('baths') or value.get('bathrooms')
                        if not parking and ('parking' in value or 'parkingSpaces' in value):
                            parking = value.get('parking') or value.get('parkingSpaces')
                        if not land_size and ('landSize' in value or 'landArea' in value):
                            land_size = value.get('landSize') or value.get('landArea')
                        if not prop_type and ('propertyType' in value or 'type' in value):
                            if value.get('__typename') in ['Property', 'Address']:
                                prop_type = value.get('propertyType') or value.get('type')
            
            # Rental estimates
            weekly_rent = valuation.get('rentPerWeek') or valuation.get('weeklyRent')
            rent_yield = valuation.get('rentYield') or valuation.get('yield')
            
            if not weekly_rent or not rent_yield:
                for key, value in apollo_state.items():
                    if isinstance(value, dict):
                        if value.get('__typename') == 'RentalEstimate':
                            if not weekly_rent:
                                weekly_rent = value.get('price') or value.get('weeklyRent') or value.get('rentPerWeek')
                            if not rent_yield:
                                rent_yield = value.get('yield') or value.get('rentYield')
            
            property_data = {
                'url': url,
                'address': address,
                'scraped_at': datetime.now().isoformat(),
                'features': {
                    'bedrooms': beds,
                    'bathrooms': baths,
                    'car_spaces': parking,
                    'land_size': land_size,
                    'property_type': prop_type
                },
                'valuation': {
                    'low': valuation.get('lowerPrice'),
                    'mid': valuation.get('midPrice'),
                    'high': valuation.get('upperPrice'),
                    'accuracy': valuation.get('priceConfidence'),
                    'date': valuation.get('date')
                },
                'rental_estimate': {
                    'weekly_rent': weekly_rent,
                    'yield': rent_yield
                }
            }
            
            # Extract timeline
            timeline_raw = property_obj.get('timeline', [])
            property_data['property_timeline'] = []
            
            if timeline_raw:
                for event in timeline_raw:
                    clean_event = self.transform_timeline_event(event)
                    property_data['property_timeline'].append(clean_event)
                print(f"  ✓ Extracted {len(property_data['property_timeline'])} timeline events")
            
            # Extract images
            property_data['images'] = []
            media_key = 'media({"categories":["IMAGE"]})'
            images = property_obj.get(media_key, [])
            
            for idx, img in enumerate(images):
                img_url = img.get('url({"fitIn":true,"imageFormat":"WEBP","resolution":{"height":3240,"width":5760}})')
                if not img_url:
                    img_url = img.get('url')
                
                if img_url:
                    property_data['images'].append({
                        'url': img_url,
                        'index': idx,
                        'date': img.get('date')
                    })
            
            # HTML FALLBACK for rental data
            if not weekly_rent or not rent_yield:
                try:
                    rental_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Rental estimate')]")
                    if rental_elements:
                        parent = rental_elements[0].find_element(By.XPATH, "./ancestor::*[3]")
                        rent_text = parent.text
                        
                        rent_match = re.search(r'\$[\d,]+', rent_text)
                        if rent_match and not weekly_rent:
                            weekly_rent = int(rent_match.group(0).replace('$', '').replace(',', ''))
                            property_data['rental_estimate']['weekly_rent'] = weekly_rent
                        
                        yield_match = re.search(r'([\d.]+)%', rent_text)
                        if yield_match and not rent_yield:
                            rent_yield = float(yield_match.group(1))
                            property_data['rental_estimate']['yield'] = rent_yield
                        
                        print(f"  ✓ Extracted rental from HTML: ${weekly_rent}/week, {rent_yield}%")
                except:
                    pass
            
            timeline_count = len(property_data.get('property_timeline', []))
            print(f"  ✓ Data: {beds}bed {baths}bath, {len(property_data.get('images', []))} images, {timeline_count} timeline events")
            
            # Check for empty timeline and retry if needed
            if timeline_count == 0 and retry_count < max_retries:
                print(f"  ⚠ Empty timeline - retrying after delay...")
                delay = 30 * (retry_count + 1)
                time.sleep(delay)
                return self.extract_property_data(url, address, retry_count + 1, max_retries)
            
            if timeline_count == 0:
                print(f"  ⚠ Warning: Timeline empty after {max_retries} retries")
            
            return property_data
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            
            if retry_count < max_retries:
                delay = 30 * (retry_count + 1)
                print(f"  ⚠ Retrying after {delay}s delay...")
                time.sleep(delay)
                return self.extract_property_data(url, address, retry_count + 1, max_retries)
            
            return None
    
    def save_to_mongodb(self, collection_name: str, mongo_id, property_data: Dict) -> bool:
        """Save scraped property data directly to MongoDB document"""
        try:
            collection = self.db[collection_name]
            
            # Update the existing document with scraped data
            result = collection.update_one(
                {'_id': mongo_id},
                {
                    '$set': {
                        'scraped_data': property_data,
                        'scraped_at': datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"  ✓ Saved to MongoDB: Gold_Coast.{collection_name}")
                return True
            else:
                print(f"  ⚠ MongoDB update failed")
                return False
            
        except Exception as e:
            print(f"  ✗ MongoDB save error: {e}")
            return False
    
    def run(self):
        """Main worker execution"""
        print(f"\n{'='*70}")
        print(f"MULTI-SUBURB WORKER {self.worker_id} STARTING")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # Get my addresses
        addresses = self.get_my_addresses()
        
        if not addresses:
            print("No unscraped addresses to process")
            return
        
        # Print initial summary
        print(f"\n{'='*70}")
        print(f"PROCESSING PLAN")
        print(f"{'='*70}")
        print(f"Worker ID:           {self.worker_id}")
        print(f"Total workers:       {self.total_workers}")
        print(f"My addresses:        {len(addresses):,}")
        print(f"Target suburbs:      {len(self.TARGET_SUBURBS)}")
        print(f"Expected rate:       ~120 addresses/hour")
        print(f"Estimated duration:  {len(addresses) / 120:.1f} hours")
        print(f"Started at:          {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # Setup driver
        print(f"Initializing Chrome driver...")
        self.setup_driver()
        
        # Process addresses
        successful = 0
        failed = 0
        suburb_stats = {}
        
        try:
            for i, addr_info in enumerate(addresses, 1):
                suburb = addr_info['suburb']
                if suburb not in suburb_stats:
                    suburb_stats[suburb] = {'successful': 0, 'failed': 0}
                
                print(f"\n[{i}/{len(addresses)}] [{suburb}] {addr_info['address']}")
                
                # Build URL
                url = self.build_domain_url(addr_info['address'])
                
                # Scrape
                property_data = self.extract_property_data(url, addr_info['address'])
                
                if property_data:
                    # Add metadata
                    property_data.update({
                        'address_pid': addr_info['address_pid'],
                        'suburb': addr_info['suburb'],
                        'worker_id': self.worker_id
                    })
                    
                    # Save to MongoDB
                    if self.save_to_mongodb(addr_info['collection'], addr_info['mongo_id'], property_data):
                        successful += 1
                        suburb_stats[suburb]['successful'] += 1
                    else:
                        failed += 1
                        suburb_stats[suburb]['failed'] += 1
                else:
                    failed += 1
                    suburb_stats[suburb]['failed'] += 1
                
                # Rate limiting (3 seconds between requests)
                time.sleep(3)
                
                # Progress update every 10 addresses
                if i % 10 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 3600
                    rate = i / elapsed if elapsed > 0 else 0
                    remaining = (len(addresses) - i) / rate if rate > 0 else 0
                    percentage = (i / len(addresses) * 100)
                    
                    print(f"\n{'─'*60}")
                    print(f"  📊 PROGRESS UPDATE - Worker {self.worker_id}")
                    print(f"{'─'*60}")
                    print(f"  Processed:       {i:,} / {len(addresses):,} addresses ({percentage:.1f}%)")
                    print(f"  Successful:      {successful:,} ({successful/i*100:.1f}%)")
                    print(f"  Failed:          {failed:,} ({failed/i*100:.1f}%)")
                    print(f"  Elapsed time:    {elapsed:.2f} hours")
                    print(f"  Current rate:    {rate:.1f} addresses/hour")
                    print(f"  Est. remaining:  {remaining:.1f} hours")
                    print(f"  Est. completion: {(datetime.now() + timedelta(hours=remaining)).strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"{'─'*60}\n")
        
        finally:
            if self.driver:
                self.driver.quit()
                print("\n✓ Chrome driver closed")
            
            self.mongo_client.close()
            print("✓ MongoDB connection closed")
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"MULTI-SUBURB WORKER {self.worker_id} COMPLETE")
        print(f"{'='*70}")
        print(f"Total addresses: {len(addresses):,}")
        print(f"Successful:      {successful:,} ({successful/len(addresses)*100:.1f}% if len(addresses) > 0 else 0)")
        print(f"Failed:          {failed:,} ({failed/len(addresses)*100:.1f}% if len(addresses) > 0 else 0)")
        print(f"Duration:        {duration}")
        if duration.total_seconds() > 0:
            print(f"Rate:            {len(addresses) / (duration.total_seconds() / 3600):.1f} addresses/hour")
        
        print(f"\nPer-suburb statistics:")
        for suburb in sorted(suburb_stats.keys()):
            stats = suburb_stats[suburb]
            total = stats['successful'] + stats['failed']
            print(f"  {suburb:30s}: {stats['successful']:4d} success, {stats['failed']:4d} failed ({total:4d} total)")
        
        print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        scraper = MultiSuburbScraperMongoDB()
        scraper.run()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
