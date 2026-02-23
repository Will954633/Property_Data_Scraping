#!/usr/bin/env python3
"""
HTML Parser for Domain.com.au SOLD Listing Pages
Extracts all property data including sale date from sold listings
Based on the for-sale parser with sold-specific enhancements
"""

import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser as date_parser


def parse_sold_listing_html(html, address):
    """
    Parse domain.com.au SOLD listing page HTML to extract all property data
    
    Args:
        html: Raw HTML string from the sold listing page
        address: The address being searched
        
    Returns:
        dict: Complete property data extracted from HTML including sale_date
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    property_data = {
        "address": address,
        "extraction_method": "HTML",
        "extraction_date": datetime.now().isoformat()
    }
    
    # 1. Extract sale date (CRITICAL for sold properties)
    try:
        sale_date = extract_sale_date(soup)
        if sale_date:
            property_data['sale_date'] = sale_date
            print(f"  ✓ Extracted sale date: {sale_date}")
        else:
            print(f"  ⚠ No sale date found")
    except Exception as e:
        print(f"  ⚠ Sale date extraction failed: {e}")
    
    # 2. Try to extract JSON-LD structured data first (most reliable)
    try:
        json_ld_data = extract_json_ld(soup)
        if json_ld_data:
            property_data.update(json_ld_data)
            print(f"  ✓ Extracted data from JSON-LD schema")
    except Exception as e:
        print(f"  ⚠ JSON-LD extraction failed: {e}")
    
    # 3. Extract from meta tags (fallback)
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
    
    # 4. Extract from HTML elements (additional fallback)
    try:
        element_data = extract_html_elements(soup)
        if element_data:
            for key, value in element_data.items():
                if key not in property_data and value:
                    property_data[key] = value
            print(f"  ✓ Extracted data from HTML elements")
    except Exception as e:
        print(f"  ⚠ HTML element extraction failed: {e}")
    
    # 5. Extract Domain Says section (includes time on market and other insights)
    try:
        domain_says_data = extract_domain_says(soup)
        if domain_says_data:
            property_data.update(domain_says_data)
            if 'time_on_market_days' in domain_says_data:
                print(f"  ✓ Extracted Domain Says: {domain_says_data['time_on_market_days']} days on market")
            else:
                print(f"  ✓ Extracted Domain Says section")
    except Exception as e:
        print(f"  ⚠ Domain Says extraction failed: {e}")
    
    # 6. Extract agent information
    try:
        agent_info = extract_agent_info(soup)
        if agent_info:
            property_data.update(agent_info)
            print(f"  ✓ Extracted agent information")
    except Exception as e:
        print(f"  ⚠ Agent info extraction failed: {e}")
    
    # 7. Extract property features
    try:
        features = extract_features(soup)
        if features:
            property_data['features'] = features
            print(f"  ✓ Found {len(features)} property features")
    except Exception as e:
        print(f"  ⚠ Feature extraction failed: {e}")
    
    # 8. Extract images and floor plans
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


def extract_sale_date(soup):
    """
    Extract sale date from sold listing page
    
    Priority order:
    1. JSON-LD structured data (most reliable)
    2. data-testid elements
    3. Text pattern matching ("Sold on DD MMM YYYY")
    4. Meta tags
    
    Returns:
        ISO date string (YYYY-MM-DD) or None
    """
    
    # Method 1: JSON-LD structured data
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            json_data = json.loads(script.string)
            
            # Handle array of JSON-LD objects
            if isinstance(json_data, list):
                for item in json_data:
                    # Look for dateSold or datePosted
                    if 'dateSold' in item:
                        return parse_date_string(item['dateSold'])
                    elif 'datePosted' in item and item.get('@type') in ['RealEstateListing', 'Offer']:
                        return parse_date_string(item['datePosted'])
            else:
                # Single JSON-LD object
                if 'dateSold' in json_data:
                    return parse_date_string(json_data['dateSold'])
                elif 'datePosted' in json_data:
                    return parse_date_string(json_data['datePosted'])
        except:
            continue
    
    # Method 2: Look for CSS class-based elements (common in sold listings)
    # Pattern: <span class="css-1ycmcro">Sold by private treaty 15 Dec 2025</span>
    sold_date_span = soup.find('span', class_='css-1ycmcro')
    if sold_date_span:
        date_text = sold_date_span.get_text(strip=True)
        parsed = parse_date_string(date_text)
        if parsed:
            return parsed
    
    # Method 3: Look for data-testid elements
    sold_date_elem = soup.find(attrs={'data-testid': 'listing-details__sold-date'})
    if sold_date_elem:
        date_text = sold_date_elem.get_text(strip=True)
        parsed = parse_date_string(date_text)
        if parsed:
            return parsed
    
    # Method 4: Look for "Sold on DD MMM YYYY" or "Sold DD MMM YYYY" text patterns
    text_patterns = [
        r'Sold by private treaty (\d{1,2}\s+\w+\s+\d{4})',
        r'Sold on (\d{1,2}\s+\w+\s+\d{4})',
        r'Sold (\d{1,2}\s+\w+\s+\d{4})',
        r'Sale date[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
    ]
    
    page_text = soup.get_text()
    for pattern in text_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            date_text = match.group(1)
            parsed = parse_date_string(date_text)
            if parsed:
                return parsed
    
    # Method 5: Check meta tags
    meta_date = soup.find('meta', property='article:published_time')
    if meta_date and meta_date.get('content'):
        parsed = parse_date_string(meta_date['content'])
        if parsed:
            return parsed
    
    return None


def parse_date_string(date_str):
    """
    Parse various date string formats to ISO format (YYYY-MM-DD)
    
    Handles:
    - ISO format: 2024-11-15T10:30:00Z
    - Australian format: 15 Nov 2024
    - US format: Nov 15, 2024
    - Numeric: 15/11/2024
    """
    if not date_str:
        return None
    
    try:
        # Use dateutil parser for flexible parsing
        dt = date_parser.parse(date_str, dayfirst=True)  # Australian format preference
        return dt.strftime('%Y-%m-%d')
    except:
        return None


def is_within_6_months(sale_date_str):
    """
    Check if sale date is within last 6 months from today
    
    Args:
        sale_date_str: ISO date string (YYYY-MM-DD)
        
    Returns:
        bool: True if within 6 months, False otherwise
    """
    if not sale_date_str:
        return False
    
    try:
        sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d')
        six_months_ago = datetime.now() - timedelta(days=182)  # ~6 months
        return sale_date >= six_months_ago
    except:
        return False


def extract_json_ld(soup):
    """Extract data from JSON-LD structured data"""
    data = {}
    
    # Find all script tags with type application/ld+json
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    
    for script in json_ld_scripts:
        try:
            json_data = json.loads(script.string)
            
            # Handle array of JSON-LD objects
            if isinstance(json_data, list):
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
                
                # Price (sold price)
                if 'offers' in json_data:
                    offers = json_data['offers']
                    if isinstance(offers, dict):
                        if 'price' in offers:
                            data['sale_price'] = str(offers['price'])
                        elif 'priceSpecification' in offers:
                            data['sale_price'] = str(offers['priceSpecification'])
                
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
    
    # PRIORITY 1: Extract from CSS class-based container (common in sold listings)
    # Pattern: <div class="css-fpm9y"> contains sale date, price, address, features
    main_container = soup.find('div', class_='css-fpm9y')
    if main_container:
        # Extract sale price from <div class="css-1eoy87d">SOLD - $2,900,000</div>
        price_div = main_container.find('div', class_='css-1eoy87d')
        if price_div:
            price_text = price_div.get_text(strip=True)
            # Remove "SOLD - " or "SOLD-" prefix
            price_text = re.sub(r'^SOLD\s*-\s*', '', price_text, flags=re.IGNORECASE)
            if price_text:
                data['sale_price'] = price_text
        
        # Extract features from <div class="css-1o7d3sk">5Beds4Baths2Parking859m²House</div>
        features_div = main_container.find('div', class_='css-1o7d3sk')
        if features_div:
            features_text = features_div.get_text(strip=True)
            
            # Extract bedrooms
            bed_match = re.search(r'(\d+)\s*Bed', features_text, re.IGNORECASE)
            if bed_match:
                data['bedrooms'] = int(bed_match.group(1))
            
            # Extract bathrooms
            bath_match = re.search(r'(\d+)\s*Bath', features_text, re.IGNORECASE)
            if bath_match:
                data['bathrooms'] = int(bath_match.group(1))
            
            # Extract parking/carspaces
            park_match = re.search(r'(\d+)\s*Parking', features_text, re.IGNORECASE)
            if park_match:
                data['carspaces'] = int(park_match.group(1))
            
            # Extract land size
            land_match = re.search(r'(\d+)\s*m²', features_text)
            if land_match:
                data['land_size_sqm'] = int(land_match.group(1))
            
            # Extract property type (last word in the string)
            type_match = re.search(r'(House|Apartment|Townhouse|Unit|Villa|Land)$', features_text, re.IGNORECASE)
            if type_match:
                data['property_type'] = type_match.group(1).capitalize()
    
    # PRIORITY 2: Extract from property-features section using data-testid (fallback)
    if 'bedrooms' not in data or 'bathrooms' not in data:
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
                            
                            # Map to our field names (only if not already extracted)
                            if 'bed' in label and 'bedrooms' not in data:
                                data['bedrooms'] = number
                            elif 'bath' in label and 'bathrooms' not in data:
                                data['bathrooms'] = number
                            elif ('park' in label or 'car' in label) and 'carspaces' not in data:
                                data['carspaces'] = number
    
    # Extract property type from listing-summary-property-type (fallback)
    if 'property_type' not in data:
        property_type_elem = soup.find(attrs={'data-testid': 'listing-summary-property-type'})
        if property_type_elem:
            prop_type_text = property_type_elem.get_text(strip=True)
            if prop_type_text:
                data['property_type'] = prop_type_text
    
    # PRIORITY 3: Extract price from data-testid (fallback)
    if 'sale_price' not in data:
        price_elem = soup.find(attrs={'data-testid': 'listing-details__summary-title'})
        if price_elem:
            # Get only the direct text content of the span, not nested elements
            price_span = price_elem.find('span')
            if price_span:
                price_text = price_span.get_text(strip=True)
            else:
                price_text = price_elem.get_text(strip=True)
            
            # Clean the price text - remove "SOLD - " prefix if present
            if price_text:
                # Remove "SOLD - " or "SOLD-" prefix
                price_text = re.sub(r'^SOLD\s*-\s*', '', price_text, flags=re.IGNORECASE)
                data['sale_price'] = price_text
    
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
    
    return data


def extract_domain_says(soup):
    """
    Extract the complete "Domain Says" section which contains valuable insights
    
    Example text: "First listed on 18 November, this house has been on Domain for 27 days 
                   (last updated on 10 November). It was last sold in 2021 and 144 other 
                   4 bedroom house in Robina have recently been sold."
    
    Returns:
        dict: Contains 'domain_says_text' and optionally 'time_on_market_days', 
              'first_listed_date', 'last_updated_date', 'previous_sale_year'
    """
    data = {}
    
    try:
        # Find the Domain Says section
        domain_says = soup.find(attrs={'data-testid': 'listing-details__domain-says-text'})
        
        if domain_says:
            text = domain_says.get_text(strip=True)
            
            # Store the complete text
            data['domain_says_text'] = text
            
            # Extract time on market (days)
            days_match = re.search(r'(?:has been |)on Domain for (\d+) days?', text, re.IGNORECASE)
            if days_match:
                data['time_on_market_days'] = int(days_match.group(1))
            
            # Extract first listed date
            first_listed_match = re.search(r'First listed on (\d{1,2}\s+\w+)', text, re.IGNORECASE)
            if first_listed_match:
                data['first_listed_date'] = first_listed_match.group(1)
            
            # Extract last updated date
            last_updated_match = re.search(r'last updated on (\d{1,2}\s+\w+)', text, re.IGNORECASE)
            if last_updated_match:
                data['last_updated_date'] = last_updated_match.group(1)
            
            # Extract previous sale year
            prev_sale_match = re.search(r'(?:was |)last sold in (\d{4})', text, re.IGNORECASE)
            if prev_sale_match:
                data['previous_sale_year'] = int(prev_sale_match.group(1))
            
            # Extract comparable sales info (handle missing spaces in text)
            # Pattern: "34other 5 bedroom houseinRobinahave recently been sold"
            comparable_match = re.search(r'(\d+)\s*other\s*(\d+)\s*bedroom\s*([\w\s]+?)\s*in\s*([\w\s]+?)\s*have\s+recently\s+been\s+sold', text, re.IGNORECASE)
            if comparable_match:
                data['comparable_sales_count'] = int(comparable_match.group(1))
                data['comparable_bedrooms'] = int(comparable_match.group(2))
                # Clean up property type and suburb (remove extra spaces)
                prop_type = comparable_match.group(3).strip()
                suburb = comparable_match.group(4).strip()
                data['comparable_property_type'] = prop_type
                data['comparable_suburb'] = suburb
    
    except Exception as e:
        pass
    
    return data


def extract_agent_info(soup):
    """Extract agent and agency information"""
    data = {}
    
    # PRIORITY 1: Extract from digitalData JavaScript object (most reliable for sold properties)
    try:
        # Find script tag containing digitalData
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'var digitalData' in script.string:
                script_text = script.string
                
                # Extract agency name
                agency_match = re.search(r'"agency"\s*:\s*"([^"]+)"', script_text)
                if agency_match:
                    data['agency_name'] = agency_match.group(1)
                
                # Extract agent names
                agent_match = re.search(r'"agentNames"\s*:\s*"([^"]+)"', script_text)
                if agent_match:
                    data['agent_name'] = agent_match.group(1)
                
                # Extract agency ID
                agency_id_match = re.search(r'"agencyId"\s*:\s*(\d+)', script_text)
                if agency_id_match:
                    data['agency_id'] = agency_id_match.group(1)
                
                break
    except Exception as e:
        pass
    
    # PRIORITY 2: Extract from agent details card (for active listings)
    if not data.get('agent_name'):
        agent_details = soup.find(attrs={'data-testid': 'listing-details__agent-details'})
        if agent_details:
            # Agent name
            agent_name_link = agent_details.find('a', attrs={'data-testid': 'listing-details__agent-details-agent-name'})
            if agent_name_link:
                agent_name_div = agent_name_link.find('div')
                if agent_name_div:
                    data['agent_name'] = agent_name_div.get_text(strip=True)
            
            # Agency name
            agency_name_link = agent_details.find('a', attrs={'data-testid': 'listing-details__agent-details-agency-name'})
            if agency_name_link:
                agency_name_div = agency_name_link.find('div')
                if agency_name_div:
                    data['agency_name'] = agency_name_div.get_text(strip=True)
            
            # Agent profile URL
            if agent_name_link:
                agent_url = agent_name_link.get('href', '')
                if agent_url:
                    data['agent_profile_url'] = agent_url if agent_url.startswith('http') else f"https://www.domain.com.au{agent_url}"
            
            # Agency profile URL
            if agency_name_link:
                agency_url = agency_name_link.get('href', '')
                if agency_url:
                    data['agency_profile_url'] = agency_url if agency_url.startswith('http') else f"https://www.domain.com.au{agency_url}"
            
            # Agency logo
            agency_logo_link = agent_details.find('a', attrs={'data-testid': 'listing-details__agent-details-agency-logo'})
            if agency_logo_link:
                agency_logo = agency_logo_link.find('img')
                if agency_logo:
                    logo_src = agency_logo.get('src', '')
                    if logo_src:
                        data['agency_logo_url'] = logo_src
            
            # Phone number
            phone_button = soup.find('button', attrs={'data-testid': 'listing-details__phone-cta-button'})
            if phone_button:
                # Phone might be in href or text
                phone_link = phone_button if phone_button.name == 'a' else soup.find('a', attrs={'data-testid': 'listing-details__phone-cta-button'})
                if phone_link:
                    phone = phone_link.get('href', '').replace('tel:', '')
                    if phone:
                        data['agent_phone'] = phone
    
    # PRIORITY 3: Extract from residential header (mobile view)
    if not data.get('agent_name'):
        residential_header = soup.find(attrs={'data-testid': 'listing-details__residential-header'})
        if residential_header:
            # Agent name and agency from links
            agent_links = residential_header.find_all('a')
            for link in agent_links:
                href = link.get('href', '')
                if '/real-estate-agent/' in href and not data.get('agent_name'):
                    data['agent_name'] = link.get_text(strip=True)
                    data['agent_profile_url'] = href if href.startswith('http') else f"https://www.domain.com.au{href}"
                elif '/real-estate-agencies/' in href and not data.get('agency_name'):
                    data['agency_name'] = link.get_text(strip=True)
                    data['agency_profile_url'] = href if href.startswith('http') else f"https://www.domain.com.au{href}"
    
    # FALLBACK: Old method if nothing found
    if not data.get('agent_name'):
        agent_elems = soup.find_all(['a', 'span', 'div'], class_=re.compile(r'agent|contact', re.I))
        for elem in agent_elems:
            name = elem.get_text(strip=True)
            if name and len(name.split()) >= 2 and not any(word in name.lower() for word in ['contact', 'agent', 'call']):
                data['agent_name'] = name
                break
    
    if not data.get('agency_name'):
        agency_elems = soup.find_all(class_=re.compile(r'agency|office', re.I))
        for elem in agency_elems:
            agency = elem.get_text(strip=True)
            if agency and len(agency) > 2:
                data['agency_name'] = agency
                break
    
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
    """Extract all property images and floor plans from HTML"""
    property_images = []
    floor_plans = []

    # 1. Extract ORIGINAL bucket-api URLs (largest format) as baseline property images
    bucket_pattern = r'https://bucket-api\.domain\.com\.au/v1/bucket/image/[^\s"\'<>]+'
    bucket_urls = re.findall(bucket_pattern, html)

    for url in bucket_urls:
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
        print(f"  ⚠ __NEXT_DATA__ image extraction failed: {e}")

    # 3. De-duplicate while preserving order
    def _dedupe(seq):
        seen = set()
        result = []
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
    int_fields = ['bedrooms', 'bathrooms', 'parking', 'carspaces', 'land_size_sqm']
    for field in int_fields:
        if field in property_data and isinstance(property_data[field], str):
            try:
                property_data[field] = int(property_data[field].replace(',', ''))
            except:
                pass
    
    # Clean price field
    if 'sale_price' in property_data:
        price = property_data['sale_price']
        if isinstance(price, (int, float)):
            property_data['sale_price'] = f"${price:,}"
    
    return property_data


if __name__ == "__main__":
    # Test the parser
    print("HTML Parser for Domain.com.au SOLD Listings")
    print("This module is imported by property_detail_scraper_sold.py")
