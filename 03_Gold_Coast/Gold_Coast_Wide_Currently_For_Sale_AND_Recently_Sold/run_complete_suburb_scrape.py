#!/usr/bin/env python3
"""
Complete Suburb Property Scraper - FIXED VERSION
Last Updated: 17/02/2026 (Brisbane Time)

CRITICAL FIXES APPLIED:
1. ✅ Extract suburb from actual property address (NOT search parameter)
2. ✅ Add address normalization for duplicate detection
3. ✅ Add cross-collection deduplication
4. ✅ Add listing ID tracking and history
5. ✅ Add photo validation
6. ✅ Add data quality checks before saving

ROOT CAUSE FIXED:
- OLD: property_data['suburb'] = self.suburb_name  # WRONG!
- NEW: property_data['suburb'] = extract_suburb_from_address(address)  # CORRECT!

PURPOSE:
Complete end-to-end property scraping for a suburb with data integrity checks.

USAGE:
python3 run_complete_suburb_scrape_FIXED.py --suburb "Varsity Lakes" --postcode 4227
"""

import time
import os
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Optional, List
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from bs4 import BeautifulSoup
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium webdriver-manager pymongo beautifulsoup4")
    exit(1)

# Import the HTML parser from the existing production system
sys.path.append('../../07_Undetectable_method/Simple_Method/../00_Production_System/02_Individual_Property_Google_Search')
try:
    from html_parser import parse_listing_html, clean_property_data
except ImportError:
    print("ERROR: html_parser not found!")
    print("Make sure the path to html_parser.py is correct")
    exit(1)

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
DATABASE_NAME = 'Gold_Coast'  # Unified database (was Gold_Coast_Currently_For_Sale)
PAGE_LOAD_WAIT = 5
SCROLL_WAIT = 1.5
BETWEEN_PROPERTY_DELAY = 2
MAX_PAGES = 20
MIN_LISTINGS_PER_PAGE = 5
MONITORED_FIELDS = ['price', 'inspection_times', 'agents_description']

# Target market suburbs for cross-collection deduplication
TARGET_MARKET_SUBURBS = [
    'robina', 'mudgeeraba', 'varsity_lakes', 'reedy_creek',
    'burleigh_waters', 'merrimac', 'worongary'
]


