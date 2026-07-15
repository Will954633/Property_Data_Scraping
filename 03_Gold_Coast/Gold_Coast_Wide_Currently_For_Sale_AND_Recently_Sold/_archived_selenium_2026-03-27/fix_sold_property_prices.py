#!/usr/bin/env python3
"""
Fix Sold Property Prices - Retroactive Price Data Correction
Last Updated: 03/02/2026, 8:13 pm (Brisbane Time)

PURPOSE:
Fixes existing sold properties in Gold_Coast_Recently_Sold database that have incorrect price data:
1. Properties where 'price' field contains "SOLD - $X,XXX,XXX" instead of listing price
2. Properties where 'sale_price' is None but should contain the sold price
3. Re-scrapes the sold listing page to extract the correct sold price

WHAT IT DOES:
- Scans all sold properties in Gold_Coast_Recently_Sold database
- Identifies properties with missing or incorrect price data
- Re-visits the listing URL to extract the sold price
- Updates documents with:
  * listing_price: Original listing price (if available, otherwise "Unknown")
  * sale_price: Extracted sold price from the sold listing page
  * price_fix_date: Timestamp of when the fix was applied

USAGE:
python3 fix_sold_property_prices.py --all
python3 fix_sold_property_prices.py --suburbs "main_beach" "biggera_waters"
python3 fix_sold_property_prices.py --test  # Test mode: first 5 properties only
python3 fix_sold_property_prices.py --report  # Show what needs fixing
"""

import time
import re
import argparse
from datetime import datetime
from typing import Dict, Optional
from pymongo import MongoClient
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium webdriver-manager pymongo beautifulsoup4")
    exit(1)

# Configuration
MONGODB_URI = 'mongodb://127.0.0.1:27017/'
SOLD_DATABASE_NAME = 'Gold_Coast_Recently_Sold'
PAGE_LOAD_WAIT = 5
BETWEEN_PROPERTY_DELAY = 2


class SoldPriceFixer:
    """Fix sold property prices"""
    
    def __init__(self, collection_name: str):
        """Initialize fixer"""
        self.collection_name = collection_name
        self.driver = None
        
        # Connect to MongoDB
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[SOLD_DATABASE_NAME]
        self.collection = self.db[collection_name]
        
        print(f"[{collection_name}] Connected to MongoDB")
        
        # Setup WebDriver
        self.setup_driver()
    
    def setup_driver(self):
        """Setup headless Chrome WebDriver"""
        print(f"[{self.collection_name}] Setting up headless Chrome...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"[{self.collection_name}] ✓ Chrome ready")
        except Exception as e:
            raise Exception(f"Failed to create WebDriver: {e}")
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
                print(f"[{self.collection_name}] ✓ Browser closed")
            except Exception as e:
                print(f"[{self.collection_name}] ⚠ Error closing browser: {e}")
    
    def extract_sale_price(self, soup: BeautifulSoup, html: str) -> Optional[str]:
        """Extract sale price from sold property page"""
        sale_price = None
        
        # METHOD 1: Look for "SOLD - $X,XXX,XXX" in summary title
        summary_title = soup.find('div', {'data-testid': 'listing-details__summary-title'})
        if summary_title:
            title_text = summary_title.get_text().strip()
            if 'SOLD' in title_text.upper() and '$' in title_text:
                price_match = re.search(r'\$[\d,]+', title_text)
                if price_match:
                    return price_match.group(0)
        
        # METHOD 2: Look for price in any element with "SOLD" text
        price_elements = soup.find_all(['div', 'span', 'p', 'h1', 'h2'], 
                                       class_=re.compile(r'price|Price|summary|title', re.IGNORECASE))
        for elem in price_elements:
            text = elem.get_text().strip()
            if 'SOLD' in text.upper() and '$' in text:
                price_match = re.search(r'\$[\d,]+', text)
                if price_match:
                    return price_match.group(0)
        
        # METHOD 3: Check meta tags
        og_price = soup.find('meta', property='og:price:amount')
        if og_price and og_price.get('content'):
            return f"${og_price.get('content')}"
        
        # METHOD 4: Look in page text for price patterns near "SOLD"
        sold_pattern = r'SOLD[^$]{0,50}\$[\d,]+'
        match = re.search(sold_pattern, html, re.IGNORECASE)
        if match:
            price_match = re.search(r'\$[\d,]+', match.group(0))
            if price_match:
                return price_match.group(0)
        
        return sale_price
    
    def needs_fixing(self, doc: Dict) -> bool:
        """Check if document needs price fixing"""
        price = doc.get('price', '')
        sale_price = doc.get('sale_price')
        
        # Case 1: price field contains "SOLD - $X,XXX,XXX"
        if price and 'SOLD' in str(price).upper() and '$' in str(price):
            return True
        
        # Case 2: sale_price is None or empty
        if not sale_price:
            return True
        
        return False
    
    def fix_property(self, doc: Dict) -> bool:
        """Fix a single property's price data"""
        try:
            listing_url = doc.get('listing_url')
            if not listing_url:
                return False
            
            address = doc.get('address', 'Unknown')
            print(f"[{self.collection_name}] Fixing: {address}")
            
            # Navigate to page
            self.driver.get(listing_url)
            time.sleep(PAGE_LOAD_WAIT)
            
            html = self.driver.page_source
            if not html or len(html) < 100:
                print(f"[{self.collection_name}]   ⚠ Failed to load page")
                return False
            
            # Extract sold price
            soup = BeautifulSoup(html, 'html.parser')
            sale_price = self.extract_sale_price(soup, html)
            
            if not sale_price:
                print(f"[{self.collection_name}]   ⚠ Could not extract sale price")
                return False
            
            # Determine listing price
            current_price = doc.get('price', '')
            listing_price = doc.get('listing_price')
            
            # If listing_price doesn't exist, try to preserve original
            if not listing_price:
                # If current price field doesn't contain "SOLD", use it as listing price
                if current_price and 'SOLD' not in str(current_price).upper():
                    listing_price = current_price
                else:
                    # Extract from price field if it contains both
                    # e.g., "SOLD - $1,100,000" -> we can't recover original listing price
                    listing_price = "Unknown - Not preserved"
            
            # Update document
            update_result = self.collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "listing_price": listing_price,
                        "sale_price": sale_price,
                        "price_fix_date": datetime.now(),
                        "price_fix_applied": True
                    }
                }
            )
            
            if update_result.modified_count > 0:
                print(f"[{self.collection_name}]   ✓ Fixed: listing_price={listing_price}, sale_price={sale_price}")
                return True
            else:
                print(f"[{self.collection_name}]   ⚠ Update failed")
                return False
                
        except Exception as e:
            print(f"[{self.collection_name}]   ✗ Error: {e}")
            return False
    
    def run(self, test_mode: bool = False):
        """Main execution"""
        try:
            # Get all properties that need fixing
            all_docs = list(self.collection.find({}))
            docs_to_fix = [doc for doc in all_docs if self.needs_fixing(doc)]
            
            if test_mode:
                docs_to_fix = docs_to_fix[:5]
                print(f"[{self.collection_name}] TEST MODE: Fixing first 5 properties")
            
            print(f"[{self.collection_name}] Total properties: {len(all_docs)}")
            print(f"[{self.collection_name}] Need fixing: {len(docs_to_fix)}")
            
            if not docs_to_fix:
                print(f"[{self.collection_name}] No properties need fixing!")
                return
            
            # Fix each property
            fixed_count = 0
            failed_count = 0
            
            for i, doc in enumerate(docs_to_fix, 1):
                print(f"[{self.collection_name}] Progress: {i}/{len(docs_to_fix)}")
                
                if self.fix_property(doc):
                    fixed_count += 1
                else:
                    failed_count += 1
                
                if i < len(docs_to_fix):
                    time.sleep(BETWEEN_PROPERTY_DELAY)
            
            print(f"\n[{self.collection_name}] COMPLETE:")
            print(f"[{self.collection_name}]   Fixed: {fixed_count}")
            print(f"[{self.collection_name}]   Failed: {failed_count}")
            
        except Exception as e:
            print(f"[{self.collection_name}] Fatal error: {e}")
        finally:
            self.close()


