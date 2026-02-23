"""
Harcourts Property Scraper
Scrapes property listings from Harcourts Property Hub
"""

import time
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


class HarcourtsPropertyScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome options"""
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless=new')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Add additional anti-detection measures
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = None
        self.wait = None

    def start_driver(self):
        """Start the Chrome driver"""
        self.driver = webdriver.Chrome(options=self.chrome_options)
        
        # Execute CDP commands to further hide automation
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 15)
        print("✓ Chrome driver started")

    def close_driver(self):
        """Close the Chrome driver"""
        if self.driver:
            self.driver.quit()
            print("✓ Chrome driver closed")

    def get_property_links(self, search_url):
        """Get all property links from the search results page with pagination support"""
        print(f"\nFetching property listings from: {search_url}")
        
        all_property_links = []
        page = 1
        
        while True:
            # Construct URL with page parameter
            if '?' in search_url:
                page_url = f"{search_url}&page={page}"
            else:
                page_url = f"{search_url}?page={page}"
            
            print(f"\nFetching page {page}: {page_url}")
            self.driver.get(page_url)
            
            # Wait for property cards to load
            time.sleep(5)
            
            page_property_links = []
            
            try:
                # Find property cards using .card a selector
                cards = self.driver.find_elements(By.CSS_SELECTOR, '.card a')
                
                for card in cards:
                    href = card.get_attribute('href')
                    # Filter for actual listing URLs (not agent pages or other links)
                    if href and '/listing/' in href and href not in all_property_links:
                        page_property_links.append(href)
                        all_property_links.append(href)
                
                print(f"✓ Found {len(page_property_links)} properties on page {page} (Total: {len(all_property_links)})")
                
                # Check if there are more pages - look for next page button or page numbers
                try:
                    # Check if we can find the next page number
                    next_page_exists = False
                    pagination_links = self.driver.find_elements(By.CSS_SELECTOR, '.pagination a, .page-item a')
                    
                    for link in pagination_links:
                        link_text = link.text.strip()
                        # Check if next page number exists
                        if link_text.isdigit() and int(link_text) == page + 1:
                            next_page_exists = True
                            break
                        # Or check for "Next" button
                        elif link_text.lower() in ['next', '›', '»']:
                            next_page_exists = True
                            break
                    
                    # If no new properties found on this page, also stop
                    if not page_property_links or not next_page_exists:
                        print(f"✓ No more pages found. Stopping pagination.")
                        break
                    
                except:
                    # If we can't find pagination elements, stop after this page
                    if not page_property_links:
                        break
                
                page += 1
                
                # Safety check - don't go beyond reasonable page count
                if page > 10:
                    print("Safety limit reached (10 pages)")
                    break
                
            except Exception as e:
                print(f"✗ Error finding property links on page {page}: {str(e)}")
                break
        
        print(f"\n✓ Total properties found across all pages: {len(all_property_links)}")
        return all_property_links

    def safe_find_element(self, selector, method=By.CSS_SELECTOR):
        """Safely find an element and return its text"""
        try:
            element = self.driver.find_element(method, selector)
            return element.text.strip()
        except (NoSuchElementException, TimeoutException):
            return ""

    def scrape_property(self, url):
        """Scrape individual property data"""
        print(f"\nScraping: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(4)  # Wait longer for JavaScript to render
            
            # Get page source for BeautifulSoup as backup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            property_data = {
                'url': url,
                'title': '',
                'address': '',
                'bed': '',
                'bathrooms': '',
                'car_spaces': '',
                'price': '',
                'description': '',
                'listing_agent': '',
                'image_urls': [],
                'scraped_at': datetime.now().isoformat()
            }
            
            # Title - try multiple selectors
            title_selectors = [
                'body > section._property-residential-attributes-mobile-block.block-first-border > div > div:nth-child(1) > div > div > p',
                '.property-title',
                'h1'
            ]
            for selector in title_selectors:
                property_data['title'] = self.safe_find_element(selector)
                if property_data['title']:
                    break
            
            # Address - use BeautifulSoup for better reliability
            try:
                # Look for h3 containing address pattern
                h3_tags = soup.find_all('h3')
                for h3 in h3_tags:
                    h3_text = h3.get_text(strip=True)
                    # Address typically contains QLD and a postcode
                    if 'QLD' in h3_text and any(char.isdigit() for char in h3_text):
                        property_data['address'] = h3_text
                        break
            except:
                pass
            
            # Property features (beds, bath, cars) - extract from ul.summary
            try:
                # Find all list items in the summary section
                summary_items = self.driver.find_elements(By.CSS_SELECTOR, 'ul.summary li')
                
                for item in summary_items:
                    try:
                        # Get the class name to identify the attribute type
                        item_class = item.get_attribute('class')
                        
                        # Find the span containing the value
                        span = item.find_element(By.TAG_NAME, 'span')
                        # Use innerHTML since .text returns empty
                        value = span.get_attribute('innerHTML').strip()
                        
                        if 'bed' in item_class:
                            property_data['bed'] = value
                        elif 'bath' in item_class:
                            property_data['bathrooms'] = value
                        elif 'garage' in item_class or 'car' in item_class or 'parking' in item_class:
                            property_data['car_spaces'] = value
                    except:
                        continue
                    
            except Exception as e:
                print(f"  Warning: Could not extract property features: {str(e)}")
            
            # Price
            price_selectors = [
                'body > section._property-residential-attributes-mobile-block.block-first-border > div > div:nth-child(1) > div > div > div.price-by-negotiation-container > div > div',
                '.property-price',
                '.price',
                '[class*="price"]'
            ]
            for selector in price_selectors:
                property_data['price'] = self.safe_find_element(selector)
                if property_data['price']:
                    break
            
            # Open inspection times - extract multiple inspections like Ray White format
            try:
                inspection_items = self.driver.find_elements(By.CSS_SELECTOR, '#mobile-inspections > div > div > div > div > div:nth-child(2) > div > ul > li')
                for idx, item in enumerate(inspection_items, 1):
                    try:
                        inspection_text = item.find_element(By.CSS_SELECTOR, 'div:nth-child(1)').text.strip()
                        if inspection_text:
                            property_data[f'Inspection_{idx:02d}'] = inspection_text
                    except:
                        continue
            except Exception as e:
                print(f"  Warning: Could not extract inspection times: {str(e)}")
            
            # Description - use BeautifulSoup to find the description div
            try:
                # Look for divs that contain the full description
                divs = soup.find_all('div', class_='col-12')
                
                for div in divs:
                    div_text = div.get_text(strip=True)
                    # Description is long and starts with property title/details
                    # Exclude navigation/menu text
                    if (len(div_text) > 500 and 
                        any(kw in div_text.lower() for kw in ['bedroom', 'bathroom', 'kitchen', 'features']) and
                        'Property Hub' not in div_text[:100]):  # Avoid navigation
                        property_data['description'] = div_text
                        break
            except:
                pass
            
            # Listing Agent - use BeautifulSoup to find agent names
            try:
                # Find all elements with class 'agent-name'
                agent_elements = soup.find_all(class_='agent-name')
                agent_names = []
                
                for elem in agent_elements:
                    name = elem.get_text(strip=True)
                    # Avoid duplicates
                    if name and name not in agent_names:
                        agent_names.append(name)
                
                if agent_names:
                    property_data['listing_agent'] = ', '.join(agent_names)
            except:
                pass
            
            # Extract property images
            try:
                image_urls = []
                # Look for property images
                img_elements = soup.find_all('img', src=True)
                for img in img_elements:
                    src = img.get('src', '')
                    # Filter for actual property images (exclude icons, logos, etc.)
                    if src and any(pattern in src for pattern in ['/property', '/listing', 'cloudinary', 'images']):
                        # Convert relative URLs to absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                        
                        # Only add unique image URLs
                        if src not in image_urls and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            image_urls.append(src)
                
                property_data['image_urls'] = image_urls
            except Exception as e:
                print(f"  Warning: Could not extract images: {str(e)}")
            
            print(f"✓ Scraped: {property_data['address'] or 'Unknown address'}")
            return property_data
            
        except Exception as e:
            print(f"✗ Error scraping property: {str(e)}")
            return None

    def save_to_csv(self, data, filename='harcourts_properties.csv'):
        """Save scraped data to CSV file"""
        if not data:
            print("No data to save")
            return
        
        keys = data[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        
        print(f"\n✓ Data saved to {filename}")

    def save_to_json(self, data, filename='harcourts_properties.json'):
        """Save scraped data to JSON file"""
        if not data:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Data saved to {filename}")

    def scrape_listings(self, search_url, max_properties=None):
        """Main method to scrape all property listings"""
        try:
            self.start_driver()
            
            # Get all property links
            property_links = self.get_property_links(search_url)
            
            if not property_links:
                print("No property links found!")
                return []
            
            # Limit properties if specified
            if max_properties:
                property_links = property_links[:max_properties]
                print(f"Limiting to {max_properties} properties")
            
            # Scrape each property
            all_properties = []
            for i, link in enumerate(property_links, 1):
                print(f"\n[{i}/{len(property_links)}]", end=" ")
                property_data = self.scrape_property(link)
                if property_data:
                    all_properties.append(property_data)
                
                # Be polite - add delay between requests
                time.sleep(2)
            
            return all_properties
            
        finally:
            self.close_driver()


def main():
    # Harcourts search URL for multiple suburbs (Mudgeeraba, Robina, Carrara, Varsity Lakes, Reedy Creek, Burleigh Waters, Merrimac, Worongary)
    search_url = "https://harcourts.net/au/listings/buy/?property-type=House&include-suburb=1&location=mudgeeraba-3955_Robina-4023_Carrara-3937_Varsity+Lakes-6108_Reedy+Creek-4025_Burleigh+Waters-4005_Merrimac-4022_Worongary-3958&listing-category=residential"
    
    print("=" * 60)
    print("Harcourts Property Scraper - Multi-Suburb")
    print("=" * 60)
    
    # Initialize scraper
    scraper = HarcourtsPropertyScraper(headless=True)
    
    # Scrape all properties (remove max_properties limit to get all 39 properties)
    properties = scraper.scrape_listings(search_url)
    
    if properties:
        print(f"\n{'=' * 60}")
        print(f"Successfully scraped {len(properties)} properties")
        print(f"{'=' * 60}")
        
        # Save to both CSV and JSON
        scraper.save_to_csv(properties)
        scraper.save_to_json(properties)
        
        # Print summary
        print("\nSummary:")
        for i, prop in enumerate(properties, 1):
            print(f"\n{i}. {prop['address'] or 'Unknown'}")
            print(f"   Price: {prop['price'] or 'N/A'}")
            print(f"   Beds: {prop['bed'] or 'N/A'}, "
                  f"Baths: {prop['bathrooms'] or 'N/A'}, "
                  f"Cars: {prop['car_spaces'] or 'N/A'}")
            print(f"   Images: {len(prop.get('image_urls', []))}")
    else:
        print("\nNo properties were scraped!")


if __name__ == "__main__":
    main()
