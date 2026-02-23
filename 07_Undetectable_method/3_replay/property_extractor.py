#!/usr/bin/env python3
"""
Property Data Extractor - Extracts structured data from property pages

Handles parsing realestate.com.au property detail pages and 
extracting all relevant information.
"""

import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from datetime import datetime
import json


class PropertyExtractor:
    """Extracts property data from HTML"""
    
    def __init__(self):
        self.property_data = {}
    
    def extract_from_html(self, html: str, page_url: str, suburb: str, session_id: str) -> Dict:
        """
        Extract property data from HTML
        
        Args:
            html: Page HTML content
            page_url: URL of the property page
            suburb: Suburb name
            session_id: Recording session ID
            
        Returns:
            Dict: Structured property data
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        property_data = {
            'property_url': page_url,
            'suburb': suburb.lower(),
            'session_used': session_id,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Extract address
        property_data['address'] = self._extract_address(soup, page_url)
        
        # Extract price
        property_data['price'] = self._extract_price(soup)
        
        # Extract property type
        property_data['property_type'] = self._extract_property_type(soup)
        
        # Extract features (beds, baths, parking)
        property_data['features'] = self._extract_features(soup)
        
        # Extract description
        property_data['description'] = self._extract_description(soup)
        
        # Extract amenities/features list
        property_data['amenities'] = self._extract_amenities(soup)
        
        # Extract agent information
        property_data['agent'] = self._extract_agent(soup)
        
        # Extract images
        property_data['images'] = self._extract_images(soup)
        
        # Extract listing date if available
        property_data['listing_date'] = self._extract_listing_date(soup)
        
        # Store raw HTML snippet for debugging
        property_data['raw_html_snippet'] = self._get_html_snippet(soup)
        
        return property_data
    
    def _extract_address(self, soup: BeautifulSoup, page_url: str) -> Dict:
        """Extract property address"""
        address = {
            'full': None,
            'street': None,
            'suburb': None,
            'state': None,
            'postcode': None
        }
        
        # Try multiple selectors for address
        selectors = [
            'h1[class*="address"]',
            'h1',
            '[data-testid="address"]',
            '[class*="property-address"]',
            'span[itemprop="streetAddress"]'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                address['full'] = elem.get_text(strip=True)
                break
        
        # If no address found, try to extract from URL
        if not address['full']:
            # Try to parse from URL pattern
            url_pattern = r'/property/([^/]+)'
            match = re.search(url_pattern, page_url)
            if match:
                address['full'] = match.group(1).replace('-', ' ').title()
        
        # Parse address components if we have full address
        if address['full']:
            # Try to extract postcode
            postcode_match = re.search(r'\b(\d{4})\b', address['full'])
            if postcode_match:
                address['postcode'] = postcode_match.group(1)
            
            # Try to extract state
            state_match = re.search(r'\b(QLD|NSW|VIC|SA|WA|TAS|NT|ACT)\b', address['full'], re.IGNORECASE)
            if state_match:
                address['state'] = state_match.group(1).upper()
            
            # Try to extract suburb (word before state/postcode)
            if address['state'] or address['postcode']:
                parts = address['full'].split(',')
                if len(parts) >= 2:
                    address['suburb'] = parts[-2].strip()
                    address['street'] = ','.join(parts[:-2]).strip() if len(parts) > 2 else parts[0].strip()
        
        return address
    
    def _extract_price(self, soup: BeautifulSoup) -> Dict:
        """Extract price information"""
        price = {
            'display': None,
            'value': None,
            'type': None
        }
        
        # Try multiple selectors for price
        selectors = [
            '[data-testid="listing-details__summary-title"]',
            '[class*="property-price"]',
            '[class*="price"]',
            'p[class*="price"]',
            'span[class*="price"]'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                # Check if it looks like a price
                if '$' in price_text or 'contact' in price_text.lower() or 'auction' in price_text.lower():
                    price['display'] = price_text
                    break
        
        # Try to extract numeric value
        if price['display']:
            # Remove $ and commas, try to extract number
            cleaned = re.sub(r'[^\d.]', '', price['display'])
            if cleaned:
                try:
                    price['value'] = int(float(cleaned))
                except ValueError:
                    pass
            
            # Determine price type
            price_lower = price['display'].lower()
            if 'auction' in price_lower:
                price['type'] = 'auction'
            elif 'contact' in price_lower or 'offers' in price_lower:
                price['type'] = 'contact_agent'
            elif '-' in price['display'] and '$' in price['display']:
                price['type'] = 'range'
            else:
                price['type'] = 'fixed'
        
        return price
    
    def _extract_property_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property type (House, Unit, Townhouse, etc.)"""
        # Try to find property type
        selectors = [
            '[data-testid="listing-summary-property-type"]',
            '[class*="property-type"]'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        # Try to infer from page content
        text = soup.get_text().lower()
        if 'house' in text and 'townhouse' not in text:
            return 'House'
        elif 'unit' in text or 'apartment' in text:
            return 'Unit'
        elif 'townhouse' in text:
            return 'Townhouse'
        elif 'villa' in text:
            return 'Villa'
        
        return None
    
    def _extract_features(self, soup: BeautifulSoup) -> Dict:
        """Extract property features (beds, baths, parking, sizes)"""
        features = {
            'bedrooms': None,
            'bathrooms': None,
            'parking': None,
            'land_size': None,
            'building_size': None
        }
        
        # Look for feature elements
        feature_selectors = [
            '[class*="property-features"]',
            '[data-testid*="property-features"]',
            '[class*="listing-details__summary"]'
        ]
        
        feature_text = ''
        for selector in feature_selectors:
            elem = soup.select_one(selector)
            if elem:
                feature_text = elem.get_text()
                break
        
        # If not found, get all text
        if not feature_text:
            feature_text = soup.get_text()
        
        # Extract bedrooms
        bed_match = re.search(r'(\d+)\s*(?:bed|bedroom|br)', feature_text, re.IGNORECASE)
        if bed_match:
            features['bedrooms'] = int(bed_match.group(1))
        
        # Extract bathrooms
        bath_match = re.search(r'(\d+)\s*(?:bath|bathroom)', feature_text, re.IGNORECASE)
        if bath_match:
            features['bathrooms'] = int(bath_match.group(1))
        
        # Extract parking
        parking_match = re.search(r'(\d+)\s*(?:car|parking|garage)', feature_text, re.IGNORECASE)
        if parking_match:
            features['parking'] = int(parking_match.group(1))
        
        # Extract land size
        land_match = re.search(r'(\d+(?:,\d+)?)\s*(?:m²|sqm|m2).*?land', feature_text, re.IGNORECASE)
        if land_match:
            features['land_size'] = land_match.group(1).replace(',', '') + ' sqm'
        
        # Extract building size
        building_match = re.search(r'(?:building|internal).*?(\d+(?:,\d+)?)\s*(?:m²|sqm|m2)', feature_text, re.IGNORECASE)
        if building_match:
            features['building_size'] = building_match.group(1).replace(',', '') + ' sqm'
        
        return features
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property description"""
        # Try multiple selectors
        selectors = [
            '[data-testid="listing-details__description"]',
            '[class*="property-description"]',
            '[class*="description"]'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                description = elem.get_text(strip=True)
                if len(description) > 50:  # Ensure it's substantive
                    return description
        
        return None
    
    def _extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """Extract list of amenities/features"""
        amenities = []
        
        # Look for feature lists
        feature_lists = soup.select('ul li, [class*="feature"] li')
        
        for item in feature_lists:
            text = item.get_text(strip=True)
            # Filter out very short or numeric-only items
            if text and len(text) > 2 and not text.isdigit():
                amenities.append(text)
        
        # Deduplicate
        amenities = list(set(amenities))
        
        return amenities[:20]  # Limit to 20 items
    
    def _extract_agent(self, soup: BeautifulSoup) -> Dict:
        """Extract agent information"""
        agent = {
            'name': None,
            'agency': None,
            'phone': None
        }
        
        # Try to find agent name
        agent_selectors = [
            '[class*="agent-name"]',
            '[data-testid*="agent-name"]'
        ]
        
        for selector in agent_selectors:
            elem = soup.select_one(selector)
            if elem:
                agent['name'] = elem.get_text(strip=True)
                break
        
        # Try to find agency
        agency_selectors = [
            '[class*="agency-name"]',
            '[data-testid*="agency"]'
        ]
        
        for selector in agency_selectors:
            elem = soup.select_one(selector)
            if elem:
                agent['agency'] = elem.get_text(strip=True)
                break
        
        # Try to find phone
        phone_match = re.search(r'(\d{2}\s?\d{4}\s?\d{4})|(\(\d{2}\)\s?\d{4}\s?\d{4})', soup.get_text())
        if phone_match:
            agent['phone'] = phone_match.group(0)
        
        return agent
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract image URLs"""
        images = []
        
        # Find all images
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and 'property' in src.lower():
                # Skip tiny images (likely logos/icons)
                if 'thumb' not in src.lower() and 'icon' not in src.lower():
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.realestate.com.au' + src
                    images.append(src)
        
        # Deduplicate while preserving order
        seen = set()
        unique_images = []
        for img in images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        return unique_images[:15]  # Limit to 15 images
    
    def _extract_listing_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract listing date if available"""
        date_text = soup.get_text()
        
        # Look for date patterns
        date_patterns = [
            r'listed\s+(\d{1,2}\s+\w+\s+\d{4})',
            r'added\s+(\d{1,2}\s+\w+\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _get_html_snippet(self, soup: BeautifulSoup) -> str:
        """Get a snippet of HTML for debugging"""
        # Get first 500 characters of text
        text = soup.get_text(strip=True)
        return text[:500] if text else ''
    
    def validate_extraction(self, property_data: Dict, required_fields: List[str] = None) -> tuple:
        """
        Validate that required fields were extracted
        
        Args:
            property_data: Extracted property data
            required_fields: List of required field names
            
        Returns:
            tuple: (is_valid, missing_fields)
        """
        if required_fields is None:
            required_fields = ['property_url', 'address', 'price']
        
        missing = []
        
        for field in required_fields:
            if field not in property_data or not property_data[field]:
                missing.append(field)
            elif isinstance(property_data[field], dict):
                # Check if dict has any non-None values
                if not any(property_data[field].values()):
                    missing.append(field)
        
        is_valid = len(missing) == 0
        return is_valid, missing


def test_extractor():
    """Test the property extractor with sample HTML"""
    print("\n" + "="*70)
    print("  TESTING PROPERTY EXTRACTOR")
    print("="*70)
    
    # Sample HTML (simplified realestate.com.au structure)
    sample_html = """
    <html>
        <h1>123 Test Street, Robina QLD 4226</h1>
        <p class="property-price">$750,000</p>
        <div class="property-features">
            <span>4 bed</span>
            <span>2 bath</span>
            <span>2 car</span>
        </div>
        <div class="property-description">
            Beautiful family home in prime location with pool and large backyard.
        </div>
    </html>
    """
    
    extractor = PropertyExtractor()
    result = extractor.extract_from_html(
        sample_html,
        'https://www.realestate.com.au/property/123-test-st',
        'robina',
        'test_session'
    )
    
    print("\n📊 Extracted Data:")
    print(json.dumps(result, indent=2, default=str))
    
    is_valid, missing = extractor.validate_extraction(result)
    
    if is_valid:
        print("\n✅ Validation PASSED")
    else:
        print(f"\n⚠️  Validation FAILED - Missing fields: {missing}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_extractor()
