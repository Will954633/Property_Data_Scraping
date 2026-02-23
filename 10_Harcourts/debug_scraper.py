"""
Debug script to inspect the Harcourts page structure
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

try:
    url = "https://propertyhub.harcourts.com.au/property-hub/listings/buy/?property-type=House&location=Robina-4023&include-suburb=1&category=buy&listing-category=residential"
    
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait for page to load
    print("Waiting 5 seconds for page to load...")
    time.sleep(5)
    
    # Save page source
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("✓ Page source saved to page_source.html")
    
    # Try different selectors to find property links
    selectors = [
        'a[href*="/property/"]',
        'a[href*="property"]',
        'a.property-card',
        '.property-listing a',
        'article a',
        '.card a',
        'a'
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"\nSelector '{selector}': Found {len(elements)} elements")
            
            if elements and len(elements) < 50:  # Only show details if reasonable number
                for i, elem in enumerate(elements[:5], 1):  # Show first 5
                    href = elem.get_attribute('href')
                    text = elem.text[:50] if elem.text else ''
                    print(f"  {i}. {href} - {text}")
        except Exception as e:
            print(f"  Error with selector '{selector}': {e}")
    
    # Check for common class names
    print("\n\nChecking common class patterns...")
    patterns = ['property', 'listing', 'card', 'result', 'item']
    for pattern in patterns:
        elements = driver.find_elements(By.CSS_SELECTOR, f'[class*="{pattern}"]')
        print(f"Elements with class containing '{pattern}': {len(elements)}")
    
finally:
    driver.quit()
    print("\n✓ Browser closed")
