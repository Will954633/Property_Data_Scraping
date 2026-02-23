#!/usr/bin/env python3
"""
Gold Coast Database Updater
Last Updated: 30/01/2026, 7:35 pm (Brisbane Time)

Updates the Gold Coast database with fresh Domain.com.au data while preserving history.

UPDATE STRATEGY:
- REPLACES: property_timeline, images (always current)
- PRESERVES HISTORY: valuation_history, rental_estimate_history (append-only)
- Maintains all other fields unchanged

Run monthly or quarterly to keep data fresh while tracking valuation/rental trends.
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


class GoldCoastDatabaseUpdater:
    """Updates Gold Coast database with fresh Domain data while preserving history"""
    
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
        """Initialize updater with MongoDB connection and configuration"""
        # Configuration from environment
        self.worker_id = int(os.getenv('WORKER_ID', 0))
        self.total_workers = int(os.getenv('TOTAL_WORKERS', 1))
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
        self.update_threshold_days = int(os.getenv('UPDATE_THRESHOLD_DAYS', 15))
        
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
        
        # Get all suburb collections
        self.suburb_collections = [name for name in self.db.list_collection_names() 
                                   if name not in ['system.indexes']]
        
        print(f"✓ Found {len(self.suburb_collections)} suburb collections")
        
        # Selenium driver
        self.driver = None
        
        print(f"\nUpdater Worker {self.worker_id}/{self.total_workers} initialized")
        print(f"MongoDB: {self.mongodb_uri.split('@')[1] if '@' in self.mongodb_uri else 'localhost'}")
        print(f"Target: Update all properties with existing scraped_data")
    
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
            
            # Ensure features is a dict
            if not isinstance(features, dict):
                print(f"  ⚠ features is not a dict, it's a {type(features)}")
                features = {}
            
            valuation = property_obj.get('valuation', {})
            
            # Ensure valuation is a dict
            if not isinstance(valuation, dict):
                print(f"  ⚠ valuation is not a dict, it's a {type(valuation)}")
                valuation = {}
            
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
            
            # Ensure timeline_raw is a list
            if not isinstance(timeline_raw, list):
                timeline_raw = []
            
            if timeline_raw:
                for event in timeline_raw:
                    # Skip if event is not a dict
                    if not isinstance(event, dict):
                        continue
                    clean_event = self.transform_timeline_event(event)
                    property_data['property_timeline'].append(clean_event)
                print(f"  ✓ Extracted {len(property_data['property_timeline'])} timeline events")
            
            # Extract images
            property_data['images'] = []
            media_key = 'media({"categories":["IMAGE"]})'
            images = property_obj.get(media_key, [])
            
            # Ensure images is a list
            if not isinstance(images, list):
                images = []
            
            for idx, img in enumerate(images):
                # Skip if img is not a dict
                if not isinstance(img, dict):
                    continue
                    
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
            import traceback
            print(f"  ✗ Traceback:")
            traceback.print_exc()
            
            if retry_count < max_retries:
                delay = 30 * (retry_count + 1)
                print(f"  ⚠ Retrying after {delay}s delay...")
                time.sleep(delay)
                return self.extract_property_data(url, address, retry_count + 1, max_retries)
            
            return None
    
    def has_valuation_changed(self, old_val: Dict, new_val: Dict) -> bool:
        """Check if valuation has meaningfully changed"""
        if not old_val or not new_val:
            return True
        
        # Compare mid prices (main indicator)
        old_mid = old_val.get('mid')
        new_mid = new_val.get('mid')
        
        if old_mid != new_mid:
            return True
        
        # Also check low/high for completeness
        if old_val.get('low') != new_val.get('low'):
            return True
        if old_val.get('high') != new_val.get('high'):
            return True
        
        return False
    
    def has_rental_estimate_changed(self, old_rent: Dict, new_rent: Dict) -> bool:
        """Check if rental estimate has meaningfully changed"""
        if not old_rent or not new_rent:
            return True
        
        # Compare weekly rent and yield
        if old_rent.get('weekly_rent') != new_rent.get('weekly_rent'):
            return True
        if old_rent.get('yield') != new_rent.get('yield'):
            return True
        
        return False
    
    def append_to_valuation_history(self, existing_data: Dict, new_valuation: Dict) -> List[Dict]:
        """Append new valuation to history array"""
        # Get existing history or create new
        history = existing_data.get('scraped_data', {}).get('valuation_history', [])
        
        # Add current valuation to history with timestamp
        valuation_entry = {
            **new_valuation,
            'recorded_at': datetime.now().isoformat()
        }
        
        history.append(valuation_entry)
        return history
    
    def append_to_rental_history(self, existing_data: Dict, new_rental: Dict) -> List[Dict]:
        """Append new rental estimate to history array"""
        # Get existing history or create new
        history = existing_data.get('scraped_data', {}).get('rental_estimate_history', [])
        
        # Add current rental estimate to history with timestamp
        rental_entry = {
            **new_rental,
            'recorded_at': datetime.now().isoformat()
        }
        
        history.append(rental_entry)
        return history
    
    def get_all_scraped_addresses(self) -> List[Dict]:
        """Get all properties that need updating (>15 days old or never updated)"""
        print(f"\nRetrieving properties that need updating...")
        print(f"Update threshold: {self.update_threshold_days} days")
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=self.update_threshold_days)
        print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"(Properties updated before this date will be re-updated)\n")
        
        all_properties = []
        total_with_scraped = 0
        total_needing_update = 0
        
        # Collect properties from each suburb collection
        for suburb in self.suburb_collections:
            collection = self.db[suburb]
            
            # Find documents that:
            # 1. Have scraped_data AND
            # 2. Either have no updated_at OR updated_at is older than threshold
            query = {
                'scraped_data': {'$exists': True},
                '$or': [
                    {'updated_at': {'$exists': False}},  # Never updated
                    {'updated_at': {'$lt': cutoff_date}}  # Updated >15 days ago
                ]
            }
            
            docs = list(collection.find(query, {
                'scraped_data.address': 1,
                'scraped_data.valuation': 1,
                'scraped_data.rental_estimate': 1,
                'updated_at': 1,
                '_id': 1
            }))
            
            # Also count total with scraped_data for reporting
            total_scraped_in_suburb = collection.count_documents({'scraped_data': {'$exists': True}})
            total_with_scraped += total_scraped_in_suburb
            total_needing_update += len(docs)
            
            for doc in docs:
                scraped_data = doc.get('scraped_data', {})
                address = scraped_data.get('address')
                updated_at = doc.get('updated_at')
                
                # Calculate days since last update
                if updated_at:
                    days_old = (datetime.now() - updated_at).days
                else:
                    days_old = None  # Never updated
                
                if address:
                    all_properties.append({
                        'address': address,
                        'suburb': suburb,
                        'mongo_id': doc.get('_id'),
                        'collection': suburb,
                        'existing_valuation': scraped_data.get('valuation'),
                        'existing_rental': scraped_data.get('rental_estimate'),
                        'days_since_update': days_old,
                        'last_updated': updated_at
                    })
            
            print(f"  {suburb:30s}: {len(docs):6,d} need update / {total_scraped_in_suburb:6,d} total")
        
        # Sort by suburb then address for consistent ordering
        all_properties.sort(key=lambda x: (x['suburb'], x['address']))
        
        # Calculate this worker's slice
        total = len(all_properties)
        per_worker = total // self.total_workers
        start_idx = self.worker_id * per_worker
        
        # Last worker gets remainder
        if self.worker_id == self.total_workers - 1:
            end_idx = total
        else:
            end_idx = start_idx + per_worker
        
        my_properties = all_properties[start_idx:end_idx]
        
        print(f"\n{'='*70}")
        print(f"SELECTION SUMMARY")
        print(f"{'='*70}")
        print(f"Total properties with scraped_data: {total_with_scraped:,}")
        print(f"Properties needing update (>{self.update_threshold_days} days old): {total_needing_update:,}")
        print(f"Properties up-to-date (<{self.update_threshold_days} days old): {total_with_scraped - total_needing_update:,}")
        print(f"My worker slice: {start_idx:,} to {end_idx:,} ({len(my_properties):,} properties)")
        
        # Show suburb distribution for this worker
        suburb_counts = {}
        for prop in my_properties:
            suburb_counts[prop['suburb']] = suburb_counts.get(prop['suburb'], 0) + 1
        
        print(f"\nMy suburb distribution:")
        for suburb, count in sorted(suburb_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {suburb:30s}: {count:6,d} properties")
        
        return my_properties
    
    def update_property(self, prop_info: Dict, existing_doc: Dict) -> bool:
        """Update a single property with fresh data while preserving history"""
        try:
            # Build URL and scrape fresh data
            url = self.build_domain_url(prop_info['address'])
            fresh_data = self.extract_property_data(url, prop_info['address'])
            
            if not fresh_data:
                print(f"  ✗ Failed to scrape fresh data")
                return False
            
            # Get existing scraped_data
            existing_scraped = existing_doc.get('scraped_data', {})
            
            # Build update document
            update_doc = {
                **fresh_data,
                'address_pid': existing_scraped.get('address_pid'),
                'suburb': prop_info['suburb'],
                'worker_id': self.worker_id
            }
            
            # Check if valuation changed - if so, append to history
            if self.has_valuation_changed(prop_info['existing_valuation'], fresh_data['valuation']):
                update_doc['valuation_history'] = self.append_to_valuation_history(
                    existing_doc, fresh_data['valuation']
                )
                print(f"  📊 Valuation changed - added to history")
            else:
                # Preserve existing history
                update_doc['valuation_history'] = existing_scraped.get('valuation_history', [])
            
            # Check if rental estimate changed - if so, append to history
            if self.has_rental_estimate_changed(prop_info['existing_rental'], fresh_data['rental_estimate']):
                update_doc['rental_estimate_history'] = self.append_to_rental_history(
                    existing_doc, fresh_data['rental_estimate']
                )
                print(f"  📊 Rental estimate changed - added to history")
            else:
                # Preserve existing history
                update_doc['rental_estimate_history'] = existing_scraped.get('rental_estimate_history', [])
            
            # Update MongoDB
            collection = self.db[prop_info['collection']]
            result = collection.update_one(
                {'_id': prop_info['mongo_id']},
                {
                    '$set': {
                        'scraped_data': update_doc,
                        'updated_at': datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"  ✓ Updated in MongoDB: Gold_Coast.{prop_info['collection']}")
                return True
            else:
                print(f"  ⚠ MongoDB update returned 0 modified")
                return False
            
        except Exception as e:
            print(f"  ✗ Update error: {e}")
            return False
    
    def run(self):
        """Main updater execution"""
        print(f"\n{'='*70}")
        print(f"GOLD COAST DATABASE UPDATER - WORKER {self.worker_id} STARTING")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # Get properties to update
        properties = self.get_all_scraped_addresses()
        
        if not properties:
            print("No properties to update")
            return
        
        # Print initial summary
        print(f"\n{'='*70}")
        print(f"UPDATE PLAN")
        print(f"{'='*70}")
        print(f"Worker ID:           {self.worker_id}")
        print(f"Total workers:       {self.total_workers}")
        print(f"My properties:       {len(properties):,}")
        print(f"Target suburbs:      {len(self.suburb_collections)}")
        print(f"Expected rate:       ~120 properties/hour")
        print(f"Estimated duration:  {len(properties) / 120:.1f} hours")
        print(f"Started at:          {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # Setup driver
        print(f"Initializing Chrome driver...")
        self.setup_driver()
        
        # Process properties
        successful = 0
        failed = 0
        valuation_changes = 0
        rental_changes = 0
        suburb_stats = {}
        
        try:
            for i, prop_info in enumerate(properties, 1):
                suburb = prop_info['suburb']
                if suburb not in suburb_stats:
                    suburb_stats[suburb] = {'successful': 0, 'failed': 0}
                
                print(f"\n[{i}/{len(properties)}] [{suburb}] {prop_info['address']}")
                
                # Get existing document
                collection = self.db[prop_info['collection']]
                existing_doc = collection.find_one({'_id': prop_info['mongo_id']})
                
                if not existing_doc:
                    print(f"  ✗ Document not found in database")
                    failed += 1
                    suburb_stats[suburb]['failed'] += 1
                    continue
                
                # Update property
                if self.update_property(prop_info, existing_doc):
                    successful += 1
                    suburb_stats[suburb]['successful'] += 1
                else:
                    failed += 1
                    suburb_stats[suburb]['failed'] += 1
                
                # Rate limiting (3 seconds between requests)
                time.sleep(3)
                
                # Progress update every 10 properties
                if i % 10 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 3600
                    rate = i / elapsed if elapsed > 0 else 0
                    remaining = (len(properties) - i) / rate if rate > 0 else 0
                    percentage = (i / len(properties) * 100)
                    
                    print(f"\n{'─'*60}")
                    print(f"  📊 PROGRESS UPDATE - Worker {self.worker_id}")
                    print(f"{'─'*60}")
                    print(f"  Processed:       {i:,} / {len(properties):,} properties ({percentage:.1f}%)")
                    print(f"  Successful:      {successful:,} ({successful/i*100:.1f}%)")
                    print(f"  Failed:          {failed:,} ({failed/i*100:.1f}%)")
                    print(f"  Elapsed time:    {elapsed:.2f} hours")
                    print(f"  Current rate:    {rate:.1f} properties/hour")
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
        print(f"UPDATER WORKER {self.worker_id} COMPLETE")
        print(f"{'='*70}")
        print(f"Total properties: {len(properties):,}")
        print(f"Successful:       {successful:,} ({successful/len(properties)*100:.1f}% if len(properties) > 0 else 0)")
        print(f"Failed:           {failed:,} ({failed/len(properties)*100:.1f}% if len(properties) > 0 else 0)")
        print(f"Duration:         {duration}")
        if duration.total_seconds() > 0:
            print(f"Rate:             {len(properties) / (duration.total_seconds() / 3600):.1f} properties/hour")
        
        print(f"\nPer-suburb statistics:")
        for suburb in sorted(suburb_stats.keys()):
            stats = suburb_stats[suburb]
            total = stats['successful'] + stats['failed']
            print(f"  {suburb:30s}: {stats['successful']:4d} success, {stats['failed']:4d} failed ({total:4d} total)")
        
        print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        updater = GoldCoastDatabaseUpdater()
        updater.run()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
