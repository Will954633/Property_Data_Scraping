#!/usr/bin/env python3
"""
Test timeline extraction locally without GCS - save to local files
"""

import json
import os
import time
import re
from datetime import datetime
from typing import Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class TimelineTestLocal:
    """Local test for timeline extraction"""
    
    @staticmethod
    def transform_timeline_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw timeline event to clean, readable format
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
        self.driver = None
        self.output_dir = 'timeline_test_results'
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Timeline test initialized - output to {self.output_dir}/")
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        # Use webdriver-manager to auto-download compatible chromedriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        print("✓ Chrome driver initialized")
    
    def load_test_addresses(self):
        """Load test addresses"""
        with open('test_addresses_5.json', 'r') as f:
            addresses = json.load(f)
        print(f"Loaded {len(addresses)} test addresses")
        return addresses
    
    def build_domain_url(self, address: str) -> str:
        """Build Domain URL"""
        url_slug = re.sub(r'^[A-Z]\s+', '', address.upper())
        url_slug = url_slug.lower().strip()
        url_slug = re.sub(r'[,\s/]+', '-', url_slug)
        url_slug = re.sub(r'[^a-z0-9\-]', '', url_slug)
        url_slug = re.sub(r'-+', '-', url_slug)
        url_slug = url_slug.strip('-')
        return f"https://www.domain.com.au/property-profile/{url_slug}"
    
    def extract_property_data(self, url: str, address: str) -> Optional[Dict]:
        """Extract property data with timeline"""
        try:
            print(f"  Accessing: {url}")
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
            
            property_data = {
                'url': url,
                'address': address,
                'scraped_at': datetime.now().isoformat(),
            }
            
            # Extract property timeline - use the 'timeline' field from Apollo state
            timeline_raw = property_obj.get('timeline', [])
            property_data['property_timeline'] = []
            
            if timeline_raw:
                # Transform each event to clean format
                for event in timeline_raw:
                    clean_event = self.transform_timeline_event(event)
                    property_data['property_timeline'].append(clean_event)
                
                print(f"  ✓ Extracted {len(property_data['property_timeline'])} timeline events")
                
                # Print summary
                categories = {}
                for event in property_data['property_timeline']:
                    cat = event.get('category', 'Unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                
                print(f"     - Sales: {categories.get('Sale', 0)}")
                print(f"     - Rentals: {categories.get('Rental', 0)}")
            else:
                print(f"  ⚠ No timeline data found")
            
            return property_data
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_results(self, address_pid: str, property_data: Dict):
        """Save to local file"""
        filename = f"{self.output_dir}/{address_pid}_timeline.json"
        with open(filename, 'w') as f:
            json.dump(property_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Saved to: {filename}")
    
    def run(self):
        """Main test execution"""
        print(f"\n{'='*70}")
        print(f"TIMELINE EXTRACTION TEST - 5 PROPERTIES")
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
        total_timeline_events = 0
        
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
                    })
                    
                    # Save results
                    self.save_results(str(addr_info['address_pid']), property_data)
                    successful += 1
                    total_timeline_events += len(property_data.get('property_timeline', []))
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
        print(f"Total properties:      {len(addresses)}")
        print(f"Successful:            {successful} ({successful/len(addresses)*100:.1f}%)")
        print(f"Failed:                {failed}")
        print(f"Total timeline events: {total_timeline_events}")
        print(f"Avg events/property:   {total_timeline_events/successful if successful > 0 else 0:.1f}")
        print(f"Duration:              {duration}")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        tester = TimelineTestLocal()
        tester.run()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
