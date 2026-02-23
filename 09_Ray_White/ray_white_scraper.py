"""
Ray White Robina Property Scraper
Scrapes all property data from Ray White Robina properties for sale
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ray_white_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RayWhiteRobinaScraper:
    """Main scraper class for Ray White Robina properties"""
    
    def __init__(self, headless: bool = True):
        """Initialize the scraper with Chrome WebDriver"""
        self.headless = headless
        self.driver = None
        
        # Multiple listing URLs to scrape from different Ray White offices and suburbs
        self.listing_urls = [
            # Ray White Robina listings
            "https://raywhiterobina.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Robina+4226",
            "https://raywhiterobina.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Mudgeeraba+4213",
            "https://raywhiterobina.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Varsity+Lakes+4227",
            "https://raywhiterobina.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Carrara+4211",
            "https://raywhiterobina.com.au/properties/residential-for-sale?category=&keywords=Reedy+Creek&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=",
            "https://raywhiterobina.com.au/properties?keywords=&price=&sort=creationTime+desc&suburbPostCode=Merrimac+4226",
            "https://raywhiterobina.com.au/properties?keywords=&price=&sort=creationTime+desc&suburbPostCode=Worongary+4213",
            
            # Ray White TMG listings
            "https://raywhitetmg.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Carrara+4211",
            "https://raywhitetmg.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Worongary+4213",
            "https://raywhitetmg.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Robina+4226",
            "https://raywhitetmg.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Mudgeeraba+4213",
            "https://raywhitetmg.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Reedy+Creek+4227",
            "https://raywhitetmg.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Merrimac+4226",
            
            # Ray White Malan and Co listings
            "https://raywhitemalanandco.com.au/properties/residential-for-sale?category=&keywords=&maxFloor=0&maxLand=0&minBaths=0&minBeds=0&minCars=0&minFloor=0&minLand=0&price=&sort=creationTime+desc&suburbPostCode=Burleigh+Waters+4220",
        ]
        
        self.properties_data = []
        
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Install chromedriver and get the path
        driver_path = ChromeDriverManager().install()
        
        # Fix for ChromeDriver path issue - ensure we have the actual binary
        import os
        if 'THIRD_PARTY_NOTICES' in driver_path or not driver_path.endswith('chromedriver'):
            driver_dir = os.path.dirname(driver_path)
            # Look for the actual chromedriver binary
            for file in os.listdir(driver_dir):
                if file == 'chromedriver' or file == 'chromedriver.exe':
                    driver_path = os.path.join(driver_dir, file)
                    break
        
        # Ensure chromedriver has execute permissions
        if os.path.exists(driver_path):
            os.chmod(driver_path, 0o755)
            logger.info(f"Set execute permissions for: {driver_path}")
        
        self.driver = webdriver.Chrome(
            service=Service(driver_path),
            options=chrome_options
        )
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("Chrome WebDriver initialized successfully")
        
    def get_property_urls_from_page(self, listing_url: str) -> List[str]:
        """Get all property URLs from a single listing page"""
        property_urls = []
        
        try:
            logger.info(f"Fetching property listing page: {listing_url}")
            self.driver.get(listing_url)
            time.sleep(5)  # Wait for page to load
            
            # Extract base URL for this listing page
            from urllib.parse import urlparse
            parsed_url = urlparse(listing_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Get the page source and parse
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Try multiple selectors to find property links
            links = []
            
            # Look for article or div elements that contain property info
            property_containers = soup.find_all(['article', 'div'], class_=lambda x: x and ('property' in x.lower() or 'listing' in x.lower() or 'card' in x.lower()))
            
            if property_containers:
                logger.info(f"Found {len(property_containers)} property containers")
                seen_property_paths = set()  # Track unique property paths to avoid duplicates
                
                for idx, container in enumerate(property_containers, 1):
                    # Find ALL links in each container
                    container_links = container.find_all('a', href=True)
                    logger.info(f"Container {idx} has {len(container_links)} links")
                    
                    for link in container_links:
                        href = link.get('href', '')
                        # Only add links that look like property pages
                        if href and href != '#' and not href.startswith('javascript:'):
                            # Check if it's a property-related link
                            if any(pattern in href for pattern in ['/properties/', '/property/', '/listing/', '/house/', '/apartment/', '/unit/', '/duplex']):
                                # Only add unique property links (avoid duplicates from multiple containers)
                                if href not in seen_property_paths:
                                    seen_property_paths.add(href)
                                    links.append(link)
                                    logger.info(f"✓ Adding unique property link: {href}")
            
            # If no containers, try finding all links with property-related hrefs
            if not links:
                logger.info("Trying to find property links directly...")
                all_links = soup.find_all('a', href=True)
                links = [link for link in all_links if any(pattern in link.get('href', '') for pattern in ['/properties/', '/property/', '/listing/'])]
            
            logger.info(f"Found {len(links)} links to process")
            
            # Process found links
            for link in links:
                href = link['href']
                
                # Skip empty or anchor-only links
                if not href or href == '#' or href.startswith('javascript:'):
                    continue
                
                # Build full URL using the base_url from the current listing page
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = base_url + href
                else:
                    full_url = base_url + '/' + href
                
                # Add unique URLs only
                if full_url not in property_urls and full_url != base_url and full_url != base_url + '/':
                    # Exclude navigation and non-property links
                    exclude_patterns = ['/contact', '/about', '/agents', '/team', '/careers', '/news', '/blog', '/offices']
                    if not any(pattern in full_url.lower() for pattern in exclude_patterns):
                        property_urls.append(full_url)
                        logger.info(f"Found property URL: {full_url}")
            
        except Exception as e:
            logger.error(f"Error getting property URLs: {e}", exc_info=True)
        
        logger.info(f"Found {len(property_urls)} property URLs from {listing_url}")
        return property_urls
    
    def get_all_property_urls(self) -> List[str]:
        """Get all property URLs from all listing pages"""
        all_property_urls = []
        
        logger.info(f"Fetching property URLs from {len(self.listing_urls)} listing pages")
        
        for idx, listing_url in enumerate(self.listing_urls, 1):
            logger.info(f"Processing listing page {idx}/{len(self.listing_urls)}")
            property_urls = self.get_property_urls_from_page(listing_url)
            
            # Add only unique URLs
            for url in property_urls:
                if url not in all_property_urls:
                    all_property_urls.append(url)
                else:
                    logger.info(f"Skipping duplicate property URL: {url}")
            
            # Be polite - add delay between listing pages
            time.sleep(2)
        
        logger.info(f"Found {len(all_property_urls)} unique property URLs across all listing pages")
        return all_property_urls
    
    def extract_property_data(self, url: str) -> Optional[Dict]:
        """Extract detailed data from a property page"""
        try:
            logger.info(f"Extracting data from: {url}")
            self.driver.get(url)
            time.sleep(2)
            
            # Wait for main content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            property_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract title - specific selector
            title = soup.select_one('#app > div > div > article > div.pdp_header > div > span')
            if title:
                property_data['title'] = title.get_text(strip=True)
            
            # Extract address - specific selector
            address = soup.select_one('#app > div > div > article > div.pdp_header > div > div > h1')
            if address:
                property_data['address'] = address.get_text(strip=True)
            
            # Extract price - specific selector
            price = soup.select_one('#app > div > div > article > div.pdp_header > div > div > span')
            if price:
                property_data['price'] = price.get_text(strip=True)
            
            # Extract bed, bath, car spaces - specific selector
            features_ul = soup.select_one('#app > div > div > article > div.pdp_header > div > ul')
            if features_ul:
                # Parse the ul for bed, bath, car values
                feature_items = features_ul.find_all('li')
                for item in feature_items:
                    text = item.get_text(strip=True)
                    
                    # Try to extract numbers and identify feature type
                    if re.search(r'\d+', text):
                        if 'bed' in text.lower():
                            property_data['bed'] = re.search(r'\d+', text).group()
                        elif 'bath' in text.lower():
                            property_data['bathrooms'] = re.search(r'\d+', text).group()
                        elif 'car' in text.lower() or 'garage' in text.lower() or 'parking' in text.lower():
                            property_data['car_spaces'] = re.search(r'\d+', text).group()
            
            # Extract inspection times
            inspection_selectors = [
                '#app > div > div > article > div.pdp_events_wrap.inner_lg > div > div.event_cards.no_final_event > div > ul > li:nth-child(1) > div',
                '#app > div > div > article > div.pdp_events_wrap.inner_lg > div > div.event_cards.no_final_event > div > ul > li:nth-child(2) > div',
                '#app > div > div > article > div.pdp_events_wrap.inner_lg > div > div.event_cards.no_final_event > div > ul > li:nth-child(3) > div'
            ]
            
            for idx, selector in enumerate(inspection_selectors, 1):
                inspection = soup.select_one(selector)
                if inspection:
                    # Extract inspection details
                    inspection_text = inspection.get_text(strip=True)
                    
                    # Try to format as "Inspection: Day Date Time"
                    event_type = inspection.select_one('.event_type')
                    event_heading = inspection.select_one('.event_heading')
                    event_date = inspection.select_one('.event_date')
                    event_month = inspection.select_one('.event_month')
                    event_time = inspection.select_one('.event_time')
                    
                    if event_type and event_heading and event_date and event_month and event_time:
                        formatted_inspection = f"{event_type.get_text(strip=True)}{event_heading.get_text(strip=True)}{event_date.get_text(strip=True)}{event_month.get_text(strip=True)}{event_time.get_text(strip=True)}"
                        property_data[f'Inspection_{idx:02d}'] = formatted_inspection
                    else:
                        # Fallback to raw text
                        property_data[f'Inspection_{idx:02d}'] = inspection_text
            
            # Extract description - specific selector
            description = soup.select_one('#description > div > div')
            if description:
                property_data['description'] = description.get_text(strip=True)
            
            # Extract listing agent - specific selector
            agent_section = soup.select_one('#agents')
            if agent_section:
                agent_text = agent_section.get_text(strip=True)
                property_data['listing_agent'] = agent_text
                
                # Try to parse agent details
                agent_info = {}
                
                # Look for name - extract just the name using a better pattern
                # Name is typically 2-3 words with capital letters after "Agents" and before job title
                # Stop before words like "Independent", "Contractor", "Licensed", etc.
                name_match = re.search(r"Agents?\s*([A-Z][a-z]+\s+[A-Z]['']?[A-Z]?[a-z]+)(?=\s*(?:Independent|Contractor|Licensed|Real|Team|Agent|\+|$))", agent_text)
                if name_match:
                    agent_info['name'] = name_match.group(1).strip()
                
                # Look for phone - try to find phone pattern
                phone_match = re.search(r'\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{3,4}', agent_text)
                if phone_match:
                    agent_info['phone'] = phone_match.group()
                
                # Look for email - extract and clean
                email_match = re.search(r'([\w\.-]+@[\w\.-]+\.(?:com|au|net|org))', agent_text)
                if email_match:
                    # Clean the email - remove any trailing text
                    email = email_match.group(1)
                    # Remove any leading digits (like "706") that might have been captured
                    email = re.sub(r'^\d+', '', email)
                    agent_info['email'] = email
                
                if agent_info:
                    property_data['agent_details'] = agent_info
            
            # Extract base domain to understand which Ray White office this is from
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            property_data['source_domain'] = parsed_url.netloc
            
            # Extract property type - fallback selector
            type_selectors = ['.property-type', '.listing-type', '[itemprop="propertyType"]']
            for selector in type_selectors:
                prop_type = soup.select_one(selector)
                if prop_type:
                    property_data['property_type'] = prop_type.get_text(strip=True)
                    break
            
            # Extract images - CRITICAL FEATURE
            image_urls = []
            
            # Look for various image elements
            img_selectors = [
                'img[src*="property"]',
                'img[src*="listing"]',
                '.property-image img',
                '.gallery img',
                '.slider img',
                '.carousel img',
                '[class*="image"] img',
                '.property-photos img'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                    if src:
                        # Convert relative URLs to absolute (using the property's domain)
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            src = base_url + src
                        
                        if src not in image_urls and ('jpg' in src.lower() or 'jpeg' in src.lower() or 'png' in src.lower() or 'webp' in src.lower()):
                            image_urls.append(src)
            
            property_data['image_urls'] = image_urls
            logger.info(f"Extracted {len(image_urls)} images")
            
            # Extract additional details
            details = {}
            
            # Look for detail lists
            detail_items = soup.find_all(['li', 'div', 'span'], class_=re.compile(r'detail|spec|attribute'))
            for item in detail_items:
                text = item.get_text(strip=True)
                if ':' in text:
                    key, value = text.split(':', 1)
                    details[key.strip()] = value.strip()
            
            if details:
                property_data['additional_details'] = details
            
            # Extract listing ID
            listing_id = soup.select_one('[data-listing-id], .listing-id')
            if listing_id:
                property_data['listing_id'] = listing_id.get('data-listing-id') or listing_id.get_text(strip=True)
            
            # Extract date listed
            date_listed = soup.select_one('.date-listed, [itemprop="datePosted"]')
            if date_listed:
                property_data['date_listed'] = date_listed.get_text(strip=True)
            
            logger.info(f"Successfully extracted data for: {property_data.get('title', 'Unknown')}")
            return property_data
            
        except Exception as e:
            logger.error(f"Error extracting property data from {url}: {e}", exc_info=True)
            return None
    
    def scrape_all_properties(self) -> List[Dict]:
        """Main method to scrape all properties"""
        try:
            self.setup_driver()
            
            # Get all property URLs from all listing pages
            property_urls = self.get_all_property_urls()
            
            if not property_urls:
                logger.warning("No property URLs found!")
                return []
            
            # Extract data from each property
            for idx, url in enumerate(property_urls, 1):
                logger.info(f"Processing property {idx}/{len(property_urls)}")
                property_data = self.extract_property_data(url)
                
                if property_data:
                    # Skip properties with title "Apartment for Sale"
                    if property_data.get('title') == 'Apartment for Sale':
                        logger.info(f"Skipping property: {property_data.get('address', 'Unknown')} - Title is 'Apartment for Sale'")
                        continue
                    
                    self.properties_data.append(property_data)
                
                # Be polite - add delay between requests
                time.sleep(2)
            
            logger.info(f"Successfully scraped {len(self.properties_data)} properties")
            return self.properties_data
            
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def save_to_json(self, filename: Optional[str] = None):
        """Save scraped data to JSON file"""
        if filename is None:
            filename = f"ray_white_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'total_properties': len(self.properties_data),
                    'total_listing_pages': len(self.listing_urls),
                    'source_urls': self.listing_urls,
                    'properties': self.properties_data
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved to {filename}")
            print(f"\n✅ Successfully saved {len(self.properties_data)} properties to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}", exc_info=True)
            raise


def main():
    """Main execution function"""
    print("=" * 60)
    print("Ray White Robina Property Scraper")
    print("=" * 60)
    print()
    
    # Create scraper instance
    scraper = RayWhiteRobinaScraper(headless=True)
    
    # Scrape all properties
    print("Starting scraping process...")
    properties = scraper.scrape_all_properties()
    
    # Save to JSON
    if properties:
        scraper.save_to_json()
        print(f"\n📊 Summary:")
        print(f"   - Total properties scraped: {len(properties)}")
        print(f"   - Properties with images: {sum(1 for p in properties if p.get('image_urls'))}")
        print(f"   - Total images collected: {sum(len(p.get('image_urls', [])) for p in properties)}")
    else:
        print("\n⚠️ No properties were scraped!")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