def generate_report():
    """Generate report of properties that need fixing"""
    client = MongoClient(MONGODB_URI)
    db = client[SOLD_DATABASE_NAME]
    
    print("\n" + "=" * 80)
    print("SOLD PROPERTIES PRICE FIX REPORT")
    print("=" * 80 + "\n")
    
    collections = db.list_collection_names()
    
    total_properties = 0
    total_need_fixing = 0
    suburb_stats = {}
    
    for coll_name in collections:
        coll = db[coll_name]
        all_docs = list(coll.find({}))
        
        needs_fixing = 0
        for doc in all_docs:
            price = doc.get('price', '')
            sale_price = doc.get('sale_price')
            
            # Check if needs fixing
            if (price and 'SOLD' in str(price).upper() and '$' in str(price)) or not sale_price:
                needs_fixing += 1
        
        if len(all_docs) > 0:
            total_properties += len(all_docs)
            total_need_fixing += needs_fixing
            suburb_stats[coll_name] = {
                'total': len(all_docs),
                'needs_fixing': needs_fixing
            }
    
    print(f"Total Sold Properties: {total_properties}")
    print(f"Need Price Fixing: {total_need_fixing}")
    print(f"Percentage: {(total_need_fixing/total_properties*100):.1f}%\n")
    
    print("By Suburb:")
    for suburb, stats in sorted(suburb_stats.items(), key=lambda x: x[1]['needs_fixing'], reverse=True):
        if stats['needs_fixing'] > 0:
            print(f"  {suburb}: {stats['needs_fixing']}/{stats['total']} need fixing")
    
    print("\n" + "=" * 80 + "\n")
    client.close()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Fix sold property prices retroactively",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Fix all suburbs')
    parser.add_argument('--suburbs', nargs='+',
                       help='Specific suburbs (collection names, e.g., "main_beach" "biggera_waters")')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: first 5 properties only')
    parser.add_argument('--report', action='store_true',
                       help='Generate report of properties needing fixes')
    
    args = parser.parse_args()
    
    if args.report:
        generate_report()
        return 0
    
    # Get list of collections to fix
    if args.suburbs:
        collections = args.suburbs
    elif args.all:
        client = MongoClient(MONGODB_URI)
        db = client[SOLD_DATABASE_NAME]
        collections = db.list_collection_names()
        client.close()
    else:
        print("\nPlease specify --all, --suburbs, or --report")
        parser.print_help()
        return 1
    
    print("\n" + "=" * 80)
    print("SOLD PROPERTY PRICE FIXER")
    print("=" * 80)
    print(f"\nCollections to fix: {len(collections)}")
    for coll in collections:
        print(f"  - {coll}")
    if args.test:
        print(f"\nMode: TEST (first 5 properties per collection)")
    print("=" * 80 + "\n")
    
    # Fix each collection
    for coll_name in collections:
        fixer = SoldPriceFixer(coll_name)
        fixer.run(test_mode=args.test)
        print()
    
    print("=" * 80)
    print("ALL COLLECTIONS COMPLETE")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
