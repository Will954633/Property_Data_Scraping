#!/usr/bin/env python3
"""
Domain.com.au List Page Scraper - SOLD PROPERTIES (Last 12 Months)
Last Edit: 13/02/2026, 11:44 AM (Thursday) — Brisbane Time

Modified from 6-month scraper to collect 12 months of sold data for all 8 target market suburbs.
Uses Selenium WebDriver for reliable JavaScript execution and HTML extraction.
Extracts individual property URLs from sold listing pages for detailed scraping.

Changes from original:
- Extended from 5 to 8 suburbs (added Carrara, Merrimac, Worongary)
- Increased from 7 to 15 pages per suburb (6 months → 12 months)
- Updated for Gold_Coast_Recently_Sold database
"""

import time
import os
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"ERROR: Required package not installed: {e}")
    print("Please install with:")
    print("  pip3 install --break-system-packages selenium webdriver-manager beautifulsoup4 python-dateutil")
    exit(1)

# URLs to scrape - SOLD PROPERTIES BY SUBURB (12 MONTHS = 15 PAGES)
# All 8 target market suburbs from /Users/projects/Documents/Cline/Rules/Target Market Subrubs.md
SUBURB_URLS = {
    "robina": [
        f"https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1" + (f"&page={i}" if i > 1 else "")
        for i in range(1, 16)  # Pages 1-15
    ],
    "mudgeeraba": [
        f"https://www.domain.com.au/sold-listings/mudgeeraba-qld-4213/house/?excludepricewithheld=1" + (f"&page={i}" if i > 1 else "")
        for i in range(1, 16)  # Pages 1-15
    ],
    "varsity-lakes": [
        f"https://www.domain.com.au/sold-listings/varsity-lakes-qld-4227/house/?excludepricewithheld=1" + (f"&page={i}" if i > 1 else "")
        for i in range(1, 16)  # Pages 1-15
    ],
    "reedy-creek": [
        f"https://www.domain.com.au/sold-listings/reedy-creek-qld-4227/house/?excludepricewithheld=1" + (f"&page={i}" if i > 1 else "")
        for i in range(1, 16)  # Pages 1-15
    ],
    "burleigh-waters": [
        f"https://www.domain.com.au/sold-listings/burleigh-waters-qld-4220/house/?excludepricewithheld=1" + (f"&page={i}" if i > 1 else "")
        for i in range(1, 16)  # Pages 1-15
    ],
    # NEW SUBURBS (3 additional target market suburbs)
    "carrara": [
        f"https://www.domain.com.au/sold-listings/carrara-qld-4211/house/?excludepricewithheld=1" + (f"&page={i}" if i > 1 else "")
        for i in range(1, 16)  # Pages 1-15
    ],
    "merrimac": [
        f"https://www.domain.com.au/sold-listings/merrimac-qld-4226/house/?excludepricewithheld=1" + (f"&page={i}" if i > 1 else "")
        for i in range(1, 16)  # Pages 1-15
    ],
    "worongary": [
        f"https://www.domain.com.au/sold-listings/worongary-qld-4213/house/?excludepricewithheld=1" + (f"&page={i}" if i > 1 else "")
        for i in range(1, 16)  # Pages 1-15
    ]
}

RESULTS_DIR = "listing_results_sold"


def create_driver():
    """Create and configure Selenium WebDriver"""
    print("→ Setting up Chrome WebDriver...")
    print("  → Using webdriver-manager to auto-download matching chromedriver...")
    
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Use webdriver-manager to automatically handle chromedriver versions
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("  ✓ Chrome WebDriver ready")
        return driver
    except Exception as e:
        print(f"  ✗ Failed to create WebDriver: {e}")
        print("\nPlease ensure:")
        print("  1. Google Chrome is installed")
        print("  2. Python packages installed: pip3 install selenium webdriver-manager")
        return None


def scroll_page(driver):
    """Scroll page to load lazy-loaded content"""
    print("  → Scrolling to load all content...")
    
    try:
        # Scroll down in increments
        for i in range(5):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1.5)
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        print("  ✓ Scrolling complete")
        return True
    except Exception as e:
        print(f"  ✗ Scrolling error: {e}")
        return False


