#!/usr/bin/env python3
"""
Sold Property Monitor - Selenium Version
Monitors properties in the properties_for_sale collection and detects when they've been sold.
Moves sold properties to the properties_sold collection with sold date and price information.

Last Updated: 27/01/2026, 10:25 AM (Monday) - Brisbane
- ADDED AUCTION DATA EXTRACTION: Now captures auction date, time, and venue information
- Stores auction details in database for properties going to auction
- Enables tracking of upcoming auctions and post-auction monitoring
- FIXED FALSE POSITIVE: Removed "SOLD BY" pattern detection that was incorrectly flagging auction properties
- Added auction exclusion logic to prevent misclassification
- "SOLD BY [AGENT]" indicates the selling agent for auctions, NOT that property is sold
- Enhanced detection now checks for auction indicators before marking as sold
- Previous updates:
  - UPGRADED TO SELENIUM: Replaced requests library with Selenium WebDriver
  - Avoids bot detection by using real browser instead of HTTP client
  - Renders JavaScript for fully loaded HTML content
  - Enhanced sold detection with multiple fallback methods
  - Added breadcrumb navigation detection for "/sold/" paths
  - Added URL redirect detection
  - Added comprehensive logging for detection methods
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import time
import re
import json
import argparse
from typing import Dict, Optional, Tuple
import logging

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
FOR_SALE_COLLECTION = "properties_for_sale"
SOLD_COLLECTION = "properties_sold"

# Selenium Configuration
PAGE_LOAD_WAIT = 5  # seconds to wait for page to load
BETWEEN_PROPERTY_DELAY = 2  # seconds between property checks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SoldPropertyMonitor:
    def __init__(self, mongodb_uri: str = MONGODB_URI, db_name: str = DATABASE_NAME, headless: bool = True):
        """Initialize MongoDB connection and Selenium WebDriver"""
        # MongoDB setup
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.for_sale_collection = self.db[FOR_SALE_COLLECTION]
        self.sold_collection = self.db[SOLD_COLLECTION]
        self.ensure_indexes()
        
        # Selenium setup
        self.driver = None
        self.headless = headless
        self.init_driver()
    
    def init_driver(self):
        """Initialize Selenium WebDriver with Chrome"""
        logger.info("→ Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Additional headers to avoid detection
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("  ✓ Chrome WebDriver ready")
        except Exception as e:
            logger.error(f"  ✗ Failed to create WebDriver: {e}")
            raise
    
    def ensure_indexes(self):
        """Create necessary indexes for both collections"""
        # For sale collection indexes
        self.for_sale_collection.create_index("address", unique=True)
        self.for_sale_collection.create_index("listing_url")
        
        # Sold collection indexes
        self.sold_collection.create_index("address", unique=True)
        self.sold_collection.create_index("listing_url")
        self.sold_collection.create_index("sold_detection_date")
        self.sold_collection.create_index("sold_date")
        
        logger.info("✓ MongoDB indexes ensured")
    
    def fetch_listing_html(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch HTML content from a listing URL using Selenium
        Returns: (html_content, final_url)
        The final_url may differ from the original if there was a redirect
        """
        try:
            logger.debug(f"  → Loading page: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(PAGE_LOAD_WAIT)
            
            # Get final URL (may be different if redirected)
            final_url = self.driver.current_url
            
            if final_url != url:
                logger.debug(f"  → URL redirected: {url} -> {final_url}")
            
            # Verify page loaded successfully
            if not final_url or 'domain.com.au' not in final_url:
                logger.error(f"  ✗ Page load failed for {url}")
                return None, None
            
            # Extract fully rendered HTML
            html = self.driver.page_source
            
            if not html or len(html) < 100:
                logger.error(f"  ✗ HTML too small or empty for {url}")
                return None, None
            
            logger.debug(f"  ✓ Extracted HTML ({len(html):,} chars)")
            
            return html, final_url
            
        except Exception as e:
            logger.error(f"  ✗ Error fetching {url}: {e}")
            return None, None
    
    def check_if_sold(self, html: str, url: str = "") -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Check if property is sold by parsing HTML using multiple detection methods
        Returns: (is_sold, sold_date_text, sale_price, detection_method)
        
        Detection methods (in order of priority):
        1. Primary: listing-details__listing-tag with "Sold" text
        2. Breadcrumb: Navigation breadcrumb containing "/sold/" or "Sold in"
        3. URL Pattern: URL contains "/sold/"
        4. Meta Tags: og:type or other meta tags indicating sold status
        
        IMPORTANT: Checks for auction indicators to prevent false positives
        """
        if not html:
            return False, None, None, None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        is_sold = False
        sold_date_text = None
        detection_method = None
        
        # ========================================================================
        # PRE-CHECK: Detect if this is an auction listing (to prevent false positives)
        # ========================================================================
        is_auction = self._is_auction_listing(soup, html)
        if is_auction:
            logger.debug("  ⚠ Auction listing detected - will require strong sold indicators")
        
        # ========================================================================
        # METHOD 1: Primary - Check for sold tag in listing details
        # ========================================================================
        sold_tag = soup.find('span', {'data-testid': 'listing-details__listing-tag'})
        
        if sold_tag and sold_tag.text:
            tag_text = sold_tag.text.strip()
            if 'Sold' in tag_text or 'SOLD' in tag_text:
                is_sold = True
                sold_date_text = tag_text
                detection_method = "listing_tag"
                logger.info(f"  ✓ Detection Method 1 (Listing Tag): {tag_text}")
        
        # ========================================================================
        # METHOD 2: Breadcrumb Navigation - Check for "Sold in" or "/sold/" paths
        # ========================================================================
        if not is_sold:
            # Look for breadcrumb navigation
            breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], class_=re.compile(r'breadcrumb', re.IGNORECASE))
            for breadcrumb in breadcrumbs:
                breadcrumb_text = breadcrumb.get_text()
                if 'Sold in' in breadcrumb_text or 'sold' in breadcrumb_text.lower():
                    is_sold = True
                    detection_method = "breadcrumb_navigation"
                    logger.info(f"  ✓ Detection Method 2 (Breadcrumb): Found 'Sold' in navigation")
                    logger.debug(f"    Breadcrumb text: {breadcrumb_text[:100]}")
                    break
            
            # Also check for links containing "/sold/"
            if not is_sold:
                sold_links = soup.find_all('a', href=re.compile(r'/sold/', re.IGNORECASE))
                if sold_links:
                    # Check if these are navigation breadcrumbs (not just random links)
                    for link in sold_links:
                        parent_classes = ' '.join(link.parent.get('class', []))
                        if 'breadcrumb' in parent_classes.lower() or 'nav' in parent_classes.lower():
                            is_sold = True
                            detection_method = "breadcrumb_link"
                            logger.info(f"  ✓ Detection Method 2b (Breadcrumb Link): Found '/sold/' in navigation link")
                            break
        
        # ========================================================================
        # METHOD 3: URL Pattern - Check if URL contains "/sold/"
        # ========================================================================
        if not is_sold and url:
            if '/sold/' in url.lower():
                is_sold = True
                detection_method = "url_pattern"
                logger.info(f"  ✓ Detection Method 4 (URL Pattern): URL contains '/sold/'")
        
        # ========================================================================
        # METHOD 4: Meta Tags - Check og:type or other indicators
        # ========================================================================
        if not is_sold:
            og_type = soup.find('meta', property='og:type')
            if og_type and og_type.get('content'):
                og_type_value = og_type.get('content').lower()
                if 'sold' in og_type_value:
                    is_sold = True
                    detection_method = "meta_og_type"
                    logger.info(f"  ✓ Detection Method 5 (Meta Tag): og:type contains 'sold'")
        
        # ========================================================================
        # Extract sale price from various possible locations
        # ========================================================================
        sale_price = None
        
        # Price Method 1: Check for "SOLD - $X,XXX,XXX" format in price display
        price_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'price|Price'))
        for elem in price_elements:
            text = elem.get_text().strip()
            if 'SOLD' in text.upper() and '$' in text:
                sale_price = text
                logger.debug(f"Found sale price in price element: {sale_price}")
                break
        
        # Price Method 2: Check meta tags
        if not sale_price:
            og_price = soup.find('meta', property='og:price:amount')
            if og_price and og_price.get('content'):
                sale_price = f"${og_price.get('content')}"
        
        # Price Method 3: Check title for "Sold" information
        if not sale_price:
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title = og_title.get('content')
                if 'Sold' in title or 'SOLD' in title:
                    # Try to extract price from title
                    price_match = re.search(r'\$[\d,]+', title)
                    if price_match:
                        sale_price = price_match.group()
        
        # Price Method 4: Look for price in description
        if not sale_price:
            description = soup.find('meta', {'name': 'description'})
            if description and description.get('content'):
                desc_text = description.get('content')
                if 'sold' in desc_text.lower():
                    price_match = re.search(r'SOLD.*?\$[\d,]+', desc_text, re.IGNORECASE)
                    if price_match:
                        sale_price = price_match.group()
        
        # ========================================================================
        # FINAL CHECK: If auction listing, require stronger evidence
        # ========================================================================
        if is_sold and is_auction:
            # For auction listings, only trust Method 1 (listing tag) or URL-based methods
            if detection_method not in ['listing_tag', 'url_pattern', 'breadcrumb_link']:
                logger.warning(f"  ⚠ Auction listing - ignoring weak sold indicator: {detection_method}")
                is_sold = False
                detection_method = None
                sold_date_text = None
        
        if not is_sold:
            logger.debug("  ✗ No sold indicators found")
        
        return is_sold, sold_date_text, sale_price, detection_method
    
    def _is_auction_listing(self, soup: BeautifulSoup, html: str) -> bool:
        """
        Check if this is an auction listing
        Returns True if auction indicators are found
        """
        # Check for "Auction" text in common locations
        auction_indicators = [
            'Auction',
            'Going to auction',
            'For auction',
            'Auction date',
            'Auction time',
        ]
        
        # Check listing type/method tags
        listing_type_elements = soup.find_all(['span', 'div', 'p'], 
                                              class_=re.compile(r'listing-type|sale-method|property-type', re.IGNORECASE))
        for elem in listing_type_elements:
            text = elem.get_text().strip()
            if any(indicator.lower() in text.lower() for indicator in auction_indicators):
                logger.debug(f"  → Auction indicator found in listing type: {text}")
                return True
        
        # Check meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_text = meta_desc.get('content')
            if any(indicator.lower() in desc_text.lower() for indicator in auction_indicators):
                logger.debug(f"  → Auction indicator found in meta description")
                return True
        
        # Check for auction-specific data attributes or classes
        auction_elements = soup.find_all(class_=re.compile(r'auction', re.IGNORECASE))
        if auction_elements:
            logger.debug(f"  → Found {len(auction_elements)} elements with 'auction' in class name")
            return True
        
        # Check page title
        title = soup.find('title')
        if title and 'auction' in title.get_text().lower():
            logger.debug(f"  → Auction indicator found in page title")
            return True
        
        return False
    
    def extract_auction_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract auction date, time, and location from HTML
        Returns dict with auction details or None if not an auction
        """
        auction_data = {
            'is_auction': False,
            'auction_date': None,
            'auction_time': None,
            'auction_day': None,
            'auction_venue': None,
            'auction_address': None,
        }
        
        # Check if this is an auction listing
        if not self._is_auction_listing(soup, str(soup)):
            return None
        
        auction_data['is_auction'] = True
        
        # Get all text content
        page_text = soup.get_text()
        
        # Extract date - Pattern: "Saturday, 31 Jan"
        date_patterns = [
            r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                if len(match.groups()) == 3:
                    day, date_num, month = match.groups()
                    auction_data['auction_day'] = day
                    auction_data['auction_date'] = f"{date_num} {month}"
                    logger.debug(f"  → Found auction date: {day}, {date_num} {month}")
                break
        
        # Extract time - Pattern: "10:00am"
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)',
            r'(\d{1,2})\s*(am|pm|AM|PM)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, page_text)
            if match:
                auction_data['auction_time'] = match.group(0)
                logger.debug(f"  → Found auction time: {match.group(0)}")
                break
        
        # Extract venue - Pattern: "In - [Venue Name] - [Address]"
        venue_patterns = [
            r'In\s*-\s*([^-\n]+?)\s*-\s*([^-\n]+?)(?=\s*(?:Saturday|Monday|Tuesday|Wednesday|Thursday|Friday|Sunday|\d|$))',
            r'At\s+([^\n]+)',
            r'Venue:\s*([^\n]+)',
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    venue = match.group(1).strip()
                    address = match.group(2).strip()
                    # Clean up the address (remove extra text)
                    address = re.split(r'(?:Saturday|Monday|Tuesday|Wednesday|Thursday|Friday|Sunday)', address)[0].strip()
                    auction_data['auction_venue'] = venue
                    auction_data['auction_address'] = address
                    logger.debug(f"  → Found venue: {venue}")
                    logger.debug(f"  → Found address: {address}")
                else:
                    auction_data['auction_venue'] = match.group(1).strip()
                    logger.debug(f"  → Found venue: {match.group(1).strip()}")
                break
        
        return auction_data
    
    def parse_sold_date(self, sold_text: str) -> Optional[str]:
        """
        Parse sold date from text like 'Sold by private treaty 25 Nov 2025'
        Returns date string in format YYYY-MM-DD or original text if parsing fails
        """
        if not sold_text:
            return None
        
        # Try to extract date pattern
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
                except Exception as e:
                    logger.warning(f"Error parsing date from {sold_text}: {e}")
        
        # Return original text if can't parse
        return sold_text
    
    def move_to_sold_collection(self, property_doc: Dict) -> bool:
        """Move property from for_sale to sold collection"""
        try:
            address = property_doc.get('address')
            
            # Check if property already exists in sold collection (by address)
            existing = self.sold_collection.find_one({"address": address})
            
            if existing:
                logger.info(f"⚠ Property already in sold collection (skipping): {address}")
                # Still remove from for_sale collection
                self.for_sale_collection.delete_one({"_id": property_doc["_id"]})
                logger.info(f"✓ Removed from for_sale collection: {address}")
                return True
            
            # Add sold collection metadata
            property_doc['moved_to_sold_date'] = datetime.now()
            property_doc['original_collection'] = FOR_SALE_COLLECTION
            
            # Insert into sold collection
            self.sold_collection.insert_one(property_doc)
            
            # Remove from for_sale collection
            self.for_sale_collection.delete_one({"_id": property_doc["_id"]})
            
            logger.info(f"✓ Moved property to sold collection: {property_doc.get('address')}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving property to sold collection: {e}")
            # Try to at least remove from for_sale if it's a duplicate
            if "duplicate key error" in str(e):
                try:
                    self.for_sale_collection.delete_one({"_id": property_doc["_id"]})
                    logger.info(f"✓ Removed duplicate from for_sale collection: {property_doc.get('address')}")
                    return True
                except Exception as e2:
                    logger.error(f"Failed to remove from for_sale: {e2}")
            return False
    
    def monitor_property(self, property_doc: Dict) -> bool:
        """
        Monitor a single property to check if it's sold
        Returns True if property was found to be sold and moved
        """
        address = property_doc.get('address', 'Unknown')
        
        # Try multiple locations for the listing URL
        listing_url = property_doc.get('listing_url')
        
        # Check nested locations if not found at top level
        if not listing_url:
            # Check enrichment_data.listing_url
            enrichment_data = property_doc.get('enrichment_data', {})
            listing_url = enrichment_data.get('listing_url')
        
        if not listing_url:
            # Check gold_coast_data.scraped_data.url
            gold_coast_data = property_doc.get('gold_coast_data', {})
            scraped_data = gold_coast_data.get('scraped_data', {})
            listing_url = scraped_data.get('url')
        
        if not listing_url:
            logger.warning(f"No listing_url for property: {address}")
            return False
        
        logger.info(f"Checking: {address}")
        logger.debug(f"URL: {listing_url}")
        
        # Fetch the listing page using Selenium
        html, final_url = self.fetch_listing_html(listing_url)
        if not html:
            return False
        
        # Check if URL was redirected to a sold listing
        url_redirected = final_url and final_url != listing_url
        if url_redirected:
            logger.debug(f"  URL redirected to: {final_url}")
        
        # Parse HTML for both sold and auction detection
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract auction data if this is an auction listing
        auction_data = self.extract_auction_data(soup)
        if auction_data:
            logger.info(f"📅 AUCTION PROPERTY DETECTED: {address}")
            if auction_data.get('auction_date') and auction_data.get('auction_time'):
                logger.info(f"  Auction: {auction_data['auction_day']}, {auction_data['auction_date']} at {auction_data['auction_time']}")
                if auction_data.get('auction_venue'):
                    logger.info(f"  Venue: {auction_data['auction_venue']}")
            
            # Store auction data in the property document
            property_doc['auction_data'] = auction_data
            property_doc['auction_data_updated'] = datetime.now()
            
            # Update the property in the for_sale collection with auction info
            try:
                self.for_sale_collection.update_one(
                    {"_id": property_doc["_id"]},
                    {"$set": {
                        "auction_data": auction_data,
                        "auction_data_updated": datetime.now()
                    }}
                )
                logger.debug(f"  ✓ Updated property with auction data")
            except Exception as e:
                logger.warning(f"  ⚠ Failed to update auction data: {e}")
        
        # Check if sold using multiple detection methods
        is_sold, sold_date_text, sale_price, detection_method = self.check_if_sold(html, final_url or listing_url)
        
        if is_sold:
            logger.info(f"🏠 SOLD PROPERTY DETECTED: {address}")
            logger.info(f"  Detection Method: {detection_method}")
            
            # Parse sold date
            sold_date = self.parse_sold_date(sold_date_text) if sold_date_text else None
            
            # Add sold information to document
            property_doc['sold_status'] = 'sold'
            property_doc['sold_detection_date'] = datetime.now()
            property_doc['sold_date_text'] = sold_date_text
            property_doc['sold_date'] = sold_date
            property_doc['sale_price'] = sale_price
            property_doc['detection_method'] = detection_method
            property_doc['url_redirected'] = url_redirected
            property_doc['final_url'] = final_url
            
            logger.info(f"  Sold Date: {sold_date or sold_date_text or 'Not available'}")
            logger.info(f"  Sale Price: {sale_price or 'Not disclosed'}")
            
            # Move to sold collection
            return self.move_to_sold_collection(property_doc)
        
        return False
    
    def monitor_all_properties(self, limit: Optional[int] = None, delay: float = BETWEEN_PROPERTY_DELAY):
        """
        Monitor all properties in the for_sale collection
        
        Args:
            limit: Maximum number of properties to check (None for all)
            delay: Delay in seconds between requests (default from config)
        """
        logger.info("="*80)
        logger.info("SOLD PROPERTY MONITORING (SELENIUM VERSION)")
        logger.info("="*80)
        
        # Get all properties from for_sale collection
        query = {}
        cursor = self.for_sale_collection.find(query)
        
        if limit:
            cursor = cursor.limit(limit)
        
        total_properties = self.for_sale_collection.count_documents(query)
        logger.info(f"Total properties to monitor: {total_properties if not limit else min(limit, total_properties)}")
        
        sold_count = 0
        checked_count = 0
        error_count = 0
        
        for property_doc in cursor:
            checked_count += 1
            
            try:
                if self.monitor_property(property_doc):
                    sold_count += 1
                
                # Delay between requests to be polite
                if checked_count < (limit or total_properties):
                    time.sleep(delay)
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing property: {e}")
                continue
        
        # Summary
        logger.info("="*80)
        logger.info("MONITORING SUMMARY")
        logger.info("="*80)
        logger.info(f"Properties checked: {checked_count}")
        logger.info(f"Properties sold: {sold_count}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Properties still for sale: {checked_count - sold_count}")
        
        # Collection stats
        for_sale_count = self.for_sale_collection.count_documents({})
        sold_collection_count = self.sold_collection.count_documents({})
        
        logger.info("")
        logger.info("DATABASE STATUS:")
        logger.info(f"  properties_for_sale: {for_sale_count}")
        logger.info(f"  properties_sold: {sold_collection_count}")
        logger.info("="*80)
    
    def get_sold_properties_report(self) -> Dict:
        """Generate a report of sold properties"""
        sold_properties = list(self.sold_collection.find({}))
        
        report = {
            'total_sold': len(sold_properties),
            'properties': []
        }
        
        for prop in sold_properties:
            report['properties'].append({
                'address': prop.get('address'),
                'listing_url': prop.get('listing_url'),
                'sold_date': prop.get('sold_date'),
                'sold_date_text': prop.get('sold_date_text'),
                'sale_price': prop.get('sale_price'),
                'sold_detection_date': prop.get('sold_detection_date').isoformat() if prop.get('sold_detection_date') else None,
                'original_price': prop.get('price'),
                'detection_method': prop.get('detection_method')
            })
        
        return report
    
    def close(self):
        """Close MongoDB connection and Selenium driver"""
        if self.driver:
            logger.info("→ Closing browser...")
            self.driver.quit()
            logger.info("  ✓ Browser closed")
        
        self.client.close()
        logger.info("  ✓ MongoDB connection closed")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Monitor for-sale properties and detect sold properties (Selenium version)')
    parser.add_argument('--limit', type=int, help='Limit number of properties to check')
    parser.add_argument('--delay', type=float, default=BETWEEN_PROPERTY_DELAY, help=f'Delay between requests in seconds (default: {BETWEEN_PROPERTY_DELAY})')
    parser.add_argument('--report', action='store_true', help='Generate sold properties report')
    parser.add_argument('--mongodb-uri', default=MONGODB_URI, help=f'MongoDB connection URI (default: {MONGODB_URI})')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-headless', action='store_true', help='Run browser in visible mode (not headless)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        monitor = SoldPropertyMonitor(
            mongodb_uri=args.mongodb_uri,
            headless=not args.no_headless
        )
        
        if args.report:
            # Generate and display report
            report = monitor.get_sold_properties_report()
            print(json.dumps(report, indent=2, default=str))
        else:
            # Run monitoring
            monitor.monitor_all_properties(limit=args.limit, delay=args.delay)
        
        monitor.close()
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n⚠ Monitoring interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
