"""
DuckDuckGo Property Search Test
Last Updated: 04/02/2026, 7:19 am (Brisbane Time)

This script tests DuckDuckGo search for property addresses.
DuckDuckGo is more bot-friendly than Google.

Test Case:
- Address: 11 South Bay Drive Varsity Lakes, QLD 4227
- Agency: Ray White Malan + Co - Broadbeach
- Expected to find: raywhitemalanandco.com.au
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time


class DuckDuckGoPropertySearch:
    def __init__(self):
        self.results = {
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_address': '11 South Bay Drive Varsity Lakes, QLD 4227',
            'expected_agency': 'Ray White Malan + Co - Broadbeach',
            'search_results': []
        }
        
        # User agent to appear as a regular browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def search_duckduckgo(self, query):
        """Search DuckDuckGo HTML version (more bot-friendly)"""
        print(f"\n=== Searching DuckDuckGo for: {query} ===")
        
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query}
            
            # Add a small delay to be respectful
            time.sleep(1)
            
            response = requests.post(url, data=data, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✓ DuckDuckGo responded with status {response.status_code}")
                return response.text
            else:
                print(f"✗ DuckDuckGo responded with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Error searching DuckDuckGo: {e}")
            return None
    
    def parse_results(self, html):
        """Parse DuckDuckGo search results"""
        print("\n=== Parsing Search Results ===")
        
        if not html:
            print("✗ No HTML to parse")
            return []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            # Find all result links
            result_links = soup.find_all('a', class_='result__a')
            
            print(f"✓ Found {len(result_links)} total results")
            
            for link in result_links:
                try:
                    title = link.text.strip()
                    href = link.get('href', '')
                    
                    # DuckDuckGo wraps URLs, extract the actual URL
                    if href.startswith('//duckduckgo.com/l/?'):
                        # Extract the actual URL from the redirect
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        if 'uddg' in parsed:
                            href = parsed['uddg'][0]
                    
                    if title and href:
                        results.append({
                            'title': title,
                            'url': href
                        })
                except Exception as e:
                    continue
            
            print(f"✓ Parsed {len(results)} valid results")
            return results
            
        except Exception as e:
            print(f"✗ Error parsing results: {e}")
            return []
    
    def filter_ray_white_results(self, results):
        """Filter results to find Ray White links"""
        print("\n=== Filtering for Ray White Results ===")
        
        ray_white_results = []
        
        for result in results:
            url_lower = result['url'].lower()
            title_lower = result['title'].lower()
            
            # Check if it's a Ray White link
            if 'raywhite' in url_lower or 'ray white' in title_lower:
                ray_white_results.append(result)
                print(f"✓ Found Ray White: {result['title'][:60]}...")
        
        print(f"\n✓ Total Ray White results: {len(ray_white_results)}")
        return ray_white_results
    
    def run_test(self):
        """Run the complete DuckDuckGo search test"""
        print("=" * 70)
        print("DUCKDUCKGO PROPERTY SEARCH TEST")
        print("=" * 70)
        
        # Build search query
        search_query = f"{self.results['test_address']} Ray White"
        
        # Search DuckDuckGo
        html = self.search_duckduckgo(search_query)
        
        if html:
            # Parse results
            all_results = self.parse_results(html)
            
            # Filter for Ray White
            ray_white_results = self.filter_ray_white_results(all_results)
            
            # Store results
            self.results['search_query'] = search_query
            self.results['total_results'] = len(all_results)
            self.results['ray_white_results'] = len(ray_white_results)
            self.results['search_results'] = ray_white_results
            self.results['success'] = len(ray_white_results) > 0
            
            # Check if we found the expected URL
            expected_domain = 'raywhitemalanandco.com.au'
            found_expected = any(expected_domain in r['url'].lower() for r in ray_white_results)
            self.results['found_expected_agency'] = found_expected
            
        else:
            self.results['success'] = False
            self.results['error'] = 'Failed to get search results'
        
        return self.results
    
    def print_summary(self):
        """Print a summary of the test results"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        if self.results.get('success'):
            print(f"\n✓ SUCCESS - DuckDuckGo search worked!")
            print(f"\nSearch Query: {self.results.get('search_query', 'N/A')}")
            print(f"Total Results: {self.results.get('total_results', 0)}")
            print(f"Ray White Results: {self.results.get('ray_white_results', 0)}")
            print(f"Found Expected Agency: {'✓ Yes' if self.results.get('found_expected_agency') else '✗ No'}")
            
            print(f"\n--- Ray White Links Found ---")
            for i, result in enumerate(self.results.get('search_results', [])[:5], 1):
                print(f"\n{i}. {result['title'][:60]}")
                print(f"   URL: {result['url'][:80]}")
        else:
            print(f"\n✗ FAILED")
            print(f"Error: {self.results.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 70)
    
    def save_results(self, filename='duckduckgo_test_results.json'):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to {filename}")


def main():
    """Main function to run the test"""
    test = DuckDuckGoPropertySearch()
    
    # Run the test
    results = test.run_test()
    
    # Print summary
    test.print_summary()
    
    # Save results
    test.save_results()
    
    # Return success status
    return results.get('success', False)


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
