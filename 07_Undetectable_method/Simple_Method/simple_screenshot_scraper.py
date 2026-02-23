#!/usr/bin/env python3
"""
Simple screenshot scraper for realestate.com.au
Connects to your existing Chrome browser and takes screenshots while scrolling
"""

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Target URL
TARGET_URL = "https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-1?includeSurrounding=false&activeSort=relevance&sourcePage=rea:homepage&sourceElement=suburb-select:recent%20searches%20tiles"

# Create screenshots directory
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def connect_to_existing_chrome():
    """
    Connect to existing Chrome browser using remote debugging
    
    IMPORTANT: Before running this script, start Chrome with remote debugging:
    
    On macOS, run this in terminal:
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev_profile"
    
    Or if you want to use your existing profile:
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
    """
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✓ Successfully connected to existing Chrome browser")
        return driver
    except Exception as e:
        print(f"✗ Failed to connect to Chrome: {e}")
        print("\nPlease start Chrome with remote debugging enabled:")
        print("Run this command in a new terminal:")
        print("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        return None

def scroll_and_screenshot(driver, url):
    """
    Navigate to URL, scroll down, and take screenshots of each section
    """
    print(f"\n→ Navigating to: {url}")
    driver.get(url)
    
    # Wait for page to load
    time.sleep(3)
    print("✓ Page loaded")
    
    # Get total page height
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    
    print(f"\nPage dimensions:")
    print(f"  Total height: {total_height}px")
    print(f"  Viewport height: {viewport_height}px")
    
    # Calculate number of scrolls needed
    num_scrolls = int(total_height / viewport_height) + 1
    print(f"  Number of screenshots needed: {num_scrolls}")
    
    screenshots = []
    scroll_position = 0
    
    print("\n📸 Taking screenshots...")
    
    for i in range(num_scrolls):
        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SCREENSHOT_DIR}/section_{i+1:02d}_{timestamp}.png"
        
        driver.save_screenshot(filename)
        print(f"  ✓ Screenshot {i+1}/{num_scrolls}: {filename}")
        screenshots.append(filename)
        
        # Scroll down
        if i < num_scrolls - 1:  # Don't scroll after last screenshot
            scroll_position += viewport_height
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(1)  # Wait for content to load
    
    print(f"\n✓ Completed! {len(screenshots)} screenshots saved to {SCREENSHOT_DIR}/")
    return screenshots

def main():
    """Main function"""
    print("=" * 60)
    print("SIMPLE SCREENSHOT SCRAPER")
    print("=" * 60)
    
    # Connect to existing Chrome
    driver = connect_to_existing_chrome()
    if not driver:
        return
    
    try:
        # Scroll and screenshot
        screenshots = scroll_and_screenshot(driver, TARGET_URL)
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Screenshots saved: {len(screenshots)}")
        print(f"Location: {os.path.abspath(SCREENSHOT_DIR)}/")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        # Don't close the browser - leave it open for the user
        print("\n✓ Browser left open")

if __name__ == "__main__":
    main()
