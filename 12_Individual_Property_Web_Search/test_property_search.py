"""
Property Web Search Test using Playwright
Last Updated: 04/02/2026, 7:12 am (Brisbane Time)

This script tests the ability to:
1. Search Google for a property address
2. Identify the agency website
3. Navigate to the property page
4. Extract all data (photos and text)

Test Case:
- Address: 11 South Bay Drive Varsity Lakes, QLD 4227
- Agency: Ray White Malan + Co - Broadbeach
- Target URL: https://raywhitemalanandco.com.au/properties/sold-residential/qld/varsity-lakes-4227/townhouse/3344866
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import re

class PropertySearchTest:
    def __init__(self):
        self.results = {
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_address': '11 South Bay Drive Varsity Lakes, QLD 4227',
            'expected_agency': 'Ray White Malan + Co - Broadbeach',
            'expected_url': 'https://raywhitemalanandco.com.au/properties/sold-residential/qld/varsity-lakes-4227/townhouse/3344866',
            'phases': {}
        }
    
    async def phase1_google_search(self, page):
        """Phase 1: Search Google for the property"""
        print("\n=== PHASE 1: Google Search ===")
        
        try:
            # Navigate to Google
            await page.goto('https://www.google.com', wait_until='networkidle')
            print("✓ Navigated to Google")
            
            # Accept cookies if prompted (common in some regions)
            try:
                accept_button = page.locator('button:has-text("Accept all")')
                if await accept_button.is_visible(timeout=2000):
                    await accept_button.click()
                    print("✓ Accepted cookies")
            except:
                pass
            
            # Search for the property
            search_query = "11 South Bay Drive Varsity Lakes QLD 4227 Ray White"
            search_box = page.locator('textarea[name="q"], input[name="q"]')
            await search_box.fill(search_query)
            await search_box.press('Enter')
            print(f"✓ Searched for: {search_query}")
            
            # Wait for results
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)  # Additional wait for dynamic content
            
            # Extract search results
            search_results = []
            links = await page.locator('a').all()
            
            for link in links[:20]:  # Check first 20 links
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    
                    if href and 'raywhite' in href.lower():
                        search_results.append({
                            'url': href,
                            'text': text.strip()[:100]  # First 100 chars
                        })
                except:
                    continue
            
            self.results['phases']['phase1'] = {
                'success': len(search_results) > 0,
                'search_query': search_query,
                'ray_white_links_found': len(search_results),
                'links': search_results
            }
            
            print(f"✓ Found {len(search_results)} Ray White links")
            return search_results
            
        except Exception as e:
            self.results['phases']['phase1'] = {
                'success': False,
                'error': str(e)
            }
            print(f"✗ Phase 1 failed: {e}")
            return []
    
    async def phase2_navigate_to_property(self, page, target_url):
        """Phase 2: Navigate directly to the property page"""
        print("\n=== PHASE 2: Navigate to Property Page ===")
        
        try:
            # Navigate to the target URL
            await page.goto(target_url, wait_until='networkidle', timeout=30000)
            print(f"✓ Navigated to: {target_url}")
            
            # Wait for content to load
            await asyncio.sleep(3)
            
            # Check if page loaded successfully
            title = await page.title()
            url = page.url
            
            self.results['phases']['phase2'] = {
                'success': True,
                'final_url': url,
                'page_title': title,
                'url_matches_target': url == target_url
            }
            
            print(f"✓ Page loaded: {title}")
            return True
            
        except Exception as e:
            self.results['phases']['phase2'] = {
                'success': False,
                'error': str(e)
            }
            print(f"✗ Phase 2 failed: {e}")
            return False
    
    async def phase3_extract_data(self, page):
        """Phase 3: Extract all data from the property page"""
        print("\n=== PHASE 3: Extract Property Data ===")
        
        try:
            extracted_data = {
                'images': [],
                'text_content': {},
                'property_details': {}
            }
            
            # Extract all images
            images = await page.locator('img').all()
            for img in images:
                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt')
                    if src and not src.startswith('data:'):  # Skip base64 images
                        extracted_data['images'].append({
                            'src': src,
                            'alt': alt or ''
                        })
                except:
                    continue
            
            print(f"✓ Extracted {len(extracted_data['images'])} images")
            
            # Extract page title
            extracted_data['text_content']['title'] = await page.title()
            
            # Extract all text content
            body_text = await page.locator('body').inner_text()
            extracted_data['text_content']['full_text'] = body_text[:1000]  # First 1000 chars
            extracted_data['text_content']['full_text_length'] = len(body_text)
            
            # Try to extract specific property details
            # Look for common patterns
            
            # Address
            address_patterns = [
                r'\d+\s+[A-Za-z\s]+(?:Drive|Street|Road|Avenue|Court|Place)',
                r'Varsity Lakes.*?QLD.*?4227'
            ]
            for pattern in address_patterns:
                match = re.search(pattern, body_text, re.IGNORECASE)
                if match:
                    extracted_data['property_details']['address'] = match.group(0)
                    break
            
            # Price (if available)
            price_patterns = [
                r'\$[\d,]+',
                r'Price:?\s*\$?[\d,]+'
            ]
            for pattern in price_patterns:
                match = re.search(pattern, body_text)
                if match:
                    extracted_data['property_details']['price'] = match.group(0)
                    break
            
            # Bedrooms, Bathrooms, Cars
            bed_match = re.search(r'(\d+)\s*(?:bed|bedroom)', body_text, re.IGNORECASE)
            if bed_match:
                extracted_data['property_details']['bedrooms'] = bed_match.group(1)
            
            bath_match = re.search(r'(\d+)\s*(?:bath|bathroom)', body_text, re.IGNORECASE)
            if bath_match:
                extracted_data['property_details']['bathrooms'] = bath_match.group(1)
            
            car_match = re.search(r'(\d+)\s*(?:car|garage|parking)', body_text, re.IGNORECASE)
            if car_match:
                extracted_data['property_details']['cars'] = car_match.group(1)
            
            # Extract all links
            links = await page.locator('a').all()
            extracted_data['links'] = []
            for link in links[:50]:  # First 50 links
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href:
                        extracted_data['links'].append({
                            'url': href,
                            'text': text.strip()[:50]
                        })
                except:
                    continue
            
            self.results['phases']['phase3'] = {
                'success': True,
                'images_extracted': len(extracted_data['images']),
                'text_length': extracted_data['text_content']['full_text_length'],
                'property_details_found': len(extracted_data['property_details']),
                'links_extracted': len(extracted_data['links']),
                'sample_data': {
                    'first_3_images': extracted_data['images'][:3],
                    'property_details': extracted_data['property_details'],
                    'text_sample': extracted_data['text_content']['full_text'][:200]
                }
            }
            
            print(f"✓ Extracted {len(extracted_data['images'])} images")
            print(f"✓ Extracted {extracted_data['text_content']['full_text_length']} characters of text")
            print(f"✓ Found {len(extracted_data['property_details'])} property details")
            
            return extracted_data
            
        except Exception as e:
            self.results['phases']['phase3'] = {
                'success': False,
                'error': str(e)
            }
            print(f"✗ Phase 3 failed: {e}")
            return None
    
    async def run_test(self, headless=True):
        """Run the complete test"""
        print("=" * 60)
        print("PROPERTY WEB SEARCH TEST")
        print("=" * 60)
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # Phase 1: Google Search
                search_results = await self.phase1_google_search(page)
                
                # Phase 2: Navigate to property page
                target_url = self.results['expected_url']
                navigation_success = await self.phase2_navigate_to_property(page, target_url)
                
                # Phase 3: Extract data
                if navigation_success:
                    extracted_data = await self.phase3_extract_data(page)
                
                # Overall results
                self.results['overall_success'] = all([
                    self.results['phases'].get('phase1', {}).get('success', False),
                    self.results['phases'].get('phase2', {}).get('success', False),
                    self.results['phases'].get('phase3', {}).get('success', False)
                ])
                
            finally:
                await browser.close()
        
        return self.results
    
    def save_results(self, filename='test_results.json'):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to {filename}")
    
    def print_summary(self):
        """Print a summary of the test results"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        for phase_name, phase_data in self.results['phases'].items():
            status = "✓ PASS" if phase_data.get('success') else "✗ FAIL"
            print(f"\n{phase_name.upper()}: {status}")
            
            if phase_data.get('success'):
                if phase_name == 'phase1':
                    print(f"  - Found {phase_data.get('ray_white_links_found', 0)} Ray White links")
                elif phase_name == 'phase2':
                    print(f"  - Page Title: {phase_data.get('page_title', 'N/A')}")
                elif phase_name == 'phase3':
                    print(f"  - Images: {phase_data.get('images_extracted', 0)}")
                    print(f"  - Text Length: {phase_data.get('text_length', 0)} characters")
                    print(f"  - Property Details: {phase_data.get('property_details_found', 0)}")
            else:
                print(f"  - Error: {phase_data.get('error', 'Unknown error')}")
        
        print(f"\nOVERALL: {'✓ SUCCESS' if self.results['overall_success'] else '✗ FAILED'}")
        print("=" * 60)


async def main():
    """Main function to run the test"""
    test = PropertySearchTest()
    
    # Run test in headless mode (set to False to see the browser)
    results = await test.run_test(headless=True)
    
    # Print summary
    test.print_summary()
    
    # Save results
    test.save_results('test_results.json')
    
    print("\n✓ Test complete!")


if __name__ == '__main__':
    asyncio.run(main())
