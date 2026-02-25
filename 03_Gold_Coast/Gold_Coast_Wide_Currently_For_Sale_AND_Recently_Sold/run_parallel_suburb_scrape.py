#!/usr/bin/env python3
"""
Parallel Suburb Property Scraper - Process Multiple Suburbs Simultaneously
Last Updated: 12/02/2026, 8:48 am (Wednesday) - Brisbane

CRITICAL FIX (12/02/2026):
- ADDED PERIODIC BROWSER RESTART: Prevents Chrome crashes from memory exhaustion
- Restarts Chrome every 20 properties to clear accumulated memory
- Fixes "invalid session id" errors after 30+ properties (Carrara crash issue)
- Maintains shared driver performance benefits with minimal overhead
- See CARRARA_CHROME_CRASH_ANALYSIS.md for full details

Previous Updates:
- 06/02/2026, 3:15 pm (Friday) - Brisbane

CRITICAL FIX (06/02/2026):
- Added sys.stdout.reconfigure(line_buffering=True) to force unbuffered output
- This ensures print() output is visible when launched via subprocess.Popen
  (orchestrator). Without this, Python buffers stdout when it's a pipe (not a TTY),
  causing the orchestrator to think the process is hung when it's actually working.
- Works in conjunction with PYTHONUNBUFFERED=1 set by the orchestrator.

CRITICAL FIX (05/02/2026):
- ADDED SELENIUM TIMEOUTS: Prevents indefinite hangs on page loads
- set_page_load_timeout(90): 90 second timeout for page loads
- implicitly_wait(30): 30 second timeout for element waits
- set_script_timeout(30): 30 second timeout for script execution
- Added TimeoutException handling with retry logic
- Fixes 14+ hour hang issue in orchestrator

CHROMEDRIVER PERFORMANCE FIX (04/02/2026):
- CHROMEDRIVER PERFORMANCE FIX APPLIED: Removed per-property driver creation
- Now uses ONE shared driver per suburb (eliminates 60s cleanup delays)
- Removed scrape_property_with_own_driver() method
- Sequential scraping with shared driver is faster than parallel with per-property drivers
- --parallel-properties parameter is now ignored (always uses shared driver)

PREVIOUS CHANGES:
- Added parallel processing for multiple suburbs using multiprocessing
- Each suburb runs in its own process with dedicated browser instance
- Real-time progress monitoring for all suburbs
- Consolidated final summary
- Implemented connection pooling for MongoDB to support 5+ simultaneous suburbs

PURPOSE:
Process multiple suburbs in parallel for faster scraping:
1. Each suburb gets its own process and browser
2. Discovery and scraping happen simultaneously
3. All data stored in MongoDB (one collection per suburb)
4. Progress monitoring across all processes
5. Shared MongoDB connection pool for scalability

USAGE:
python3 run_parallel_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227"
python3 run_parallel_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227" "Burleigh Heads:4220" "Mermaid Beach:4218" "Burleigh Waters:4220"
"""

import time
import os
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from multiprocessing import Process, Queue, Manager

# CRITICAL: Force unbuffered stdout so output is visible when launched via subprocess.Popen
# Without this, Python buffers stdout when it's a pipe (not a TTY), causing the orchestrator
# to think the process is hung. This is the #1 reason for "scraping hang" issues.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from bs4 import BeautifulSoup
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, InvalidSessionIdException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium webdriver-manager pymongo beautifulsoup4")
    exit(1)

# Import the HTML parser from the existing production system
sys.path.append('../../07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search')
try:
    from html_parser import parse_listing_html, clean_property_data
except ImportError:
    print("ERROR: html_parser not found!")
    print("Make sure the path to html_parser.py is correct")
    exit(1)

# Import scraping failures logger
sys.path.append('../../../Fields_Orchestrator/01_Debug_Log')
try:
    from scraping_failures_logger import log_scraping_failure
    FAILURES_LOGGING_ENABLED = True
except ImportError:
    print("WARNING: scraping_failures_logger not found - failure logging disabled")
    FAILURES_LOGGING_ENABLED = False
    def log_scraping_failure(*args, **kwargs):
        pass  # No-op if logger not available

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
DATABASE_NAME = 'Gold_Coast_Currently_For_Sale'
MASTER_DATABASE_NAME = 'Gold_Coast'

