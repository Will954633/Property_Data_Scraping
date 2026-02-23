#!/usr/bin/env python3
"""
Headless Property Discovery Test Script
Last Updated: 31/01/2026, 9:54 am (Brisbane Time)

PURPOSE:
Test if we can discover new for-sale properties in headless mode by scraping
Domain.com.au search/list pages and extracting property listing URLs.

This script tests the DISCOVERY component that's missing from the current
headless_forsale_mongodb_scraper.py implementation.

Based on:
- list_page_scraper_forsale.py (visible browser discovery)
- headless_forsale_mongodb_scraper.py (headless scraping pattern)

TEST SCOPE:
- Scrape 1-2 Domain.com.au search pages in headless mode
- Extract property listing URLs from search results
- Verify URL extraction works correctly
- Compare results with visible browser method
"""

import time
import os
import json
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium webdriver-manager beautifulsoup4")
    exit(1)

# Test configuration - Base URL (pagination will be added automatically)
BASE_SEARCH_URL = "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0"

RESULTS_DIR = "discovery_test_results"
PAGE_LOAD_WAIT = 5
SCROLL_WAIT = 1.5
MAX_PAGES = 20  # Safety limit to prevent infinite loops
MIN_LISTINGS_PER_PAGE = 5  # Stop if page has fewer than this many listings


