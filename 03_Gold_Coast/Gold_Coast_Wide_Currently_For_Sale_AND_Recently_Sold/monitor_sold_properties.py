#!/usr/bin/env python3
"""
Sold Property Monitor - Headless Parallel Version with Optimized Driver Reuse
Last Updated: 12/02/2026, 9:13 AM (Wednesday) - Brisbane Time

CHROME WEBDRIVER FIX (12/02/2026):
- Fixed "session not created from disconnected" error
- Now uses system ChromeDriver instead of webdriver-manager
- Added --headless=new flag for better stability
- Added --remote-debugging-port=0 to prevent port conflicts

MONGODB RETRYABLE WRITES FIX (12/02/2026):
- Fixed "Retryable writes are not supported" error with Azure Cosmos DB
- Changed retryWrites=True to retryWrites=False in connection
- This is required for Azure Cosmos DB compatibility

Previous Update: 06/02/2026, 9:37 pm Friday (Brisbane Time) - Fixed --test flag bug

PRICE TRACKING FIX:
- Now preserves original listing price in 'listing_price' field
- Extracts sold price properly from HTML into 'sale_price' field
- Improved sold price extraction with multiple methods
- Keeps price history separate: listing_price vs sale_price

ADDRESS MATCHING FIX:
- Fixed collection name mismatch: now uses collection_name (lowercase with underscores)
  instead of suburb_name (with spaces and capitals) when accessing master database
- Master database collections use format: "mermaid_waters" not "Mermaid Waters"

PERFORMANCE FIX:
- Now creates ONE ChromeDriver per suburb process (not per property)
- Reuses the same driver for all properties in the suburb
- Eliminates 60+ second cleanup delays between properties
- Expected performance: ~10 properties per minute (vs ~1 property per minute before)

PURPOSE:
Monitors properties in Gold_Coast_Currently_For_Sale collections (52 suburbs) and detects
when they've been sold. Moves sold properties to Gold_Coast_Recently_Sold collection.

FEATURES:
- Headless Chrome operation
- Parallel processing (multiple suburbs + multiple properties)
- 5 detection methods for sold status
- Auction protection (prevents false positives)
- Extracts sold date and sale price
- Preserves all historical data
- MongoDB safe with connection pooling

USAGE:
python3 monitor_sold_properties.py --all --max-concurrent 3 --parallel-properties 2
python3 monitor_sold_properties.py --suburbs "Robina:4226" "Varsity Lakes:4227"
python3 monitor_sold_properties.py --test --max-concurrent 2
python3 monitor_sold_properties.py --report
"""

import time
import os
import json
import re
import argparse
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from multiprocessing import Process, Queue, Manager
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from pymongo import MongoClient, ASCENDING
from bs4 import BeautifulSoup


def normalize_address(address: str) -> str:
    """
    Normalize address for matching (handles case, commas, unit numbers)
    
    Examples:
        "27 South Bay Drive Varsity, Lakes, QLD 4227" 
        -> "27 SOUTH BAY DRIVE VARSITY LAKES QLD 4227"
        
        "1 2 Pappas Way, Carrara, QLD 4211"
        -> "1/2 PAPPAS WAY CARRARA QLD 4211"
    """
    if not address:
        return ""
    
    # Convert to uppercase
    normalized = address.upper()
    
    # Remove all commas
    normalized = normalized.replace(',', '')
    
    # Normalize unit numbers: "2 36 BONOGIN" -> "2/36 BONOGIN"
    unit_pattern = r'^(\d+)\s+(\d+)\s+'
    match = re.match(unit_pattern, normalized)
    if match:
        unit = match.group(1)
        street_num = match.group(2)
        rest = normalized[match.end():]
        normalized = f"{unit}/{street_num} {rest}"
    
    # Normalize multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    
    return normalized


