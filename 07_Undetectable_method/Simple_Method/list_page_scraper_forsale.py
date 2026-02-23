#!/usr/bin/env python3
"""
Domain.com.au List Page Scraper - FOR-SALE PROPERTIES
Uses Selenium WebDriver for reliable JavaScript execution and HTML extraction
Adapted for Simple_Method directory structure
"""

import time
import os
import json
from datetime import datetime
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
    print("  pip3 install --break-system-packages selenium webdriver-manager")
    exit(1)

# URLs to scrape - FOR-SALE PROPERTIES IN ROBINA
URLS = [
    "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0",
    "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0&page=2",
    "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0&page=3",
    "https://www.domain.com.au/sale/mudgeeraba-qld-4213/house/?excludeunderoffer=1&ssubs=0",
    "https://www.domain.com.au/sale/varsity-lakes-qld-4227/house/?excludeunderoffer=1&ssubs=0",
    "https://www.domain.com.au/sale/reedy-creek-qld-4227/house/?excludeunderoffer=1&ssubs=0",
    "https://www.domain.com.au/sale/reedy-creek-qld-4227/house/?excludeunderoffer=1&ssubs=0&page=2",
    "https://www.domain.com.au/sale/burleigh-waters-qld-4220/house/?excludeunderoffer=1&ssubs=0",
    "https://www.domain.com.au/sale/burleigh-waters-qld-4220/house/?excludeunderoffer=1&ssubs=0&page=2"
]

RESULTS_DIR = "listing_results"


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


def scrape_list_page(driver, url, page_num):
    """Scrape a single list page using Selenium"""
    print(f"\n{'='*80}")
    print(f"Scraping List Page {page_num}")
    print(f"{'='*80}")
    
    result = {
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
        html_file = os.path.join(RESULTS_DIR, f"list_page_{page_num}_raw.html")
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
            print(f"  ✓ Found {len(listing_urls)} property listings")
            
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


def main():
    """Main scraping workflow"""
    print("\n" + "=" * 80)
    print("DOMAIN.COM.AU LIST PAGE SCRAPER - FOR-SALE PROPERTIES (Selenium)")
    print("=" * 80)
    print(f"\nScraping {len(URLS)} list pages for FOR-SALE properties in Robina...")
    print(f"Results will be saved to: {RESULTS_DIR}/\n")
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Create Selenium driver
    driver = create_driver()
    if not driver:
        print("\n✗ Cannot proceed without WebDriver")
        return 1
    
    try:
        # Scrape each list page
        all_results = []
        all_listing_urls = []
        
        for i, url in enumerate(URLS, 1):
            result = scrape_list_page(driver, url, i)
            all_results.append(result)
            
            if result["success"]:
                all_listing_urls.extend(result["listing_urls"])
            
            # Brief pause between pages
            if i < len(URLS):
                print(f"\n→ Waiting 3 seconds before next page...")
                time.sleep(3)
        
        # Remove duplicates
        unique_listing_urls = list(dict.fromkeys(all_listing_urls))
        
        # Generate summary report
        print(f"\n{'='*80}")
        print("SCRAPING COMPLETE")
        print(f"{'='*80}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save combined results
        combined_report = {
            "scrape_info": {
                "timestamp": datetime.now().isoformat(),
                "property_type": "FOR-SALE",
                "total_list_pages": len(URLS),
                "successful_pages": sum(1 for r in all_results if r["success"]),
                "failed_pages": sum(1 for r in all_results if not r["success"]),
                "total_listings_found": len(all_listing_urls),
                "unique_listings": len(unique_listing_urls)
            },
            "list_pages": all_results,
            "all_listing_urls": unique_listing_urls
        }
        
        report_file = os.path.join(RESULTS_DIR, f"list_scrape_report_{timestamp}.json")
        with open(report_file, 'w') as f:
            json.dump(combined_report, f, indent=2)
        
        # Save URLs file
        urls_file = os.path.join(RESULTS_DIR, f"property_listing_urls_{timestamp}.json")
        with open(urls_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "property_type": "FOR-SALE",
                "total_count": len(unique_listing_urls),
                "urls": unique_listing_urls
            }, f, indent=2)
        
        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"  Property type: FOR-SALE")
        print(f"  List pages scraped: {len(URLS)}")
        print(f"  Successful: {combined_report['scrape_info']['successful_pages']}")
        print(f"  Failed: {combined_report['scrape_info']['failed_pages']}")
        print(f"  Total listings found: {len(all_listing_urls)}")
        print(f"  Unique listings: {len(unique_listing_urls)}")
        print(f"\n📁 Files saved:")
        print(f"  • Report: {report_file}")
        print(f"  • URLs: {urls_file}")
        
        if unique_listing_urls:
            print(f"\n💡 Next step: Run property detail scraper:")
            print(f"   python3 property_detail_scraper_forsale.py --input {urls_file}")
        
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
