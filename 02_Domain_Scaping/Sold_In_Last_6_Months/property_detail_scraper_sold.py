#!/usr/bin/env python3
"""
Property Detail Scraper for Domain.com.au - SOLD PROPERTIES (Last 6 Months)
Processes individual sold property listing URLs using Selenium for reliable HTML extraction
Includes sale date extraction and suburb tracking
"""

import time
import os
import json
import sys
import glob
from datetime import datetime
import argparse

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Please install with: pip3 install selenium webdriver-manager")
    exit(1)

# Import the HTML parser for sold listings
from html_parser_sold import parse_sold_listing_html, clean_property_data

RESULTS_DIR = "property_data"
PAGE_LOAD_WAIT = 5
BETWEEN_PROPERTY_DELAY = 2


def create_driver():
    """Create and configure Selenium WebDriver"""
    print("→ Setting up Chrome WebDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("  ✓ Chrome WebDriver ready")
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


def process_property_url(driver, url, index, total, suburb_name):
    """Process a single sold property listing URL using Selenium"""
    print(f"\n{'='*80}")
    print(f"Processing Property {index}/{total} ({suburb_name.upper()})")
    print(f"{'='*80}")
    print(f"URL: {url}")
    
    start_time = datetime.now()
    
    address = extract_address_from_url(url)
    print(f"Address: {address}")
    
    result = {
        "listing_url": url,
        "address": address,
        "suburb_scraped": suburb_name,
        "index": index,
        "success": False,
        "property_data": None,
        "error": None,
        "time_seconds": 0
    }
    
    try:
        # Navigate to listing URL
        print(f"→ Loading listing page...")
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
        
        html_file = os.path.join(html_dir, f"sold_{suburb_name}_{index}_{timestamp}_{safe_address}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓ Saved HTML: {html_file}")
        
        # Parse HTML for property data (including sale date)
        print(f"→ Parsing property data...")
        property_data = parse_sold_listing_html(html, address)
        property_data = clean_property_data(property_data)
        
        if property_data:
            property_data['listing_url'] = url
            property_data['suburb_scraped'] = suburb_name
            
            # Check if sale date was extracted
            if 'sale_date' in property_data:
                print(f"  ✓ Sale date: {property_data['sale_date']}")
            else:
                print(f"  ⚠ WARNING: No sale date found for this property")
            
            print(f"  ✓ Extracted property data:")
            for key, value in property_data.items():
                if key not in ['address', 'extraction_method', 'extraction_date', 'listing_url', 'suburb_scraped'] and value:
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
        return data['urls'], data.get('suburb', 'unknown')
    elif 'all_listing_urls' in data:
        return data['all_listing_urls'], data.get('suburb', 'unknown')
    elif isinstance(data, list):
        return data, 'unknown'
    else:
        raise ValueError("Unknown JSON format - expected 'urls' or 'all_listing_urls' field")


def find_latest_urls_file(suburb_name):
    """Find the most recent URLs file for a suburb"""
    pattern = f"listing_results_sold/sold_urls_{suburb_name}_*.json"
    files = glob.glob(pattern)
    
    if not files:
        return None
    
    # Return most recent file
    return max(files, key=os.path.getmtime)


def generate_report(results, suburb_name, output_file):
    """Generate comprehensive report"""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    # Count properties with sale dates
    with_sale_date = sum(1 for r in results if r["success"] and r["property_data"].get("sale_date"))
    
    total_time = sum(r["time_seconds"] for r in results)
    avg_time = total_time / total if total > 0 else 0
    
    report = {
        "scrape_info": {
            "timestamp": datetime.now().isoformat(),
            "suburb": suburb_name,
            "property_type": "SOLD",
            "total_properties": total,
            "successful": successful,
            "failed": failed,
            "with_sale_date": with_sale_date,
            "missing_sale_date": successful - with_sale_date,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            "sale_date_rate": f"{(with_sale_date/successful*100):.1f}%" if successful > 0 else "0%",
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
    parser = argparse.ArgumentParser(description="Process Domain.com.au sold property listing URLs")
    parser.add_argument('--suburb', required=True, help='Suburb name to process')
    parser.add_argument('--input', help='Input JSON file with property URLs (optional, will auto-find if not specified)')
    parser.add_argument('--limit', type=int, help='Limit number of properties to process (for testing)')
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("PROPERTY DETAIL SCRAPER - SOLD PROPERTIES (Last 6 Months)")
    print("=" * 80)
    print(f"\nSuburb: {args.suburb.upper()}")
    
    # Find or use specified input file
    if args.input:
        input_file = args.input
    else:
        input_file = find_latest_urls_file(args.suburb)
        if not input_file:
            print(f"\n✗ No URLs file found for suburb: {args.suburb}")
            print(f"  Expected pattern: listing_results_sold/sold_urls_{args.suburb}_*.json")
            print(f"\n  Run list_page_scraper_sold.py first to generate URLs")
            return 1
        print(f"\n→ Auto-detected URLs file: {input_file}")
    
    # Load URLs from input file
    if not os.path.exists(input_file):
        print(f"\n✗ Input file not found: {input_file}")
        return 1
    
    print(f"\n→ Loading property URLs from: {input_file}")
    urls, suburb_from_file = load_urls_from_file(input_file)
    
    # Use suburb from file if available, otherwise use command line arg
    suburb_name = suburb_from_file if suburb_from_file != 'unknown' else args.suburb
    
    # Apply limit if specified
    if args.limit:
        urls = urls[:args.limit]
        print(f"  ✓ Loaded {len(urls)} property URLs (limited from total)")
    else:
        print(f"  ✓ Loaded {len(urls)} property URLs")
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Create Selenium driver
    driver = create_driver()
    if not driver:
        print("\n✗ Cannot proceed without WebDriver")
        return 1
    
    try:
        print(f"\n{'='*80}")
        print(f"Starting property scraping for {suburb_name.upper()}...")
        print(f"{'='*80}\n")
        
        # Process each property
        results = []
        for i, url in enumerate(urls, 1):
            result = process_property_url(driver, url, i, len(urls), suburb_name)
            results.append(result)
            
            # Brief pause between properties
            if i < len(urls):
                print(f"\n→ Waiting {BETWEEN_PROPERTY_DELAY} seconds before next property...")
                time.sleep(BETWEEN_PROPERTY_DELAY)
        
        # Generate report
        print(f"\n{'='*80}")
        print(f"SCRAPING COMPLETE - {suburb_name.upper()}")
        print(f"{'='*80}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(RESULTS_DIR, f"sold_scrape_{suburb_name}_{timestamp}.json")
        report = generate_report(results, suburb_name, report_file)
        
        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"  Suburb: {suburb_name.upper()}")
        print(f"  Property type: SOLD")
        print(f"  Total properties: {report['scrape_info']['total_properties']}")
        print(f"  Successful: {report['scrape_info']['successful']}")
        print(f"  Failed: {report['scrape_info']['failed']}")
        print(f"  With sale date: {report['scrape_info']['with_sale_date']}")
        print(f"  Missing sale date: {report['scrape_info']['missing_sale_date']}")
        print(f"  Success rate: {report['scrape_info']['success_rate']}")
        print(f"  Sale date rate: {report['scrape_info']['sale_date_rate']}")
        print(f"  Total time: {report['scrape_info']['total_time_seconds']}s")
        print(f"  Average time: {report['scrape_info']['average_time_seconds']}s per property")
        print(f"\n📁 Report saved: {report_file}")
        
        if report['scrape_info']['missing_sale_date'] > 0:
            print(f"\n⚠ WARNING: {report['scrape_info']['missing_sale_date']} properties missing sale dates")
            print(f"  These properties will be skipped during MongoDB upload")
        
        print(f"\n💡 Next step: Upload to MongoDB:")
        print(f"   python3 mongodb_uploader_sold.py")
        
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