# Target market suburbs — these write to Gold_Coast_Currently_For_Sale.
# All other suburbs upsert into Gold_Coast (the master GIS/cadastral database).
TARGET_MARKET_SUBURBS = {
    'robina', 'mudgeeraba', 'varsity lakes', 'reedy creek',
    'burleigh waters', 'merrimac', 'worongary', 'carrara'
}
PAGE_LOAD_WAIT = 5
SCROLL_WAIT = 1.5
BETWEEN_PROPERTY_DELAY = 2
MAX_PAGES = 20
MIN_LISTINGS_PER_PAGE = 5
MONITORED_FIELDS = ['price', 'inspection_times', 'agents_description']

# Parallel property scraping configuration
PARALLEL_PROPERTIES = 3  # Number of properties to scrape simultaneously per suburb

# Browser restart configuration (prevents memory exhaustion crashes)
BROWSER_RESTART_INTERVAL = 15  # Restart Chrome every N properties to prevent crashes (reduced for low-memory VM)


# Global MongoDB client (one per process, reused for all operations)
_mongo_client = None
_mongo_db = None
_mongo_master_db = None


def get_mongodb_connection():
    """Get or create MongoDB connection (one per process)"""
    global _mongo_client, _mongo_db, _mongo_master_db

    if _mongo_client is None:
        max_retries = 3
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                _mongo_client = MongoClient(
                    MONGODB_URI,
                    maxPoolSize=50,  # Connection pool size
                    minPoolSize=10,
                    maxIdleTimeMS=45000,
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    retryWrites=False,
                    retryReads=False
                )
                _mongo_db = _mongo_client[DATABASE_NAME]
                _mongo_master_db = _mongo_client[MASTER_DATABASE_NAME]

                # Test connection
                _mongo_client.admin.command('ping')
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"MongoDB connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"MongoDB connection failed after {max_retries} attempts: {e}")

    return _mongo_client, _mongo_db, _mongo_master_db


