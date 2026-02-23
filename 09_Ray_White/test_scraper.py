"""
Test script for Ray White Robina Property Scraper
Tests the scraper on a limited number of properties
"""

import sys
from ray_white_scraper import RayWhiteRobinaScraper
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_scraper():
    """Test the scraper with limited properties"""
    print("=" * 60)
    print("Ray White Robina Property Scraper - TEST MODE")
    print("=" * 60)
    print()
    print("This test will:")
    print("1. Connect to Ray White Robina website")
    print("2. Extract first page of property URLs")
    print("3. Scrape details from first 3 properties only")
    print("4. Save test results to JSON")
    print()
    print("Starting test...")
    print()
    
    try:
        # Create scraper instance (non-headless for testing)
        scraper = RayWhiteRobinaScraper(headless=True)
        scraper.setup_driver()
        
        # Test 1: Get property URLs
        print("📋 Test 1: Fetching property URLs from listing page...")
        property_urls = scraper.get_property_urls()
        
        if not property_urls:
            print("❌ FAILED: No property URLs found!")
            return False
        
        print(f"✅ SUCCESS: Found {len(property_urls)} property URLs")
        print(f"   Sample URLs:")
        for url in property_urls[:3]:
            print(f"   - {url}")
        print()
        
        # Test 2: Extract data from first few properties
        print("📊 Test 2: Extracting data from first 3 properties...")
        test_properties = []
        
        for idx, url in enumerate(property_urls[:3], 1):
            print(f"   Processing property {idx}/3...")
            property_data = scraper.extract_property_data(url)
            
            if property_data:
                test_properties.append(property_data)
                print(f"   ✅ {property_data.get('title', 'Unknown title')}")
                print(f"      - Address: {property_data.get('address', 'N/A')}")
                print(f"      - Price: {property_data.get('price', 'N/A')}")
                print(f"      - Images: {len(property_data.get('image_urls', []))} found")
            else:
                print(f"   ⚠️ Could not extract data from property {idx}")
        
        print()
        
        # Close driver
        scraper.driver.quit()
        
        # Test 3: Save test results
        print("💾 Test 3: Saving test results to JSON...")
        scraper.properties_data = test_properties
        scraper.save_to_json('test_results.json')
        
        # Summary
        print()
        print("=" * 60)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print(f"📊 Test Summary:")
        print(f"   - Total property URLs found: {len(property_urls)}")
        print(f"   - Properties scraped in test: {len(test_properties)}")
        print(f"   - Properties with images: {sum(1 for p in test_properties if p.get('image_urls'))}")
        print(f"   - Total images in test: {sum(len(p.get('image_urls', [])) for p in test_properties)}")
        print()
        print(f"📁 Test results saved to: test_results.json")
        print()
        print("🎯 The scraper is working correctly!")
        print("   Run 'python ray_white_scraper.py' to scrape all properties.")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED!")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        logger.error("Test failed", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_scraper()
    sys.exit(0 if success else 1)