def extract_listing_urls_from_html(html):
    """Extract all property listing URLs from sold listing page HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    listing_urls = []
    
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link['href']
        
        # Match pattern: /slug-PROPERTYID (7-10 digits at end)
        # Sold listings use same URL pattern as for-sale
        if re.match(r'^/[\w-]+-\d{7,10}$', href):
            full_url = f"https://www.domain.com.au{href}"
            if full_url not in listing_urls:
                listing_urls.append(full_url)
        
        # Also match full URLs
        elif 'domain.com.au' in href and re.search(r'-\d{7,10}$', href):
            if href not in listing_urls:
                listing_urls.append(href)
    
    return listing_urls


def scrape_list_page(driver, url, page_num, suburb):
    """Scrape a single sold listing page using Selenium"""
    print(f"\n{'='*80}")
    print(f"Scraping {suburb.upper()} - List Page {page_num}")
    print(f"{'='*80}")
    
    result = {
        "suburb": suburb,
        "list_page_url": url,
        "page_number": page_num,
        "success": False,
        "listing_urls": [],
        "listing_count": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Navigate to URL
        print(f"  → Navigating to URL...")
        driver.get(url)
        
        # Wait for page to load
        print(f"  → Waiting for page to load...")
        time.sleep(5)
        
        # Scroll to trigger lazy loading
        scroll_page(driver)
        
        # Get page HTML
        print(f"→ Extracting page HTML...")
        html = driver.page_source
        
        if not html or len(html) < 100:
            result["error"] = "HTML too small or empty"
            print(f"  ✗ HTML extraction failed")
            return result
        
        print(f"  ✓ Extracted HTML ({len(html):,} chars)")
        
        # Save raw HTML
        os.makedirs(RESULTS_DIR, exist_ok=True)
        html_file = os.path.join(RESULTS_DIR, f"{suburb}_page_{page_num}_raw.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓ Saved HTML: {html_file}")
        
        # Extract listing URLs
        print(f"→ Extracting listing URLs...")
        listing_urls = extract_listing_urls_from_html(html)
        
        if listing_urls:
            result["success"] = True
            result["listing_urls"] = listing_urls
            result["listing_count"] = len(listing_urls)
            print(f"  ✓ Found {len(listing_urls)} sold property listings")
            
            # Print sample
            print(f"\n  Sample URLs:")
            for i, listing_url in enumerate(listing_urls[:3], 1):
                print(f"    {i}. {listing_url}")
            if len(listing_urls) > 3:
                print(f"    ... and {len(listing_urls) - 3} more")
        else:
            result["error"] = "No listing URLs found"
            print(f"  ⚠ No listing URLs found in HTML")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  ✗ Error: {e}")
    
    return result


def scrape_suburb(driver, suburb, urls):
    """Scrape all list pages for a single suburb"""
    print(f"\n{'#'*80}")
    print(f"# SUBURB: {suburb.upper()}")
    print(f"# Pages to scrape: {len(urls)}")
    print(f"{'#'*80}")
    
    suburb_results = []
    suburb_listing_urls = []
    
    for i, url in enumerate(urls, 1):
        result = scrape_list_page(driver, url, i, suburb)
        suburb_results.append(result)
        
        if result["success"]:
            suburb_listing_urls.extend(result["listing_urls"])
        
        # Brief pause between pages
        if i < len(urls):
            print(f"\n→ Waiting 3 seconds before next page...")
            time.sleep(3)
    
    # Remove duplicates
    unique_urls = list(dict.fromkeys(suburb_listing_urls))
    
    print(f"\n{'='*80}")
    print(f"SUBURB COMPLETE: {suburb.upper()}")
    print(f"  Pages scraped: {len(urls)}")
    print(f"  Successful: {sum(1 for r in suburb_results if r['success'])}")
    print(f"  Total listings: {len(suburb_listing_urls)}")
    print(f"  Unique listings: {len(unique_urls)}")
    print(f"{'='*80}")
    
    return {
        "suburb": suburb,
        "pages_scraped": len(urls),
        "successful_pages": sum(1 for r in suburb_results if r["success"]),
        "total_listings": len(suburb_listing_urls),
        "unique_listings": len(unique_urls),
        "page_results": suburb_results,
        "listing_urls": unique_urls
    }


def main():
    """Main scraping workflow"""
    print("\n" + "=" * 80)
    print("DOMAIN.COM.AU LIST PAGE SCRAPER - SOLD PROPERTIES (Last 12 Months)")
    print("=" * 80)
    print(f"\nScraping sold listings for {len(SUBURB_URLS)} suburbs...")
    print(f"Target: 12 months of data (15 pages per suburb)")
    print(f"Results will be saved to: {RESULTS_DIR}/\n")
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Create Selenium driver
    driver = create_driver()
    if not driver:
        print("\n✗ Cannot proceed without WebDriver")
        return 1
    
    try:
        # Scrape each suburb
        all_suburb_results = []
        all_listing_urls = []
        
        for suburb, urls in SUBURB_URLS.items():
            suburb_result = scrape_suburb(driver, suburb, urls)
            all_suburb_results.append(suburb_result)
            all_listing_urls.extend(suburb_result["listing_urls"])
            
            # Pause between suburbs
            print(f"\n→ Waiting 5 seconds before next suburb...")
            time.sleep(5)
        
        # Remove duplicates across all suburbs
        unique_listing_urls = list(dict.fromkeys(all_listing_urls))
        
        # Generate summary report
        print(f"\n{'='*80}")
        print("SCRAPING COMPLETE - ALL SUBURBS")
        print(f"{'='*80}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save combined results
        combined_report = {
            "scrape_info": {
                "timestamp": datetime.now().isoformat(),
                "property_type": "SOLD",
                "target_period": "Last 12 Months",
                "total_suburbs": len(SUBURB_URLS),
                "total_list_pages": sum(len(urls) for urls in SUBURB_URLS.values()),
                "successful_pages": sum(r["successful_pages"] for r in all_suburb_results),
                "total_listings_found": len(all_listing_urls),
                "unique_listings": len(unique_listing_urls)
            },
            "suburbs": all_suburb_results,
            "all_listing_urls": unique_listing_urls
        }
        
        report_file = os.path.join(RESULTS_DIR, f"sold_list_scrape_report_12months_{timestamp}.json")
        with open(report_file, 'w') as f:
            json.dump(combined_report, f, indent=2)
        
        # Save URLs file for property detail scraper
        urls_file = os.path.join(RESULTS_DIR, f"sold_property_urls_12months_{timestamp}.json")
        with open(urls_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "property_type": "SOLD",
                "target_period": "Last 12 Months",
                "total_count": len(unique_listing_urls),
                "urls": unique_listing_urls
            }, f, indent=2)
        
        # Also save individual suburb URL files for property detail scraper
        for result in all_suburb_results:
            suburb_name = result['suburb']
            suburb_urls = result['listing_urls']
            suburb_urls_file = os.path.join(RESULTS_DIR, f"sold_urls_{suburb_name}_12months_{timestamp}.json")
            with open(suburb_urls_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "suburb": suburb_name,
                    "property_type": "SOLD",
                    "target_period": "Last 12 Months",
                    "total_count": len(suburb_urls),
                    "urls": suburb_urls
                }, f, indent=2)

        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"  Property type: SOLD (Last 12 Months)")
        print(f"  Suburbs scraped: {len(SUBURB_URLS)}")
        print(f"  List pages scraped: {combined_report['scrape_info']['total_list_pages']}")
        print(f"  Successful pages: {combined_report['scrape_info']['successful_pages']}")
        print(f"  Total listings found: {len(all_listing_urls)}")
        print(f"  Unique listings: {len(unique_listing_urls)}")
        
        print(f"\n📁 Files saved:")
        print(f"  • Report: {report_file}")
        print(f"  • URLs: {urls_file}")
        
        # Per-suburb breakdown
        print(f"\n📍 Per-Suburb Breakdown:")
        for result in all_suburb_results:
            print(f"  • {result['suburb'].upper()}: {result['unique_listings']} properties")
        
        if unique_listing_urls:
            print(f"\n💡 Next step: Run property detail scraper:")
            print(f"   python3 property_detail_scraper_sold.py --input {urls_file}")
        
        print(f"\n{'='*80}\n")
        
        return 0
        
    finally:
        # Always close the driver
        if driver:
            print("→ Closing browser...")
            driver.quit()
            print("  ✓ Browser closed\n")


if __name__ == "__main__":
    exit(main())
