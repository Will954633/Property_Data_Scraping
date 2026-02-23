#!/usr/bin/env python3
"""
Debug script to find the car spaces selector
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

try:
    url = "https://propertyhub.harcourts.com.au/listing/r2-4792933-925-medinah-avenue-robina-qld-4226"
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait for page to load
    time.sleep(5)
    
    # Find the attributes section
    print("\n=== Looking for property attributes ===")
    
    # First, look for ANY ul elements
    try:
        all_uls = driver.find_elements(By.TAG_NAME, "ul")
        print(f"Found {len(all_uls)} total UL elements on page")
        
        for idx, ul in enumerate(all_uls[:10]):  # Check first 10
            ul_class = ul.get_attribute('class')
            ul_text = ul.text.strip()[:100]
            print(f"\nUL {idx+1}:")
            print(f"  Class: {ul_class}")
            print(f"  Text preview: {ul_text}")
            
            # Check if this UL contains bed/bath/car info
            if any(keyword in ul_text.lower() for keyword in ['bed', 'bath', 'car', 'garage']):
                print(f"  ^^^ THIS UL MIGHT CONTAIN PROPERTY ATTRIBUTES")
                lis = ul.find_elements(By.TAG_NAME, "li")
                print(f"  Contains {len(lis)} LI elements")
                for li_idx, li in enumerate(lis):
                    print(f"    LI {li_idx+1}: {li.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Try to find the ul element with property attributes using simpler selector
    print("\n=== Trying simpler UL selector ===")
    try:
        attributes_ul = driver.find_element(By.CSS_SELECTOR, "ul.summary")
        print(f"Found UL with class 'summary'")
        
        # Get all li elements  
        li_elements = attributes_ul.find_elements(By.TAG_NAME, "li")
        print(f"\nFound {len(li_elements)} li elements:")
        
        for i, li in enumerate(li_elements):
            print(f"\n--- LI {i+1} ---")
            print(f"Text: {li.text}")
            print(f"HTML: {li.get_attribute('outerHTML')[:200]}")
            
            # Look for spans
            spans = li.find_elements(By.TAG_NAME, "span")
            for j, span in enumerate(spans):
                print(f"  Span {j+1}: {span.text} | Class: {span.get_attribute('class')}")
                
    except Exception as e:
        print(f"Error finding UL: {e}")
    
    # Also try alternative selectors
    print("\n=== Trying alternative selectors ===")
    
    selectors = [
        "ul.property-attributes li",
        ".property-attributes li",
        "li[class*='car']",
        "li[class*='parking']",
        "span[class*='car']",
        "span[class*='parking']"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"\nSelector '{selector}' found {len(elements)} elements:")
                for elem in elements[:3]:  # Show first 3
                    print(f"  Text: {elem.text}")
        except:
            pass

finally:
    driver.quit()
    print("\nDriver closed")