try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium pymongo beautifulsoup4")
    exit(1)

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
DATABASE_NAME = 'Gold_Coast_Currently_For_Sale'
SOLD_DATABASE_NAME = 'Gold_Coast_Recently_Sold'  # Separate database for sold properties
MASTER_DATABASE_NAME = 'Gold_Coast'  # Master property database
PAGE_LOAD_WAIT = 5
BETWEEN_PROPERTY_DELAY = 2

# Global MongoDB client (one per process)
_mongo_client = None
_mongo_db = None
_sold_db = None
_sold_collection = None
_master_db = None


def get_mongodb_connection():
    """Get or create MongoDB connection (one per process)"""
    global _mongo_client, _mongo_db, _sold_db, _sold_collection, _master_db
    
    if _mongo_client is None:
        max_retries = 3
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                _mongo_client = MongoClient(
                    MONGODB_URI,
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=45000,
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    retryWrites=False,  # CRITICAL: Cosmos DB doesn't support retryable writes
                    retryReads=True
                )
                _mongo_db = _mongo_client[DATABASE_NAME]
                _sold_db = _mongo_client[SOLD_DATABASE_NAME]  # Separate database for sold properties
                _master_db = _mongo_client[MASTER_DATABASE_NAME]
                
                # Test connection
                _mongo_client.admin.command('ping')
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"MongoDB connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"MongoDB connection failed after {max_retries} attempts: {e}")
    
    return _mongo_client, _mongo_db, _sold_db, _master_db


