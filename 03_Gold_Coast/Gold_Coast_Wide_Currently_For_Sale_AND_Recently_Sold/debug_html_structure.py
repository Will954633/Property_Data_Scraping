#!/usr/bin/env python3
"""
Debug HTML Structure - Find Agent/Agency Elements
Last Updated: 31/01/2026, 9:47 am (Brisbane Time)

This script saves the HTML and searches for agent/agency related elements
to help us understand the actual HTML structure Domain.com.au uses.
"""

import sys
import re
from bs4 import BeautifulSoup

sys.path.append('../../07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search')

try:
    from headless_forsale_mongodb_scraper import HeadlessForSaleMongoDBScraper
except ImportError as e:
    print(f"ERROR: Could not import scraper: {e}")
    exit(1)


def debug_html_structure(url: str):
    """Debug the HTML structure to find agent/agency elements"""
    print("\n" + "=" * 80)
    print("DEBUG HTML STRUCTURE FOR AGENT/AGENCY EXTRACTION")
    print("=" * 80)
    print(f"\nURL: {url}\n")
    
    scraper = None
    try:
        scraper = HeadlessForSaleMongoDBScraper('test')
        
        # Load the page
        print("→ Loading page...")
        scraper.driver.get(url)
        import time
        time.sleep(5)
        
        html = scraper.driver.page_source
        print(f"✓ HTML loaded ({len(html):,} chars)\n")
        
        # Save HTML to file
        html_file = 'debug_html_output.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✓ HTML saved to: {html_file}\n")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        print("=" * 80)
        print("SEARCHING FOR AGENT/AGENCY ELEMENTS")
        print("=" * 80)
        
        # 1. Find all elements with data-testid containing 'agent'
        print("\n1. Elements with data-testid containing 'agent':")
        print("-" * 80)
        agent_testids = soup.find_all(attrs={'data-testid': re.compile(r'agent', re.I)})
        if agent_testids:
            for elem in agent_testids[:10]:  # Limit to first 10
                testid = elem.get('data-testid')
                text = elem.get_text(strip=True)[:100]
                print(f"   data-testid=\"{testid}\"")
                print(f"   Text: {text}")
                print()
        else:
            print("   ❌ No elements found")
        
        # 2. Find all elements with data-testid containing 'agency'
        print("\n2. Elements with data-testid containing 'agency':")
        print("-" * 80)
        agency_testids = soup.find_all(attrs={'data-testid': re.compile(r'agency', re.I)})
        if agency_testids:
            for elem in agency_testids[:10]:
                testid = elem.get('data-testid')
                text = elem.get_text(strip=True)[:100]
                print(f"   data-testid=\"{testid}\"")
                print(f"   Text: {text}")
                print()
        else:
            print("   ❌ No elements found")
        
        # 3. Find all links to agent profiles
        print("\n3. Links to agent profiles (/real-estate-agent/):")
        print("-" * 80)
        agent_links = soup.find_all('a', href=re.compile(r'/real-estate-agent/', re.I))
        if agent_links:
            for link in agent_links[:10]:
                href = link.get('href')
                text = link.get_text(strip=True)
                print(f"   href=\"{href}\"")
                print(f"   Text: {text}")
                print()
        else:
            print("   ❌ No agent profile links found")
        
        # 4. Search for text containing "Ray White"
        print("\n4. Elements containing 'Ray White':")
        print("-" * 80)
        ray_white_elems = soup.find_all(string=re.compile(r'Ray White', re.I))
        if ray_white_elems:
            for elem in ray_white_elems[:5]:
                parent = elem.parent
                tag = parent.name if parent else 'N/A'
                classes = parent.get('class', []) if parent else []
                testid = parent.get('data-testid', 'N/A') if parent else 'N/A'
                print(f"   Tag: <{tag}> class=\"{' '.join(classes)}\" data-testid=\"{testid}\"")
                print(f"   Text: {elem.strip()[:100]}")
                print()
        else:
            print("   ❌ No 'Ray White' text found")
        
        # 5. Find all data-testid attributes
        print("\n5. All unique data-testid values (first 50):")
        print("-" * 80)
        all_testids = set()
        for elem in soup.find_all(attrs={'data-testid': True}):
            all_testids.add(elem.get('data-testid'))
        
        sorted_testids = sorted(list(all_testids))[:50]
        for testid in sorted_testids:
            print(f"   - {testid}")
        
        print(f"\n   Total unique data-testid values: {len(all_testids)}")
        
        # 6. Save all data-testid values to file
        testid_file = 'debug_all_testids.txt'
        with open(testid_file, 'w') as f:
            for testid in sorted(list(all_testids)):
                f.write(f"{testid}\n")
        print(f"   ✓ All data-testid values saved to: {testid_file}")
        
        print("\n" + "=" * 80)
        print("DEBUG COMPLETE")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review debug_html_output.html to see the full page structure")
        print("2. Review debug_all_testids.txt to see all data-testid values")
        print("3. Search for agent/agency related testids in the list")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if scraper:
            scraper.close()


def main():
    url = input("Enter Domain.com.au URL: ").strip()
    if not url:
        url = "https://www.domain.com.au/7-turnberry-court-robina-qld-4226-2020210482"
        print(f"Using default URL: {url}")
    
    debug_html_structure(url)


if __name__ == "__main__":
    main()
