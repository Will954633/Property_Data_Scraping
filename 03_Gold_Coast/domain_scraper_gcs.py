#!/usr/bin/env python3
"""
Domain Property Scraper - Google Cloud Storage Version
Scrapes properties from Domain.com.au and saves JSON files to GCS
"""

import json
import os
import time
import sys
import re
from datetime import datetime
from typing import Dict, Optional, List, Any
from pymongo import MongoClient
from google.cloud import storage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests


class DomainScraperGCS:
    """Domain scraper that saves to Google Cloud Storage"""
    
    @staticmethod
    def transform_timeline_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw timeline event to clean, readable format
        
        Args:
            event: Raw timeline event dict from Apollo state
            
        Returns:
            Cleaned and formatted event dict
        """
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
        self.total_workers = int(os.getenv('TOTAL_WORKERS', 200))
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.gcs_bucket = os.getenv('GCS_BUCKET')
        
        # Validate configuration
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable required")
        if not self.gcs_bucket:
            raise ValueError("GCS_BUCKET environment variable required")
        
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
        
        # Initialize GCS client
        print(f"Connecting to Google Cloud Storage...")
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.gcs_bucket)
        
        # Test GCS connection
        try:
            self.bucket.exists()
            print(f"✓ GCS bucket connected")
        except Exception as e:
            raise Exception(f"GCS connection failed: {e}")
        
        # Selenium driver
        self.driver = None
        
        print(f"\nWorker {self.worker_id}/{self.total_workers} initialized")
        print(f"MongoDB: {self.mongodb_uri.split('@')[1] if '@' in self.mongodb_uri else 'localhost'}")
        print(f"GCS Bucket: gs://{self.gcs_bucket}")
    
    def setup_driver(self):
        """Setup Chrome WebDriver for GCP environment or local"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Detect ChromeDriver location (Linux vs macOS)
        import platform
        import shutil
        
        chromedriver_path = None
        if platform.system() == 'Darwin':  # macOS
            # Try common macOS locations
            possible_paths = [
                '/opt/homebrew/bin/chromedriver',  # ARM Mac (M1/M2)
                '/usr/local/bin/chromedriver',      # Intel Mac
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    break
            
            # If not found in common locations, try to find in PATH
            if not chromedriver_path:
                chromedriver_path = shutil.which('chromedriver')
        else:  # Linux (GCP)
            chromedriver_path = '/usr/bin/chromedriver'
        
        if chromedriver_path:
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            # Let selenium auto-detect
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.implicitly_wait(10)
        
        print("✓ Chrome driver initialized")
    
    def build_address_from_components(self, doc: Dict) -> Optional[str]:
        """
        Build address string from MongoDB document components
        
        Examples:
        - House: "414 MARINE PARADE, BIGGERA WATERS QLD 4216"
        - Unit: "U 12/414 MARINE PARADE, BIGGERA WATERS QLD 4216"
        - Villa: "V 5/123 MAIN STREET, SURFERS PARADISE QLD 4217"
        """
        parts = []
        
        # Unit/Villa prefix (e.g., "U 12/", "V 5/")
        if doc.get('UNIT_TYPE') and doc.get('UNIT_NUMBER'):
            unit_type = str(doc['UNIT_TYPE']).upper()
            unit_num = str(doc['UNIT_NUMBER'])
            parts.append(f"{unit_type} {unit_num}/")
        
        # Street number (e.g., "414")
        if doc.get('STREET_NO_1'):
            parts.append(str(doc['STREET_NO_1']))
        
        # Street name and type (e.g., "MARINE PARADE")
        if doc.get('STREET_NAME'):
            street_part = str(doc['STREET_NAME'])
            if doc.get('STREET_TYPE'):
                street_part += f" {doc['STREET_TYPE']}"
            parts.append(street_part)
        
        # Locality, state, and postcode (e.g., "BIGGERA WATERS QLD 4216")
        if doc.get('LOCALITY'):
            locality = str(doc['LOCALITY'])
            locality_part = f"{locality} QLD"
            
            # Add postcode if available
            if doc.get('POSTCODE'):
                locality_part += f" {doc['POSTCODE']}"
            
            parts.append(locality_part)
        
        if not parts:
            return None
        
        # Join parts with appropriate spacing
        address = ' '.join(parts)
        
        # Clean up spacing around "/"
        address = re.sub(r'\s*/\s*', '/', address)
        address = re.sub(r'/\s+', '/', address)
        
        return address
    
    def get_my_addresses(self) -> List[Dict]:
        """Get addresses assigned to this worker"""
        print(f"\nRetrieving addresses from MongoDB...")
        
        # Get all collections (suburbs)
        collections = self.db.list_collection_names()
        print(f"Found {len(collections)} suburb collections")
        
        addresses = []
        for collection_name in collections:
            collection = self.db[collection_name]
            docs = list(collection.find({}, {
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
                # Build address from components
                address = self.build_address_from_components(doc)
                
                if address:  # Only add if we could build a valid address
                    addresses.append({
                        'address_pid': doc.get('ADDRESS_PID'),
                        'address': address,
                        'suburb': doc.get('LOCALITY'),
                        'doc_id': str(doc.get('_id')),
                        'collection': collection_name
                    })
        
        # Sort to ensure consistent ordering across workers
        addresses.sort(key=lambda x: (x.get('address_pid') or 0))
        
        # Calculate this worker's slice
        total = len(addresses)
        per_worker = total // self.total_workers
        start_idx = self.worker_id * per_worker
        
        # Last worker gets any remainder
        if self.worker_id == self.total_workers - 1:
            end_idx = total
        else:
            end_idx = start_idx + per_worker
        
        my_addresses = addresses[start_idx:end_idx]
        
        print(f"Total addresses: {total:,}")
        print(f"My slice: {start_idx:,} to {end_idx:,} ({len(my_addresses):,} addresses)")
        
        return my_addresses
    
    def build_domain_url(self, address: str) -> str:
        """
        Build Domain property profile URL from address
        
        Domain URL format: https://www.domain.com.au/property-profile/{slug}
        
        Rules for units - Domain.com.au does NOT include the unit type prefix:
        - "U 12/414 MARINE PARADE BIGGERA WATERS QLD 4216"
          → "12-414-marine-parade-biggera-waters-qld-4216" (NO "u-" prefix)
        
        Rules for houses:
        - "414 MARINE PARADE BIGGERA WATERS QLD 4216"
          → "414-marine-parade-biggera-waters-qld-4216"
        
        Steps:
        1. Remove unit type prefix (U, V, etc.) if present
        2. Convert to lowercase
        3. Replace spaces, commas, slashes with hyphens
        4. Remove special characters (keep only alphanumeric and hyphens)
        5. Remove multiple consecutive hyphens
        6. Trim leading/trailing hyphens
        """
        # Remove unit type prefix (e.g., "U ", "V ", etc.) at the start
        # Pattern: Single letter followed by space at start
        url_slug = re.sub(r'^[A-Z]\s+', '', address.upper())
        
        # Convert to lowercase
        url_slug = url_slug.lower().strip()
        
        # Replace separators (spaces, commas, slashes) with hyphens
        url_slug = re.sub(r'[,\s/]+', '-', url_slug)
        
        # Remove special characters (keep only alphanumeric and hyphens)
        url_slug = re.sub(r'[^a-z0-9\-]', '', url_slug)
        
        # Remove multiple consecutive hyphens
        url_slug = re.sub(r'-+', '-', url_slug)
        
        # Remove leading/trailing hyphens
        url_slug = url_slug.strip('-')
        
        return f"https://www.domain.com.au/property-profile/{url_slug}"
    
    def extract_property_data(self, url: str, address: str, retry_count: int = 0, max_retries: int = 2) -> Optional[Dict]:
        """
        Extract property data from Domain.com.au with improved data extraction
        
        Args:
            url: Property URL to scrape
            address: Property address
            retry_count: Current retry attempt (internal use)
            max_retries: Maximum number of retries for empty timelines
            
        Returns:
            Property data dict or None if extraction fails
        """
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
            
            # Extract data - search more thoroughly through Apollo state
            features = property_obj.get('features', {})
            valuation = property_obj.get('valuation', {})
            
            # Try to find bedrooms/bathrooms/parking in multiple places
            beds = features.get('beds') or features.get('bedrooms')
            baths = features.get('baths') or features.get('bathrooms')
            parking = features.get('parking') or features.get('parkingSpaces') or features.get('carSpaces')
            
            #  Extract property type - check multiple locations
            prop_type = (features.get('propertyType') or features.get('type') or 
                        property_obj.get('propertyType') or property_obj.get('type'))
            
            # Extract land size - check multiple field names
            land_size = (features.get('landSize') or features.get('land_size') or 
                        features.get('landArea') or features.get('sizeInSquareMetres'))
            
            # If still null, search entire apollo_state for these values
            if not beds or not baths or not prop_type or not land_size:
                for key, value in apollo_state.items():
                    if isinstance(value, dict):
                        if not beds and 'beds' in value:
                            beds = value.get('beds')
                        if not beds and 'bedrooms' in value:
                            beds = value.get('bedrooms')
                        if not baths and 'baths' in value:
                            baths = value.get('baths')
                        if not baths and 'bathrooms' in value:
                            baths = value.get('bathrooms')
                        if not parking and 'parking' in value:
                            parking = value.get('parking')
                        if not parking and 'parkingSpaces' in value:
                            parking = value.get('parkingSpaces')
                        if not land_size and ('landSize' in value or 'landArea' in value):
                            land_size = value.get('landSize') or value.get('landArea')
                        if not prop_type and ('propertyType' in value or 'type' in value):
                            if value.get('__typename') in ['Property', 'Address']:
                                prop_type = value.get('propertyType') or value.get('type')
            
            # Extract rental estimates - check multiple locations in valuation and apollo state
            weekly_rent = valuation.get('rentPerWeek') or valuation.get('weeklyRent')
            rent_yield = valuation.get('rentYield') or valuation.get('yield')
            
            # Search for rental estimate objects in Apollo state
            if not weekly_rent or not rent_yield:
                for key, value in apollo_state.items():
                    if isinstance(value, dict):
                        # Check for RentalEstimate objects
                        if value.get('__typename') == 'RentalEstimate':
                            if not weekly_rent:
                                weekly_rent = value.get('price') or value.get('weeklyRent') or value.get('rentPerWeek')
                            if not rent_yield:
                                rent_yield = value.get('yield') or value.get('rentYield')
                        # Check valuation-like objects
                        elif 'rent' in key.lower() or 'rental' in key.lower():
                            if not weekly_rent and ('price' in value or 'weeklyRent' in value):
                                weekly_rent = value.get('price') or value.get('weeklyRent')
                            if not rent_yield and 'yield' in value:
                                rent_yield = value.get('yield')
            
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
            
            # Extract property timeline - use the 'timeline' field from Apollo state
            # This is the proper, reliable way to get complete property history
            timeline_raw = property_obj.get('timeline', [])
            property_data['property_timeline'] = []
            
            if timeline_raw:
                # Transform each event to clean format
                for event in timeline_raw:
                    clean_event = self.transform_timeline_event(event)
                    property_data['property_timeline'].append(clean_event)
                
                print(f"  ✓ Extracted {len(property_data['property_timeline'])} timeline events from Apollo state")
            
            # Extract images
            property_data['images'] = []
            media_key = 'media({"categories":["IMAGE"]})'
            images = property_obj.get(media_key, [])
            
            for idx, img in enumerate(images[:20]):
                img_url = img.get('url({"fitIn":true,"imageFormat":"WEBP","resolution":{"height":3240,"width":5760}})')
                if not img_url:
                    img_url = img.get('url')
                
                if img_url:
                    property_data['images'].append({
                        'url': img_url,
                        'index': idx,
                        'date': img.get('date')
                    })
            
            # HTML FALLBACK: If rental data still missing, scrape from HTML
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
                except Exception as e:
                    pass  # HTML fallback failed, keep nulls
            
            timeline_count = len(property_data.get('property_timeline', []))
            print(f"  ✓ Extracted: {features.get('beds')}bed {features.get('baths')}bath, {len(property_data.get('images', []))} images, {timeline_count} timeline events")
            
            # Check for empty timeline and retry if needed
            if timeline_count == 0 and retry_count < max_retries:
                print(f"  ⚠ Empty timeline detected - retrying after delay...")
                # Exponential backoff: 30s, 60s, 90s
                delay = 30 * (retry_count + 1)
                time.sleep(delay)
                print(f"  Retrying after {delay}s delay...")
                return self.extract_property_data(url, address, retry_count + 1, max_retries)
            
            # Log empty timeline after all retries exhausted
            if timeline_count == 0:
                print(f"  ⚠ Warning: Timeline empty after {max_retries} retries - may be rate limited by Domain")
            
            return property_data
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            
            # Retry on error if we haven't exceeded max retries
            if retry_count < max_retries:
                delay = 30 * (retry_count + 1)
                print(f"  ⚠ Retrying after {delay}s delay due to error...")
                time.sleep(delay)
                return self.extract_property_data(url, address, retry_count + 1, max_retries)
            
            return None
    
    def save_to_gcs(self, address_pid: str, suburb: str, property_data: Dict) -> bool:
        """Save property data to Google Cloud Storage as JSON"""
        try:
            # Sanitize suburb name for path
            suburb_clean = re.sub(r'[^\w]', '_', suburb).lower()
            
            # Create file path: scraped_data/worker_XXX/suburb/address_pid.json
            blob_name = f"scraped_data/worker_{self.worker_id:03d}/{suburb_clean}/{address_pid}.json"
            blob = self.bucket.blob(blob_name)
            
            # Upload JSON
            blob.upload_from_string(
                json.dumps(property_data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            
            print(f"  ✓ Saved to: gs://{self.gcs_bucket}/{blob_name}")
            return True
            
        except Exception as e:
            print(f"  ✗ GCS save error: {e}")
            return False
    
    def run(self):
        """Main worker execution"""
        print(f"\n{'='*70}")
        print(f"WORKER {self.worker_id} STARTING")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # Get my addresses
        addresses = self.get_my_addresses()
        
        if not addresses:
            print("No addresses to process")
            return
        
        # Setup driver
        print(f"\nInitializing Chrome driver...")
        self.setup_driver()
        
        # Process addresses
        successful = 0
        failed = 0
        
        try:
            for i, addr_info in enumerate(addresses, 1):
                print(f"\n[{i}/{len(addresses)}] {addr_info['address']}")
                
                # Build URL
                url = self.build_domain_url(addr_info['address'])
                
                # Scrape
                property_data = self.extract_property_data(url, addr_info['address'])
                
                if property_data:
                    # Add metadata
                    property_data.update({
                        'address_pid': addr_info['address_pid'],
                        'suburb': addr_info['suburb'],
                        'collection': addr_info['collection'],
                        'doc_id': addr_info['doc_id'],
                        'worker_id': self.worker_id
                    })
                    
                    # Save to GCS
                    if self.save_to_gcs(str(addr_info['address_pid']), addr_info['suburb'], property_data):
                        successful += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                
                # Rate limiting (3 seconds between requests)
                time.sleep(3)
                
                # Progress update every 10 addresses
                if i % 10 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 3600
                    rate = i / elapsed if elapsed > 0 else 0
                    remaining = (len(addresses) - i) / rate if rate > 0 else 0
                    print(f"\n  Progress: {i}/{len(addresses)} ({i/len(addresses)*100:.1f}%)")
                    print(f"  Success: {successful} | Failed: {failed}")
                    print(f"  Rate: {rate:.1f} addr/hr | Est. remaining: {remaining:.1f} hrs")
        
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
        print(f"WORKER {self.worker_id} COMPLETE")
        print(f"{'='*70}")
        print(f"Total addresses: {len(addresses):,}")
        print(f"Successful:      {successful:,} ({successful/len(addresses)*100:.1f}%)")
        print(f"Failed:          {failed:,} ({failed/len(addresses)*100:.1f}%)")
        print(f"Duration:        {duration}")
        print(f"Rate:            {len(addresses) / (duration.total_seconds() / 3600):.1f} addresses/hour")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        scraper = DomainScraperGCS()
        scraper.run()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
