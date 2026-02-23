#!/usr/bin/env python3
"""
Domain Property Scraper - GCS JSON Version (No MongoDB Required)
Reads address list from GCS JSON, scrapes properties, saves results to GCS
"""

import json
import os
import time
import sys
import re
from datetime import datetime
from typing import Dict, Optional, List, Any
from google.cloud import storage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class DomainScraperGCSJSON:
    """Domain scraper that reads addresses from GCS JSON (no MongoDB)"""
    
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
        self.total_workers = int(os.getenv('TOTAL_WORKERS', 150))
        self.gcs_bucket = os.getenv('GCS_BUCKET')
        self.addresses_file = os.getenv('ADDRESSES_FILE', 'all_gold_coast_addresses.json')
        
        # Validate configuration
        if not self.gcs_bucket:
            raise ValueError("GCS_BUCKET environment variable required")
        
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
        print(f"GCS Bucket: gs://{self.gcs_bucket}")
        print(f"Addresses file: {self.addresses_file}")
    
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
    
    def load_addresses_from_gcs(self) -> List[str]:
        """Load address URLs from GCS JSON file"""
        print(f"\nLoading addresses from gs://{self.gcs_bucket}/{self.addresses_file}...")
        
        try:
            blob = self.bucket.blob(self.addresses_file)
            addresses_json = blob.download_as_text()
            urls = json.loads(addresses_json)
            
            if not isinstance(urls, list):
                raise ValueError("Addresses file must contain a JSON array of URLs")
            
            print(f"✓ Loaded {len(urls):,} addresses from GCS")
            return urls
            
        except Exception as e:
            raise Exception(f"Failed to load addresses from GCS: {e}")
    
    def get_my_urls(self) -> List[str]:
        """Get URLs assigned to this worker"""
        # Load all URLs from GCS
        all_urls = self.load_addresses_from_gcs()
        
        # Calculate this worker's slice
        total = len(all_urls)
        per_worker = total // self.total_workers
        start_idx = self.worker_id * per_worker
        
        # Last worker gets any remainder
        if self.worker_id == self.total_workers - 1:
            end_idx = total
        else:
            end_idx = start_idx + per_worker
        
        my_urls = all_urls[start_idx:end_idx]
        
        print(f"Total addresses: {total:,}")
        print(f"My slice: {start_idx:,} to {end_idx:,} ({len(my_urls):,} addresses)")
        
        return my_urls
    
    def extract_address_from_url(self, url: str) -> str:
        """Extract human-readable address from Domain URL"""
        # Extract slug from URL
        match = re.search(r'/property-profile/(.+)', url)
        if not match:
            return url
        
        slug = match.group(1)
        
        # Convert slug back to address (approximate)
        address = slug.replace('-', ' ').upper()
        return address
    
    def extract_property_data(self, url: str, retry_count: int = 0, max_retries: int = 2) -> Optional[Dict]:
        """
        Extract property data from Domain.com.au with improved data extraction
        
        Args:
            url: Property URL to scrape
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
            
            # Extract address from property object
            address_obj = property_obj.get('address', {})
            if isinstance(address_obj, dict):
                address = address_obj.get('display')
            else:
                address = self.extract_address_from_url(url)
            
            # Extract data - search more thoroughly through Apollo state
            features = property_obj.get('features', {})
            valuation = property_obj.get('valuation', {})
            
            # Try to find bedrooms/bathrooms/parking in multiple places
            beds = features.get('beds') or features.get('bedrooms')
            baths = features.get('baths') or features.get('bathrooms')
            parking = features.get('parking') or features.get('parkingSpaces') or features.get('carSpaces')
            
            # Extract property type - check multiple locations
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
            
            # Extract rental estimates - check multiple locations
            weekly_rent = valuation.get('rentPerWeek') or valuation.get('weeklyRent')
            rent_yield = valuation.get('rentYield') or valuation.get('yield')
            
            # Search for rental estimate objects in Apollo state
            if not weekly_rent or not rent_yield:
                for key, value in apollo_state.items():
                    if isinstance(value, dict):
                        if value.get('__typename') == 'RentalEstimate':
                            if not weekly_rent:
                                weekly_rent = value.get('price') or value.get('weeklyRent') or value.get('rentPerWeek')
                            if not rent_yield:
                                rent_yield = value.get('yield') or value.get('rentYield')
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
            
            # Extract property timeline
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
                        
                        print(f"  ✓ Extracted rental from HTML")
                except Exception:
                    pass
            
            timeline_count = len(property_data.get('property_timeline', []))
            print(f"  ✓ Extracted: {beds}bed {baths}bath, {len(property_data.get('images', []))} images, {timeline_count} timeline events")
            
            # Check for empty timeline and retry if needed
            if timeline_count == 0 and retry_count < max_retries:
                print(f"  ⚠ Empty timeline - retrying after delay...")
                delay = 30 * (retry_count + 1)
                time.sleep(delay)
                return self.extract_property_data(url, retry_count + 1, max_retries)
            
            if timeline_count == 0:
                print(f"  ⚠ Timeline empty after {max_retries} retries")
            
            return property_data
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            
            if retry_count < max_retries:
                delay = 30 * (retry_count + 1)
                print(f"  ⚠ Retrying after {delay}s delay...")
                time.sleep(delay)
                return self.extract_property_data(url, retry_count + 1, max_retries)
            
            return None
    
    def save_to_gcs(self, url: str, property_data: Dict) -> bool:
        """Save property data to Google Cloud Storage as JSON"""
        try:
            # Extract property ID from URL for filename
            match = re.search(r'/property-profile/(.+)', url)
            if match:
                slug = match.group(1)
                # Use slug as filename (sanitize)
                filename = re.sub(r'[^\w\-]', '_', slug)[:200]  # Limit length
            else:
                # Fallback to hash
                import hashlib
                filename = hashlib.md5(url.encode()).hexdigest()
            
            # Create file path: scraped_data/worker_XXX/properties/filename.json
            blob_name = f"scraped_data/worker_{self.worker_id:03d}/properties/{filename}.json"
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
        
        # Get my URLs
        urls = self.get_my_urls()
        
        if not urls:
            print("No URLs to process")
            return
        
        # Setup driver
        print(f"\nInitializing Chrome driver...")
        self.setup_driver()
        
        # Process URLs
        successful = 0
        failed = 0
        
        try:
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] Processing URL")
                
                # Scrape
                property_data = self.extract_property_data(url)
                
                if property_data:
                    # Add metadata
                    property_data['worker_id'] = self.worker_id
                    
                    # Save to GCS
                    if self.save_to_gcs(url, property_data):
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
                    remaining = (len(urls) - i) / rate if rate > 0 else 0
                    print(f"\n  Progress: {i}/{len(urls)} ({i/len(urls)*100:.1f}%)")
                    print(f"  Success: {successful} | Failed: {failed}")
                    print(f"  Rate: {rate:.1f} addr/hr | Est. remaining: {remaining:.1f} hrs")
        
        finally:
            if self.driver:
                self.driver.quit()
                print("\n✓ Chrome driver closed")
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"WORKER {self.worker_id} COMPLETE")
        print(f"{'='*70}")
        print(f"Total URLs:      {len(urls):,}")
        print(f"Successful:      {successful:,} ({successful/len(urls)*100:.1f}%)")
        print(f"Failed:          {failed:,} ({failed/len(urls)*100:.1f}%)")
        print(f"Duration:        {duration}")
        print(f"Rate:            {len(urls) / (duration.total_seconds() / 3600):.1f} addresses/hour")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        scraper = DomainScraperGCSJSON()
        scraper.run()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
