#!/usr/bin/env python3
"""
Sold Property Monitor
Monitors properties in the properties_for_sale collection and detects when they've been sold.
Moves sold properties to the properties_sold collection with sold date and price information.

Last Updated: 27/01/2026, 8:39 AM (Monday) - Brisbane
- Enhanced sold detection with multiple fallback methods
- Added breadcrumb navigation detection for "/sold/" paths
- Added "SOLD BY" text pattern detection in descriptions
- Added URL redirect detection
- Added comprehensive logging for detection methods
- Improved robustness to catch properties missed by simple tag detection
"""

import requests
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SoldPropertyMonitor:
    def __init__(self, mongodb_uri: str = MONGODB_URI, db_name: str = DATABASE_NAME):
        """Initialize MongoDB connection"""
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.for_sale_collection = self.db[FOR_SALE_COLLECTION]
        self.sold_collection = self.db[SOLD_COLLECTION]
        self.ensure_indexes()
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
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
        Fetch HTML content from a listing URL
        Returns: (html_content, final_url)
        The final_url may differ from the original if there was a redirect
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            # Check if URL was redirected (e.g., from /buy/ to /sold/)
            final_url = response.url
            if final_url != url:
                logger.debug(f"URL redirected: {url} -> {final_url}")
            
            return response.text, final_url
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None, None
    
    def check_if_sold(self, html: str, url: str = "") -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Check if property is sold by parsing HTML using multiple detection methods
        Returns: (is_sold, sold_date_text, sale_price, detection_method)
        
        Detection methods (in order of priority):
        1. Primary: listing-details__listing-tag with "Sold" text
        2. Breadcrumb: Navigation breadcrumb containing "/sold/" or "Sold in"
        3. Description: "SOLD BY" text pattern in property description
        4. URL Pattern: URL contains "/sold/"
        5. Meta Tags: og:type or other meta tags indicating sold status
        """
        if not html:
            return False, None, None, None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        is_sold = False
        sold_date_text = None
        detection_method = None
        
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
        # METHOD 3: Description Text - Check for "SOLD BY" patterns
        # ========================================================================
        if not is_sold:
            # Check main description/content areas
            description_selectors = [
                {'name': 'description'},  # meta description
                {'property': 'og:description'},  # Open Graph description
                {'class': re.compile(r'description|content|detail', re.IGNORECASE)},  # description divs
            ]
            
            for selector in description_selectors:
                if 'name' in selector or 'property' in selector:
                    desc_elem = soup.find('meta', selector)
                    if desc_elem and desc_elem.get('content'):
                        desc_text = desc_elem.get('content')
                        if self._check_sold_by_pattern(desc_text):
                            is_sold = True
                            detection_method = "description_sold_by"
                            logger.info(f"  ✓ Detection Method 3 (Description): Found 'SOLD BY' pattern")
                            logger.debug(f"    Description excerpt: {desc_text[:150]}")
                            break
                else:
                    desc_elems = soup.find_all(['div', 'p', 'section'], selector)
                    for elem in desc_elems:
                        desc_text = elem.get_text()
                        if self._check_sold_by_pattern(desc_text):
                            is_sold = True
                            detection_method = "description_sold_by"
                            logger.info(f"  ✓ Detection Method 3 (Description): Found 'SOLD BY' pattern")
                            logger.debug(f"    Description excerpt: {desc_text[:150]}")
                            break
                    if is_sold:
                        break
        
        # ========================================================================
        # METHOD 4: URL Pattern - Check if URL contains "/sold/"
        # ========================================================================
        if not is_sold and url:
            if '/sold/' in url.lower():
                is_sold = True
                detection_method = "url_pattern"
                logger.info(f"  ✓ Detection Method 4 (URL Pattern): URL contains '/sold/'")
        
        # ========================================================================
        # METHOD 5: Meta Tags - Check og:type or other indicators
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
        
        if not is_sold:
            logger.debug("  ✗ No sold indicators found")
        
        return is_sold, sold_date_text, sale_price, detection_method
    
    def _check_sold_by_pattern(self, text: str) -> bool:
        """
        Check if text contains "SOLD BY" patterns indicating a sold property
        Returns True if pattern is found
        """
        if not text:
            return False
        
        # Patterns that indicate a property has been sold
        sold_patterns = [
            r'SOLD BY\s+[A-Z\s]+',  # "SOLD BY TINA NENADIC"
            r'Sold by\s+[A-Za-z\s]+',  # "Sold by John Smith"
            r'SOLD\s*-\s*[A-Z\s]+',  # "SOLD - AGENT NAME"
        ]
        
        for pattern in sold_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
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
        
        # Fetch the listing page
        html, final_url = self.fetch_listing_html(listing_url)
        if not html:
            return False
        
        # Check if URL was redirected to a sold listing
        url_redirected = final_url and final_url != listing_url
        if url_redirected:
            logger.debug(f"  URL redirected to: {final_url}")
        
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
    
    def monitor_all_properties(self, limit: Optional[int] = None, delay: float = 2.0):
        """
        Monitor all properties in the for_sale collection
        
        Args:
            limit: Maximum number of properties to check (None for all)
            delay: Delay in seconds between requests (default 2.0)
        """
        logger.info("="*80)
        logger.info("SOLD PROPERTY MONITORING")
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
                'original_price': prop.get('price')
            })
        
        return report
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Monitor for-sale properties and detect sold properties')
    parser.add_argument('--limit', type=int, help='Limit number of properties to check')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds (default: 2.0)')
    parser.add_argument('--report', action='store_true', help='Generate sold properties report')
    parser.add_argument('--mongodb-uri', default=MONGODB_URI, help=f'MongoDB connection URI (default: {MONGODB_URI})')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        monitor = SoldPropertyMonitor(mongodb_uri=args.mongodb_uri)
        
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
