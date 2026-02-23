#!/usr/bin/env python3
"""
Test script to extract auction time and location data from Domain listings

Last Updated: 27/01/2026, 10:21 AM (Monday) - Brisbane
- Created to test extraction of auction details from Domain property listings
- Extracts: auction date, time, location/venue
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from typing import Dict, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_driver(headless: bool = True):
    """Initialize Selenium WebDriver"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless=new')
    
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def extract_auction_data(html: str) -> Optional[Dict]:
    """
    Extract auction date, time, and location from HTML
    Returns dict with auction details or None if not an auction
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    auction_data = {
        'is_auction': False,
        'auction_date': None,
        'auction_time': None,
        'auction_day': None,
        'auction_venue': None,
        'auction_address': None,
        'raw_auction_text': None
    }
    
    # Method 1: Look for auction-specific sections
    # Common patterns: "Auction", "Inspection & Auction times"
    
    # Search for elements containing "auction" in text
    auction_sections = soup.find_all(['div', 'section', 'span', 'p'], 
                                     string=re.compile(r'auction', re.IGNORECASE))
    
    if auction_sections:
        logger.info(f"Found {len(auction_sections)} elements mentioning 'auction'")
        auction_data['is_auction'] = True
    
    # Method 2: Look for specific auction time patterns
    # Pattern examples:
    # "Saturday, 31 Jan"
    # "10:00am"
    # "In - Rooms at The Event, Star Casino - 1 Casino Drive Broadbeach"
    
    # Search for date patterns
    date_patterns = [
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
        r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
    ]
    
    # Search for time patterns
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)',
        r'(\d{1,2})\s*(am|pm|AM|PM)',
    ]
    
    # Get all text content
    page_text = soup.get_text()
    
    # Extract date
    for pattern in date_patterns:
        match = re.search(pattern, page_text)
        if match:
            auction_data['raw_auction_text'] = match.group(0)
            if len(match.groups()) == 3:
                day, date_num, month = match.groups()
                auction_data['auction_day'] = day
                auction_data['auction_date'] = f"{date_num} {month}"
                logger.info(f"Found auction date: {day}, {date_num} {month}")
            break
    
    # Extract time
    for pattern in time_patterns:
        match = re.search(pattern, page_text)
        if match:
            auction_data['auction_time'] = match.group(0)
            logger.info(f"Found auction time: {match.group(0)}")
            break
    
    # Method 3: Look for venue/location information
    # Pattern: "In - [Venue Name] - [Address]" or "At [Location]"
    venue_patterns = [
        r'In\s*-\s*([^-]+)-\s*(.+?)(?:\n|$)',
        r'At\s+([^\n]+)',
        r'Venue:\s*([^\n]+)',
    ]
    
    for pattern in venue_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                auction_data['auction_venue'] = match.group(1).strip()
                auction_data['auction_address'] = match.group(2).strip()
                logger.info(f"Found venue: {match.group(1).strip()}")
                logger.info(f"Found address: {match.group(2).strip()}")
            else:
                auction_data['auction_venue'] = match.group(1).strip()
                logger.info(f"Found venue: {match.group(1).strip()}")
            break
    
    # Method 4: Look for structured data in specific elements
    # Check for data-testid or specific class names
    auction_elements = soup.find_all(attrs={'data-testid': re.compile(r'auction', re.IGNORECASE)})
    if auction_elements:
        logger.info(f"Found {len(auction_elements)} elements with auction data-testid")
        for elem in auction_elements:
            logger.debug(f"  Element: {elem.name}, text: {elem.get_text()[:100]}")
    
    # Check for inspection/auction time sections
    inspection_sections = soup.find_all(['div', 'section'], 
                                       class_=re.compile(r'inspection|auction|time', re.IGNORECASE))
    if inspection_sections:
        logger.info(f"Found {len(inspection_sections)} inspection/auction sections")
        for section in inspection_sections[:3]:  # Check first 3
            section_text = section.get_text()
            logger.debug(f"  Section text: {section_text[:200]}")
            
            # Try to extract structured data from these sections
            if 'auction' in section_text.lower():
                # Look for date in this section
                for pattern in date_patterns:
                    match = re.search(pattern, section_text)
                    if match and not auction_data['auction_date']:
                        if len(match.groups()) == 3:
                            day, date_num, month = match.groups()
                            auction_data['auction_day'] = day
                            auction_data['auction_date'] = f"{date_num} {month}"
                
                # Look for time in this section
                for pattern in time_patterns:
                    match = re.search(pattern, section_text)
                    if match and not auction_data['auction_time']:
                        auction_data['auction_time'] = match.group(0)
    
    return auction_data if auction_data['is_auction'] else None


def test_auction_extraction(url: str):
    """Test auction data extraction on a specific URL"""
    logger.info("="*80)
    logger.info("AUCTION DATA EXTRACTION TEST")
    logger.info("="*80)
    logger.info(f"Testing URL: {url}")
    
    driver = init_driver(headless=True)
    
    try:
        # Load the page
        logger.info("Loading page...")
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Get HTML
        html = driver.page_source
        logger.info(f"Extracted HTML ({len(html):,} chars)")
        
        # Extract auction data
        logger.info("\nExtracting auction data...")
        auction_data = extract_auction_data(html)
        
        # Display results
        logger.info("\n" + "="*80)
        logger.info("EXTRACTION RESULTS")
        logger.info("="*80)
        
        if auction_data:
            logger.info(f"✓ Is Auction: {auction_data['is_auction']}")
            logger.info(f"  Auction Day: {auction_data['auction_day'] or 'Not found'}")
            logger.info(f"  Auction Date: {auction_data['auction_date'] or 'Not found'}")
            logger.info(f"  Auction Time: {auction_data['auction_time'] or 'Not found'}")
            logger.info(f"  Auction Venue: {auction_data['auction_venue'] or 'Not found'}")
            logger.info(f"  Auction Address: {auction_data['auction_address'] or 'Not found'}")
            
            # Summary
            if auction_data['auction_date'] and auction_data['auction_time']:
                logger.info(f"\n📅 AUCTION SCHEDULED:")
                logger.info(f"   {auction_data['auction_day']}, {auction_data['auction_date']} at {auction_data['auction_time']}")
                if auction_data['auction_venue']:
                    logger.info(f"   Venue: {auction_data['auction_venue']}")
                    if auction_data['auction_address']:
                        logger.info(f"   Address: {auction_data['auction_address']}")
            else:
                logger.warning("⚠ Auction detected but date/time not fully extracted")
        else:
            logger.info("✗ Not an auction listing or no auction data found")
        
        logger.info("="*80)
        
        return auction_data
        
    finally:
        driver.quit()
        logger.info("Browser closed")


if __name__ == "__main__":
    # Test with the specific property mentioned
    test_url = "https://www.domain.com.au/330-ron-penhaligon-way-robina-qld-4226-2020515164"
    
    result = test_auction_extraction(test_url)
    
    if result:
        print("\n" + "="*80)
        print("JSON OUTPUT:")
        print("="*80)
        import json
        print(json.dumps(result, indent=2))
