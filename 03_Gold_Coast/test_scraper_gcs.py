#!/usr/bin/env python3
"""
Test Domain Property Scraper for Google Cloud Storage
Scrapes 5 test addresses and saves to GCS
"""

import json
import os
import time
import sys
import re
from datetime import datetime
from typing import Dict, Optional, Any
from google.cloud import storage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class TestScraperGCS:
    """Test scraper for 5 addresses - saves to GCS"""
    
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
        self.gcs_bucket = os.getenv('GCS_BUCKET')
        
        if not self.gcs_bucket:
            raise ValueError("GCS_BUCKET environment variable required")
        
        # Initialize GCS client
        print(f"Connecting to Google Cloud Storage...")
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.gcs_bucket)
        
        # Test GCS connection
        try:
            if not self.bucket.exists():
                print(f"Creating bucket: {self.gcs_bucket}")
                self.bucket.create(location='us-central1')
            print(f"✓ GCS bucket connected: gs://{self.gcs_bucket}")
        except Exception as e:
            raise Exception(f"GCS connection failed: {e}")
        
        # Selenium driver
        self.driver = None
        
        print(f"Test scraper initialized")
    
    def setup_driver(self):
        """Setup Chrome WebDriver for GCP environment"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Use system chromium-driver
        service = Service('/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        
        print("✓ Chrome driver initialized")
    
    def load_test_addresses(self):
        """Load test addresses from JSON file"""
        with open('test_addresses_5.json', 'r') as f:
            addresses = json.load(f)
        print(f"Loaded {len(addresses)} test addresses")
        return addresses
    
    def build_domain_url(self, address: str) -> str:
        """Build Domain property profile URL from address"""
        # Remove unit type prefix (e.g., "U ", "V ") at start
        url_slug = re.sub(r'^[A-Z]\s+', '', address.upper())
        
        # Convert to lowercase
        url_slug = url_slug.lower().strip()
        
        # Replace separators with hyphens
        url_slug = re.sub(r'[,\s/]+', '-', url_slug)
        
        # Remove special characters
        url_slug = re.sub(r'[^a-z0-9\-]', '', url_slug)
        
        # Remove multiple consecutive hyphens
        url_slug = re.sub(r'-+', '-', url_slug)
        
        # Trim hyphens
        url_slug = url_slug.strip('-')
        
        return f"https://www.domain.com.au/property-profile/{url_slug}"
    
    def extract_property_data(self, url: str, address: str, retry_count: int = 0, max_retries: int = 2) -> Optional[Dict]:
        """
        Extract property data from Domain.com.au
        
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
                # Exponential backoff: 30s, 60s
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
        """Save property data to GCS"""
        try:
            suburb_clean = re.sub(r'[^\w]', '_', suburb).lower()
            blob_name = f"test_data/{suburb_clean}/{address_pid}.json"
            blob = self.bucket.blob(blob_name)
            
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
        """Main test execution"""
        print(f"\n{'='*70}")
        print(f"TEST SCRAPER STARTING - 5 ADDRESSES")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # Load test addresses
        addresses = self.load_test_addresses()
        
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
                        'doc_id': addr_info['doc_id']
                    })
                    
                    # Save to GCS
                    if self.save_to_gcs(str(addr_info['address_pid']), addr_info['suburb'], property_data):
                        successful += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                
                # Rate limiting
                time.sleep(3)
        
        finally:
            if self.driver:
                self.driver.quit()
                print("\n✓ Chrome driver closed")
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"TEST COMPLETE")
        print(f"{'='*70}")
        print(f"Total addresses: {len(addresses)}")
        print(f"Successful:      {successful} ({successful/len(addresses)*100:.1f}%)")
        print(f"Failed:          {failed} ({failed/len(addresses)*100:.1f}%)")
        print(f"Duration:        {duration}")
        print(f"{'='*70}\n")
        
        # List saved files
        print("Saved files in GCS:")
        blobs = list(self.bucket.list_blobs(prefix='test_data/'))
        for blob in blobs:
            print(f"  - gs://{self.gcs_bucket}/{blob.name}")


if __name__ == "__main__":
    try:
        scraper = TestScraperGCS()
        scraper.run()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
