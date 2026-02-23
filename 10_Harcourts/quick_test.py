"""Quick test of the Harcourts scraper with just 2 properties"""

from harcourts_scraper import HarcourtsPropertyScraper

search_url = "https://propertyhub.harcourts.com.au/property-hub/listings/buy/?property-type=House&location=Robina-4023&include-suburb=1&category=buy&listing-category=residential"

print("Testing Harcourts Scraper with 2 properties...")
print("=" * 60)

scraper = HarcourtsPropertyScraper(headless=True)
properties = scraper.scrape_listings(search_url, max_properties=2)

if properties:
    print(f"\n✓ Successfully scraped {len(properties)} properties")
    
    # Save results
    scraper.save_to_csv(properties, 'test_output.csv')
    scraper.save_to_json(properties, 'test_output.json')
    
    # Display results
    for i, prop in enumerate(properties, 1):
        print(f"\n{i}. {prop['address']}")
        print(f"   Title: {prop['title']}")
        print(f"   Price: {prop['price']}")
        print(f"   Beds: {prop['bed']}, Baths: {prop['bathrooms']}, Cars: {prop['car_spaces']}")
        print(f"   Images: {len(prop.get('image_urls', []))}")
        print(f"   URL: {prop['url']}")
else:
    print("\n✗ No properties scraped")
