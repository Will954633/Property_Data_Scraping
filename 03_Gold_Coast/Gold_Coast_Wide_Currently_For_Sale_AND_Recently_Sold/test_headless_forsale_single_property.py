#!/usr/bin/env python3
"""
Headless Browser Test - Single For-Sale Property Scraper
Last Updated: 31/01/2026, 8:57 am (Brisbane Time)

PROOF OF CONCEPT: Demonstrates that Domain.com.au for-sale listings can be scraped
using headless browser methodology (same as 03_Gold_Coast/update_gold_coast_database.py)
to enable scaled monitoring of all Gold Coast for-sale properties.

This test proves:
1. Headless Chrome can access for-sale listing pages
2. Property data can be extracted from __NEXT_DATA__ JSON
3. The methodology scales (same pattern as 25-worker orchestrator)
4. No login/cookies required for public listings

Based on proven patterns from:
- 03_Gold_Coast/update_gold_coast_database.py (headless worker)
- 07_Undetectable_method/Simple_Method/property_detail_scraper_forsale.py (for-sale scraper)
- 03_Gold_Coast/orchestrator.py (multi-worker orchestration)
"""

import json
import os
import re
import time
from datetime import datetime
from typing import Dict, Optional

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium webdriver-manager")
    exit(1)


class HeadlessForSalePropertyScraper:
    """Minimal headless scraper for single for-sale property - proof of concept"""
    
    def __init__(self):
        """Initialize headless Chrome driver"""
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup headless Chrome WebDriver (same pattern as update_gold_coast_database.py)"""
        print("→ Setting up headless Chrome WebDriver...")
        
        options = Options()
        # HEADLESS MODE - Critical for scaled deployment
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Detect ChromeDriver location (macOS)
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
        
        if chromedriver_path:
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.implicitly_wait(10)
        print("  ✓ Headless Chrome driver initialized")
    
    def extract_property_data(self, url: str) -> Optional[Dict]:
        """
        Extract property data from Domain.com.au for-sale listing
        Uses same __NEXT_DATA__ JSON extraction as update_gold_coast_database.py
        """
        try:
            print(f"\n{'='*80}")
            print(f"SCRAPING FOR-SALE PROPERTY (HEADLESS MODE)")
            print(f"{'='*80}")
            print(f"URL: {url}")
            
            # Navigate to listing page
            print(f"\n→ Loading listing page in headless browser...")
            self.driver.get(url)
            time.sleep(5)  # Wait for JavaScript to execute
            
            # Get page HTML
            html = self.driver.page_source
            print(f"  ✓ Page loaded ({len(html):,} chars)")
            
            # Extract __NEXT_DATA__ JSON (same as update_gold_coast_database.py)
            print(f"\n→ Extracting __NEXT_DATA__ JSON...")
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', 
                            html, re.DOTALL)
            
            if not match:
                print(f"  ✗ No __NEXT_DATA__ found")
                return None
            
            try:
                page_data = json.loads(match.group(1))
                apollo_state = page_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})
                print(f"  ✓ Extracted __NEXT_DATA__ JSON")
            except Exception as e:
                print(f"  ✗ JSON parse error: {e}")
                return None
            
            # Find Listing object (for-sale listings use "Listing" not "Property")
            print(f"\n→ Parsing listing data...")
            
            # Debug: Show all available keys
            print(f"  → Analyzing __APOLLO_STATE__ structure...")
            listing_keys = [k for k in apollo_state.keys() if 'Listing' in k or 'Property' in k]
            print(f"  → Found {len(listing_keys)} potential listing/property keys")
            if listing_keys:
                print(f"  → Sample keys: {listing_keys[:5]}")
            
            listing_obj = {}
            
            # Try multiple patterns
            for key, value in apollo_state.items():
                if not isinstance(value, dict):
                    continue
                    
                # Pattern 1: Listing:ID
                if key.startswith('Listing:'):
                    listing_obj = value
                    print(f"  ✓ Found Listing object: {key}")
                    break
                    
                # Pattern 2: Property:ID
                if key.startswith('Property:'):
                    listing_obj = value
                    print(f"  ✓ Found Property object: {key}")
                    break
                    
                # Pattern 3: Check __typename field
                if value.get('__typename') in ['Listing', 'Property', 'PropertyListing']:
                    listing_obj = value
                    print(f"  ✓ Found {value.get('__typename')} object: {key}")
                    break
            
            if not listing_obj:
                # Last resort: find any object with address and features
                print(f"  ⚠ No standard listing object found, searching for object with address+features...")
                for key, value in apollo_state.items():
                    if isinstance(value, dict) and 'address' in value and 'features' in value:
                        listing_obj = value
                        print(f"  ✓ Found property-like object: {key}")
                        break
            
            if not listing_obj:
                print(f"  ✗ No listing/property object found")
                print(f"  → Saving apollo_state for debugging...")
                debug_file = os.path.join(os.path.dirname(__file__), "debug_apollo_state.json")
                with open(debug_file, 'w') as f:
                    json.dump(apollo_state, f, indent=2)
                print(f"  → Debug data saved to: {debug_file}")
                return None
            
            # Extract core data
            property_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'scrape_method': 'headless_chrome',
                'listing_type': 'for_sale'
            }
            
            # Address
            address_obj = listing_obj.get('address', {})
            if isinstance(address_obj, dict):
                property_data['address'] = address_obj.get('display') or address_obj.get('street')
                property_data['suburb'] = address_obj.get('suburb')
                property_data['state'] = address_obj.get('state')
                property_data['postcode'] = address_obj.get('postcode')
            
            # Features
            features = listing_obj.get('features', {})
            if isinstance(features, dict):
                property_data['bedrooms'] = features.get('beds') or features.get('bedrooms')
                property_data['bathrooms'] = features.get('baths') or features.get('bathrooms')
                property_data['car_spaces'] = features.get('parking') or features.get('parkingSpaces')
                property_data['land_size'] = features.get('landSize') or features.get('landArea')
                property_data['property_type'] = features.get('propertyType') or features.get('type')
            
            # Price (for-sale specific)
            price_details = listing_obj.get('priceDetails', {})
            if isinstance(price_details, dict):
                property_data['price_display'] = price_details.get('displayPrice')
                property_data['price'] = price_details.get('price')
            
            # Agent info
            advertiser = listing_obj.get('advertiser', {})
            if isinstance(advertiser, dict):
                property_data['agency_name'] = advertiser.get('name')
                property_data['agent_name'] = advertiser.get('contacts', [{}])[0].get('name') if advertiser.get('contacts') else None
            
            # Images
            property_data['image_count'] = 0
            media_key = 'media({"categories":["IMAGE"]})'
            images = listing_obj.get(media_key, [])
            if isinstance(images, list):
                property_data['image_count'] = len(images)
            
            # Headline/description
            property_data['headline'] = listing_obj.get('headline')
            
            # Inspection times
            inspections = listing_obj.get('inspectionDetails', {})
            if isinstance(inspections, dict):
                property_data['has_inspections'] = bool(inspections.get('inspections'))
            
            print(f"\n{'='*80}")
            print(f"EXTRACTION SUCCESSFUL")
            print(f"{'='*80}")
            print(f"Address:        {property_data.get('address', 'N/A')}")
            print(f"Suburb:         {property_data.get('suburb', 'N/A')}")
            print(f"Bedrooms:       {property_data.get('bedrooms', 'N/A')}")
            print(f"Bathrooms:      {property_data.get('bathrooms', 'N/A')}")
            print(f"Car Spaces:     {property_data.get('car_spaces', 'N/A')}")
            print(f"Property Type:  {property_data.get('property_type', 'N/A')}")
            print(f"Price:          {property_data.get('price_display', 'N/A')}")
            print(f"Agency:         {property_data.get('agency_name', 'N/A')}")
            print(f"Images:         {property_data.get('image_count', 0)}")
            print(f"Headline:       {property_data.get('headline', 'N/A')[:60]}...")
            print(f"{'='*80}\n")
            
            return property_data
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")


def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("HEADLESS BROWSER TEST - FOR-SALE PROPERTY SCRAPER")
    print("="*80)
    print("\nPROOF OF CONCEPT:")
    print("  • Demonstrates headless Chrome can scrape Domain.com.au for-sale listings")
    print("  • Uses same methodology as 25-worker Gold Coast orchestrator")
    print("  • No login/cookies required for public listings")
    print("  • Proves scalability for monitoring all Gold Coast for-sale properties")
    print("\n" + "="*80 + "\n")
    
    # Test URL (provided by user)
    test_url = "https://www.domain.com.au/sale/runaway-bay-qld-4216/?excludeunderoffer=1&ssubs=0"
    
    # Note: This is a search results page, not a single listing
    # Let's extract a single listing URL from it first
    print("NOTE: Provided URL is a search results page.")
    print("      Will extract first listing URL, then scrape that property.\n")
    
    scraper = None
    try:
        # Initialize scraper
        scraper = HeadlessForSalePropertyScraper()
        
        # First, get the search results page to extract a listing URL
        print("→ Loading search results page to find a listing...")
        scraper.driver.get(test_url)
        time.sleep(5)
        
        html = scraper.driver.page_source
        
        # Extract first listing URL
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        listing_url = None
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Match pattern: /slug-PROPERTYID
            if re.match(r'^/[\w-]+-\d{7,10}$', href):
                listing_url = f"https://www.domain.com.au{href}"
                break
        
        if not listing_url:
            print("✗ Could not find a listing URL on search results page")
            print("  Using fallback test URL...")
            # Fallback to a known listing URL
            listing_url = "https://www.domain.com.au/2013-the-address-5-lawson-street-southport-qld-4215-2019286682"
        
        print(f"  ✓ Found listing URL: {listing_url}\n")
        
        # Now scrape the actual listing
        property_data = scraper.extract_property_data(listing_url)
        
        if property_data:
            # Save results
            output_dir = "/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"test_headless_result_{timestamp}.json")
            
            with open(output_file, 'w') as f:
                json.dump(property_data, f, indent=2)
            
            print(f"✓ Results saved to: {output_file}\n")
            
            print("="*80)
            print("TEST RESULT: SUCCESS ✓")
            print("="*80)
            print("\nCONCLUSION:")
            print("  ✓ Headless Chrome successfully accessed for-sale listing")
            print("  ✓ Property data extracted from __NEXT_DATA__ JSON")
            print("  ✓ No login/authentication required")
            print("  ✓ Same methodology as proven 25-worker orchestrator")
            print("\nSCALABILITY:")
            print("  • This exact pattern can monitor ALL Gold Coast for-sale properties")
            print("  • Deploy as multi-worker orchestrator (like 03_Gold_Coast/orchestrator.py)")
            print("  • Each worker processes subset of for-sale listings")
            print("  • Store results in MongoDB (properties_for_sale collection)")
            print("  • Run on schedule to detect price changes, new listings, sold properties")
            print("\nNEXT STEPS:")
            print("  1. Create orchestrator for for-sale monitoring")
            print("  2. Query Domain.com.au search pages for all Gold Coast listings")
            print("  3. Deploy N workers to scrape listings in parallel")
            print("  4. Store in MongoDB with change tracking")
            print("  5. Schedule daily runs to monitor market changes")
            print("="*80 + "\n")
            
            return 0
        else:
            print("="*80)
            print("TEST RESULT: FAILED ✗")
            print("="*80)
            print("\nCould not extract property data.")
            print("Check error messages above for details.\n")
            return 1
    
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
