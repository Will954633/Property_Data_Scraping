#!/usr/bin/env python3
"""
Gold Coast Suburb URL Builder and Validator
Last Updated: 31/01/2026, 10:14 am (Brisbane Time)

PURPOSE:
- Load Gold Coast suburbs from JSON
- Build Domain.com.au URLs for each suburb
- Test that URLs are valid and accessible
- Extract property count from each suburb page

URL FORMAT:
https://www.domain.com.au/sale/{suburb-slug}/?excludeunderoffer=1&ssubs=0

Example:
https://www.domain.com.au/sale/robina-qld-4226/?excludeunderoffer=1&ssubs=0
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Install with: pip3 install selenium webdriver-manager beautifulsoup4")
    exit(1)

# Configuration
SUBURBS_FILE = "gold_coast_suburbs.json"
RESULTS_DIR = "suburb_url_test_results"
PAGE_LOAD_WAIT = 5
TEST_LIMIT = 5  # Test first 5 suburbs only


class SuburbURLTester:
    """Test and validate suburb URLs"""
    
    def __init__(self):
        """Initialize headless browser"""
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
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
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("  ✓ Headless Chrome ready")
        except Exception as e:
            raise Exception(f"Failed to create WebDriver: {e}")
    
    def build_suburb_url(self, suburb_slug: str) -> str:
        """Build Domain.com.au URL for suburb"""
        return f"https://www.domain.com.au/sale/{suburb_slug}/?excludeunderoffer=1&ssubs=0"
    
    def extract_property_count(self, html: str) -> Dict:
        """Extract property count from page (e.g., '51 Properties for sale in Robina, QLD, 4226')"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for the property count text
        # Pattern: "XX Properties for sale in SUBURB, QLD, POSTCODE"
        # or "X Property for sale in SUBURB, QLD, POSTCODE" (singular)
        
        # Try multiple selectors
        count_info = {
            "found": False,
            "count": None,
            "text": None,
            "method": None
        }
        
        # Method 1: Look for h1 tag with property count
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text(strip=True)
            # Match patterns like "51 Properties for sale" or "1 Property for sale"
            match = re.search(r'(\d+)\s+(Properties|Property)\s+for\s+sale', text, re.IGNORECASE)
            if match:
                count_info["found"] = True
                count_info["count"] = int(match.group(1))
                count_info["text"] = text
                count_info["method"] = "h1_tag"
                return count_info
        
        # Method 2: Look for any text containing the pattern
        all_text = soup.get_text()
        match = re.search(r'(\d+)\s+(Properties|Property)\s+for\s+sale\s+in\s+([^,]+),\s*QLD', all_text, re.IGNORECASE)
        if match:
            count_info["found"] = True
            count_info["count"] = int(match.group(1))
            count_info["text"] = match.group(0)
            count_info["method"] = "text_search"
            return count_info
        
        # Method 3: Look for data attributes or specific classes
        # (Domain.com.au may use specific classes for this)
        for elem in soup.find_all(attrs={'data-testid': True}):
            text = elem.get_text(strip=True)
            match = re.search(r'(\d+)\s+(Properties|Property)\s+for\s+sale', text, re.IGNORECASE)
            if match:
                count_info["found"] = True
                count_info["count"] = int(match.group(1))
                count_info["text"] = text
                count_info["method"] = "data_testid"
                return count_info
        
        return count_info
    
    def test_suburb_url(self, suburb: Dict, index: int, total: int) -> Dict:
        """Test a single suburb URL"""
        print(f"\n{'='*80}")
        print(f"Testing Suburb {index}/{total}: {suburb['name']}")
        print(f"{'='*80}")
        
        url = self.build_suburb_url(suburb['slug'])
        print(f"URL: {url}")
        
        result = {
            "suburb_name": suburb['name'],
            "postcode": suburb['postcode'],
            "slug": suburb['slug'],
            "url": url,
            "success": False,
            "property_count": None,
            "property_count_text": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Navigate to URL
            print(f"  → Loading page...")
            self.driver.get(url)
            time.sleep(PAGE_LOAD_WAIT)
            
            # Verify page loaded
            current_url = self.driver.current_url
            if not current_url or 'domain.com.au' not in current_url:
                result["error"] = "Page load failed"
                print(f"  ✗ Page load failed")
                return result
            
            print(f"  ✓ Page loaded")
            
            # Get HTML
            html = self.driver.page_source
            if not html or len(html) < 100:
                result["error"] = "HTML too small"
                print(f"  ✗ HTML extraction failed")
                return result
            
            print(f"  ✓ HTML extracted ({len(html):,} chars)")
            
            # Extract property count
            print(f"  → Extracting property count...")
            count_info = self.extract_property_count(html)
            
            if count_info["found"]:
                result["success"] = True
                result["property_count"] = count_info["count"]
                result["property_count_text"] = count_info["text"]
                result["extraction_method"] = count_info["method"]
                print(f"  ✓ Found: {count_info['text']}")
                print(f"  ✓ Count: {count_info['count']} properties")
            else:
                result["success"] = True  # URL works, just couldn't find count
                result["error"] = "Could not extract property count"
                print(f"  ⚠ Could not extract property count")
                print(f"  ℹ URL is valid but count extraction failed")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ✗ Error: {e}")
        
        return result
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")


def load_suburbs(filepath: str) -> List[Dict]:
    """Load suburbs from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data['suburbs']


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("GOLD COAST SUBURB URL BUILDER AND VALIDATOR")
    print("=" * 80)
    print(f"\nLoading suburbs from: {SUBURBS_FILE}")
    
    # Load suburbs
    if not os.path.exists(SUBURBS_FILE):
        print(f"\n✗ Suburbs file not found: {SUBURBS_FILE}")
        return 1
    
    suburbs = load_suburbs(SUBURBS_FILE)
    print(f"  ✓ Loaded {len(suburbs)} suburbs")
    
    # Limit for testing
    test_suburbs = suburbs[:TEST_LIMIT]
    print(f"  ℹ Testing first {len(test_suburbs)} suburbs")
    
    print(f"\n{'='*80}")
    print("URL FORMAT TEST")
    print(f"{'='*80}")
    print(f"\nBase URL pattern:")
    print(f"  https://www.domain.com.au/sale/{{suburb-slug}}/?excludeunderoffer=1&ssubs=0")
    print(f"\nExample URLs:")
    for i, suburb in enumerate(test_suburbs[:3], 1):
        url = f"https://www.domain.com.au/sale/{suburb['slug']}/?excludeunderoffer=1&ssubs=0"
        print(f"  {i}. {suburb['name']}: {url}")
    print(f"{'='*80}")
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Initialize tester
    tester = None
    try:
        tester = SuburbURLTester()
        
        # Test each suburb
        all_results = []
        
        for i, suburb in enumerate(test_suburbs, 1):
            result = tester.test_suburb_url(suburb, i, len(test_suburbs))
            all_results.append(result)
            
            # Brief pause between suburbs
            if i < len(test_suburbs):
                print(f"\n→ Waiting 3 seconds before next suburb...")
                time.sleep(3)
        
        # Generate report
        print(f"\n{'='*80}")
        print("TEST COMPLETE")
        print(f"{'='*80}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Calculate statistics
        successful = sum(1 for r in all_results if r["success"])
        with_count = sum(1 for r in all_results if r["property_count"] is not None)
        total_properties = sum(r["property_count"] for r in all_results if r["property_count"] is not None)
        
        # Save test results
        test_report = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "test_name": "Gold Coast Suburb URL Validation Test",
                "total_suburbs_tested": len(test_suburbs),
                "successful_urls": successful,
                "urls_with_property_count": with_count,
                "total_properties_found": total_properties
            },
            "url_format": "https://www.domain.com.au/sale/{suburb-slug}/?excludeunderoffer=1&ssubs=0",
            "suburbs_tested": all_results
        }
        
        report_file = os.path.join(RESULTS_DIR, f"suburb_url_test_{timestamp}.json")
        with open(report_file, 'w') as f:
            json.dump(test_report, f, indent=2)
        
        # Print summary
        print(f"\n📊 TEST RESULTS:")
        print(f"  Suburbs tested: {len(test_suburbs)}")
        print(f"  Successful URLs: {successful}")
        print(f"  Property counts extracted: {with_count}")
        print(f"  Total properties found: {total_properties}")
        
        print(f"\n📋 SUBURB SUMMARY:")
        for result in all_results:
            status = "✅" if result["success"] else "❌"
            count_str = f"{result['property_count']} properties" if result['property_count'] else "count not found"
            print(f"  {status} {result['suburb_name']}: {count_str}")
        
        print(f"\n📁 Files saved:")
        print(f"  • Test report: {report_file}")
        
        # Test verdict
        print(f"\n{'='*80}")
        if successful == len(test_suburbs) and with_count > 0:
            print("✅ TEST PASSED: URL format is correct and property counts can be extracted!")
            print(f"   Successfully tested {successful} suburbs")
            print(f"   Extracted property counts from {with_count} suburbs")
            print(f"\n💡 Next steps:")
            print(f"   1. Review test results in: {report_file}")
            print(f"   2. Run full test on all {len(suburbs)} Gold Coast suburbs")
            print(f"   3. Integrate into discovery script")
        else:
            print("⚠️ TEST PARTIAL: Some URLs worked but property count extraction needs improvement")
            print(f"   Successful URLs: {successful}/{len(test_suburbs)}")
            print(f"   Property counts extracted: {with_count}/{len(test_suburbs)}")
        print(f"{'='*80}\n")
        
        return 0 if successful > 0 else 1
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"TEST ERROR")
        print(f"{'='*80}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if tester:
            tester.close()


if __name__ == "__main__":
    exit(main())
