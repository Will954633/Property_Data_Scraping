#!/usr/bin/env python3
"""
Test Run - Small Sample (5-10 properties)
Last Edit: 13/02/2026, 11:53 AM (Thursday) — Brisbane Time

Purpose: Test the scraper with a small sample before full production run
- Scrapes 1 page from Carrara (~10 properties)
- Saves all data to local JSON files
- Does NOT upload to MongoDB
- Allows manual inspection of data quality

Usage:
    python3 test_run_small.py
"""

import sys
import os

# Add current directory to path so we can import the scrapers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from list_page_scraper_12months import create_driver, scrape_list_page
from html_parser_sold import parse_sold_listing_html
import json
from datetime import datetime
import time

def main():
    print("="*80)
    print("TEST RUN - SMALL SAMPLE (5-10 PROPERTIES)")
    print("="*80)
    print("\nThis test will:")
    print("  1. Scrape 1 page from Carrara (~10 property URLs)")
    print("  2. Scrape details for each property")
    print("  3. Save all data to local JSON files")
    print("  4. NOT upload to MongoDB")
    print("\nYou can then inspect the JSON files before running the full scraper.\n")
    
    # Create output directory
    test_output_dir = "test_output"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Step 1: Scrape list page
    print("\n" + "="*80)
    print("STEP 1: Scraping Carrara list page (page 1)")
    print("="*80)
    
    driver = create_driver()
    if not driver:
        print("✗ Failed to create WebDriver")
        return 1
    
    try:
        # Scrape first page of Carrara
        carrara_url = "https://www.domain.com.au/sold-listings/carrara-qld-4211/house/?excludepricewithheld=1"
        result = scrape_list_page(driver, carrara_url, 1, "carrara")
        
        if not result["success"]:
            print(f"✗ Failed to scrape list page: {result.get('error', 'Unknown error')}")
            return 1
        
        property_urls = result["listing_urls"]
        print(f"\n✓ Found {len(property_urls)} property URLs")
        
        # Save URLs to file
        urls_file = os.path.join(test_output_dir, "test_property_urls.json")
        with open(urls_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "suburb": "carrara",
                "page": 1,
                "count": len(property_urls),
                "urls": property_urls
            }, f, indent=2)
        print(f"✓ Saved URLs to: {urls_file}")
        
        # Step 2: Scrape property details
        print("\n" + "="*80)
        print(f"STEP 2: Scraping details for {len(property_urls)} properties")
        print("="*80)
        
        properties_data = []
        
        for i, url in enumerate(property_urls, 1):
            print(f"\n[{i}/{len(property_urls)}] Scraping: {url}")
            
            try:
                # Navigate to property page
                driver.get(url)
                time.sleep(3)  # Wait for page to load
                
                # Get HTML
                html = driver.page_source
                
                # Extract address from URL for parser
                address = url.split('/')[-1].replace('-', ' ').title()
                
                # Parse property data
                property_data = parse_sold_listing_html(html, address)
                
                if property_data:
                    properties_data.append({
                        "url": url,
                        "success": True,
                        "data": property_data
                    })
                    print(f"  ✓ Success: {property_data.get('address', 'Unknown address')}")
                    print(f"    Sale date: {property_data.get('sale_date', 'N/A')}")
                    print(f"    Sale price: ${property_data.get('sale_price', 'N/A'):,}" if property_data.get('sale_price') else "    Sale price: N/A")
                    print(f"    Beds: {property_data.get('bedrooms', 'N/A')}, Baths: {property_data.get('bathrooms', 'N/A')}, Cars: {property_data.get('car_spaces', 'N/A')}")
                else:
                    properties_data.append({
                        "url": url,
                        "success": False,
                        "error": "Failed to parse property data"
                    })
                    print(f"  ✗ Failed to parse property data")
                
            except Exception as e:
                properties_data.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
                print(f"  ✗ Error: {e}")
            
            # Brief pause between properties
            if i < len(property_urls):
                time.sleep(2)
        
        # Step 3: Save results
        print("\n" + "="*80)
        print("STEP 3: Saving results")
        print("="*80)
        
        # Save detailed results
        results_file = os.path.join(test_output_dir, "test_properties_detailed.json")
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "suburb": "carrara",
                "total_properties": len(property_urls),
                "successful": sum(1 for p in properties_data if p["success"]),
                "failed": sum(1 for p in properties_data if not p["success"]),
                "properties": properties_data
            }, f, indent=2)
        print(f"✓ Saved detailed results to: {results_file}")
        
        # Save summary
        summary_file = os.path.join(test_output_dir, "test_summary.txt")
        with open(summary_file, 'w') as f:
            f.write("TEST RUN SUMMARY\n")
            f.write("="*80 + "\n\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Suburb: Carrara\n")
            f.write(f"Total properties: {len(property_urls)}\n")
            f.write(f"Successful: {sum(1 for p in properties_data if p['success'])}\n")
            f.write(f"Failed: {sum(1 for p in properties_data if not p['success'])}\n\n")
            
            f.write("SUCCESSFUL PROPERTIES:\n")
            f.write("-"*80 + "\n")
            for p in properties_data:
                if p["success"]:
                    data = p["data"]
                    f.write(f"\nAddress: {data.get('address', 'N/A')}\n")
                    f.write(f"Sale Date: {data.get('sale_date', 'N/A')}\n")
                    f.write(f"Sale Price: ${data.get('sale_price', 'N/A'):,}\n" if data.get('sale_price') else "Sale Price: N/A\n")
                    f.write(f"Beds: {data.get('bedrooms', 'N/A')}, Baths: {data.get('bathrooms', 'N/A')}, Cars: {data.get('car_spaces', 'N/A')}\n")
                    f.write(f"Lot Size: {data.get('lot_size', 'N/A')}\n")
                    f.write(f"Floor Area: {data.get('floor_area', 'N/A')}\n")
                    f.write(f"Features: {len(data.get('features', []))} items\n")
                    f.write(f"Images: {len(data.get('images', []))} images\n")
                    f.write(f"Floor Plans: {len(data.get('floor_plans', []))} plans\n")
            
            if any(not p["success"] for p in properties_data):
                f.write("\n\nFAILED PROPERTIES:\n")
                f.write("-"*80 + "\n")
                for p in properties_data:
                    if not p["success"]:
                        f.write(f"\nURL: {p['url']}\n")
                        f.write(f"Error: {p.get('error', 'Unknown error')}\n")
        
        print(f"✓ Saved summary to: {summary_file}")
        
        # Print final summary
        print("\n" + "="*80)
        print("TEST RUN COMPLETE")
        print("="*80)
        print(f"\n📊 RESULTS:")
        print(f"  Total properties: {len(property_urls)}")
        print(f"  Successful: {sum(1 for p in properties_data if p['success'])}")
        print(f"  Failed: {sum(1 for p in properties_data if not p['success'])}")
        
        print(f"\n📁 OUTPUT FILES:")
        print(f"  • URLs: {urls_file}")
        print(f"  • Detailed data: {results_file}")
        print(f"  • Summary: {summary_file}")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"  1. Review the files in {test_output_dir}/")
        print(f"  2. Check data quality (sale dates, prices, features)")
        print(f"  3. If satisfied, run the full scraper")
        print(f"  4. If issues found, we can adjust the scraper")
        
        print("\n" + "="*80 + "\n")
        
        return 0
        
    finally:
        if driver:
            print("→ Closing browser...")
            driver.quit()
            print("  ✓ Browser closed\n")

if __name__ == "__main__":
    sys.exit(main())
