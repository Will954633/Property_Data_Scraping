#!/usr/bin/env python3
"""
Test different approaches to extract property timeline data
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

url = "https://www.domain.com.au/property-profile/11-matina-street-biggera-waters-qld-4216"
driver = setup_driver()

try:
    print(f"Loading: {url}\n")
    driver.get(url)
    time.sleep(5)
    
    print("="*80)
    print("APPROACH 1: Extract from full page body text")
    print("="*80)
    
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    
    # Check if timeline data is in the text
    if 'Jul' in body_text and '2024' in body_text and 'RENTED' in body_text:
        print("✓ Timeline text IS present in page body\n")
        
        # Extract timeline section
        # Look for pattern: "Month Year TYPE $price"
        timeline_pattern = r'([A-Z][a-z]{2})\s*(\d{4})\s*(SOLD|RENTED)\s*\$([^\s]+)'
        matches = re.findall(timeline_pattern, body_text)
        
        print(f"Found {len(matches)} timeline entries using regex:")
        for i, match in enumerate(matches, 1):
            month, year, event_type, price = match
            print(f"  {i}. {month} {year} - {event_type} - ${price}")
    else:
        print("✗ Timeline text NOT found\n")
    
    print("\n" + "="*80)
    print("APPROACH 2: Look for specific elements")
    print("="*80)
    
    # Try finding elements with SOLD/RENTED
    sold_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'SOLD')]")
    rented_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'RENTED')]")
    
    print(f"Elements containing 'SOLD': {len(sold_elements)}")
    print(f"Elements containing 'RENTED': {len(rented_elements)}")
    
    if sold_elements or rented_elements:
        all_events = sold_elements + rented_elements
        print(f"\nFirst 5 event elements:")
        for i, elem in enumerate(all_events[:5], 1):
            text = elem.text[:100] if elem.text else "(empty)"
            parent_tag = elem.find_element(By.XPATH, "./..").tag_name
            print(f"  {i}. Tag: {elem.tag_name}, Parent: {parent_tag}")
            print(f"     Text: {text}")
    
    print("\n" + "="*80)
    print("APPROACH 3: Scroll down and wait")
    print("="*80)
    
    # Scroll down to load more content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(2)
    
    # Re-check for timeline elements
    sold_elements2 = driver.find_elements(By.XPATH, "//*[contains(text(), 'SOLD')]")
    rented_elements2 = driver.find_elements(By.XPATH, "//*[contains(text(), 'RENTED')]")
    
    print(f"After scroll - SOLD: {len(sold_elements2)}, RENTED: {len(rented_elements2)}")
    
    print("\n" + "="*80)
    print("APPROACH 4: Look for list structure")
    print("="*80)
    
    # Find all list items
    all_li = driver.find_elements(By.TAG_NAME, 'li')
    print(f"Total <li> elements: {len(all_li)}")
    
    # Filter for timeline-related items
    timeline_li = []
    for li in all_li:
        text = li.text
        if text and ('SOLD' in text or 'RENTED' in text) and len(text) > 20:
            timeline_li.append(li)
    
    print(f"Timeline-related <li> elements: {len(timeline_li)}")
    if timeline_li:
        print("\nFirst timeline entry:")
        print(f"  Text: {timeline_li[0].text[:200]}")

finally:
    driver.quit()
    print("\n" + "="*80)
    print("Test complete")
    print("="*80)
