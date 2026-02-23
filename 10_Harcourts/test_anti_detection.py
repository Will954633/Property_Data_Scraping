#!/usr/bin/env python3
"""
Test anti-detection measures
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Setup Chrome options with anti-detection
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=chrome_options)

try:
    # Execute CDP commands to further hide automation
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    url = "https://propertyhub.harcourts.com.au/listing/r2-4792933-925-medinah-avenue-robina-qld-4226"
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait for page to load and JavaScript to render
    time.sleep(8)
    
    # Check if we got blocked
    page_text = driver.find_element(By.TAG_NAME, "body").text
    
    if '403' in page_text or 'ERROR' in page_text:
        print("\n✗ BLOCKED - Got 403 error")
        print(page_text[:200])
    else:
        print("\n✓ SUCCESS - Page loaded")
        
        # Try to find property attributes
        try:
            summary_ul = driver.find_element(By.CSS_SELECTOR, "ul.summary")
            print(f"✓ Found ul.summary")
            
            lis = summary_ul.find_elements(By.TAG_NAME, "li")
            print(f"✓ Found {len(lis)} property attributes")
            
            for idx, li in enumerate(lis, 1):
                print(f"\n  LI {idx}:")
                print(f"    Text: '{li.text}'")
                print(f"    HTML: {li.get_attribute('outerHTML')[:300]}")
                
                # Try to find spans within LI
                spans = li.find_elements(By.TAG_NAME, "span")
                for span_idx, span in enumerate(spans, 1):
                    print(f"    Span {span_idx}: '{span.text}' | innerHTML: {span.get_attribute('innerHTML')[:100]}")
                
                # Try to find SVG icons
                svgs = li.find_elements(By.TAG_NAME, "svg")
                print(f"    SVGs found: {len(svgs)}")
                
        except Exception as e:
            print(f"✗ Could not find ul.summary: {e}")
            
            # Try broader search
            print("\nSearching for any ul elements...")
            uls = driver.find_elements(By.TAG_NAME, "ul")
            print(f"Found {len(uls)} ul elements total")

finally:
    driver.quit()
    print("\nDriver closed")
