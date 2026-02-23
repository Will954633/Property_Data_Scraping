#!/usr/bin/env python3
"""
Property Detail Scraper for Domain.com.au - FOR-SALE PROPERTIES (HEADLESS MODE)
Last Updated: 31/01/2026, 9:04 am (Brisbane Time)

HEADLESS VERSION of property_detail_scraper_forsale.py
- Runs Chrome in headless mode (no GUI)
- Same data extraction as original
- Suitable for cloud deployment and multi-worker orchestration
- Preserves original working scraper

Processes individual property listing URLs using Selenium for reliable HTML extraction
Adapted for Simple_Method directory structure
"""

import time
import os
import json
import sys
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Please install with: pip3 install --break-system-packages selenium webdriver-manager")
    exit(1)

# Import the HTML parser from the existing production system
sys.path.append('../00_Production_System/02_Individual_Property_Google_Search')
from html_parser import parse_listing_html, clean_property_data

RESULTS_DIR = "property_data"
PAGE_LOAD_WAIT = 5
BETWEEN_PROPERTY_DELAY = 2


def create_driver():
    """Create and configure Selenium WebDriver in HEADLESS mode"""
    print("→ Setting up Chrome WebDriver (HEADLESS MODE)...")
    
    chrome_options = Options()
    
    # HEADLESS MODE - Critical for scaled deployment
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Anti-detection settings
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("  ✓ Chrome WebDriver ready (HEADLESS)")
        return driver
    except Exception as e:
        print(f"  ✗ Failed to create WebDriver: {e}")
        return None


def extract_address_from_url(url):
    """Extract property address from Domain.com.au URL"""
    import re
    
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


def process_property_url(driver, url, index, total):
    """Process a single property listing URL using Selenium (HEADLESS)"""
    print(f"\n{'='*80}")
    print(f"Processing Property {index}/{total} (HEADLESS MODE)")
    print(f"{'='*80}")
    print(f"URL: {url}")
    
    start_time = datetime.now()
    
    address = extract_address_from_url(url)
    print(f"Address: {address}")
    
    result = {
        "listing_url": url,
        "address": address,
        "index": index,
        "success": False,
        "property_data": None,
        "error": None,
        "time_seconds": 0,
        "scrape_mode": "headless"
    }
    
    try:
        # Navigate to listing URL
        print(f"→ Loading listing page (headless)...")
        driver.get(url)
        time.sleep(PAGE_LOAD_WAIT)
        
        # Verify page loaded
        current_url = driver.current_url
        if not current_url or 'domain.com.au' not in current_url:
            result["error"] = "Failed to load listing"
            print(f"  ✗ Page load failed")
            return result
        
        print(f"  ✓ Page loaded successfully")
        
        # Extract HTML using Selenium
        print(f"→ Extracting page HTML...")
        html = driver.page_source
        
        if not html or len(html) < 100:
            result["error"] = "HTML too small or empty"
            print(f"  ✗ HTML extraction failed")
            return result
        
        print(f"  ✓ Extracted HTML ({len(html):,} chars)")
        
        # Save raw HTML
        os.makedirs(RESULTS_DIR, exist_ok=True)
        html_dir = os.path.join(RESULTS_DIR, "html")
        os.makedirs(html_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_address = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in address).strip().replace(' ', '_')
        
        html_file = os.path.join(html_dir, f"property_{index}_{timestamp}_{safe_address}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓ Saved HTML: {html_file}")
        
        # Parse HTML for property data
        print(f"→ Parsing property data...")
        property_data = parse_listing_html(html, address)
        property_data = clean_property_data(property_data)
        
        if property_data:
            property_data['listing_url'] = url
            property_data['scrape_mode'] = 'headless'
            
            print(f"  ✓ Extracted property data:")
            for key, value in property_data.items():
                if key not in ['address', 'extraction_method', 'extraction_date', 'listing_url', 'scrape_mode'] and value:
                    if isinstance(value, str) and len(value) > 60:
                        print(f"    • {key}: {value[:60]}...")
                    elif isinstance(value, list) and len(value) > 3:
                        print(f"    • {key}: [{len(value)} items]")
                    else:
                        print(f"    • {key}: {value}")
            
            result["success"] = True
            result["property_data"] = property_data
        else:
            result["error"] = "No property data extracted"
            print(f"  ⚠ No property data extracted")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"  ✗ Error: {e}")
    
    end_time = datetime.now()
    result["time_seconds"] = (end_time - start_time).total_seconds()
    
    return result


