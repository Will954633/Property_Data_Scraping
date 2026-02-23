#!/usr/bin/env python3
"""
Test Script: Single Property Scraper
Tests the sold properties scraper on a single property to verify functionality
"""

import time
import os
import json
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"ERROR: Required package not installed: {e}")
    print("Please install with:")
    print("  pip3 install selenium webdriver-manager")
    exit(1)

from html_parser_sold import parse_sold_listing_html, clean_property_data, is_within_6_months
from bs4 import BeautifulSoup
import re

# Test URL - List page to extract a property from
LIST_URL = "https://www.domain.com.au/sold-listings/robina-qld-4226/house/?excludepricewithheld=1"

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


def extract_first_property_url(driver):
    """Extract the first property URL from the list page"""
    print("→ Loading list page to find a property...")
    driver.get(LIST_URL)
    time.sleep(5)
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find property links - Domain uses data-testid for property cards
    property_links = soup.find_all('a', attrs={'data-testid': re.compile(r'listing-card-wrapper')})
    
    if not property_links:
        # Fallback: look for any links to sold property pages
        property_links = soup.find_all('a', href=re.compile(r'/\d+-[a-z-]+-qld-\d+'))
    
    if property_links:
        # Get the first property URL
        first_link = property_links[0]
        href = first_link.get('href', '')
        
        # Make it absolute if needed
        if href.startswith('/'):
            property_url = f"https://www.domain.com.au{href}"
        else:
            property_url = href
        
        # Extract address from the link text or nearby elements
        address_elem = first_link.find(attrs={'data-testid': 'address-line1'})
        if address_elem:
            address = address_elem.get_text(strip=True)
        else:
            # Try to extract from URL
            match = re.search(r'/(\d+-.+?-qld-\d+)', href)
            if match:
                address = match.group(1).replace('-', ' ').title()
            else:
                address = "Unknown Address"
        
        print(f"  ✓ Found property: {address}")
        print(f"  ✓ URL: {property_url}")
        
        return property_url, address
    else:
        print("  ✗ No property links found on list page")
        return None, None


def test_single_property():
    """Test scraping a single sold property"""
    print("\n" + "=" * 80)
    print("SOLD PROPERTY SCRAPER - SINGLE PROPERTY TEST")
    print("=" * 80)
    print(f"\nList URL: {LIST_URL}")
    print(f"Expected: Property sold in last 6 months with complete data\n")
    
    # Create driver
    driver = create_driver()
    if not driver:
        print("\n✗ Cannot proceed without WebDriver")
        return 1
    
    try:
        # First, extract a property URL from the list page
        property_url, address = extract_first_property_url(driver)
        
        if not property_url:
            print("\n✗ Could not find a property to test")
            return 1
        
        # Navigate to the individual property page
        print(f"\n→ Loading individual property page...")
        driver.get(property_url)
        time.sleep(5)
        
        # Get HTML
        print("→ Extracting HTML...")
        html = driver.page_source
        print(f"  ✓ Extracted {len(html):,} characters")
        
        # Save HTML for inspection
        os.makedirs("test_output", exist_ok=True)
        html_file = "test_output/test_property.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓ Saved HTML: {html_file}")
        
        # Parse property data
        print("\n→ Parsing property data...")
        property_data = parse_sold_listing_html(html, address)
        property_data = clean_property_data(property_data)
        
        # Add URL
        property_data['listing_url'] = property_url
        property_data['suburb_scraped'] = 'robina'
        
        # Save parsed data
        data_file = "test_output/test_property_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(property_data, f, indent=2)
        print(f"\n  ✓ Saved parsed data: {data_file}")
        
        # Analyze results
        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        
        # Check critical fields
        critical_fields = {
            'sale_date': 'Sale Date',
            'sale_price': 'Sale Price',
            'address': 'Address',
            'bedrooms': 'Bedrooms',
            'bathrooms': 'Bathrooms',
            'property_type': 'Property Type'
        }
        
        print("\n✓ CRITICAL FIELDS:")
        all_critical_present = True
        for field, label in critical_fields.items():
            value = property_data.get(field)
            if value:
                print(f"  ✓ {label}: {value}")
            else:
                print(f"  ✗ {label}: MISSING")
                all_critical_present = False
        
        # Check sale date validity
        sale_date = property_data.get('sale_date')
        if sale_date:
            within_6_months = is_within_6_months(sale_date)
            print(f"\n✓ SALE DATE VALIDATION:")
            print(f"  Sale date: {sale_date}")
            print(f"  Within 6 months: {'YES ✓' if within_6_months else 'NO ✗'}")
            
            if not within_6_months:
                print(f"  ⚠ WARNING: This property is >6 months old")
                print(f"  ⚠ Stop condition A would trigger after 3 consecutive like this")
        else:
            print(f"\n✗ SALE DATE VALIDATION:")
            print(f"  ✗ No sale date found - this is a CRITICAL ERROR")
        
        # Check optional fields
        optional_fields = {
            'carspaces': 'Car Spaces',
            'land_size_sqm': 'Land Size',
            'property_images': 'Property Images',
            'floor_plans': 'Floor Plans',
            'features': 'Features',
            'agents_description': 'Description'
        }
        
        print(f"\n✓ OPTIONAL FIELDS:")
        for field, label in optional_fields.items():
            value = property_data.get(field)
            if value:
                if isinstance(value, list):
                    print(f"  ✓ {label}: {len(value)} items")
                elif isinstance(value, str) and len(value) > 60:
                    print(f"  ✓ {label}: {len(value)} chars")
                else:
                    print(f"  ✓ {label}: {value}")
            else:
                print(f"  - {label}: Not found")
        
        # Overall assessment
        print("\n" + "=" * 80)
        print("OVERALL ASSESSMENT")
        print("=" * 80)
        
        if all_critical_present and sale_date:
            print("\n✅ TEST PASSED")
            print("  • All critical fields extracted successfully")
            print("  • Sale date found and parsed correctly")
            print("  • System is ready for production use")
            
            if within_6_months:
                print("  • Property is within 6 months (would be inserted)")
            else:
                print("  • Property is >6 months old (would count toward stop condition)")
            
            return 0
        else:
            print("\n⚠ TEST FAILED")
            if not all_critical_present:
                print("  • Some critical fields are missing")
            if not sale_date:
                print("  • Sale date extraction failed (CRITICAL)")
            print("  • Review html_parser_sold.py extraction methods")
            print("  • Check test_output/test_property.html for HTML structure")
            
            return 1
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if driver:
            print("\n→ Closing browser...")
            driver.quit()
            print("  ✓ Browser closed")


if __name__ == "__main__":
    exit(test_single_property())