def extract_suburb_from_address(address: str) -> Optional[str]:
    """
    Extract suburb from address string.
    Example: "48 Peach Drive, Robina, QLD 4226" → "Robina"

    This function extracts the actual suburb from the property's address string,
    which is CRITICAL for preventing properties from being stored in the wrong
    MongoDB collection. Without this, properties are assigned to the search suburb
    parameter instead of their actual location.

    Args:
        address: Full property address string

    Returns:
        Extracted suburb name or None if extraction fails

    Root Cause Fix:
        This fixes the bug where "48 Peach Drive, Robina, QLD 4226" was stored
        in the "varsity_lakes" collection because Domain.com.au search returns
        properties from nearby suburbs with the same postcode.
    """
    if not address:
        return None

    # Match pattern: ", <SUBURB>, QLD"
    # This handles addresses like "48 Peach Drive, Robina, QLD 4226"
    match = re.search(r',\s*([^,]+),\s*(QLD|NSW|VIC|SA|WA|TAS|NT|ACT)', address, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


class ParallelSuburbScraper:
    """Scraper for a single suburb (runs in its own process)"""
    
    def __init__(self, suburb_name: str, postcode: str, progress_queue: Queue, parallel_properties: int = 1):
        """Initialize scraper"""
        self.suburb_name = suburb_name
        self.postcode = postcode
        self.suburb_slug = self.build_suburb_slug(suburb_name, postcode)
        self.collection_name = suburb_name.lower().replace(' ', '_')
        self.driver = None
        self.progress_queue = progress_queue
        self.parallel_properties = parallel_properties
        self.progress_lock = Lock()  # Thread-safe progress updates
        
        # Get shared MongoDB connection
        self.log(f"Connecting to MongoDB...")
        self.mongo_client, self.db, self.master_db = get_mongodb_connection()
        self.collection = self.db[self.collection_name]
        self.log(f"MongoDB connected - Collection: {self.collection_name}")
        
        # Create indexes
        self.create_indexes()
        
        # Setup headless browser (shared driver for all properties - PERFORMANCE FIX)
        self.log(f"Using shared driver for all properties (ChromeDriver performance fix)")
        self.setup_driver()
    
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
    
    def build_suburb_slug(self, suburb_name: str, postcode: str) -> str:
        """Build suburb slug for URL"""
        slug = suburb_name.lower().replace(' ', '-')
        return f"{slug}-qld-{postcode}"
    
    def create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            self.collection.create_index([("listing_url", ASCENDING)], unique=True)
            self.collection.create_index([("address", ASCENDING)])
            self.collection.create_index([("last_updated", ASCENDING)])
            self.log(f"Indexes created/verified")
        except Exception as e:
            self.log(f"Index creation warning: {e}")
    
    def setup_driver(self):
        """Setup headless Chrome WebDriver with timeouts"""
        self.log("Setting up headless Chrome WebDriver...")

        chrome_options = Options()

        # Essential flags for headless mode on Linux server
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.binary_location = os.environ.get('CHROME_BINARY_PATH', '/snap/bin/chromium')

        # Retry logic for WebDriver creation with self-healing zombie cleanup
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                service = Service(os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver'))
                self.driver = webdriver.Chrome(service=service, options=chrome_options)

                # ✅ CRITICAL: Set timeouts to prevent indefinite hangs
                self.driver.set_page_load_timeout(90)  # 90 second page load timeout
                self.driver.implicitly_wait(30)  # 30 second element wait timeout
                self.driver.set_script_timeout(30)  # 30 second script execution timeout

                self.log("Headless Chrome ready with timeouts configured (90s page load, 30s implicit wait)")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    self.log(f"WebDriver creation failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")

                    # Self-healing: Clean up zombie Chrome processes before retry
                    self.log("🔧 Self-healing: Cleaning up zombie Chrome processes...")
                    try:
                        import subprocess
                        kill_cmd = "killall -9 chrome chromedriver 2>/dev/null || true"
                        subprocess.run(kill_cmd, shell=True, timeout=10)
                        self.log("✅ Zombie cleanup completed")
                    except Exception as cleanup_error:
                        self.log(f"⚠️ Zombie cleanup warning: {cleanup_error}")

                    time.sleep(retry_delay)
                else:
                    raise Exception(f"Failed to create WebDriver after {max_retries} attempts: {e}")
    
    def build_search_url(self, page_num: int = 1) -> str:
        """Build search URL for suburb"""
        base_url = f"https://www.domain.com.au/sale/{self.suburb_slug}/?excludeunderoffer=1&ssubs=0"
        if page_num == 1:
            return base_url
        else:
            return f"{base_url}&page={page_num}"
    
    def extract_property_count(self, html: str) -> Optional[int]:
        """Extract expected property count from search page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try h1 tags first
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text(strip=True)
            match = re.search(r'(\d+)\s+(Properties|Property)\s+for\s+sale', text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Try text search
        all_text = soup.get_text()
        match = re.search(r'(\d+)\s+(Properties|Property)\s+for\s+sale\s+in', all_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return None
    
    def extract_listing_urls_from_html(self, html: str) -> List[str]:
        """Extract property listing URLs from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        listing_urls = []
        
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link['href']
            
            # Match pattern: /slug-PROPERTYID (7-10 digits at end)
            if re.match(r'^/[\w-]+-\d{7,10}$', href):
                full_url = f"https://www.domain.com.au{href}"
                if full_url not in listing_urls:
                    listing_urls.append(full_url)
            
            # Also match full URLs
            elif 'domain.com.au' in href and re.search(r'-\d{7,10}$', href):
                if href not in listing_urls:
                    listing_urls.append(href)
        
        return listing_urls
    
    def discover_all_properties(self) -> Dict:
        """Discover all property URLs with auto-pagination"""
        self.log("Starting property discovery...")
        self.update_progress('discovery_started')
        
        all_urls = []
        expected_count = None
        page_num = 1
        
        while page_num <= MAX_PAGES:
            url = self.build_search_url(page_num)
            
            try:
                # Load page with timeout protection
                try:
                    self.driver.get(url)
                    time.sleep(PAGE_LOAD_WAIT)
                except TimeoutException:
                    self.log(f"Timeout loading search page {page_num}, retrying once...")
                    time.sleep(5)
                    self.driver.get(url)
                    time.sleep(PAGE_LOAD_WAIT)
                
                # Scroll to load lazy content
                for i in range(5):
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(SCROLL_WAIT)
                
                html = self.driver.page_source
                
                # Extract expected count from first page
                if page_num == 1:
                    expected_count = self.extract_property_count(html)
                    if expected_count:
                        self.log(f"Expected property count: {expected_count}")
                
                # Extract URLs
                urls = self.extract_listing_urls_from_html(html)
                self.log(f"Page {page_num}: Found {len(urls)} listings")
                
                if len(urls) == 0:
                    break
                
                all_urls.extend(urls)
                
                if len(urls) < MIN_LISTINGS_PER_PAGE:
                    break
                
                page_num += 1
                
                if page_num <= MAX_PAGES:
                    time.sleep(3)
                    
            except Exception as e:
                self.log(f"Error on page {page_num}: {e}")
                break
        
        # Remove duplicates
        unique_urls = list(dict.fromkeys(all_urls))
        
        self.log(f"Discovery complete: {len(unique_urls)} unique URLs found")
        self.update_progress('discovery_complete', {
            'expected_count': expected_count,
            'discovered_urls': len(unique_urls),
            'pages_scraped': page_num - 1
        })
        
        return {
            "expected_count": expected_count,
            "discovered_urls": unique_urls,
            "pages_scraped": page_num - 1
        }
    
    def extract_address_from_url(self, url: str) -> str:
        """Extract property address from Domain.com.au URL"""
        path = url.replace('https://www.domain.com.au/', '').replace('http://www.domain.com.au/', '')
        path = re.sub(r'-\d{7,10}$', '', path)
        parts = path.split('-')
        
        suburb_idx = -1
        for i, part in enumerate(parts):
            if part in ['qld', 'nsw', 'vic', 'sa', 'wa', 'tas', 'nt', 'act']:
                suburb_idx = i - 1
                break
        
        if suburb_idx > 0:
            street_parts = parts[:suburb_idx]
            street_address = ' '.join(street_parts).title()
            suburb = parts[suburb_idx].title()
            state = parts[suburb_idx + 1].upper() if suburb_idx + 1 < len(parts) else ''
            postcode = parts[suburb_idx + 2] if suburb_idx + 2 < len(parts) else ''
            full_address = f"{street_address}, {suburb}, {state} {postcode}"
            return full_address
        
        return ' '.join(parts).title()
    
    def extract_first_listed_date(self, html: str) -> Dict:
        """Extract 'First listed' date and days on market from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        result = {
            'first_listed_date': None,
            'first_listed_year': None,
            'first_listed_full': None,
            'first_listed_timestamp': None,
            'days_on_domain': None,
            'last_updated_date': None,
        }
        
        # PRIMARY METHOD: Extract from "dateListed" JSON field in HTML
        date_listed_pattern = r'"dateListed"\s*:\s*"([^"]+)"'
        date_match = re.search(date_listed_pattern, html)
        
        if date_match:
            timestamp_str = date_match.group(1)
            result['first_listed_timestamp'] = timestamp_str
            
            try:
                listed_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').split('.')[0])
                result['first_listed_date'] = listed_date.strftime('%d %B')
                result['first_listed_year'] = listed_date.year
                result['first_listed_full'] = listed_date.strftime('%d %B %Y')
                
                current_date = datetime.now()
                days_diff = (current_date - listed_date).days
                result['days_on_domain'] = days_diff
                
            except Exception as e:
                pass
        
        return result
    
    def scrape_property(self, url: str) -> Optional[Dict]:
        """Scrape single property with timeout and session error handling"""
        max_retries = 2

        for attempt in range(max_retries):
            try:
                # Load property page with timeout protection
                try:
                    self.driver.get(url)
                    time.sleep(PAGE_LOAD_WAIT)
                except TimeoutException:
                    if attempt < max_retries - 1:
                        self.log(f"Timeout loading {url}, retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(5)
                        continue
                    else:
                        self.log(f"Failed to load {url} after {max_retries} timeout attempts")
                        # Log failure to debug system
                        if FAILURES_LOGGING_ENABLED:
                            log_scraping_failure(
                                url=url,
                                suburb=self.suburb_name,
                                error_type="timeout",
                                error_message=f"Page load timeout after {max_retries} attempts (90s each)",
                                retry_count=max_retries
                            )
                        return None
                except (InvalidSessionIdException, WebDriverException) as e:
                    # Browser session died - restart browser and retry
                    if attempt < max_retries - 1:
                        self.log(f"⚠️ Browser session lost ({type(e).__name__}), restarting and retrying ({attempt + 1}/{max_retries})...")
                        try:
                            self.driver.quit()
                        except:
                            pass
                        time.sleep(3)
                        self.setup_driver()
                        continue
                    else:
                        self.log(f"❌ Browser session failed after {max_retries} restart attempts")
                        if FAILURES_LOGGING_ENABLED:
                            log_scraping_failure(
                                url=url,
                                suburb=self.suburb_name,
                                error_type="session_error",
                                error_message=f"{type(e).__name__}: {str(e)}",
                                retry_count=max_retries
                            )
                        return None
            
                # Capture agent carousel (wait for rotations)
                all_agents = set()
                agency = None
                
                for i in range(3):
                    html = self.driver.page_source
                    if html and len(html) > 100:
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        if not agency:
                            agency_elem = soup.find(attrs={'data-testid': 'listing-details__agent-details-agency-name'})
                            if agency_elem:
                                agency = agency_elem.get_text(strip=True)
                        
                        agent_detail_sections = soup.find_all(attrs={'data-testid': 'listing-details__agent-details'})
                        for section in agent_detail_sections:
                            agent_name_elem = section.find(attrs={'data-testid': 'listing-details__agent-details-agent-name'})
                            if agent_name_elem:
                                name = agent_name_elem.get_text(strip=True)
                                if name:
                                    all_agents.add(name)
                    
                    if i < 2:
                        time.sleep(12)
                
                # Get final HTML
                html = self.driver.page_source
                if not html or len(html) < 100:
                    return None
                
                # Parse HTML
                address = self.extract_address_from_url(url)
                property_data = parse_listing_html(html, address)
                property_data = clean_property_data(property_data)

                # CRITICAL FIX (Issue #2): Validate this is an individual property page, not a listing page
                # Listing pages have og_title like "33 Real Estate Properties for Sale in..." instead of actual address
                og_title = property_data.get('og_title', '')
                if og_title:
                    og_title_lower = og_title.lower()
                    listing_page_keywords = [
                        'real estate properties for sale',
                        'properties for sale in',
                        'real estate for sale',
                        'property for sale in'
                    ]
                    if any(keyword in og_title_lower for keyword in listing_page_keywords):
                        self.log(f"  ⚠️ SKIPPING: Listing page detected (not individual property)")
                        self.log(f"  og_title: {og_title[:100]}")
                        if FAILURES_LOGGING_ENABLED:
                            log_scraping_failure(
                                url=url,
                                suburb=self.suburb_name,
                                error_type="listing_page",
                                error_message=f"Detected listing page instead of individual property: {og_title[:100]}",
                                retry_count=0
                            )
                        return None

                # CRITICAL FIX (Issue #3): Preserve original address format from og_title
                # Extract: "205/107 - 109 Golden Four Drive, Bilinga QLD 4225 | Domain" → "205/107 - 109 Golden Four Drive, Bilinga, QLD 4225"
                if og_title:
                    # Pattern: "Address, Suburb QLD PostCode | Domain"
                    og_address_match = re.search(r'^([^|]+?)\s*\|\s*Domain', og_title)
                    if og_address_match:
                        original_address = og_address_match.group(1).strip()
                        # Ensure format is: "Street, Suburb, QLD PostCode" (add commas if missing)
                        formatted_address = re.sub(r'\s+(QLD|NSW|VIC|SA|WA|TAS|NT|ACT)\s+', r', \1 ', original_address)
                        property_data['address'] = formatted_address
                        self.log(f"  ✓ Preserved address format from og_title: {formatted_address}")

                # Override agent data
                if all_agents:
                    agent_list = sorted(list(all_agents))
                    property_data['agent_names'] = agent_list
                    property_data['agent_name'] = ', '.join(agent_list)
                if agency:
                    property_data['agency'] = agency
                
                # Extract "First listed" date and days on market
                listing_date_info = self.extract_first_listed_date(html)
                property_data['first_listed_date'] = listing_date_info['first_listed_date']
                property_data['first_listed_year'] = listing_date_info['first_listed_year']
                property_data['first_listed_full'] = listing_date_info['first_listed_full']
                property_data['first_listed_timestamp'] = listing_date_info['first_listed_timestamp']
                property_data['days_on_domain'] = listing_date_info['days_on_domain']
                property_data['last_updated_date'] = listing_date_info['last_updated_date']

                # Detect sold status from Domain's embedded JSON (saleMode field)
                # "buy" = active for-sale listing; "sold" = already sold
                sale_mode_match = re.search(r'"saleMode"\s*:\s*"([^"]+)"', html)
                if sale_mode_match and sale_mode_match.group(1).lower() == 'sold':
                    property_data['listing_status'] = 'sold'
                    self.log(f"  ⚠ Sold listing detected (saleMode=sold): {url}")
                else:
                    property_data['listing_status'] = 'for_sale'

                # Add required fields
                property_data['listing_url'] = url
                property_data['scrape_mode'] = 'headless'
                property_data['extraction_method'] = 'HTML'
                property_data['extraction_date'] = datetime.now().isoformat()
                property_data['source'] = 'parallel_suburb_scraper'

                # CRITICAL FIX: Extract actual suburb from address, not search parameter
                # This prevents properties like "48 Peach Drive, Robina" from being stored
                # in the "varsity_lakes" collection when Domain search returns cross-suburb results
                actual_suburb = extract_suburb_from_address(property_data.get('address', ''))
                if actual_suburb:
                    property_data['suburb'] = actual_suburb
                    self.log(f"  ✓ Suburb extracted from address: {actual_suburb}")
                else:
                    property_data['suburb'] = self.suburb_name  # Fallback only
                    self.log(f"  ⚠ Could not extract suburb from address, using search suburb: {self.suburb_name}")
                
                # Enrichment fields
                property_data['enriched'] = False
                property_data['enrichment_attempted'] = False
                property_data['enrichment_retry_count'] = 0
                property_data['enrichment_error'] = None
                property_data['enrichment_data'] = None
                property_data['last_enriched'] = None
                property_data['image_analysis'] = []
                
                return property_data
                
            except TimeoutException:
                if attempt < max_retries - 1:
                    self.log(f"Timeout during scraping {url}, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(5)
                    continue
                else:
                    self.log(f"Failed to scrape {url} after {max_retries} timeout attempts")
                    # Log failure to debug system
                    if FAILURES_LOGGING_ENABLED:
                        log_scraping_failure(
                            url=url,
                            suburb=self.suburb_name,
                            error_type="timeout",
                            error_message=f"Scraping timeout after {max_retries} attempts",
                            retry_count=max_retries
                        )
                    return None
            except Exception as e:
                self.log(f"Error scraping {url}: {e}")
                # Log failure to debug system
                if FAILURES_LOGGING_ENABLED:
                    log_scraping_failure(
                        url=url,
                        suburb=self.suburb_name,
                        error_type="exception",
                        error_message=str(e),
                        retry_count=attempt + 1
                    )
                return None
        
        return None
    
    def save_to_mongodb(self, property_data: Dict) -> bool:
        """
        Save property to MongoDB with database routing:
        - Target market suburbs → Gold_Coast_Currently_For_Sale (full document with history tracking)
        - All other suburbs → Gold_Coast master DB (upsert scraped fields onto existing GIS doc,
          or insert as new doc if not found)
        """
        try:
            listing_url = property_data['listing_url']

            actual_suburb = property_data.get('suburb', self.suburb_name)
            collection_name = actual_suburb.lower().replace(' ', '_')
            is_target_market = actual_suburb.lower() in TARGET_MARKET_SUBURBS

            if is_target_market:
                target_db = self.db
            else:
                target_db = self.master_db

            target_collection = target_db[collection_name]

            # Log routing decision when suburb differs from search parameter or goes to master DB
            if collection_name != self.collection_name or not is_target_market:
                db_label = DATABASE_NAME if is_target_market else MASTER_DATABASE_NAME
                self.log(f"  Routing '{actual_suburb}' → {db_label}.{collection_name}")

            existing_doc = target_collection.find_one({'listing_url': listing_url})

            if existing_doc:
                # Update existing — never overwrite pipeline-owned or first-insert-only fields
                PIPELINE_FIELDS = {
                    'first_seen',
                    'watch_article_generated',
                    'watch_article_path',
                    'watch_article_generated_at',
                }
                update_data = {k: v for k, v in property_data.items() if k not in PIPELINE_FIELDS}
                update_doc = {
                    '$set': {
                        **update_data,
                        'last_updated': datetime.now(),
                    }
                }
                target_collection.update_one({'listing_url': listing_url}, update_doc)
                if not is_target_market:
                    self.log(f"  [Gold_Coast] UPDATED _id={existing_doc['_id']} | {collection_name} | {property_data.get('address', listing_url)}")
                return True
            else:
                # Insert new
                property_data['first_seen'] = datetime.now()
                property_data['last_updated'] = datetime.now()
                property_data['change_count'] = 0
                property_data['history'] = {}

                if is_target_market:
                    for field in MONITORED_FIELDS:
                        if field in property_data and property_data[field]:
                            property_data['history'][field] = [{
                                'value': property_data[field],
                                'recorded_at': datetime.now()
                            }]

                result = target_collection.insert_one(property_data)
                if not is_target_market:
                    self.log(f"  [Gold_Coast] INSERTED _id={result.inserted_id} | {collection_name} | {property_data.get('address', listing_url)}")
                return True

        except Exception as e:
            self.log(f"  [save_to_mongodb] ERROR: {e} | {listing_url}")
            return False
    
    def scrape_all_properties(self, urls: List[str]) -> Dict:
        """Scrape all properties using shared driver with periodic restart (CRASH FIX)"""
        self.log(f"Starting property scraping ({len(urls)} properties)...")
        self.log(f"Mode: Sequential with shared driver (ChromeDriver performance fix applied)")
        self.log(f"Browser restart: Every {BROWSER_RESTART_INTERVAL} properties (prevents memory crashes)")
        self.update_progress('scraping_started', {'total_properties': len(urls)})
        
        successful = 0
        failed = 0
        
        # ALWAYS use sequential scraping with shared driver
        # This eliminates 60+ second cleanup delays per property
        for i, url in enumerate(urls, 1):
            # CRITICAL: Restart browser periodically to prevent memory exhaustion crashes
            # Chrome accumulates memory over time and crashes after 30+ properties
            # Restarting every 20 properties prevents this while maintaining performance
            if i > 1 and (i - 1) % BROWSER_RESTART_INTERVAL == 0:
                self.log(f"🔄 Restarting browser to prevent memory crash (property {i}/{len(urls)})...")
                try:
                    self.driver.quit()
                    time.sleep(5)  # Brief pause to ensure clean shutdown
                    self.setup_driver()
                    self.log(f"✅ Browser restarted successfully")
                except Exception as e:
                    self.log(f"⚠️ Browser restart warning: {e}")
                    # Try to continue anyway - setup_driver will create new instance
                    try:
                        self.setup_driver()
                    except Exception as e2:
                        self.log(f"❌ Fatal: Cannot restart browser: {e2}")
                        # Mark remaining properties as failed
                        failed += len(urls) - i + 1
                        break
            
            property_data = self.scrape_property(url)
            
            if property_data:
                if self.save_to_mongodb(property_data):
                    successful += 1
                else:
                    failed += 1
            else:
                failed += 1
            
            # Log every property for verbose orchestrator output
            address = property_data.get('address', url.split('/')[-1]) if property_data else url.split('/')[-1]
            status_icon = "✅" if property_data else "❌"
            self.log(f"{status_icon} [{i}/{len(urls)}] {address}")
            
            # Update progress every 5 properties
            if i % 5 == 0 or i == len(urls):
                self.update_progress('scraping_progress', {
                    'completed': i,
                    'total': len(urls),
                    'successful': successful,
                    'failed': failed
                })
            
            if i < len(urls):
                time.sleep(BETWEEN_PROPERTY_DELAY)
        
        self.log(f"Scraping complete: {successful} successful, {failed} failed")
        self.update_progress('scraping_complete', {
            'successful': successful,
            'failed': failed
        })
        
        return {
            "successful": successful,
            "failed": failed
        }
    
    def run(self):
        """Main execution for this suburb"""
        try:
            self.log("Starting complete suburb scrape...")
            
            # Phase 1: Discovery
            discovery_result = self.discover_all_properties()
            
            # Phase 2: Scraping
            scraping_result = self.scrape_all_properties(discovery_result['discovered_urls'])
            
            # Final summary
            self.update_progress('complete', {
                'discovery': discovery_result,
                'scraping': scraping_result,
                'final_count': self.collection.count_documents({})
            })
            
            self.log("Complete!")
            
        except Exception as e:
            self.log(f"Fatal error: {e}")
            self.update_progress('error', {'error': str(e)})
        
        finally:
            if self.driver:
                self.driver.quit()
            # Don't close MongoDB client - it's shared across the process


def run_suburb_scraper(suburb_name: str, postcode: str, progress_queue: Queue, parallel_properties: int = 1):
    """Worker function to run scraper in separate process"""
    try:
        scraper = ParallelSuburbScraper(suburb_name, postcode, progress_queue, parallel_properties)
        scraper.run()
    except Exception as e:
        print(f"[{suburb_name}] Process error: {e}")
    finally:
        # Close MongoDB connection when process ends
        global _mongo_client
        if _mongo_client:
            _mongo_client.close()


def monitor_progress(progress_queue: Queue, suburb_count: int, results_dict: dict):
    """Monitor progress from all suburb processes"""
    completed_suburbs = set()
    
    while len(completed_suburbs) < suburb_count:
        try:
            progress = progress_queue.get(timeout=1)
            suburb = progress['suburb']
            status = progress['status']
            data = progress.get('data', {})
            
            # Store results
            if suburb not in results_dict:
                results_dict[suburb] = {}
            
            results_dict[suburb][status] = data
            
            # Print progress
            if status == 'discovery_complete':
                print(f"[{suburb}] Discovery: {data.get('discovered_urls', 0)} URLs found")
            elif status == 'scraping_progress':
                completed = data.get('completed', 0)
                total = data.get('total', 0)
                successful = data.get('successful', 0)
                print(f"[{suburb}] Progress: {completed}/{total} ({successful} successful)")
            elif status == 'complete':
                completed_suburbs.add(suburb)
                print(f"[{suburb}] ✅ COMPLETE")
            elif status == 'error':
                completed_suburbs.add(suburb)
                print(f"[{suburb}] ❌ ERROR: {data.get('error', 'Unknown')}")
                
        except:
            # Timeout - continue monitoring
            pass


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Parallel suburb property scraper with connection pooling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_parallel_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227"
  python3 run_parallel_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227" "Burleigh Heads:4220" "Mermaid Beach:4218" "Burleigh Waters:4220"
        """
    )
    
    parser.add_argument('--suburbs', nargs='+', required=True, 
                       help='Suburb:Postcode pairs (e.g., "Robina:4226" "Varsity Lakes:4227")')
    parser.add_argument('--parallel-properties', type=int, default=1,
                       help='Number of properties to scrape simultaneously per suburb (default: 1, recommended: 3)')
    args = parser.parse_args()
    
    # Parse suburb arguments
    suburbs = []
    for suburb_arg in args.suburbs:
        try:
            name, postcode = suburb_arg.split(':')
            suburbs.append((name, postcode))
        except:
            print(f"✗ Invalid suburb format: {suburb_arg}")
            print("  Expected format: 'Suburb Name:Postcode'")
            return 1
    
    print("\n" + "=" * 80)
    print("PARALLEL SUBURB PROPERTY SCRAPER (WITH CONNECTION POOLING)")
    print("=" * 80)
    print(f"\nSuburbs to process: {len(suburbs)}")
    for name, postcode in suburbs:
        print(f"  - {name} ({postcode})")
    print(f"\nDatabase: {DATABASE_NAME}")
    print(f"Mode: Parallel Processing (one process per suburb)")
    print(f"Parallel Properties: {args.parallel_properties} properties at once per suburb")
    print(f"Connection: Pooled (maxPoolSize=50, supports 5+ simultaneous suburbs)")
    print("=" * 80 + "\n")
    
    # Create shared progress queue and results dict
    manager = Manager()
    progress_queue = manager.Queue()
    results_dict = manager.dict()
    
    # Start scraper processes
    processes = []
    for i, (suburb_name, postcode) in enumerate(suburbs):
        p = Process(target=run_suburb_scraper, args=(suburb_name, postcode, progress_queue, args.parallel_properties))
        p.start()
        processes.append(p)
        print(f"[{suburb_name}] Process started (PID: {p.pid})")
        # Stagger starts to avoid WebDriver timeout issues
        if i < len(suburbs) - 1:
            print(f"  Waiting 10 seconds before starting next process...")
            time.sleep(10)
    
    print("\n" + "=" * 80)
    print("MONITORING PROGRESS")
    print("=" * 80 + "\n")
    
    # Monitor progress
    monitor_progress(progress_queue, len(suburbs), results_dict)
    
    # Wait for all processes to complete
    for p in processes:
        p.join()
    
    # Final Summary
    print("\n" + "=" * 80)
    print("PARALLEL SCRAPING COMPLETE - FINAL SUMMARY")
    print("=" * 80 + "\n")
    
    for suburb_name, postcode in suburbs:
        print(f"📊 {suburb_name.upper()}")
        if suburb_name in results_dict:
            suburb_results = results_dict[suburb_name]
            
            if 'complete' in suburb_results:
                complete_data = suburb_results['complete']
                discovery = complete_data.get('discovery', {})
                scraping = complete_data.get('scraping', {})
                
                print(f"  Expected:    {discovery.get('expected_count', 'N/A')}")
                print(f"  Discovered:  {len(discovery.get('discovered_urls', []))}")
                print(f"  Successful:  {scraping.get('successful', 0)}")
                print(f"  Failed:      {scraping.get('failed', 0)}")
                print(f"  Final Count: {complete_data.get('final_count', 0)} documents in MongoDB")
            elif 'error' in suburb_results:
                print(f"  ❌ Error: {suburb_results['error'].get('error', 'Unknown')}")
            else:
                print(f"  ⚠️ Incomplete")
        else:
            print(f"  ⚠️ No results")
        print()
    
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
