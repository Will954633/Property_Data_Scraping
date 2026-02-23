#!/usr/bin/env python3
"""
Debug script to find description and agent selectors
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
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
    # Execute CDP commands
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    url = "https://propertyhub.harcourts.com.au/listing/r2-4792933-925-medinah-avenue-robina-qld-4226"
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait for JavaScript to render
    time.sleep(6)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    print("\n=== LOOKING FOR DESCRIPTION ===")
    
    # Look for divs with descriptions
    divs_with_text = soup.find_all('div')
    
    description_candidates = []
    for div in divs_with_text:
        div_text = div.get_text(strip=True)
        # Description typically starts with property details, >500 chars
        if len(div_text) > 500:
            div_class = div.get('class', [])
            div_id = div.get('id', '')
            
            # Skip navigation, headers, footers
            if not any(skip in str(div_class).lower() + div_id.lower() for skip in ['nav', 'header', 'footer', 'menu']):
                # Check if contains property keywords
                if any(kw in div_text.lower() for kw in ['bedroom', 'bathroom', 'kitchen', 'living', 'features']):
                    description_candidates.append({
                        'class': div_class,
                        'id': div_id,
                        'length': len(div_text),
                        'preview': div_text[:200]
                    })
    
    print(f"Found {len(description_candidates)} description candidates:")
    for idx, cand in enumerate(description_candidates[:3], 1):
        print(f"\n  Candidate {idx}:")
        print(f"    Class: {cand['class']}")
        print(f"    ID: {cand['id']}")
        print(f"    Length: {cand['length']} chars")
        print(f"    Preview: {cand['preview']}...")
    
    print("\n=== LOOKING FOR AGENTS ===")
    
    # Look for agent names
    agent_keywords = ['Isaac Genc', 'Frank Kasikci', 'Leanne Jenke']
    
    for keyword in agent_keywords:
        elements_with_name = soup.find_all(string=lambda text: text and keyword in text)
        if elements_with_name:
            print(f"\nFound '{keyword}':")
            for elem in elements_with_name[:2]:
                parent = elem.parent
                print(f"  Tag: {parent.name}")
                print(f"  Class: {parent.get('class', [])}")
                print(f"  Text: {elem.strip()}")
    
    # Also look for divs/sections with 'agent' in class
    print("\n=== Elements with 'agent' in class ===")
    agent_containers = soup.find_all(['div', 'section'], class_=lambda x: x and 'agent' in x.lower())
    for container in agent_containers[:3]:
        print(f"\nTag: {container.name}")
        print(f"Class: {container.get('class')}")
        print(f"Text preview: {container.get_text(strip=True)[:150]}")

finally:
    driver.quit()
    print("\n\nDriver closed")
