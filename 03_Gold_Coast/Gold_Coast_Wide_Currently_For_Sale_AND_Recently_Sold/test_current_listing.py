#!/usr/bin/env python3
"""
Test Current Listing - Extract dateListed from active property
Last Updated: 31/01/2026, 10:54 am (Brisbane Time)
"""

import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup headless Chrome"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_date_listed(html):
    """Extract dateListed from HTML"""
    pattern = r'"dateListed"\s*:\s*"([^"]+)"'
    match = re.search(pattern, html)
    if match:
        timestamp = match.group(1)
        try:
            listed_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00').split('.')[0])
            days_on_market = (datetime.now() - listed_date).days
            return {
                'timestamp': timestamp,
                'date': listed_date.strftime('%d %B %Y'),
                'days': days_on_market
            }
        except:
            return None
    return None

print("="*80)
print("TESTING CURRENT LISTING - Varsity Lakes")
print("="*80)

driver = setup_driver()

try:
    # Get current listings
    print("\n→ Finding current listings in Varsity Lakes...")
    driver.get("https://www.domain.com.au/sale/varsity-lakes-qld-4227/?excludeunderoffer=1&ssubs=0")
    time.sleep(5)
    
    html = driver.page_source
    
    # Find first property URL
    url_pattern = r'href="(/[\w-]+-\d{7,10})"'
    matches = re.findall(url_pattern, html)
    
    if matches:
        property_url = f"https://www.domain.com.au{matches[0]}"
        print(f"  ✓ Found listing: {property_url}")
        
        # Load property page
        print(f"\n→ Loading property page...")
        driver.get(property_url)
        time.sleep(5)
        
        html = driver.page_source
        
        # Extract dateListed
        print(f"\n→ Extracting dateListed...")
        result = extract_date_listed(html)
        
        if result:
            print(f"\n{'='*80}")
            print("✅ SUCCESS - Found dateListed on CURRENT listing!")
            print(f"{'='*80}")
            print(f"\n📍 Property: {property_url}")
            print(f"\n📅 Listing Data:")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  Date Listed: {result['date']}")
            print(f"  Days on Market: {result['days']} days")
            print(f"\n{'='*80}")
        else:
            print("\n⚠️ Could not extract dateListed from this property")
    else:
        print("  ⚠️ No listings found")
        
finally:
    driver.quit()
    print("\n✓ Browser closed")