class HeadlessDiscoveryTester:
    """Test property discovery in headless mode"""
    
    def __init__(self):
        """Initialize headless browser"""
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup headless Chrome WebDriver"""
        print("→ Setting up headless Chrome WebDriver...")
        
        chrome_options = Options()
        
        # HEADLESS MODE - This is what we're testing!
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
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
    
    def scroll_page(self):
        """Scroll page to load lazy-loaded content"""
        print("  → Scrolling to load all content...")
        
        try:
            # Scroll down in increments to trigger lazy loading
            for i in range(5):
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(SCROLL_WAIT)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            print("  ✓ Scrolling complete")
            return True
        except Exception as e:
            print(f"  ✗ Scrolling error: {e}")
            return False
    
    def extract_listing_urls_from_html(self, html: str) -> List[str]:
        """Extract all property listing URLs from HTML"""
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
    
    def build_page_url(self, base_url: str, page_num: int) -> str:
        """Build URL for specific page number"""
        if page_num == 1:
            return base_url
        else:
            # Add page parameter
            separator = '&' if '?' in base_url else '?'
            return f"{base_url}{separator}page={page_num}"
    
    def scrape_search_page(self, url: str, page_num: int) -> Dict:
        """Scrape a single search/list page in headless mode"""
        print(f"\n{'='*80}")
        print(f"Discovering Properties - Page {page_num}")
        print(f"{'='*80}")
        print(f"URL: {url}")
        
        result = {
            "search_page_url": url,
            "page_number": page_num,
            "success": False,
            "listing_urls": [],
            "listing_count": 0,
            "timestamp": datetime.now().isoformat(),
            "mode": "headless"
        }
        
        try:
            # Navigate to URL
            print(f"  → Loading page in headless mode...")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(PAGE_LOAD_WAIT)
            
            # Verify page loaded
            current_url = self.driver.current_url
            if not current_url or 'domain.com.au' not in current_url:
                result["error"] = "Page load failed"
                print(f"  ✗ Page load failed")
                return result
            
            print(f"  ✓ Page loaded: {current_url}")
            
            # Scroll to trigger lazy loading
            self.scroll_page()
            
            # Get page HTML
            print(f"  → Extracting page HTML...")
            html = self.driver.page_source
            
            if not html or len(html) < 100:
                result["error"] = "HTML too small or empty"
                print(f"  ✗ HTML extraction failed")
                return result
            
            print(f"  ✓ Extracted HTML ({len(html):,} chars)")
            
            # Save raw HTML for inspection
            os.makedirs(RESULTS_DIR, exist_ok=True)
            html_file = os.path.join(RESULTS_DIR, f"headless_search_page_{page_num}_raw.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"  ✓ Saved HTML: {html_file}")
            
            # Extract listing URLs
            print(f"  → Extracting property listing URLs...")
            listing_urls = self.extract_listing_urls_from_html(html)
            
            if listing_urls:
                result["success"] = True
                result["listing_urls"] = listing_urls
                result["listing_count"] = len(listing_urls)
                print(f"  ✓ Found {len(listing_urls)} property listings")
                
                # Print sample
                print(f"\n  Sample URLs:")
                for i, listing_url in enumerate(listing_urls[:5], 1):
                    print(f"    {i}. {listing_url}")
                if len(listing_urls) > 5:
                    print(f"    ... and {len(listing_urls) - 5} more")
            else:
                result["error"] = "No listing URLs found"
                print(f"  ⚠ No listing URLs found in HTML")
                print(f"  ℹ Check the saved HTML file to debug")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")


def main():
    """Main test execution"""
    print("\n" + "=" * 80)
    print("HEADLESS PROPERTY DISCOVERY TEST - AUTO PAGINATION")
    print("=" * 80)
    print(f"\nTesting: Can we discover new properties in headless mode?")
    print(f"Base URL: {BASE_SEARCH_URL}")
    print(f"Strategy: Auto-discover all pages until no more listings found")
    print(f"Results directory: {RESULTS_DIR}/")
    print("=" * 80)
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Initialize tester
    tester = None
    try:
        tester = HeadlessDiscoveryTester()
        
        # Auto-discover all pages
        all_results = []
        all_listing_urls = []
        page_num = 1
        
        print(f"\n→ Starting auto-pagination discovery...")
        print(f"  Will continue until no listings found or max {MAX_PAGES} pages reached\n")
        
        while page_num <= MAX_PAGES:
            # Build URL for this page
            url = tester.build_page_url(BASE_SEARCH_URL, page_num)
            
            # Scrape the page
            result = tester.scrape_search_page(url, page_num)
            all_results.append(result)
            
            if result["success"] and result["listing_count"] > 0:
                all_listing_urls.extend(result["listing_urls"])
                
                # Check if we should continue
                if result["listing_count"] < MIN_LISTINGS_PER_PAGE:
                    print(f"\n⚠ Page {page_num} has only {result['listing_count']} listings (below threshold of {MIN_LISTINGS_PER_PAGE})")
                    print(f"→ Stopping pagination - likely reached end of results")
                    break
                
                # Continue to next page
                page_num += 1
                
                # Brief pause between pages
                print(f"\n→ Waiting 3 seconds before next page...")
                time.sleep(3)
            else:
                # No listings found - stop
                print(f"\n⚠ Page {page_num} returned no listings")
                print(f"→ Stopping pagination - reached end of results")
                break
        
        if page_num > MAX_PAGES:
            print(f"\n⚠ Reached maximum page limit ({MAX_PAGES})")
        
        # Remove duplicates
        unique_listing_urls = list(dict.fromkeys(all_listing_urls))
        
        # Generate test report
        print(f"\n{'='*80}")
        print("TEST COMPLETE")
        print(f"{'='*80}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save test results
        test_report = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "test_name": "Headless Property Discovery Test - Auto Pagination",
                "mode": "headless",
                "base_url": BASE_SEARCH_URL,
                "pagination_strategy": "auto-discover until no listings",
                "total_search_pages": len(all_results),
                "successful_pages": sum(1 for r in all_results if r["success"]),
                "failed_pages": sum(1 for r in all_results if not r["success"]),
                "total_listings_found": len(all_listing_urls),
                "unique_listings": len(unique_listing_urls)
            },
            "search_pages": all_results,
            "discovered_urls": unique_listing_urls
        }
        
        report_file = os.path.join(RESULTS_DIR, f"headless_discovery_test_{timestamp}.json")
        with open(report_file, 'w') as f:
            json.dump(test_report, f, indent=2)
        
        # Save discovered URLs
        if unique_listing_urls:
            urls_file = os.path.join(RESULTS_DIR, f"discovered_property_urls_{timestamp}.json")
            with open(urls_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "discovery_mode": "headless_auto_pagination",
                    "source": "Domain.com.au search pages",
                    "base_url": BASE_SEARCH_URL,
                    "pages_scraped": len(all_results),
                    "total_count": len(unique_listing_urls),
                    "urls": unique_listing_urls
                }, f, indent=2)
            print(f"\n📁 Discovered URLs saved: {urls_file}")
        
        # Print summary
        print(f"\n📊 TEST RESULTS:")
        print(f"  Mode: HEADLESS with AUTO-PAGINATION")
        print(f"  Search pages discovered: {len(all_results)}")
        print(f"  Successful: {test_report['test_info']['successful_pages']}")
        print(f"  Failed: {test_report['test_info']['failed_pages']}")
        print(f"  Total listings found: {len(all_listing_urls)}")
        print(f"  Unique listings: {len(unique_listing_urls)}")
        
        print(f"\n📁 Files saved:")
        print(f"  • Test report: {report_file}")
        if unique_listing_urls:
            print(f"  • Discovered URLs: {urls_file}")
        
        # Test verdict
        print(f"\n{'='*80}")
        if test_report['test_info']['successful_pages'] > 0 and len(unique_listing_urls) > 0:
            print("✅ TEST PASSED: Headless discovery with auto-pagination is WORKING!")
            print(f"   Successfully discovered {len(unique_listing_urls)} properties across {len(all_results)} pages")
            print(f"\n💡 Next steps:")
            print(f"   1. Review discovered URLs in: {urls_file}")
            print(f"   2. Test scraping these URLs with headless_forsale_mongodb_scraper.py")
            print(f"   3. Integrate auto-pagination discovery into main scraper")
        else:
            print("❌ TEST FAILED: Headless discovery not working")
            print(f"   Check HTML files in {RESULTS_DIR}/ to debug")
            print(f"   Compare with visible browser results")
        print(f"{'='*80}\n")
        
        return 0 if len(unique_listing_urls) > 0 else 1
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"TEST ERROR")
        print(f"{'='*80}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if tester:
            tester.close()


if __name__ == "__main__":
    exit(main())