class SoldPropertyMonitor:
    """Monitor for sold properties in a single suburb"""
    
    def __init__(self, suburb_name: str, postcode: str, progress_queue: Queue, parallel_properties: int = 1):
        """Initialize monitor"""
        self.suburb_name = suburb_name
        self.postcode = postcode
        self.collection_name = suburb_name.lower().replace(' ', '_')
        self.progress_queue = progress_queue
        self.parallel_properties = parallel_properties
        self.progress_lock = Lock()
        self.driver = None
        
        # Get shared MongoDB connection
        self.log(f"Connecting to MongoDB...")
        self.mongo_client, self.db, self.sold_db, self.master_db = get_mongodb_connection()
        self.collection = self.db[self.collection_name]
        # Sold collection uses same collection name as for-sale (suburb-specific)
        self.sold_collection = self.sold_db[self.collection_name]
        
        # Create indexes for sold collection (Cosmos DB safe)
        # NOTE: Cosmos DB doesn't allow unique indexes on collections with existing documents
        # So we create non-unique indexes instead
        try:
            self.sold_collection.create_index([("listing_url", ASCENDING)])
            self.sold_collection.create_index([("address", ASCENDING)])
            self.sold_collection.create_index([("sold_detection_date", ASCENDING)])
            self.sold_collection.create_index([("sold_date", ASCENDING)])
        except Exception as e:
            # Indexes may already exist, which is fine
            self.log(f"Note: Index creation skipped (may already exist): {e}")
        
        self.log(f"MongoDB connected - For-sale: {self.collection_name}")
        self.log(f"Sold database: {SOLD_DATABASE_NAME}.{self.collection_name}")
        
        # Setup shared WebDriver for all properties
        self.setup_driver()
    
    def setup_driver(self):
        """Setup headless Chrome WebDriver (ONE driver for all properties)"""
        self.log("Setting up headless Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-dev-tools')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--remote-debugging-port=0')  # Disable remote debugging
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Use system ChromeDriver (no webdriver-manager)
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.log("✓ Headless Chrome ready (system ChromeDriver)")
        except FileNotFoundError:
            # Fallback: try without explicit service path
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.log("✓ Headless Chrome ready (default ChromeDriver)")
            except Exception as e:
                raise Exception(f"Failed to create WebDriver: {e}")
        except Exception as e:
            raise Exception(f"Failed to create WebDriver: {e}")
    
    def close(self):
        """Close browser and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
                self.log("✓ Browser closed")
            except Exception as e:
                self.log(f"⚠ Error closing browser: {e}")
    
    def log(self, message: str):
        """Log message with suburb prefix"""
        print(f"[{self.suburb_name}] {message}")
    
    def update_progress(self, status: str, data: Dict = None):
        """Update progress in shared queue"""
        progress_data = {
            'suburb': self.suburb_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        self.progress_queue.put(progress_data)
    
    def check_if_sold(self, html: str, url: str = "") -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Check if property is sold using 5 detection methods
        Returns: (is_sold, sold_date_text, sale_price, detection_method)
        """
        if not html:
            return False, None, None, None
        
        soup = BeautifulSoup(html, 'html.parser')
        is_sold = False
        sold_date_text = None
        detection_method = None
        
        # Pre-check: Detect auction listings
        is_auction = self._is_auction_listing(soup, html)
        
        # METHOD 1: Primary - Check for sold tag
        sold_tag = soup.find('span', {'data-testid': 'listing-details__listing-tag'})
        if sold_tag and sold_tag.text:
            tag_text = sold_tag.text.strip()
            if 'Sold' in tag_text or 'SOLD' in tag_text:
                is_sold = True
                sold_date_text = tag_text
                detection_method = "listing_tag"
        
        # METHOD 2: Breadcrumb Navigation
        if not is_sold:
            breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], class_=re.compile(r'breadcrumb', re.IGNORECASE))
            for breadcrumb in breadcrumbs:
                breadcrumb_text = breadcrumb.get_text()
                if 'Sold in' in breadcrumb_text or 'sold' in breadcrumb_text.lower():
                    is_sold = True
                    detection_method = "breadcrumb_navigation"
                    break
            
            if not is_sold:
                sold_links = soup.find_all('a', href=re.compile(r'/sold/', re.IGNORECASE))
                if sold_links:
                    for link in sold_links:
                        parent_classes = ' '.join(link.parent.get('class', []))
                        if 'breadcrumb' in parent_classes.lower() or 'nav' in parent_classes.lower():
                            is_sold = True
                            detection_method = "breadcrumb_link"
                            break
        
        # METHOD 3: URL Pattern
        if not is_sold and url:
            if '/sold/' in url.lower():
                is_sold = True
                detection_method = "url_pattern"
        
        # METHOD 4: Meta Tags
        if not is_sold:
            og_type = soup.find('meta', property='og:type')
            if og_type and og_type.get('content'):
                og_type_value = og_type.get('content').lower()
                if 'sold' in og_type_value:
                    is_sold = True
                    detection_method = "meta_og_type"
        
        # Extract sale price using multiple methods
        sale_price = self._extract_sale_price(soup, html)
        
        # Auction protection
        if is_sold and is_auction:
            if detection_method not in ['listing_tag', 'url_pattern', 'breadcrumb_link']:
                is_sold = False
                detection_method = None
                sold_date_text = None
        
        return is_sold, sold_date_text, sale_price, detection_method
    
    def _is_auction_listing(self, soup: BeautifulSoup, html: str) -> bool:
        """Check if this is an auction listing"""
        auction_indicators = ['Auction', 'Going to auction', 'For auction', 'Auction date', 'Auction time']
        
        listing_type_elements = soup.find_all(['span', 'div', 'p'], 
                                              class_=re.compile(r'listing-type|sale-method|property-type', re.IGNORECASE))
        for elem in listing_type_elements:
            text = elem.get_text().strip()
            if any(indicator.lower() in text.lower() for indicator in auction_indicators):
                return True
        
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_text = meta_desc.get('content')
            if any(indicator.lower() in desc_text.lower() for indicator in auction_indicators):
                return True
        
        auction_elements = soup.find_all(class_=re.compile(r'auction', re.IGNORECASE))
        if auction_elements:
            return True
        
        title = soup.find('title')
        if title and 'auction' in title.get_text().lower():
            return True
        
        return False
    
    def _extract_sale_price(self, soup: BeautifulSoup, html: str) -> Optional[str]:
        """
        Extract sale price from sold property page using multiple methods
        Returns: sale_price string (e.g., "$1,700,000" or "SOLD - $1,700,000")
        """
        sale_price = None
        
        # METHOD 1: Look for "SOLD - $X,XXX,XXX" in summary title
        summary_title = soup.find('div', {'data-testid': 'listing-details__summary-title'})
        if summary_title:
            title_text = summary_title.get_text().strip()
            if 'SOLD' in title_text.upper() and '$' in title_text:
                # Extract just the price part
                price_match = re.search(r'\$[\d,]+', title_text)
                if price_match:
                    sale_price = price_match.group(0)
                    return sale_price
        
        # METHOD 2: Look for price in any element with "SOLD" text
        price_elements = soup.find_all(['div', 'span', 'p', 'h1', 'h2'], 
                                       class_=re.compile(r'price|Price|summary|title', re.IGNORECASE))
        for elem in price_elements:
            text = elem.get_text().strip()
            if 'SOLD' in text.upper() and '$' in text:
                # Extract price
                price_match = re.search(r'\$[\d,]+', text)
                if price_match:
                    sale_price = price_match.group(0)
                    return sale_price
        
        # METHOD 3: Check meta tags
        og_price = soup.find('meta', property='og:price:amount')
        if og_price and og_price.get('content'):
            sale_price = f"${og_price.get('content')}"
            return sale_price
        
        # METHOD 4: Look in page text for price patterns near "SOLD"
        if not sale_price:
            # Search for "SOLD" followed by price within 50 characters
            sold_pattern = r'SOLD[^$]{0,50}\$[\d,]+'
            match = re.search(sold_pattern, html, re.IGNORECASE)
            if match:
                price_match = re.search(r'\$[\d,]+', match.group(0))
                if price_match:
                    sale_price = price_match.group(0)
                    return sale_price
        
        return sale_price
    
    def parse_sold_date(self, sold_text: str) -> Optional[str]:
        """Parse sold date from text"""
        if not sold_text:
            return None
        
        date_patterns = [
            r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'
        ]
        
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        
        for pattern in date_patterns:
            match = re.search(pattern, sold_text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        day, month, year = match.groups()
                        if month in month_map:
                            month = month_map[month]
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except Exception:
                    pass
        
        return sold_text
    
    def update_master_property_record(self, property_doc: Dict) -> bool:
        """Update the master property record in Gold_Coast database with sold information"""
        try:
            address = property_doc.get('address')
            
            # Try to find the property in master database by address
            # The master database uses the collection_name (lowercase with underscores)
            master_collection = self.master_db[self.collection_name]
            
            # ROBUST ADDRESS MATCHING: Normalize addresses for comparison
            # This handles: case differences, commas ("Varsity, Lakes" vs "VARSITY LAKES"),
            # unit numbers ("2 36" vs "2/36"), and extra spaces
            normalized_search_addr = normalize_address(address)
            
            # Try to find matching property using normalized address comparison
            master_property = None
            for candidate in master_collection.find({}):
                candidate_addr = candidate.get('complete_address', '')
                if normalize_address(candidate_addr) == normalized_search_addr:
                    master_property = candidate
                    break
            
            if not master_property:
                self.log(f"⚠ No master record found for: {address}")
                return False
            
            # Create the sold transaction record
            sold_transaction = {
                'listing_date': property_doc.get('first_listed_date'),
                'listing_timestamp': property_doc.get('first_listed_timestamp'),
                'days_on_market': property_doc.get('days_on_domain'),
                'listing_price': property_doc.get('price'),
                'sold_date': property_doc.get('sold_date'),
                'sold_date_text': property_doc.get('sold_date_text'),
                'sale_price': property_doc.get('sale_price'),
                'sold_detection_date': property_doc.get('sold_detection_date'),
                'detection_method': property_doc.get('detection_method'),
                'listing_url': property_doc.get('listing_url'),
                'agent_name': property_doc.get('agent_name'),
                'agency': property_doc.get('agency'),
                'property_type': property_doc.get('property_type'),
                'bedrooms': property_doc.get('bedrooms'),
                'bathrooms': property_doc.get('bathrooms'),
                'car_spaces': property_doc.get('car_spaces'),
                'land_size': property_doc.get('land_size'),
                'description': property_doc.get('agents_description'),
                'images': property_doc.get('images', []),
                'floor_plans': property_doc.get('floor_plans', [])
            }
            
            # Update the master property record - append to sales_history array
            result = master_collection.update_one(
                {"_id": master_property["_id"]},
                {
                    "$push": {
                        "sales_history": sold_transaction
                    },
                    "$set": {
                        "last_sold_date": property_doc.get('sold_date'),
                        "last_sale_price": property_doc.get('sale_price'),
                        "last_updated": datetime.now()
                    }
                },
                upsert=False  # Don't create if doesn't exist
            )
            
            if result.matched_count > 0:
                self.log(f"✓ Updated master record for: {address}")
                return True
            else:
                self.log(f"⚠ No master record found for: {address}")
                return False
                
        except Exception as e:
            self.log(f"Error updating master record: {e}")
            return False
    
    def move_to_sold_collection(self, property_doc: Dict) -> bool:
        """Move property from suburb collection to sold collection AND update master database"""
        try:
            address = property_doc.get('address')
            listing_url = property_doc.get('listing_url')
            
            # Check if already in sold collection
            existing = self.sold_collection.find_one({"listing_url": listing_url})
            
            if existing:
                self.log(f"⚠ Already in sold collection: {address}")
                # Remove from for-sale collection
                self.collection.delete_one({"_id": property_doc["_id"]})
                return True
            
            # PRESERVE ORIGINAL LISTING PRICE
            # Store the original 'price' field as 'listing_price' before it gets overwritten
            original_price = property_doc.get('price')
            if original_price:
                property_doc['listing_price'] = original_price
            
            # Add migration metadata
            property_doc['moved_to_sold_date'] = datetime.now()
            property_doc['original_collection'] = self.collection_name
            property_doc['original_suburb'] = self.suburb_name
            
            # STEP 1: Insert into sold collection
            self.sold_collection.insert_one(property_doc)
            
            # STEP 2: Update master property record in Gold_Coast database
            self.update_master_property_record(property_doc)
            
            # STEP 3: Remove from for-sale collection
            self.collection.delete_one({"_id": property_doc["_id"]})
            
            self.log(f"✓ Moved to sold collection: {address}")
            return True
            
        except Exception as e:
            self.log(f"Error moving property: {e}")
            if "duplicate key error" in str(e):
                try:
                    self.collection.delete_one({"_id": property_doc["_id"]})
                    return True
                except Exception:
                    pass
            return False
    
    def monitor_property(self, property_doc: Dict) -> Optional[Dict]:
        """Monitor single property using shared WebDriver (NO driver creation/cleanup)"""
        try:
            # Get listing URL
            listing_url = property_doc.get('listing_url')
            if not listing_url:
                return None
            
            # Navigate to page using SHARED driver
            self.driver.get(listing_url)
            time.sleep(PAGE_LOAD_WAIT)
            
            # Get final URL (may be redirected)
            final_url = self.driver.current_url
            html = self.driver.page_source
            
            if not html or len(html) < 100:
                return None
            
            # Check if sold
            is_sold, sold_date_text, sale_price, detection_method = self.check_if_sold(html, final_url)
            
            if is_sold:
                # Parse sold date
                sold_date = self.parse_sold_date(sold_date_text) if sold_date_text else None
                
                # PRESERVE ORIGINAL LISTING PRICE
                original_listing_price = property_doc.get('price')
                
                # Add sold information
                property_doc['sold_status'] = 'sold'
                property_doc['sold_detection_date'] = datetime.now()
                property_doc['sold_date_text'] = sold_date_text
                property_doc['sold_date'] = sold_date
                property_doc['sale_price'] = sale_price  # Sold price goes here
                property_doc['listing_price'] = original_listing_price  # Original price preserved
                property_doc['detection_method'] = detection_method
                property_doc['url_redirected'] = (final_url != listing_url)
                property_doc['final_url'] = final_url
                
                return property_doc
            
            return None
            
        except Exception as e:
            return None
    
    def monitor_all_properties(self, property_docs: List[Dict]) -> Dict:
        """Monitor all properties in suburb"""
        self.log(f"Starting sold property monitoring ({len(property_docs)} properties)...")
        self.update_progress('monitoring_started', {'total_properties': len(property_docs)})
        
        sold_count = 0
        checked_count = 0
        failed_count = 0
        
        # NOTE: parallel_properties is now IGNORED - we use sequential with shared driver
        # This is much faster than creating/destroying drivers for each property
        for i, property_doc in enumerate(property_docs, 1):
            result = self.monitor_property(property_doc)
            
            if result:
                if self.move_to_sold_collection(result):
                    sold_count += 1
                else:
                    failed_count += 1
            
            checked_count = i
            
            if i % 5 == 0 or i == len(property_docs):
                self.update_progress('monitoring_progress', {
                    'checked': checked_count,
                    'total': len(property_docs),
                    'sold': sold_count,
                    'failed': failed_count
                })
            
            if i < len(property_docs):
                time.sleep(BETWEEN_PROPERTY_DELAY)
        
        self.log(f"Monitoring complete: {sold_count} sold, {checked_count} checked")
        self.update_progress('monitoring_complete', {
            'sold': sold_count,
            'checked': checked_count,
            'failed': failed_count
        })
        
        return {
            "sold": sold_count,
            "checked": checked_count,
            "failed": failed_count
        }
    
    def run(self, test_mode: bool = False):
        """Main execution"""
        try:
            self.log("Starting sold property monitoring...")
            
            # Get all properties from collection
            query = {}
            if test_mode:
                property_docs = list(self.collection.find(query).limit(10))
                self.log(f"TEST MODE: Monitoring first 10 properties")
            else:
                property_docs = list(self.collection.find(query))
            
            if not property_docs:
                self.log("No properties to monitor")
                self.update_progress('complete', {'sold': 0, 'checked': 0})
                self.close()  # Close driver even if no properties
                return
            
            # Monitor all properties
            result = self.monitor_all_properties(property_docs)
            
            # Final summary
            self.update_progress('complete', {
                'monitoring': result,
                'remaining_count': self.collection.count_documents({})
            })
            
            self.log("Complete!")
            
        except Exception as e:
            self.log(f"Fatal error: {e}")
            self.update_progress('error', {'error': str(e)})
        finally:
            # Always close the driver
            self.close()


def run_suburb_monitor(suburb_name: str, postcode: str, progress_queue: Queue, 
                       parallel_properties: int = 1, test_mode: bool = False):
    """Worker function to run monitor in separate process"""
    monitor = None
    try:
        monitor = SoldPropertyMonitor(suburb_name, postcode, progress_queue, parallel_properties)
        monitor.run(test_mode)
    except Exception as e:
        print(f"[{suburb_name}] Process error: {e}")
    finally:
        # Cleanup: close driver and MongoDB
        if monitor:
            monitor.close()
        global _mongo_client
        if _mongo_client:
            try:
                _mongo_client.close()
            except:
                pass


def monitor_progress(progress_queue: Queue, suburb_count: int, results_dict: dict):
    """Monitor progress from all suburb processes"""
    completed_suburbs = set()
    
    while len(completed_suburbs) < suburb_count:
        try:
            progress = progress_queue.get(timeout=1)
            suburb = progress['suburb']
            status = progress['status']
            data = progress.get('data', {})
            
            # Must replace the entire sub-dict (manager.dict() proxy doesn't track nested mutations)
            existing = dict(results_dict.get(suburb, {}))
            existing[status] = data
            results_dict[suburb] = existing

            if status == 'monitoring_progress':
                checked = data.get('checked', 0)
                total = data.get('total', 0)
                sold = data.get('sold', 0)
                print(f"[{suburb}] Progress: {checked}/{total} ({sold} sold)")
            elif status == 'complete':
                completed_suburbs.add(suburb)
                sold = data.get('monitoring', {}).get('sold', 0)
                print(f"[{suburb}] ✅ COMPLETE - {sold} properties sold")
            elif status == 'error':
                completed_suburbs.add(suburb)
                print(f"[{suburb}] ❌ ERROR: {data.get('error', 'Unknown')}")
                
        except:
            pass


def load_suburbs_from_json(filename='gold_coast_suburbs.json'):
    """Load suburbs from JSON file"""
    with open(filename, 'r') as f:
        data = json.load(f)
    return [(s['name'], s['postcode']) for s in data['suburbs']]


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Sold property monitor with parallel processing",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--test', action='store_true',
                       help='Test with first 10 properties per suburb')
    parser.add_argument('--all', action='store_true',
                       help='Process all 52 suburbs')
    parser.add_argument('--suburbs', nargs='+',
                       help='Specific suburbs (e.g., "Robina:4226" "Varsity Lakes:4227")')
    parser.add_argument('--max-concurrent', type=int, default=3,
                       help='Maximum concurrent suburbs (default: 3)')
    parser.add_argument('--parallel-properties', type=int, default=2,
                       help='Properties to monitor simultaneously per suburb (default: 2)')
    parser.add_argument('--report', action='store_true',
                       help='Generate sold properties report')
    
    args = parser.parse_args()
    
    if args.report:
        # Generate report
        client = MongoClient(MONGODB_URI)
        sold_db = client[SOLD_DATABASE_NAME]
        
        print("\n" + "=" * 80)
        print("SOLD PROPERTIES REPORT")
        print("=" * 80)
        
        # Get all collections (suburbs) in sold database
        collections = sold_db.list_collection_names()
        
        total_sold = 0
        detection_methods = {}
        suburb_counts = {}
        
        for coll_name in collections:
            coll = sold_db[coll_name]
            count = coll.count_documents({})
            if count > 0:
                suburb_counts[coll_name] = count
                total_sold += count
                
                # Count detection methods
                for prop in coll.find({}):
                    method = prop.get('detection_method', 'unknown')
                    detection_methods[method] = detection_methods.get(method, 0) + 1
        
        print(f"\nTotal Sold Properties: {total_sold}")
        print(f"Suburbs with sold properties: {len(suburb_counts)}\n")
        
        print("By Suburb:")
        for suburb, count in sorted(suburb_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {suburb}: {count}")
        
        print("\nDetection Methods:")
        for method, count in detection_methods.items():
            print(f"  {method}: {count}")
        
        print("\n" + "=" * 80 + "\n")
        client.close()
        return 0
    
    # Load suburbs
    if args.suburbs:
        suburbs = []
        for suburb_arg in args.suburbs:
            try:
                name, postcode = suburb_arg.split(':')
                suburbs.append((name, postcode))
            except:
                print(f"✗ Invalid suburb format: {suburb_arg}")
                return 1
    elif args.test:
        suburbs = load_suburbs_from_json()[:10]
        print(f"\n🧪 TEST MODE: Processing first {len(suburbs)} suburbs (10 properties each)")
    elif args.all:
        suburbs = load_suburbs_from_json()
    else:
        print("\nPlease specify --test, --all, --suburbs, or --report")
        parser.print_help()
        return 1
    
    print("\n" + "=" * 80)
    print("SOLD PROPERTY MONITOR (HEADLESS PARALLEL)")
    print("=" * 80)
    print(f"\nSuburbs to monitor: {len(suburbs)}")
    for name, postcode in suburbs:
        print(f"  - {name} ({postcode})")
    print(f"\nFor-Sale Database: {DATABASE_NAME}")
    print(f"Sold Database: {SOLD_DATABASE_NAME}")
    print(f"Structure: Each suburb has its own collection in both databases")
    print(f"Max Concurrent: {args.max_concurrent} suburbs")
    print(f"Parallel Properties: {args.parallel_properties} per suburb")
    if args.test:
        print(f"Mode: TEST (first 10 properties per suburb)")
    print("=" * 80 + "\n")
    
    # Create shared progress queue and results dict
    manager = Manager()
    progress_queue = manager.Queue()
    results_dict = manager.dict()
    
    # Start monitor processes
    processes = []
    active_processes = {}
    pending_suburbs = list(suburbs)
    
    # Start initial batch
    while len(active_processes) < args.max_concurrent and pending_suburbs:
        suburb_name, postcode = pending_suburbs.pop(0)
        p = Process(target=run_suburb_monitor, 
                   args=(suburb_name, postcode, progress_queue, args.parallel_properties, args.test))
        p.start()
        active_processes[suburb_name] = p
        print(f"[{suburb_name}] Process started (PID: {p.pid})")
        
        if pending_suburbs and len(active_processes) < args.max_concurrent:
            time.sleep(5)
    
    print("\n" + "=" * 80)
    print("MONITORING PROGRESS")
    print("=" * 80 + "\n")
    
    # Monitor progress and spawn new processes
    completed_suburbs = []
    while active_processes or pending_suburbs:
        # Check for completed processes
        for suburb_name, process in list(active_processes.items()):
            if not process.is_alive():
                completed_suburbs.append(suburb_name)
                del active_processes[suburb_name]
                
                # Spawn new suburb if available
                if pending_suburbs:
                    new_suburb_name, new_postcode = pending_suburbs.pop(0)
                    p = Process(target=run_suburb_monitor,
                               args=(new_suburb_name, new_postcode, progress_queue, 
                                    args.parallel_properties, args.test))
                    p.start()
                    active_processes[new_suburb_name] = p
                    print(f"[{new_suburb_name}] 🚀 SPAWNED (PID: {p.pid})")
        
        # Process progress updates
        try:
            while not progress_queue.empty():
                progress = progress_queue.get_nowait()
                suburb = progress['suburb']
                status = progress['status']
                data = progress.get('data', {})
                
                # Must replace the entire sub-dict (manager.dict() proxy doesn't track nested mutations)
                existing = dict(results_dict.get(suburb, {}))
                existing[status] = data
                results_dict[suburb] = existing

                if status == 'monitoring_progress':
                    checked = data.get('checked', 0)
                    total = data.get('total', 0)
                    sold = data.get('sold', 0)
                    if checked % 10 == 0 or checked == total:
                        print(f"[{suburb}] Progress: {checked}/{total} ({sold} sold)")
        except:
            pass
        
        time.sleep(5)

    # Drain any remaining queue messages before printing summary
    try:
        while not progress_queue.empty():
            progress = progress_queue.get_nowait()
            suburb = progress['suburb']
            status = progress['status']
            data = progress.get('data', {})
            existing = dict(results_dict.get(suburb, {}))
            existing[status] = data
            results_dict[suburb] = existing
    except:
        pass

    # Final Summary
    print("\n" + "=" * 80)
    print("SOLD PROPERTY MONITORING COMPLETE - FINAL SUMMARY")
    print("=" * 80 + "\n")
    
    total_sold = 0
    total_checked = 0
    
    for suburb_name, postcode in suburbs:
        print(f"📊 {suburb_name.upper()}")
        if suburb_name in results_dict:
            suburb_results = results_dict[suburb_name]
            
            if 'complete' in suburb_results:
                complete_data = suburb_results['complete']
                monitoring = complete_data.get('monitoring', {})
                
                sold = monitoring.get('sold', 0)
                checked = monitoring.get('checked', 0)
                remaining = complete_data.get('remaining_count', 0)
                
                print(f"  Checked:   {checked}")
                print(f"  Sold:      {sold}")
                print(f"  Remaining: {remaining}")
                
                total_sold += sold
                total_checked += checked
            elif 'error' in suburb_results:
                print(f"  ❌ Error: {suburb_results['error'].get('error', 'Unknown')}")
            else:
                print(f"  ⚠️ Incomplete")
        else:
            print(f"  ⚠️ No results")
        print()
    
    print("=" * 80)
    print(f"TOTAL: {total_sold} properties sold out of {total_checked} checked")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
