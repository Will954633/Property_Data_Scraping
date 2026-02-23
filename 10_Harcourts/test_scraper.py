"""
Test script for Harcourts Property Scraper
Performs a limited test run to verify functionality
"""

from harcourts_scraper import HarcourtsPropertyScraper

def test_scraper():
    """Test the scraper with limited scope"""
    print("=" * 80)
    print("🧪 TESTING HARCOURTS SCRAPER")
    print("=" * 80)
    
    # Target URL
    listing_url = "https://propertyhub.harcourts.com.au/property-hub/listings/buy/?property-type=House&location=Robina-4023&include-suburb=1&category=buy&listing-category=residential"
    
    # Create scraper (headless mode by default)
    scraper = HarcourtsPropertyScraper(headless=True)  # Set to False for debugging
    
    try:
        # Test with just the first page and first 2 properties
        print("\n📝 Test Configuration:")
        print(f"  - URL: {listing_url}")
        print(f"  - Max pages: 1")
        print(f"  - Mode: Headless")
        print()
        print("⚠️  NOTE: The default URL may have no active listings.")
        print("    Update the listing_url variable to test with an active search.")
        print()
        
        scraper.start_driver()
        
        # Get property URLs from first page only
        property_urls = scraper.get_property_urls(listing_url, max_pages=1)
        
        if not property_urls:
            print("\n❌ Test Failed: No property URLs found")
            return False
        
        # Test scraping first 2 properties only
        print(f"\n🔍 Testing with first 2 properties out of {len(property_urls)} found...")
        test_urls = property_urls[:2]
        
        test_results = []
        for idx, url in enumerate(test_urls, 1):
            print(f"\n[Test {idx}/2]", end=" ")
            property_data = scraper.scrape_property_details(url)
            test_results.append(property_data)
        
        # Save test results
        scraper.save_to_json(test_results, "test_results.json")
        scraper.save_to_csv(test_results, "test_results.csv")
        
        # Verify test results
        print("\n" + "=" * 80)
        print("✅ TEST RESULTS")
        print("=" * 80)
        
        for idx, prop in enumerate(test_results, 1):
            print(f"\nProperty {idx}:")
            print(f"  URL: {prop['url']}")
            print(f"  Title: {'✓' if prop['title'] else '✗'} {prop['title']}")
            print(f"  Address: {'✓' if prop['address'] else '✗'} {prop['address']}")
            print(f"  Beds/Baths/Cars: {'✓' if any([prop['beds'], prop['bathrooms'], prop['carspaces']]) else '✗'} {prop['beds']}/{prop['bathrooms']}/{prop['carspaces']}")
            print(f"  Price: {'✓' if prop['price'] else '✗'} {prop['price']}")
            print(f"  Inspections: {'✓' if prop['open_inspection_times'] else '✗'} {len(prop['open_inspection_times'])} found")
            print(f"  Description: {'✓' if prop['description'] else '✗'} {len(prop['description'])} chars")
            print(f"  Agents: {'✓' if prop['agents'] else '✗'} {', '.join(prop['agents'])}")
        
        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")
        print(f"📊 Scraped {len(test_results)} properties")
        print("💾 Results saved to test_results.json and test_results.csv")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        scraper.stop_driver()


if __name__ == "__main__":
    success = test_scraper()
    exit(0 if success else 1)
