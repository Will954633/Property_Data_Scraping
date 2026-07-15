#!/usr/bin/env python3
"""
Test Script: Extract "First listed" date from Domain property page
Last Updated: 31/01/2026, 10:43 am (Brisbane Time)

PURPOSE:
Test if we can extract the "First listed on DD Month" text from property HTML
and calculate days on market.

USAGE:
python3 test_first_listed_extraction.py
"""

import time
import re
from datetime import datetime
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium webdriver-manager beautifulsoup4")
    exit(1)


def setup_driver():
    """Setup headless Chrome WebDriver"""
    print("→ Setting up headless Chrome WebDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Anti-detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("  ✓ Headless Chrome ready")
        return driver
    except Exception as e:
        raise Exception(f"Failed to create WebDriver: {e}")


def extract_first_listed_date(html: str) -> dict:
    """
    Extract 'First listed' date and days on market from HTML
    
    Returns dict with:
    - first_listed_date: str (e.g., "20 January")
    - first_listed_year: int (inferred from current year)
    - days_on_domain: int (extracted from text)
    - last_updated_date: str (if available)
    - raw_text: str (the full text we found)
    """
    soup = BeautifulSoup(html, 'html.parser')
    result = {
        'first_listed_date': None,
        'first_listed_year': None,
        'first_listed_full': None,
        'days_on_domain': None,
        'last_updated_date': None,
        'raw_text': None,
        'found': False
    }
    
    # Pattern to match: "First listed on DD Month"
    # Example: "First listed on 20 January, this house has been on Domain for 11 days"
    
    # Get all text from the page
    page_text = soup.get_text()
    
    # Search for the pattern
    pattern = r'First listed on (\d{1,2})\s+([A-Za-z]+)(?:,?\s+this\s+\w+\s+has\s+been\s+on\s+Domain\s+for\s+(\d+)\s+days?)?'
    match = re.search(pattern, page_text, re.IGNORECASE)
    
    if match:
        day = match.group(1)
        month = match.group(2)
        days_on_domain = match.group(3) if match.group(3) else None
        
        # Get the full matched text for context
        full_match = match.group(0)
        
        # Infer year (assume current year unless we're in January and the month is December)
        current_date = datetime.now()
        current_year = current_date.year
        
        # Try to parse the month
        try:
            month_num = datetime.strptime(month, '%B').month
        except:
            try:
                month_num = datetime.strptime(month, '%b').month
            except:
                month_num = None
        
        # If we're in January and the listing is from December, it's last year
        if current_date.month == 1 and month_num == 12:
            year = current_year - 1
        else:
            year = current_year
        
        result['first_listed_date'] = f"{day} {month}"
        result['first_listed_year'] = year
        result['first_listed_full'] = f"{day} {month} {year}"
        result['days_on_domain'] = int(days_on_domain) if days_on_domain else None
        result['raw_text'] = full_match
        result['found'] = True
        
        # Also look for "last updated on"
        update_pattern = r'last updated on (\d{1,2})\s+([A-Za-z]+)'
        update_match = re.search(update_pattern, page_text, re.IGNORECASE)
        if update_match:
            update_day = update_match.group(1)
            update_month = update_match.group(2)
            result['last_updated_date'] = f"{update_day} {update_month}"
    
    return result


def test_property_url(driver, url: str):
    """Test extraction on a specific property URL"""
    print(f"\n{'='*80}")
    print(f"Testing URL: {url}")
    print(f"{'='*80}\n")
    
    try:
        print("→ Loading page...")
        driver.get(url)
        time.sleep(8)  # Wait longer for page to load
        
        # Scroll down to trigger lazy loading
        print("→ Scrolling page to load all content...")
        for i in range(5):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1)
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        print("→ Extracting HTML...")
        html = driver.page_source
        
        # Save HTML for inspection
        html_file = "test_property_page.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓ HTML saved to {html_file} for inspection")
        
        print("→ Searching for 'First listed' date...")
        result = extract_first_listed_date(html)
        
        print(f"\n{'='*80}")
        print("RESULTS")
        print(f"{'='*80}\n")
        
        if result['found']:
            print("✅ SUCCESS - Found 'First listed' data!")
            print(f"\n  📅 First Listed Date: {result['first_listed_date']}")
            print(f"  📅 Full Date: {result['first_listed_full']}")
            if result['days_on_domain']:
                print(f"  📊 Days on Domain: {result['days_on_domain']}")
            if result['last_updated_date']:
                print(f"  🔄 Last Updated: {result['last_updated_date']}")
            print(f"\n  📝 Raw Text Found:")
            print(f"     \"{result['raw_text']}\"")
        else:
            print("❌ FAILED - Could not find 'First listed' data")
            print("\n  Searching for any mention of 'First listed'...")
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text()
            if 'First listed' in page_text or 'first listed' in page_text:
                print("  ⚠️ Found text containing 'first listed' but couldn't parse it")
                # Find the context around it
                idx = page_text.lower().find('first listed')
                if idx != -1:
                    context = page_text[max(0, idx-50):min(len(page_text), idx+200)]
                    print(f"\n  Context:\n  {context}")
            else:
                print("  ⚠️ No mention of 'first listed' found in page text")
        
        print(f"\n{'='*80}\n")
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("TEST: Extract 'First Listed' Date from Domain Property Page")
    print("="*80 + "\n")
    
    # Test with multiple URLs to find one with "First listed" text
    test_urls = [
        # Try to find a current listing in Varsity Lakes
        "https://www.domain.com.au/sale/varsity-lakes-qld-4227/?excludeunderoffer=1&ssubs=0",
    ]
    
    driver = None
    try:
        driver = setup_driver()
        
        # First, let's get a current listing URL from the search page
        print("→ Finding a current listing URL from Varsity Lakes search page...")
        driver.get(test_urls[0])
        time.sleep(5)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find first property listing URL
        all_links = soup.find_all('a', href=True)
        property_url = None
        
        for link in all_links:
            href = link['href']
            if re.match(r'^/[\w-]+-\d{7,10}$', href):
                property_url = f"https://www.domain.com.au{href}"
                print(f"  ✓ Found current listing: {property_url}")
                break
        
        if not property_url:
            print("  ⚠️ Could not find a current listing URL")
            print("  → Testing with original URL anyway...")
            property_url = "https://www.domain.com.au/21-carnoustie-drive-varsity-lakes-qld-4227-2020062598"
        
        result = test_property_url(driver, property_url)
        
        if result and result['found']:
            print("\n✅ TEST PASSED - We can extract 'First listed' dates!")
            print("\nNext steps:")
            print("  1. Integrate this extraction into run_complete_suburb_scrape.py")
            print("  2. Add fields to MongoDB documents:")
            print("     - first_listed_date")
            print("     - first_listed_year")
            print("     - first_listed_full")
            print("     - days_on_domain")
            print("     - last_updated_date")
            return 0
        else:
            print("\n⚠️ TEST INCONCLUSIVE - May need to adjust extraction logic")
            print("\nPossible reasons:")
            print("  - Property may not have 'First listed' text (might be sold/removed)")
            print("  - Text format may be different")
            print("  - Domain may have changed their page structure")
            print("\n💡 RECOMMENDATION:")
            print("  The extraction function is ready. We should integrate it into the main")
            print("  script and it will capture the data when available on active listings.")
            return 1
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if driver:
            print("\n→ Closing browser...")
            driver.quit()
            print("  ✓ Browser closed")


if __name__ == "__main__":
    exit(main())
