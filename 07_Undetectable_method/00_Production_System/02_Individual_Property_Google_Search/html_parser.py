#!/usr/bin/env python3
"""
HTML Parser for Domain.com.au Listing Pages
Extracts all property data from HTML without OCR

Last Edit: 31/01/2026, 9:43 am (Brisbane Time)
- Enhanced extract_agent_info() to properly scrape agency name and agent names
- Uses data-testid attributes for reliable extraction
- Supports multiple agents per listing
- Stores agent_names as array and agent_name as comma-separated string
"""

import json
import re
from bs4 import BeautifulSoup
from datetime import datetime


def parse_listing_html(html, address):
    """
    Parse domain.com.au listing page HTML to extract all property data
    
    Args:
        html: Raw HTML string from the listing page
        address: The address being searched
        
    Returns:
        dict: Complete property data extracted from HTML
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    property_data = {
        "address": address,
        "extraction_method": "HTML",
        "extraction_date": datetime.now().isoformat()
    }
    
    # 1. Try to extract JSON-LD structured data first (most reliable)
    try:
        json_ld_data = extract_json_ld(soup)
        if json_ld_data:
            property_data.update(json_ld_data)
            print(f"  ✓ Extracted data from JSON-LD schema")
    except Exception as e:
        print(f"  ⚠ JSON-LD extraction failed: {e}")
    
    # 2. Extract from meta tags (fallback)
    try:
        meta_data = extract_meta_tags(soup)
        if meta_data:
            # Only add if not already present from JSON-LD
            for key, value in meta_data.items():
                if key not in property_data and value:
                    property_data[key] = value
            print(f"  ✓ Extracted data from meta tags")
    except Exception as e:
        print(f"  ⚠ Meta tag extraction failed: {e}")
    
    # 3. Extract from HTML elements (additional fallback)
    try:
        element_data = extract_html_elements(soup)
        if element_data:
            for key, value in element_data.items():
                if key not in property_data and value:
                    property_data[key] = value
            print(f"  ✓ Extracted data from HTML elements")
    except Exception as e:
        print(f"  ⚠ HTML element extraction failed: {e}")
    
    # 4. Extract inspection times
    try:
        inspections = extract_inspection_times(soup)
        if inspections:
            property_data['inspection_times'] = inspections
            print(f"  ✓ Found {len(inspections)} inspection times")
    except Exception as e:
        print(f"  ⚠ Inspection time extraction failed: {e}")
    
    # 5. Extract agent information
    try:
        agent_info = extract_agent_info(soup)
        if agent_info:
            property_data.update(agent_info)
            print(f"  ✓ Extracted agent information")
    except Exception as e:
        print(f"  ⚠ Agent info extraction failed: {e}")
    
    # 6. Extract property features
    try:
        features = extract_features(soup)
        if features:
            property_data['features'] = features
            print(f"  ✓ Found {len(features)} property features")
    except Exception as e:
        print(f"  ⚠ Feature extraction failed: {e}")
    
    # 7. Extract images and floor plans
    try:
        property_images, floor_plans = extract_images_and_floorplans(html)
        if property_images:
            property_data['property_images'] = property_images
            print(f"  ✓ Found {len(property_images)} property images")
        if floor_plans:
            property_data['floor_plans'] = floor_plans
            print(f"  ✓ Found {len(floor_plans)} floor plans")
    except Exception as e:
        print(f"  ⚠ Image extraction failed: {e}")
    
    return property_data


def extract_json_ld(soup):
    """Extract data from JSON-LD structured data"""
    data = {}
    inspection_times = []
    
    # Find all script tags with type application/ld+json
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    
    for script in json_ld_scripts:
        try:
            json_data = json.loads(script.string)
            
            # Handle array of JSON-LD objects
            if isinstance(json_data, list):
                # Process each item in the list
                for item in json_data:
                    # Extract inspection events
                    if item.get('@type') == 'Event' and item.get('name') == 'Inspection':
                        inspection_times.append({
                            'start': item.get('startDate'),
                            'end': item.get('endDate')
                        })
                    
                    # Extract property data from Residence type
                    if item.get('@type') == 'Residence':
                        addr = item.get('address', {})
                        if isinstance(addr, dict):
                            if 'streetAddress' in addr:
                                data['street_address'] = addr['streetAddress']
                            if 'addressLocality' in addr:
                                data['suburb'] = addr['addressLocality']
                            if 'postalCode' in addr:
                                data['postcode'] = addr['postalCode']
                
                # Use first item for backwards compatibility
                json_data = json_data[0] if json_data else {}
            
            # Extract based on @type
            if json_data.get('@type') in ['SingleFamilyResidence', 'House', 'Apartment', 'RealEstateListing']:
                # Bedrooms
                if 'numberOfBedrooms' in json_data:
                    data['bedrooms'] = int(json_data['numberOfBedrooms'])
                elif 'numberOfRooms' in json_data:
                    data['bedrooms'] = int(json_data['numberOfRooms'])
                
                # Bathrooms
                if 'numberOfBathroomsTotal' in json_data:
                    data['bathrooms'] = int(json_data['numberOfBathroomsTotal'])
                
                # Price
                if 'offers' in json_data:
                    offers = json_data['offers']
                    if isinstance(offers, dict):
                        if 'price' in offers:
                            data['price'] = str(offers['price'])
                        elif 'priceSpecification' in offers:
                            data['price'] = str(offers['priceSpecification'])
                
                # Address
                if 'address' in json_data:
                    addr = json_data['address']
                    if isinstance(addr, dict):
                        if 'streetAddress' in addr:
                            data['street_address'] = addr['streetAddress']
                        if 'addressLocality' in addr:
                            data['suburb'] = addr['addressLocality']
                        if 'postalCode' in addr:
                            data['postcode'] = addr['postalCode']
                
                # Floor area / land size
                if 'floorSize' in json_data:
                    size_data = json_data['floorSize']
                    if isinstance(size_data, dict) and 'value' in size_data:
                        data['land_size_sqm'] = int(size_data['value'])
                
                # Property type
                if '@type' in json_data:
                    prop_type = json_data['@type']
                    if prop_type == 'SingleFamilyResidence':
                        data['property_type'] = 'House'
                    elif prop_type in ['House', 'Apartment', 'Townhouse']:
                        data['property_type'] = prop_type
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            continue
    
    # Add inspection times if found
    if inspection_times:
        data['inspection_times'] = inspection_times
    
    return data


def extract_meta_tags(soup):
    """Extract data from meta tags"""
    data = {}
    
    # Open Graph tags
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        data['og_title'] = og_title['content']
    
    og_description = soup.find('meta', property='og:description')
    if og_description and og_description.get('content'):
        desc = og_description['content']
        data['description'] = desc
        
        # Try to extract bed/bath from description
        bed_match = re.search(r'(\d+)\s*bed', desc, re.I)
        if bed_match and 'bedrooms' not in data:
            data['bedrooms'] = int(bed_match.group(1))
        
        bath_match = re.search(r'(\d+)\s*bath', desc, re.I)
        if bath_match and 'bathrooms' not in data:
            data['bathrooms'] = int(bath_match.group(1))
        
        car_match = re.search(r'(\d+)\s*car', desc, re.I)
        if car_match and 'parking' not in data:
            data['parking'] = int(car_match.group(1))
    
    return data


def extract_html_elements(soup):
    """Extract data from HTML elements using CSS selectors and aria-labels"""
    data = {}
    
    # PRIORITY: Extract from property-features section using data-testid
    features_wrapper = soup.find(attrs={'data-testid': 'property-features-wrapper'})
    if features_wrapper:
        # Extract bedrooms, bathrooms, parking from individual feature elements
        feature_elems = features_wrapper.find_all(attrs={'data-testid': 'property-features-feature'})
        for feature_elem in feature_elems:
            text_container = feature_elem.find(attrs={'data-testid': 'property-features-text-container'})
            if text_container:
                # Get the number (first part)
                number_text = text_container.get_text(strip=True)
                num_match = re.match(r'^(\d+)', number_text)
                if num_match:
                    number = int(num_match.group(1))
                    
                    # Get the label text
                    label_elem = text_container.find(attrs={'data-testid': 'property-features-text'})
                    if label_elem:
                        label = label_elem.get_text(strip=True).lower()
                        
                        # Map to our field names
                        if 'bed' in label:
                            data['bedrooms'] = number
                        elif 'bath' in label:
                            data['bathrooms'] = number
                        elif 'park' in label or 'car' in label:
                            data['carspaces'] = number
    
    # Extract property type from listing-summary-property-type
    property_type_elem = soup.find(attrs={'data-testid': 'listing-summary-property-type'})
    if property_type_elem:
        prop_type_text = property_type_elem.get_text(strip=True)
        if prop_type_text:
            data['property_type'] = prop_type_text
    
    # Fallback: Try old method if features not found
    if 'bedrooms' not in data:
        summary_elems = soup.find_all(string=re.compile(r'\d+\s*Beds?\d+\s*Baths?', re.I))
        for elem in summary_elems:
            parent = elem.parent
            if parent:
                full_text = parent.get_text(strip=True)
                # Parse "3 Beds2 Baths2 Parking322m²"
                feature_match = re.search(r'(\d+)\s*Beds?(\d+)\s*Baths?(\d+)\s*Parking?(\d+)m²?', full_text, re.I)
                if feature_match:
                    data['bedrooms'] = int(feature_match.group(1))
                    data['bathrooms'] = int(feature_match.group(2))
                    data['carspaces'] = int(feature_match.group(3))
                    data['land_size_sqm'] = int(feature_match.group(4))
                    break
    
    # PRIORITY: Extract price from data-testid first (most reliable)
    price_elem = soup.find(attrs={'data-testid': 'listing-details__summary-title'})
    if price_elem:
        # Get only the direct text content of the span, not nested elements
        price_span = price_elem.find('span')
        if price_span:
            data['price'] = price_span.get_text(strip=True)
        else:
            data['price'] = price_elem.get_text(strip=True)
    
    # Fallback: Look for price in text
    if 'price' not in data:
        price_elems = soup.find_all(['h1', 'span', 'div'], string=re.compile(r'(Offers over|Contact|Auction|\$[\d,]+)', re.I))
        for elem in price_elems:
            price_text = elem.get_text(strip=True)
            if price_text and ('$' in price_text or 'Offers' in price_text or 'Contact' in price_text or 'Auction' in price_text):
                if len(price_text) < 100:  # Avoid long descriptions
                    data['price'] = price_text
                    break
    
    # Extract agent's property description from collapsible panel
    agents_description_parts = []
    
    # Find the full listing description section
    desc_section = soup.find('div', attrs={'data-testid': 'listing-details__description'})
    if desc_section:
        # Extract headline
        headline_elem = desc_section.find('h3', attrs={'data-testid': 'listing-details__description-headline'})
        if headline_elem:
            agents_description_parts.append(headline_elem.get_text(strip=True))
        
        # Extract all paragraph content from the collapsible panel
        collapsible = desc_section.find(id='collapsible-panel')
        if collapsible:
            # Get all paragraphs within the expander content
            paragraphs = collapsible.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    agents_description_parts.append(text)
    
    # Combine agent's description parts
    if agents_description_parts:
        data['agents_description'] = ' '.join(agents_description_parts)
    
    # Property type - look for "House", "Unit" etc. near features
    type_patterns = [
        (r'\bHouse\b', 'House'),
        (r'\bTownhouse\b', 'Townhouse'),
        (r'\bApartment\b', 'Apartment'),
        (r'\bUnit\b', 'Unit'),
        (r'\bVilla\b', 'Villa')
    ]
    for pattern, prop_type in type_patterns:
        if re.search(pattern, soup.get_text(), re.I) and 'property_type' not in data:
            data['property_type'] = prop_type
            break
    
    return data


def extract_inspection_times(soup):
    """Extract open inspection times from listing page - cleaned and formatted"""
    inspections = []
    
    # Extract from JSON-LD structured data for clean inspection times
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            json_data = json.loads(script.string)
            if isinstance(json_data, list):
                for item in json_data:
                    if item.get('@type') == 'Event' and item.get('name') == 'Inspection':
                        start_date = item.get('startDate', '')
                        end_date = item.get('endDate', '')
                        if start_date and end_date:
                            # Parse ISO format dates
                            try:
                                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                                # Format as "Saturday, 15 Nov 11:30am - 12:00pm"
                                formatted = f"{start_dt.strftime('%A, %d %b')} {start_dt.strftime('%-I:%M%p').lower()} - {end_dt.strftime('%-I:%M%p').lower()}"
                                inspections.append(formatted)
                            except:
                                pass
        except:
            continue
    
    # FALLBACK: Look for data-testid inspection blocks for clean format
    if not inspections:
        inspection_blocks = soup.find_all(attrs={'data-testid': 'listing-details__inspections-block'})
        for block in inspection_blocks:
            day_elem = block.find(attrs={'data-testid': 'listing-details__inspections-block-day'})
            time_elem = block.find(attrs={'data-testid': 'listing-details__inspections-block-time'})
            if day_elem and time_elem:
                day = day_elem.get_text(strip=True)
                time = time_elem.get_text(strip=True)
                inspections.append(f"{day} {time}")
    
    return inspections


def extract_agent_info(soup):
    """Extract agent and agency information from Domain.com.au listing page"""
    data = {}
    agent_names = []
    
    # PRIORITY 1: Extract from data-testid attributes (most reliable)
    # Look for agency name - CORRECTED SELECTOR
    agency_elem = soup.find(attrs={'data-testid': 'listing-details__agent-details-agency-name'})
    if agency_elem:
        agency_name = agency_elem.get_text(strip=True)
        if agency_name:
            data['agency'] = agency_name
    
    # Look for agent names - CORRECTED SELECTOR
    # Domain may have multiple agent detail sections for multiple agents
    agent_detail_sections = soup.find_all(attrs={'data-testid': 'listing-details__agent-details'})
    for section in agent_detail_sections:
        agent_name_elem = section.find(attrs={'data-testid': 'listing-details__agent-details-agent-name'})
        if agent_name_elem:
            name = agent_name_elem.get_text(strip=True)
            if name and len(name.split()) >= 1 and name not in agent_names:  # At least one word
                agent_names.append(name)
    
    # PRIORITY 2: Fallback to looking for agent profile links if no agents found
    if not agent_names:
        agent_profile_links = soup.find_all('a', href=re.compile(r'/real-estate-agent/', re.I))
        for link in agent_profile_links:
            name = link.get_text(strip=True)
            if name and len(name.split()) >= 1 and name not in agent_names:
                # Avoid common false positives
                if not any(word in name.lower() for word in ['view', 'profile', 'contact', 'call', 'email', 'agent admin']):
                    agent_names.append(name)
    
    # PRIORITY 3: Look for agency name in alternative locations if not found
    if 'agency' not in data:
        # Try finding agency in links or spans with agency-related classes
        agency_elems = soup.find_all(['a', 'span', 'div'], class_=re.compile(r'agency|office', re.I))
        for elem in agency_elems:
            agency = elem.get_text(strip=True)
            # Filter out common false positives and ensure reasonable length
            if agency and 3 < len(agency) < 100:
                # Avoid generic terms
                if not any(word in agency.lower() for word in ['contact', 'call', 'email', 'phone', 'view', 'advertise']):
                    data['agency'] = agency
                    break
    
    # Store agent names
    if agent_names:
        # Remove duplicates while preserving order
        seen = set()
        unique_agents = []
        for name in agent_names:
            if name not in seen:
                seen.add(name)
                unique_agents.append(name)
        
        # Store as array for multiple agents
        data['agent_names'] = unique_agents
        # Also store as comma-separated string for backwards compatibility
        data['agent_name'] = ', '.join(unique_agents)
    
    return data


def extract_features(soup):
    """Extract property features (pool, air con, etc.) - avoiding duplicates"""
    features = []
    seen_keywords = set()
    
    # Look for features in description or feature sections
    text = soup.get_text()
    feature_keywords = ['pool', 'air conditioning', 'air con', 'garage', 'heating', 'cooling', 
                       'dishwasher', 'alarm', 'balcony', 'deck', 'shed', 'ensuite',
                       'built-in', 'fireplace', 'study', 'courtyard', 'outdoor']
    
    for keyword in feature_keywords:
        if keyword in text.lower() and keyword not in seen_keywords:
            features.append(keyword.capitalize())
            seen_keywords.add(keyword)
    
    # Look for feature containers
    feature_containers = soup.find_all(class_=re.compile(r'feature|amenity|highlight', re.I))
    for container in feature_containers:
        feature_elems = container.find_all(['li', 'span', 'div'])
        for elem in feature_elems:
            text = elem.get_text(strip=True)
            if text and 3 < len(text) < 50 and any(kw in text.lower() for kw in feature_keywords):
                if text not in features:
                    features.append(text)
    
    return features[:15]  # Limit to top 15 unique features


def extract_images_and_floorplans(html):
    """Extract all property images and floor plans from HTML.

    Strategy:
    - Treat ALL bucket-api image URLs as generic property images (after filtering avatars/logos).
    - Parse the __NEXT_DATA__ JSON to find gallery slides.
      * Any slide with mediaType == "floorplan" is treated as a true floor plan.
      * Other slides (mediaType == "image"/"photo"/None) are treated as additional property images.
    This avoids the previous brittle heuristic that assumed any filename containing "_3_" was a floor plan.
    """
    property_images: list[str] = []
    floor_plans: list[str] = []

    # 1. Extract ORIGINAL bucket-api URLs (largest format) as baseline property images
    bucket_pattern = r'https://bucket-api\.domain\.com\.au/v1/bucket/image/[^\s"\'<>]+'
    bucket_urls = re.findall(bucket_pattern, html)

    for url in bucket_urls:
        url = url.rstrip('\\')
        # Skip avatars, logos, and non-property assets
        if any(skip in url for skip in ['contact_', 'logo', 'agency', 'searchlogo', 'banner']):
            continue
        property_images.append(url)

    # 2. Parse __NEXT_DATA__ for structured gallery info (including explicit floorplan slides)
    try:
        soup = BeautifulSoup(html, 'html.parser')
        next_data_script = soup.find('script', id='__NEXT_DATA__')

        if next_data_script and next_data_script.string:
            try:
                next_data = json.loads(next_data_script.string)
            except Exception as e:
                print(f"  ⚠ Failed to parse __NEXT_DATA__ JSON: {e}")
                next_data = None

            if isinstance(next_data, dict):
                # Navigate to gallery.slides if present
                props = next_data.get('props') or {}
                page_props = props.get('pageProps') or {}
                component_props = page_props.get('componentProps') or {}
                gallery = component_props.get('gallery') or {}
                slides = gallery.get('slides') or []

                if isinstance(slides, list):
                    for slide in slides:
                        if not isinstance(slide, dict):
                            continue

                        media_type = slide.get('mediaType') or slide.get('media_type')
                        images = slide.get('images') or {}
                        original = images.get('original') or {}
                        url = original.get('url') or slide.get('url')

                        if not url:
                            continue

                        # Domain explicitly labels floor plans via mediaType
                        if media_type == 'floorplan':
                            floor_plans.append(url)
                        else:
                            # Treat everything else as a normal property image
                            property_images.append(url)
    except Exception as e:
        # Fail soft here – image extraction is non-critical compared to core data
        print(f"  ⚠ __NEXT_DATA__ image extraction failed: {e}")

    # 3. De-duplicate while preserving order
    def _dedupe(seq: list[str]) -> list[str]:
        seen = set()
        result: list[str] = []
        for item in seq:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    property_images = _dedupe(property_images)
    floor_plans = _dedupe(floor_plans)

    return property_images, floor_plans


def clean_property_data(property_data):
    """Clean and normalize extracted property data"""
    # Convert string numbers to integers where appropriate
    int_fields = ['bedrooms', 'bathrooms', 'parking', 'land_size_sqm']
    for field in int_fields:
        if field in property_data and isinstance(property_data[field], str):
            try:
                property_data[field] = int(property_data[field].replace(',', ''))
            except:
                pass
    
    # Clean price field
    if 'price' in property_data:
        price = property_data['price']
        if isinstance(price, (int, float)):
            property_data['price'] = f"${price:,}"
    
    return property_data


if __name__ == "__main__":
    # Test the parser
    print("HTML Parser for Domain.com.au")
    print("This module is imported by batch_processor.py")