def load_urls_from_file(filepath):
    """Load property listing URLs from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if 'urls' in data:
        return data['urls']
    elif 'all_listing_urls' in data:
        return data['all_listing_urls']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unknown JSON format - expected 'urls' or 'all_listing_urls' field")


def generate_report(results, output_file):
    """Generate comprehensive report"""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    total_time = sum(r["time_seconds"] for r in results)
    avg_time = total_time / total if total > 0 else 0
    
    report = {
        "scrape_info": {
            "timestamp": datetime.now().isoformat(),
            "property_type": "FOR-SALE",
            "scrape_mode": "HEADLESS",
            "total_properties": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            "total_time_seconds": round(total_time, 2),
            "average_time_seconds": round(avg_time, 2)
        },
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return report


def main():
    """Main processing workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process Domain.com.au for-sale property listing URLs (HEADLESS MODE)")
    parser.add_argument('--input', required=True, help='Input JSON file with property URLs')
    parser.add_argument('--limit', type=int, help='Limit number of properties to process (for testing)')
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("PROPERTY DETAIL SCRAPER - FOR-SALE PROPERTIES (HEADLESS MODE)")
    print("=" * 80)
    print("\nMODE: Headless Chrome (no GUI)")
    print("SUITABLE FOR: Cloud deployment, multi-worker orchestration")
    print("=" * 80)
    
    # Load URLs from input file
    if not os.path.exists(args.input):
        print(f"\n✗ Input file not found: {args.input}")
        return 1
    
    print(f"\n→ Loading property URLs from: {args.input}")
    urls = load_urls_from_file(args.input)
    
    # Apply limit if specified
    if args.limit:
        urls = urls[:args.limit]
        print(f"  ✓ Loaded {len(urls)} property URLs (limited from total)")
    else:
        print(f"  ✓ Loaded {len(urls)} property URLs")
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Create Selenium driver (HEADLESS)
    driver = create_driver()
    if not driver:
        print("\n✗ Cannot proceed without WebDriver")
        return 1
    
    try:
        print(f"\n{'='*80}")
        print("Starting property scraping (HEADLESS MODE)...")
        print(f"{'='*80}\n")
        
        # Process each property
        results = []
        for i, url in enumerate(urls, 1):
            result = process_property_url(driver, url, i, len(urls))
            results.append(result)
            
            # Brief pause between properties
            if i < len(urls):
                print(f"\n→ Waiting {BETWEEN_PROPERTY_DELAY} seconds before next property...")
                time.sleep(BETWEEN_PROPERTY_DELAY)
        
        # Generate report
        print(f"\n{'='*80}")
        print("SCRAPING COMPLETE")
        print(f"{'='*80}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(RESULTS_DIR, f"property_scrape_report_headless_{timestamp}.json")
        report = generate_report(results, report_file)
        
        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"  Property type: FOR-SALE")
        print(f"  Scrape mode:   HEADLESS")
        print(f"  Total properties: {report['scrape_info']['total_properties']}")
        print(f"  Successful:       {report['scrape_info']['successful']}")
        print(f"  Failed:           {report['scrape_info']['failed']}")
        print(f"  Success rate:     {report['scrape_info']['success_rate']}")
        print(f"  Total time:       {report['scrape_info']['total_time_seconds']}s")
        print(f"  Average time:     {report['scrape_info']['average_time_seconds']}s per property")
        print(f"\n📁 Report saved: {report_file}")
        
        if report['scrape_info']['successful'] > 0:
            print(f"\n✅ HEADLESS MODE TEST: SUCCESSFUL")
            print(f"   • {report['scrape_info']['successful']} properties scraped successfully")
            print(f"   • Data extraction working in headless mode")
            print(f"   • Ready for multi-worker orchestration")
        
        print(f"\n💡 Next step: Upload to MongoDB:")
        print(f"   python3 mongodb_uploader.py")
        
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