def extract_suburb_from_address(address: str) -> Optional[str]:
    """
    Extract suburb from address string.

    Example: "3 Equinox Court, Mudgeeraba, QLD 4213" → "Mudgeeraba"

    This is the CORRECT way to determine suburb (not from search parameter!)
    """
    if not address:
        return None

    # Match pattern: ", <SUBURB>, QLD"
    match = re.search(r',\s*([^,]+),\s*(QLD|NSW|VIC|SA|WA|TAS|NT|ACT)', address, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def normalize_address(address: str) -> str:
    """
    Normalize address for duplicate detection.

    Handles:
    - Case normalization (uppercase)
    - Whitespace normalization
    - Unit number formats: "20 1 15" → "20/1-15"
    - Remove punctuation
    """
    if not address:
        return ''

    # Uppercase
    normalized = address.upper()

    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    # Normalize unit numbers: "20 1 15" → "20/1-15"
    normalized = re.sub(r'(\d+)\s+(\d+)\s+(\d+)', r'\1/\2-\3', normalized)

    # Remove "UNIT" prefix
    normalized = re.sub(r'UNIT\s+', '', normalized)

    # Remove punctuation
    normalized = normalized.replace(',', '').replace('.', '')

    return normalized


def addresses_match(addr1: str, addr2: str) -> bool:
    """Check if two addresses match after normalization"""
    return normalize_address(addr1) == normalize_address(addr2)


def extract_listing_id_from_url(url: str) -> Optional[str]:
    """
    Extract Domain listing ID from URL.

    Example: "https://www.domain.com.au/3-equinox-court-mudgeeraba-qld-4213-2020495494" → "2020495494"
    """
    match = re.search(r'-(\d{7,10})$', url)
    return match.group(1) if match else None


class CompleteSuburbScraper:
    """Complete suburb scraper with data integrity checks"""

    def __init__(self, suburb_name: str, postcode: str):
        """Initialize scraper"""
        self.suburb_name = suburb_name
        self.postcode = postcode
        self.suburb_slug = self.build_suburb_slug(suburb_name, postcode)
        self.collection_name = suburb_name.lower().replace(' ', '_')
        self.driver = None

        # MongoDB connection
        print(f"→ Connecting to MongoDB...")
        self.mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        self.db = self.mongo_client[DATABASE_NAME]
        self.collection = self.db[self.collection_name]

        # Test connection
        try:
            self.mongo_client.admin.command('ping')
            print(f"  ✓ MongoDB connected")
            print(f"  ✓ Database: {DATABASE_NAME}")
            print(f"  ✓ Collection: {self.collection_name}")
        except Exception as e:
            raise Exception(f"MongoDB connection failed: {e}")

        # Create indexes
        self.create_indexes()

        # Setup headless browser
        self.setup_driver()

    def build_suburb_slug(self, suburb_name: str, postcode: str) -> str:
        """Build suburb slug for URL"""
        slug = suburb_name.lower().replace(' ', '-')
        return f"{slug}-qld-{postcode}"

    def create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            self.collection.create_index([("listing_url", ASCENDING)], unique=True)
            self.collection.create_index([("address", ASCENDING)])
            self.collection.create_index([("normalized_address", ASCENDING)])  # NEW!
            self.collection.create_index([("last_updated", ASCENDING)])
            print(f"  ✓ Indexes created/verified")
        except Exception as e:
            print(f"  ⚠ Index creation warning: {e}")

    def setup_driver(self):
        """Setup headless Chrome WebDriver"""
        print("→ Setting up headless Chrome WebDriver...")

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--js-flags=--max-old-space-size=256')
        chrome_options.add_argument('--window-size=1920,1080')

        # Anti-detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("  ✓ Headless Chrome ready")
        except Exception as e:
            raise Exception(f"Failed to create WebDriver: {e}")

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
        print(f"\n{'='*80}")
        print(f"PHASE 1: PROPERTY DISCOVERY")
        print(f"{'='*80}\n")

        all_urls = []
        expected_count = None
        page_num = 1

        while page_num <= MAX_PAGES:
            url = self.build_search_url(page_num)
            print(f"→ Discovering page {page_num}: {url}")

            try:
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
                        print(f"  ✓ Expected property count: {expected_count}")

                # Extract URLs
                urls = self.extract_listing_urls_from_html(html)
                print(f"  ✓ Found {len(urls)} listings on page {page_num}")

                if len(urls) == 0:
                    print(f"  → No listings found, stopping pagination")
                    break

                all_urls.extend(urls)

                if len(urls) < MIN_LISTINGS_PER_PAGE:
                    print(f"  → Only {len(urls)} listings (below threshold), stopping pagination")
                    break

                page_num += 1

                if page_num <= MAX_PAGES:
                    time.sleep(3)

            except Exception as e:
                print(f"  ✗ Error on page {page_num}: {e}")
                break

        # Remove duplicates
        unique_urls = list(dict.fromkeys(all_urls))

        print(f"\n{'='*80}")
        print(f"DISCOVERY COMPLETE")
        print(f"{'='*80}")
        print(f"  Pages scraped: {page_num - 1}")
        print(f"  Total URLs found: {len(all_urls)}")
        print(f"  Unique URLs: {len(unique_urls)}")
        print(f"  Expected count: {expected_count if expected_count else 'Not found'}")

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

        # Extract from "dateListed" JSON field (most reliable)
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
                print(f"  ⚠ Error parsing dateListed timestamp: {e}")

        return result

    def validate_property_data(self, property_data: Dict, html: str, url: str) -> tuple[bool, List[str]]:
        """
        Validate property data before saving.

        Returns: (is_valid, list_of_warnings)
        """
        warnings = []

        # Check 1: Address should not be empty
        if not property_data.get('address'):
            warnings.append("Missing address")

        # Check 2: Suburb should match address
        address = property_data.get('address', '')
        suburb_field = property_data.get('suburb')
        actual_suburb = extract_suburb_from_address(address)

        if actual_suburb and suburb_field:
            if actual_suburb.lower() != suburb_field.lower():
                warnings.append(f"Suburb mismatch: field='{suburb_field}', address='{actual_suburb}'")

        # Check 3: Photos should exist
        if not property_data.get('property_images') or len(property_data.get('property_images', [])) == 0:
            warnings.append("No photos found")

        # Check 4: Listing ID should be extractable
        listing_id = extract_listing_id_from_url(url)
        if not listing_id:
            warnings.append("Could not extract listing ID from URL")

        is_valid = len(warnings) == 0
        return is_valid, warnings

    def check_duplicate_across_collections(self, normalized_address: str, listing_id: str) -> Optional[Dict]:
        """
        Check if property already exists in ANY other suburb collection.

        Returns: Existing document if found, None otherwise
        """
        for suburb_coll in TARGET_MARKET_SUBURBS:
            if suburb_coll == self.collection_name:
                continue  # Skip current collection

            try:
                coll = self.db[suburb_coll]

                # Check by normalized address OR listing ID
                existing = coll.find_one({
                    '$or': [
                        {'normalized_address': normalized_address},
                        {'current_listing_id': listing_id}
                    ]
                })

                if existing:
                    return {
                        'document': existing,
                        'collection': suburb_coll
                    }
            except Exception as e:
                continue

        return None

    def scrape_property(self, url: str) -> Optional[Dict]:
        """Scrape single property with validation"""
        try:
            self.driver.get(url)
            time.sleep(PAGE_LOAD_WAIT)

            # Capture agent carousel
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

            # Override agent data
            if all_agents:
                agent_list = sorted(list(all_agents))
                property_data['agent_names'] = agent_list
                property_data['agent_name'] = ', '.join(agent_list)
            if agency:
                property_data['agency'] = agency

            # Extract listing date
            listing_date_info = self.extract_first_listed_date(html)
            property_data.update(listing_date_info)

            # Add required fields
            property_data['listing_url'] = url
            property_data['scrape_mode'] = 'headless'
            property_data['extraction_method'] = 'HTML'
            property_data['extraction_date'] = datetime.now().isoformat()
            property_data['source'] = 'complete_suburb_scraper_FIXED'

            # ══════════════════════════════════════════════════════════════
            # CRITICAL FIX #1: Extract suburb from ADDRESS, not search param!
            # ══════════════════════════════════════════════════════════════
            actual_suburb = extract_suburb_from_address(property_data['address'])
            if actual_suburb:
                property_data['suburb'] = actual_suburb  # ✅ CORRECT!
                print(f"  ✓ Suburb extracted from address: {actual_suburb}")
            else:
                property_data['suburb'] = self.suburb_name  # Fallback
                print(f"  ⚠ Could not extract suburb, using search suburb: {self.suburb_name}")

            # ══════════════════════════════════════════════════════════════
            # CRITICAL FIX #2: Add normalized address for deduplication
            # ══════════════════════════════════════════════════════════════
            property_data['normalized_address'] = normalize_address(property_data['address'])

            # ══════════════════════════════════════════════════════════════
            # CRITICAL FIX #3: Track listing ID and history
            # ══════════════════════════════════════════════════════════════
            listing_id = extract_listing_id_from_url(url)
            property_data['current_listing_id'] = listing_id
            property_data['listing_history'] = [{
                'listing_id': listing_id,
                'first_seen': datetime.now(),
                'price': property_data.get('price'),
                'photos_count': len(property_data.get('property_images', []))
            }]

            # ══════════════════════════════════════════════════════════════
            # CRITICAL FIX #4: Validate data before saving
            # ══════════════════════════════════════════════════════════════
            is_valid, validation_warnings = self.validate_property_data(property_data, html, url)

            if not is_valid:
                print(f"  ⚠ Validation warnings:")
                for warning in validation_warnings:
                    print(f"     - {warning}")

            property_data['data_quality_warnings'] = validation_warnings
            property_data['data_quality_score'] = 1.0 - (len(validation_warnings) * 0.1)

            # ══════════════════════════════════════════════════════════════
            # CRITICAL FIX #5: Check for duplicates across collections
            # ══════════════════════════════════════════════════════════════
            duplicate_check = self.check_duplicate_across_collections(
                property_data['normalized_address'],
                listing_id
            )

            if duplicate_check:
                existing_coll = duplicate_check['collection']
                existing_suburb = duplicate_check['document'].get('suburb')
                print(f"  ⚠ DUPLICATE DETECTED!")
                print(f"     Already exists in: {existing_coll}")
                print(f"     Existing suburb: {existing_suburb}")
                print(f"     Current suburb: {property_data['suburb']}")

                property_data['duplicate_warning'] = {
                    'exists_in_collection': existing_coll,
                    'existing_id': str(duplicate_check['document']['_id']),
                    'existing_suburb': existing_suburb
                }

            # Enrichment fields
            property_data['enriched'] = False
            property_data['enrichment_attempted'] = False
            property_data['enrichment_retry_count'] = 0
            property_data['enrichment_error'] = None
            property_data['enrichment_data'] = None
            property_data['last_enriched'] = None
            property_data['image_analysis'] = []

            return property_data

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None

    def save_to_mongodb(self, property_data: Dict) -> bool:
        """Save property to MongoDB with duplicate handling"""
        try:
            listing_url = property_data['listing_url']
            existing_doc = self.collection.find_one({'listing_url': listing_url})

            if existing_doc:
                # Update existing
                update_doc = {
                    '$set': {
                        **property_data,
                        'last_updated': datetime.now(),
                    }
                }

                # Preserve first_seen and merge listing history
                if 'first_seen' in existing_doc:
                    update_doc['$setOnInsert'] = {'first_seen': existing_doc['first_seen']}

                # Merge listing history
                if 'listing_history' in existing_doc:
                    existing_history = existing_doc['listing_history']
                    new_history = property_data.get('listing_history', [])

                    # Merge and deduplicate by listing_id
                    merged_history = {h['listing_id']: h for h in existing_history}
                    for h in new_history:
                        if h['listing_id'] not in merged_history:
                            merged_history[h['listing_id']] = h

                    property_data['listing_history'] = list(merged_history.values())

                self.collection.update_one({'listing_url': listing_url}, update_doc)
                return True
            else:
                # Insert new
                property_data['first_seen'] = datetime.now()
                property_data['last_updated'] = datetime.now()
                property_data['change_count'] = 0
                property_data['history'] = {}

                for field in MONITORED_FIELDS:
                    if field in property_data and property_data[field]:
                        property_data['history'][field] = [{
                            'value': property_data[field],
                            'recorded_at': datetime.now()
                        }]

                self.collection.insert_one(property_data)
                return True

        except Exception as e:
            print(f"  ✗ MongoDB error: {e}")
            return False

    def scrape_all_properties(self, urls: List[str]) -> Dict:
        """Scrape all discovered properties"""
        print(f"\n{'='*80}")
        print(f"PHASE 2: PROPERTY SCRAPING (WITH DATA QUALITY CHECKS)")
        print(f"{'='*80}\n")

        successful = 0
        failed = 0
        duplicates_found = 0
        validation_warnings_count = 0

        for i, url in enumerate(urls, 1):
            print(f"\n→ Property {i}/{len(urls)}")
            print(f"  URL: {url}")

            property_data = self.scrape_property(url)

            if property_data:
                # Track warnings
                if property_data.get('data_quality_warnings'):
                    validation_warnings_count += 1

                if property_data.get('duplicate_warning'):
                    duplicates_found += 1

                if self.save_to_mongodb(property_data):
                    successful += 1
                    print(f"  ✓ Saved: {property_data.get('address')}")
                    print(f"    Suburb: {property_data.get('suburb')}")
                    print(f"    {property_data.get('bedrooms')}bed, {property_data.get('bathrooms')}bath")
                    print(f"    Quality score: {property_data.get('data_quality_score', 0):.1f}")

                    if property_data.get('agent_names'):
                        print(f"    Agents: {', '.join(property_data['agent_names'])}")

                    if property_data.get('first_listed_date'):
                        print(f"    First listed: {property_data['first_listed_date']}", end='')
                        if property_data.get('days_on_domain'):
                            print(f" ({property_data['days_on_domain']} days on Domain)")
                        else:
                            print()
                else:
                    failed += 1
            else:
                failed += 1

            if i < len(urls):
                time.sleep(BETWEEN_PROPERTY_DELAY)

        return {
            "successful": successful,
            "failed": failed,
            "duplicates_found": duplicates_found,
            "validation_warnings": validation_warnings_count
        }

    def close(self):
        """Close connections"""
        if self.driver:
            self.driver.quit()
        if self.mongo_client:
            self.mongo_client.close()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Complete suburb property scraper (FIXED VERSION)")
    parser.add_argument('--suburb', required=True, help='Suburb name (e.g., "Varsity Lakes")')
    parser.add_argument('--postcode', required=True, help='Postcode (e.g., 4227)')
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("COMPLETE SUBURB PROPERTY SCRAPER - FIXED VERSION")
    print("=" * 80)
    print(f"\nSuburb: {args.suburb}")
    print(f"Postcode: {args.postcode}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Collection: {args.suburb.lower().replace(' ', '_')}")
    print("\n🔧 CRITICAL FIXES APPLIED:")
    print("  ✅ Suburb extracted from property address (not search param)")
    print("  ✅ Address normalization for duplicate detection")
    print("  ✅ Cross-collection deduplication checks")
    print("  ✅ Listing ID tracking and history")
    print("  ✅ Data validation before saving")
    print("=" * 80)

    scraper = None
    try:
        scraper = CompleteSuburbScraper(args.suburb, args.postcode)

        # Phase 1: Discovery
        discovery_result = scraper.discover_all_properties()

        # Phase 2: Scraping
        scraping_result = scraper.scrape_all_properties(discovery_result['discovered_urls'])

        # Final Summary
        print(f"\n{'='*80}")
        print("COMPLETE - FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"\n📊 DISCOVERY:")
        print(f"  Expected count: {discovery_result['expected_count']}")
        print(f"  URLs discovered: {len(discovery_result['discovered_urls'])}")
        print(f"  Pages scraped: {discovery_result['pages_scraped']}")

        print(f"\n📊 SCRAPING:")
        print(f"  Successful: {scraping_result['successful']}")
        print(f"  Failed: {scraping_result['failed']}")
        print(f"  Duplicates found: {scraping_result['duplicates_found']}")
        print(f"  Properties with warnings: {scraping_result['validation_warnings']}")

        print(f"\n📊 VALIDATION:")
        if discovery_result['expected_count']:
            if scraping_result['successful'] == discovery_result['expected_count']:
                print(f"  ✅ COUNT MATCH: {scraping_result['successful']} properties scraped (matches expected {discovery_result['expected_count']})")
            else:
                print(f"  ⚠️ COUNT MISMATCH:")
                print(f"     Expected: {discovery_result['expected_count']}")
                print(f"     Scraped: {scraping_result['successful']}")
                print(f"     Missing: {discovery_result['expected_count'] - scraping_result['successful']}")
        else:
            print(f"  ℹ️ Expected count not available for validation")

        print(f"\n💾 MONGODB:")
        print(f"  Database: {DATABASE_NAME}")
        print(f"  Collection: {args.suburb.lower().replace(' ', '_')}")
        print(f"  Documents: {scraper.collection.count_documents({})}")

        print(f"\n{'='*80}\n")

        return 0

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
