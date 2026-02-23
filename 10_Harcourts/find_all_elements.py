#!/usr/bin/env python3
"""
Comprehensive debug script to find car spaces and all property attributes
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('window-size=1920,1080')

driver = webdriver.Chrome(options=chrome_options)

try:
    url = "https://propertyhub.harcourts.com.au/listing/r2-4792933-925-medinah-avenue-robina-qld-4226"
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait for dynamic content
    time.sleep(7)
    
    # Save page source to inspect
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("Saved page source to page_source.html")
    
    # Search for any element containing "bed" or "bath" or "car"
    print("\n=== Searching for elements with bed/bath/car text ===")
    
    keywords = ['6', '4', '5', 'bed', 'bath', 'car', 'garage', 'parking']
    
    for keyword in keywords:
        try:
            # Use XPath to find any element containing the keyword
            xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')]"
            elements = driver.find_elements(By.XPATH, xpath)
            
            if elements:
                print(f"\nKeyword '{keyword}' found in {len(elements)} elements:")
                for elem in elements[:5]:  # Show first 5
                    tag = elem.tag_name
                    classes = elem.get_attribute('class')
                    text = elem.text.strip()[:80]
                    if text:  # Only show elements with text
                        print(f"  <{tag}> class='{classes}': {text}")
        except:
            pass
    
    # Look for sections
    print("\n=== Looking for SECTION elements ===")
    sections = driver.find_elements(By.TAG_NAME, "section")
    print(f"Found {len(sections)} sections")
    
    for idx, section in enumerate(sections[:5]):
        classes = section.get_attribute('class')
        text_preview = section.text.strip()[:100]
        print(f"\nSection {idx+1}:")
        print(f"  Classes: {classes}")
        print(f"  Text preview: {text_preview}")
        
        # Check for property attributes
        if any(kw in text_preview.lower() for kw in ['bed', 'bath', 'car', 'medinah']):
            print("  ^^^ CONTAINS PROPERTY INFO")

finally:
    driver.quit()
    print("\nDriver closed")
