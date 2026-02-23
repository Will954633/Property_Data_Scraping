#!/usr/bin/env python3
"""
Batch Address Processor
Processes multiple addresses from JSON file sequentially
Logs results and generates comprehensive report
"""

import subprocess
import time
import os
import json
import base64
import random
import math
import re
from datetime import datetime
from openai import OpenAI
import argparse
from bs4 import BeautifulSoup
from html_parser import parse_listing_html, clean_property_data
import pymongo
from pymongo import MongoClient

# Configuration
OPENAI_API_KEY = "REDACTED_OPENAI_KEY"
GPT_MODEL_NANO = "gpt-5-nano-2025-08-07"
GPT_MODEL_MINI = "gpt-5-mini-2025-08-07"
SCREENSHOT_DIR = "screenshots"
RESULTS_DIR = "batch_results"

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "properties_for_sale"

# Click strategy configuration
FIXED_CLICK_COORDINATES = (350, 247)
MAX_GPT_RETRIES = 2
INITIAL_LOAD_DELAY = 5
PAGE_LOAD_WAIT = 3
VALIDATION_DELAY = 1
BETWEEN_ADDRESS_DELAY = 2  # Wait between addresses

# Import all functions from hybrid_smart_clicker
def run_applescript(script):
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()

def maximize_chrome_window():
    script = '''
    tell application "Google Chrome"
        activate
        tell front window
            set bounds to {0, 0, 1920, 1080}
        end tell
    end tell
    '''
    try:
        run_applescript(script)
        time.sleep(0.5)
    except Exception as e:
        pass

def bring_chrome_to_front():
    script = '''
    tell application "Google Chrome"
        activate
    end tell
    '''
    run_applescript(script)

def focus_address_bar():
    script = '''
    tell application "System Events"
        keystroke "l" using command down
    end tell
    '''
    run_applescript(script)

def type_text(text):
    text = text.replace('"', '\\"')
    script = f'''
    tell application "System Events"
        keystroke "{text}"
    end tell
    '''
    run_applescript(script)

def press_enter():
    script = '''
    tell application "System Events"
        key code 36
    end tell
    '''
    run_applescript(script)

def get_current_url():
    script = '''
    tell application "Google Chrome"
        get URL of active tab of front window
    end tell
    '''
    try:
        url = run_applescript(script)
        return url
    except:
        return None

def validate_domain_url():
    time.sleep(VALIDATION_DELAY)
    url = get_current_url()
    if url and "domain.com.au" in url.lower():
        return True, url
    else:
        return False, url

def navigate_back():
    script = '''
    tell application "System Events"
        keystroke "[" using command down
    end tell
    '''
    run_applescript(script)
    time.sleep(2)

def get_chrome_window_bounds():
    script = '''
    tell application "Google Chrome"
        set windowBounds to bounds of front window
        return windowBounds
    end tell
    '''
    result = run_applescript(script)
    if result:
        try:
            bounds = [int(x.strip()) for x in result.split(',')]
            return bounds
        except:
            return None
    return None

def take_screenshot(filepath):
    bring_chrome_to_front()
    time.sleep(0.5)
    bounds = get_chrome_window_bounds()
    if bounds:
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1
        subprocess.run(['screencapture', '-x', '-R', f'{x1},{y1},{width},{height}', filepath])
        return bounds
    else:
        subprocess.run(['screencapture', '-x', filepath])
        return None

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot_with_gpt(screenshot_path, search_address, use_mini_model=False, find_view_listing=False):
    """Analyze screenshot with GPT Vision - can use nano or mini model"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    base64_image = encode_image_to_base64(screenshot_path)
    
    if find_view_listing:
        # Special prompt for finding "View listing" button
        prompt = """You are analyzing a domain.com.au property PROFILE page that needs to navigate to the actual listing.

TASK: Find the "View listing" button on this page and provide click coordinates.

CONTEXT:
- This is a property PROFILE/overview page (not the full listing)
- There should be a button or link that says "View listing" or "View Listing"
- This button will take us to the full property listing page with all details

WHAT TO LOOK FOR:
1. A button or clickable link with text like "View listing", "View Listing", or similar
2. It's typically a prominent button on the page
3. May be near the property overview section or at the top of the page

IMPORTANT:
- Provide coordinates for the CENTER of the "View listing" button/link
- Make sure it's the clickable element, not just text

Return ONLY this JSON format (no additional text):
{
    "found": true/false,
    "x": pixel_x_coordinate,
    "y": pixel_y_coordinate,
    "confidence": "high"/"medium"/"low",
    "reasoning": "explanation of what you found and where"
}

If you cannot find a "View listing" button, set "found" to false."""
        
        model = GPT_MODEL_MINI
    elif use_mini_model:
        # Enhanced prompt with more context for mini model
        prompt = f"""You are analyzing a Google search results page to find a specific real estate listing.

TASK: Find the domain.com.au link for the property at "{search_address}"

CONTEXT:
- This is a screenshot of Google search results
- We are looking for a listing from the website "domain.com.au" 
- The listing should match the address: "{search_address}"
- The address is located in Robina, QLD, Australia (postcode 4226)

WHAT TO LOOK FOR:
1. Search results that mention "domain.com.au" in the URL or domain
2. The result title should contain the address or key parts of it (street number, street name, suburb)
3. Look for clickable link text (usually blue or purple colored)
4. The link is typically in the TITLE/HEADING of the search result card
5. Focus on the main title link, NOT the green URL text below it

IMPORTANT:
- Provide coordinates for the CENTER of the clickable title/heading text
- NOT the green URL text
- NOT the description text
- The TITLE LINK is what needs to be clicked

Return ONLY this JSON format (no additional text):
{{
    "found": true/false,
    "x": pixel_x_coordinate,
    "y": pixel_y_coordinate,
    "confidence": "high"/"medium"/"low",
    "reasoning": "detailed explanation of what you identified and why these coordinates"
}}

If you cannot find a domain.com.au result for this address, set "found" to false."""
        
        model = GPT_MODEL_MINI
    else:
        # Standard prompt for nano model
        prompt = f"""Analyze this Google search results screenshot for: "{search_address}"
Find the domain.com.au link matching this address and provide click coordinates.
Return ONLY this JSON (no other text):
{{
    "found": true/false,
    "x": pixel_x,
    "y": pixel_y,
    "confidence": "high"/"medium"/"low",
    "reasoning": "brief explanation"
}}"""
        
        model = GPT_MODEL_NANO
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            max_completion_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        if not response_text:
            return {"found": False, "error": "Empty response"}
        
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
    except Exception as e:
        return {"found": False, "error": str(e)}

def human_like_mouse_movement(x, y, duration=0.5):
    script = '''
    use framework "CoreGraphics"
    set mouseLoc to current application's NSEvent's mouseLocation()
    return (item 1 of mouseLoc as integer) & "," & (item 2 of mouseLoc as integer)
    '''
    try:
        result = run_applescript(script)
        current_x, current_y = map(int, result.split(','))
    except:
        current_x, current_y = 960, 540
    
    distance = math.sqrt((x - current_x)**2 + (y - current_y)**2)
    num_steps = int(distance / 10) + 10
    
    for i in range(1, num_steps + 1):
        progress = i / num_steps
        curve = math.sin(progress * math.pi) * random.uniform(-10, 10)
        intermediate_x = current_x + (x - current_x) * progress + curve
        intermediate_y = current_y + (y - current_y) * progress + curve * 0.5
        subprocess.run(['cliclick', f'm:{int(intermediate_x)},{int(intermediate_y)}'], capture_output=True)
        time.sleep(duration / num_steps + random.uniform(-0.001, 0.001))
    
    subprocess.run(['cliclick', f'm:{x},{y}'], capture_output=True)

def click_at_coordinates(x, y):
    subprocess.run(['cliclick', f'c:{x},{y}'], capture_output=True)
    time.sleep(1)

def take_multiple_screenshots_while_scrolling(base_path, num_scrolls=10):
    """Take multiple screenshots while scrolling down to capture full page"""
    bring_chrome_to_front()
    time.sleep(0.5)
    
    # Scroll to top first
    script = '''
    tell application "System Events"
        key code 115
    end tell
    '''
    run_applescript(script)
    time.sleep(1)
    
    screenshot_paths = []
    
    for i in range(num_scrolls):
        # Take screenshot at current position
        screenshot_path = base_path.replace('.png', f'_section_{i+1:02d}.png')
        bring_chrome_to_front()
        time.sleep(0.3)
        take_screenshot(screenshot_path)
        screenshot_paths.append(screenshot_path)
        
        # Scroll down for next section (except on last iteration)
        if i < num_scrolls - 1:
            script = '''
            tell application "System Events"
                key code 121
            end tell
            '''
            run_applescript(script)
            time.sleep(1.2)  # Wait for content to load
    
    return screenshot_paths

def open_new_tab_and_search(address):
    """Open a fresh new Chrome tab and search for address"""
    print(f"→ Opening fresh Chrome tab for new search...")
    
    script = '''
    tell application "Google Chrome"
        activate
        tell front window
            make new tab
            set URL of active tab to "about:blank"
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(1)
    
    # Search in the new tab
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(address)
    time.sleep(0.5)
    press_enter()
    time.sleep(INITIAL_LOAD_DELAY)
    print(f"✓ Fresh tab opened and search completed")
    return True

def open_chrome_and_search(address):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Check if Chrome is already open with a tab
    try:
        current_url = get_current_url()
        if current_url:
            # Chrome is open, just search in existing tab
            bring_chrome_to_front()
            time.sleep(0.5)
            focus_address_bar()
            time.sleep(0.5)
            type_text(address)
            time.sleep(0.5)
            press_enter()
            time.sleep(INITIAL_LOAD_DELAY)
            return True
    except:
        pass
    
    # Open new Chrome window if not already open
    script = '''
    tell application "Google Chrome"
        activate
        make new window
        set URL of active tab of front window to "about:blank"
    end tell
    '''
    run_applescript(script)
    time.sleep(1)
    maximize_chrome_window()
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(address)
    time.sleep(0.5)
    press_enter()
    time.sleep(INITIAL_LOAD_DELAY)
    return True

def try_fixed_coordinates_click():
    bring_chrome_to_front()
    time.sleep(0.3)
    human_like_mouse_movement(FIXED_CLICK_COORDINATES[0], FIXED_CLICK_COORDINATES[1], duration=0.8)
    click_at_coordinates(FIXED_CLICK_COORDINATES[0], FIXED_CLICK_COORDINATES[1])
    time.sleep(PAGE_LOAD_WAIT)
    return validate_domain_url()

def try_gpt_vision_click(address, attempt_num, screenshot_path=None):
    """Try clicking using GPT Vision"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use existing screenshot if provided, otherwise take new one
    if not screenshot_path:
        screenshot_path = os.path.join(RESULTS_DIR, f"gpt_attempt_{attempt_num}_{timestamp}.png")
        window_bounds = take_screenshot(screenshot_path)
    else:
        window_bounds = get_chrome_window_bounds()
    
    # Analyze with GPT
    gpt_result = analyze_screenshot_with_gpt(screenshot_path, address)
    
    if not gpt_result.get("found", False):
        return False, None, None
    
    click_x = gpt_result.get("x")
    click_y = gpt_result.get("y")
    original_coords = (click_x, click_y)
    
    if window_bounds:
        x1, y1, x2, y2 = window_bounds
        click_x += x1
        click_y += y1
    
    bring_chrome_to_front()
    time.sleep(0.3)
    human_like_mouse_movement(click_x, click_y, duration=0.8)
    time.sleep(0.3)
    click_at_coordinates(click_x, click_y)
    time.sleep(PAGE_LOAD_WAIT)
    
    is_valid, url = validate_domain_url()
    return is_valid, url, original_coords

def parse_single_property_page(ocr_text, address):
    """Parse OCR text from a single property detail page"""
    import re
    
    property_data = {
        "address": address
    }
    
    # CRITICAL: Only parse content BEFORE the "Showing X of Y properties for sale" section
    # to avoid pulling data from OTHER properties listed below
    showing_match = re.search(r'Showing \d+ of \d+ properties for sale', ocr_text, re.IGNORECASE)
    if showing_match:
        # Only use text before this section
        ocr_text = ocr_text[:showing_match.start()]
    
    # Look for the "Property overview" section which contains accurate structured data
    # Example: "5 Picabeen Close, Robina, Qld 4226 has a land size of 459 m². It is a house with 4 bedrooms, 2 bathrooms, and 3 parking spaces."
    overview_match = re.search(
        r'Property overview.*?has a land size of (\d+,?\d*)\s*m[²2]?\.\s*It is a (\w+) with (\d+) bedroom[s]?, (\d+) bathroom[s]?, and (\d+) parking space[s]?',
        ocr_text, 
        re.IGNORECASE | re.DOTALL
    )
    
    if overview_match:
        property_data['land_size_sqm'] = int(overview_match.group(1).replace(',', ''))
        property_data['property_type'] = overview_match.group(2).capitalize()
        property_data['bedrooms'] = int(overview_match.group(3))
        property_data['bathrooms'] = int(overview_match.group(4))
        property_data['parking'] = int(overview_match.group(5))
    else:
        # Fallback patterns if overview section not found
        bed_match = re.search(r'(\d+)\s*bedroom[s]?', ocr_text, re.I)
        if bed_match:
            property_data['bedrooms'] = int(bed_match.group(1))
        
        bath_match = re.search(r'(\d+)\s*bathroom[s]?', ocr_text, re.I)
        if bath_match:
            property_data['bathrooms'] = int(bath_match.group(1))
        
        parking_match = re.search(r'(\d+)\s*(?:parking space[s]?|car)', ocr_text, re.I)
        if parking_match:
            property_data['parking'] = int(parking_match.group(1))
        
        land_match = re.search(r'land size of (\d+,?\d*)\s*m[²2]?', ocr_text, re.I)
        if land_match:
            property_data['land_size_sqm'] = int(land_match.group(1).replace(',', ''))
        
        prop_type_match = re.search(r'It is a (\w+)', ocr_text, re.I)
        if prop_type_match:
            property_data['property_type'] = prop_type_match.group(1).capitalize()
    
    # Extract price/listing type
    price_patterns = [
        (r'Expressions?\s+[Oo]f\s+[Ii]nterest', 'Expressions Of Interest'),
        (r'UNDER\s+OFFER\s+@\s+\$[\d,]+\+?', 'price_match'),  # Extract full "UNDER OFFER @ $X,XXX,XXX+"
        (r'Offers?\s+[Oo]ver\s+\$[\d,]+', 'price_match'),
        (r'\$[\d,]+,\d{3}(?:\+)?', 'price_match'),  # Match prices like $2,399,000+
        (r'Auction', 'Auction'),
        (r'Contact\s+Agent', 'Contact Agent'),
    ]
    
    for pattern, price_type in price_patterns:
        price_match = re.search(pattern, ocr_text, re.IGNORECASE)
        if price_match:
            if price_type == 'price_match':
                property_data['price'] = price_match.group(0)
            else:
                property_data['price'] = price_type
            break
    
    # Extract sold price from overview if mentioned
    sold_match = re.search(r'It was sold in \d{4} for \$([\d,]+)', ocr_text, re.I)
    if sold_match:
        property_data['previous_sale_price'] = f"${sold_match.group(1)}"
        prev_year_match = re.search(r'It was sold in (\d{4})', ocr_text, re.I)
        if prev_year_match:
            property_data['previous_sale_year'] = prev_year_match.group(1)
    
    # Extract agent name - look for "Lead Agent:" section
    lead_agent_match = re.search(r'Lead Agent:\s*[^\n]*?\n\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', ocr_text)
    if lead_agent_match:
        property_data['agent'] = lead_agent_match.group(1)
    else:
        # Fallback: Look for agent names near agency
        agent_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        agent_matches = re.findall(agent_pattern, ocr_text)
        excluded = {'Agent', 'Contact', 'Lead', 'For', 'Sale', 'New', 'Market', 'View', 'Listing',
                    'House', 'Robina', 'Close', 'Performance', 'Prestige', 'Sales', 'Specialist',
                    'Lucy', 'Cole', 'Interested', 'Check', 'Property', 'Value', 'Qld', 'Sign',
                    'Fast Book', 'Town Centre', 'Fiddly Fast', 'Hair Co'}
        
        for name in agent_matches:
            if name not in excluded:
                property_data['agent'] = name
                break
    
    # Extract agency
    agency_match = re.search(r'(Lucy\s*Cole|Ray\s*White|McGrath|Harcourts|RE\s*MAX)', ocr_text, re.I)
    if agency_match:
        property_data['agency'] = agency_match.group(1).replace(' ', '')
    
    # Extract open inspection times
    inspection_match = re.search(r'Open\s+((?:Sat|Sun|Mon|Tue|Wed|Thu|Fri)\s+\d+\s+\w+\s+\d+:\d+\s+[ap]m)', ocr_text, re.I)
    if inspection_match:
        property_data['open_inspection'] = inspection_match.group(0)
    
    # Determine listing status
    if re.search(r'For\s*sale|New\s*To\s*Market', ocr_text, re.I):
        property_data['listing_status'] = 'For Sale'
    
    return property_data

def construct_domain_url(address):
    """
    Construct direct domain.com.au URL from address with robust validation
    Ensures all Robina properties have format: street-address-robina-qld-4226
    
    Args:
        address: Property address string (e.g., "9 Applegum Court, Robina" or "4/189 Ron Penhaligon Way")
    
    Returns:
        str: Properly formatted domain.com.au property-profile URL
    
    Examples:
        "9 Applegum Court, Robina" -> "https://www.domain.com.au/property-profile/9-applegum-court-robina-qld-4226"
        "4/189 Ron Penhaligon Way" -> "https://www.domain.com.au/property-profile/4-189-ron-penhaligon-way-robina-qld-4226"
    """
    import re
    
    # Clean and normalize address
    address_clean = address.lower().strip()
    
    # Convert slashes to hyphens (for house addresses like "4/189" which means "4-189")
    # This is NOT for unit removal - we're filtering houses only
    address_clean = address_clean.replace('/', '-')
    
    # Remove all commas and extra whitespace
    address_clean = re.sub(r'[,]+', ' ', address_clean)
    address_clean = re.sub(r'\s+', ' ', address_clean).strip()
    
    # Extract components
    parts = address_clean.split()
    
    # Determine suburb, state, postcode
    suburb = 'robina'  # Default for this scraper
    state = 'qld'
    postcode = '4226'  # Robina postcode
    
    # Remove suburb/state/postcode from parts if they exist
    filtered_parts = []
    for part in parts:
        part_stripped = part.strip()
        if part_stripped in ['robina', 'qld', 'queensland', '4226']:
            # These will be added at the end in correct format
            continue
        else:
            filtered_parts.append(part_stripped)
    
    # Reconstruct street address (everything that's not suburb/state/postcode)
    street_address = ' '.join(filtered_parts)
    
    # Validate we have a street address
    if not street_address or len(street_address) < 3:
        # Fallback: use original address without suburb/state/postcode
        street_address = address_clean.replace('robina', '').replace('qld', '').replace('queensland', '').replace('4226', '').strip()
    
    # Build complete address components in order
    address_components = [street_address, suburb, state, postcode]
    
    # Join with spaces then convert to URL slug
    full_address = ' '.join(address_components)
    
    # Convert to URL slug format
    url_slug = full_address.replace(' ', '-')
    
    # Remove any special characters except hyphens and alphanumerics
    url_slug = re.sub(r'[^a-z0-9\-]', '', url_slug)
    
    # Remove double hyphens
    url_slug = re.sub(r'-+', '-', url_slug)
    
    # Remove leading/trailing hyphens
    url_slug = url_slug.strip('-')
    
    # Validate the URL format
    # Should have pattern: [street]-robina-qld-4226
    if not url_slug.endswith('-robina-qld-4226'):
        # Something went wrong, ensure it ends correctly
        if not '-robina-qld-4226' in url_slug:
            url_slug = url_slug + '-robina-qld-4226'
        else:
            # Fix malformed ending
            url_slug = re.sub(r'-robina.*$', '-robina-qld-4226', url_slug)
    
    # Construct full URL
    full_url = f"https://www.domain.com.au/property-profile/{url_slug}"
    
    return full_url

def is_property_profile_page(url):
    """Detect if we're on a property profile page vs full listing by checking URL format"""
    if not url:
        return False
    url_lower = url.lower()
    if '/property-profile/' in url_lower:
        return True
    if re.search(r'-\d{7}$', url_lower):
        return False
    return False  # Unknown format

def extract_page_html():
    """Extract HTML from current Chrome page using keyboard shortcuts"""
    try:
        bring_chrome_to_front()
        time.sleep(0.5)
        
        # Press Cmd+Option+U to view page source
        print(f"  → Opening view source (Cmd+Option+U)...")
        script = '''
        tell application "System Events"
            keystroke "u" using {command down, option down}
        end tell
        '''
        run_applescript(script)
        time.sleep(2)  # Wait for source to open
        
        # Press Cmd+A to select all
        print(f"  → Selecting all (Cmd+A)...")
        script = '''
        tell application "System Events"
            keystroke "a" using command down
        end tell
        '''
        run_applescript(script)
        time.sleep(0.5)
        
        # Press Cmd+C to copy
        print(f"  → Copying to clipboard (Cmd+C)...")
        script = '''
        tell application "System Events"
            keystroke "c" using command down
        end tell
        '''
        run_applescript(script)
        time.sleep(0.5)
        
        # Get clipboard content
        print(f"  → Reading from clipboard...")
        script = '''
        the clipboard
        '''
        html = run_applescript(script)
        
        # Close the source view tab (Cmd+W)
        script = '''
        tell application "System Events"
            keystroke "w" using command down
        end tell
        '''
        run_applescript(script)
        time.sleep(0.5)
        
        if html and len(html) > 100:
            return html
        else:
            print(f"  ✗ Clipboard content too small or empty")
            return None
            
    except Exception as e:
        print(f"  ✗ Failed to extract HTML via keyboard: {e}")
        return None

def find_listing_url_in_html(html):
    """Find the actual listing URL from the page HTML"""
    import re
    
    # Look for <a> tags with href containing domain.com.au/{slug}-{PID} or relative /slug-ID
    pattern = r'href="(/[\w-]+-\d+|https://www\.domain\.com\.au/[\w-]+-\d+)"'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    if matches:
        match = matches[0]
        if match.startswith('/'):
            return 'https://www.domain.com.au' + match
        return match
    
    return None

def navigate_to_listing_page():
    """Extract listing URL from HTML and navigate directly to it"""
    print("  → Extracting page HTML to find listing URL...")
    
    # Get page HTML
    html = extract_page_html()
    
    if not html:
        print(f"  ✗ Could not extract page HTML")
        return False, None
    
    print(f"  ✓ Extracted HTML ({len(html):,} chars)")
    
    # Find listing URL in HTML
    listing_url = find_listing_url_in_html(html)
    
    if not listing_url:
        print(f"  ✗ Could not find listing URL in HTML")
        return False, None
    
    print(f"  ✓ Found listing URL: {listing_url}")
    print(f"  → Navigating directly to listing page...")
    
    # Navigate to the extracted URL
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(listing_url)
    time.sleep(0.5)
    press_enter()
    time.sleep(PAGE_LOAD_WAIT)
    
    # Validate we're now on the listing page
    is_valid, new_url = validate_domain_url()
    return is_valid, new_url

def try_direct_url(address):
    """
    Navigate directly to constructed domain.com.au URL
    This is now the PRIMARY method (no Google search needed)
    """
    print(f"\n→ Constructing direct Domain URL...")
    
    direct_url = construct_domain_url(address)
    print(f"  • URL: {direct_url}")
    
    # Navigate to URL
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(direct_url)
    time.sleep(0.5)
    press_enter()
    time.sleep(PAGE_LOAD_WAIT)
    
    # Validate
    is_valid, url = validate_domain_url()
    
    if not is_valid:
        print(f"  ✗ Invalid or no Domain page loaded")
        return False, url
    
    # Check if we're on a property profile page (not the full listing)
    if is_property_profile_page(url):
        print(f"  ⚠ On property PROFILE page - extracting listing URL...")
        
        # Extract listing URL from HTML and navigate directly
        success, listing_url = navigate_to_listing_page()
        
        if success:
            print(f"  ✓ Navigated to full listing!")
            return True, listing_url
        else:
            print(f"  ⚠ Using PROFILE page (full listing not found)")
            return True, url
    
    # We're on the full listing page already
    print(f"  ✓ On full listing page")
    return True, url

def process_single_address(address, index, total, mongodb_mode=False):
    """Process a single address and return results"""
    print(f"\n{'='*80}")
    print(f"Processing Address {index}/{total}: {address}")
    print(f"{'='*80}")
    
    start_time = datetime.now()
    result = {
        "address": address,
        "index": index,
        "success": False,
        "method": None,
        "url": None,
        "time_seconds": 0,
        "attempts": [],
        "error": None,
        "parsed_file": None
    }
    
    try:
        # NEW APPROACH: Skip Google search entirely, go direct to Domain URL
        print("→ Using DIRECT URL method (no Google search needed)...")
        
        # Open Chrome if not already open
        try:
            current_url = get_current_url()
            if not current_url:
                # Open fresh Chrome window
                script = '''
                tell application "Google Chrome"
                    activate
                    make new window
                    set URL of active tab of front window to "about:blank"
                end tell
                '''
                run_applescript(script)
                time.sleep(1)
                maximize_chrome_window()
        except:
            pass
        
        # Try direct URL navigation (PRIMARY method)
        is_valid, url = try_direct_url(address)
        result["attempts"].append({"method": "direct_url", "success": is_valid, "url": url})
        
        if is_valid:
            result["success"] = True
            result["method"] = "DIRECT_URL"
            result["url"] = url
            print(f"✓ Success with direct URL!")
        else:
            print(f"✗ Direct URL failed")
            result["error"] = "Direct URL failed"
        
        # If we have a successful navigation to a domain page, extract HTML and parse property data
        if result["success"]:
            try:
                # Prepare paths
                os.makedirs(RESULTS_DIR, exist_ok=True)
                html_dir = os.path.join(RESULTS_DIR, "html")
                os.makedirs(html_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_address = "".join(c if c.isalnum() or c in (' ', ' _', '-') else '_' for c in address).strip().replace(' ', '_')
                
                # Extract HTML from listing page
                print("→ Extracting HTML from listing page...")
                html = extract_page_html()
                
                if not html:
                    print(f"  ✗ Failed to extract HTML")
                    result["error"] = "HTML extraction failed"
                else:
                    print(f"  ✓ Extracted HTML ({len(html):,} chars)")
                    
                    # Save raw HTML
                    html_file = os.path.join(html_dir, f"property_{index}_{timestamp}.html")
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"  ✓ Saved HTML: {html_file}")
                    
                    # Parse HTML to extract property data
                    print("→ Parsing HTML for property data...")
                    property_data = parse_listing_html(html, address)
                    property_data = clean_property_data(property_data)
                    
                    if property_data and any(v for k, v in property_data.items() if k not in ['address', 'extraction_method', 'extraction_date']):
                        print(f"  ✓ Extracted property data:")
                        for key, value in property_data.items():
                            if key not in ['address', 'extraction_method', 'extraction_date'] and value:
                                print(f"    • {key}: {value}")
                    else:
                        print(f"  ⚠ Limited property data extracted")
                    
                    # Save parsed JSON
                    parsed_output = {
                        "address_searched": address,
                        "listing_url": result.get("url"),
                        "html_file": os.path.relpath(html_file),
                        "html_size_chars": len(html),
                        "property_data": property_data,
                        "extraction_date": datetime.now().isoformat(),
                        "extraction_method": "HTML"
                    }
                    
                    parsed_filename = os.path.join(RESULTS_DIR, f"property_data_{index}_{timestamp}.json")
                    with open(parsed_filename, 'w', encoding='utf-8') as f:
                        json.dump(parsed_output, f, indent=2, ensure_ascii=False)
                    
                    result["parsed_file"] = parsed_filename
                    print(f"✓ Saved parsed property data: {parsed_filename}")
                    
            except Exception as e:
                result["error"] = f"HTML/Parsing error: {e}"
                print(f"❌ HTML/Parsing error: {e}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Error: {e}")
    
    end_time = datetime.now()
    result["time_seconds"] = (end_time - start_time).total_seconds()
    
    # Update MongoDB if in mongodb mode
    if mongodb_mode:
        if result["success"] and 'parsed_output' in locals():
            update_mongodb_after_enrichment(
                address=address,
                success=True,
                enrichment_data=parsed_output
            )
        else:
            update_mongodb_after_enrichment(
                address=address,
                success=False,
                error=result.get("error")
            )
    
    return result

def load_addresses_from_json(filepath):
    """Load addresses from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    addresses = [prop["address"] for prop in data["properties"]]
    return addresses

def get_mongodb_connection():
    """Get MongoDB connection and collection"""
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    return client, collection

def get_unenriched_addresses_from_mongodb():
    """Query MongoDB for addresses that need enrichment"""
    try:
        client, collection = get_mongodb_connection()
        
        # Query for properties that are not enriched and haven't been attempted
        # Include properties where enriched field doesn't exist or is False
        cursor = collection.find(
            {
                "$or": [
                    {"enriched": {"$exists": False}},
                    {"enriched": False}
                ],
                "$or": [
                    {"enrichment_attempted": {"$exists": False}},
                    {"enrichment_attempted": {"$ne": True}}
                ]
            },
            {"address": 1}
        )
        
        addresses = []
        for doc in cursor:
            address_field = doc.get("address")
            # Handle both string and dict address formats
            if isinstance(address_field, dict):
                address = address_field.get('full', '')
            elif isinstance(address_field, str):
                address = address_field
            else:
                continue
            
            if address:
                addresses.append(address)
        
        client.close()
        
        return addresses
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        return []

def get_all_properties_for_monitoring():
    """Query MongoDB for all properties with enrichment data for monitoring"""
    try:
        client, collection = get_mongodb_connection()
        
        # Query for properties that have enrichment_data
        cursor = collection.find(
            {"enrichment_data": {"$exists": True, "$ne": None}},
            {"address": 1, "enrichment_data": 1, "timeline": 1}
        )
        
        properties = []
        for doc in cursor:
            address_field = doc.get("address")
            # Handle both string and dict address formats
            if isinstance(address_field, dict):
                address = address_field.get('full', '')
            elif isinstance(address_field, str):
                address = address_field
            else:
                continue
            
            if address:
                properties.append({
                    "address": address,
                    "enrichment_data": doc.get("enrichment_data"),
                    "timeline": doc.get("timeline", [])
                })
        
        client.close()
        
        return properties
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        return []

def initialize_timeline_from_enrichment(enrichment_data):
    """Create initial timeline event from enrichment data"""
    if not enrichment_data:
        return None
    
    property_data = enrichment_data.get("property_data", {})
    
    initial_event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "initial_record",
        "changes": {}
    }
    
    # Extract the three monitored fields
    if "price" in property_data:
        initial_event["changes"]["price"] = {"value": property_data["price"]}
    
    if "agents_description" in property_data:
        initial_event["changes"]["agents_description"] = {"value": property_data["agents_description"]}
    
    if "inspection_times" in property_data:
        initial_event["changes"]["inspection_times"] = {"value": property_data["inspection_times"]}
    
    # Only return if we have at least one field
    if initial_event["changes"]:
        return initial_event
    
    return None

def get_latest_timeline_values(timeline):
    """Extract most recent values for monitored fields from timeline"""
    if not timeline:
        return {}
    
    latest_values = {}
    
    # Start from the most recent event and work backwards
    for event in reversed(timeline):
        changes = event.get("changes", {})
        
        # For each monitored field, get the most recent value
        for field in ["price", "agents_description", "inspection_times"]:
            if field in changes and field not in latest_values:
                # Handle both initial_record format and field_change format
                if "value" in changes[field]:
                    latest_values[field] = changes[field]["value"]
                elif "new_value" in changes[field]:
                    latest_values[field] = changes[field]["new_value"]
                elif "old_value" in changes[field]:
                    latest_values[field] = changes[field]["old_value"]
    
    return latest_values

def detect_changes(current_data, previous_values):
    """Compare current data with previous values for the 3 monitored fields"""
    changes = {}
    
    monitored_fields = ["price", "agents_description", "inspection_times"]
    
    for field in monitored_fields:
        current_value = current_data.get(field)
        previous_value = previous_values.get(field)
        
        # Skip if current value doesn't exist
        if current_value is None:
            continue
        
        # If no previous value, this is new data (shouldn't happen if timeline initialized)
        if previous_value is None:
            changes[field] = {
                "old_value": None,
                "new_value": current_value
            }
        # Compare values (handle lists and strings)
        elif current_value != previous_value:
            changes[field] = {
                "old_value": previous_value,
                "new_value": current_value
            }
    
    return changes

def create_timeline_event(changes):
    """Format new timeline entry for detected changes"""
    if not changes:
        return None
    
    return {
        "timestamp": datetime.now().isoformat(),
        "event_type": "field_change",
        "changes": changes
    }

def update_property_timeline(address, new_event):
    """Append new event to property's timeline in MongoDB"""
    try:
        client, collection = get_mongodb_connection()
        
        # Append to timeline array
        result = collection.update_one(
            {"address": address},
            {
                "$push": {"timeline": new_event},
                "$set": {"last_timeline_update": datetime.now()}
            }
        )
        
        client.close()
        return result.modified_count > 0
    except Exception as e:
        print(f"  ⚠ Timeline update error: {e}")
        return False

def navigate_to_url(url):
    """Navigate directly to a specific URL"""
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(url)
    time.sleep(0.5)
    press_enter()
    time.sleep(PAGE_LOAD_WAIT)
    
    # Validate we're on a domain.com.au page
    is_valid, current_url = validate_domain_url()
    return is_valid, current_url

def process_property_for_monitoring(property_doc, index, total):
    """Process a single property for change monitoring"""
    address = property_doc["address"]
    enrichment_data = property_doc.get("enrichment_data")
    timeline = property_doc.get("timeline", [])
    
    print(f"\n{'='*80}")
    print(f"Monitoring Property {index}/{total}: {address}")
    print(f"{'='*80}")
    
    start_time = datetime.now()
    result = {
        "address": address,
        "index": index,
        "success": False,
        "timeline_initialized": False,
        "changes_detected": False,
        "changes": {},
        "error": None,
        "time_seconds": 0
    }
    
    try:
        # Step 1: Check if timeline needs initialization
        if not timeline:
            print("→ Timeline not found - initializing from enrichment data...")
            initial_event = initialize_timeline_from_enrichment(enrichment_data)
            
            if initial_event:
                timeline = [initial_event]
                update_property_timeline(address, initial_event)
                result["timeline_initialized"] = True
                print(f"  ✓ Timeline initialized with initial values")
                for field, data in initial_event["changes"].items():
                    print(f"    • {field}: {data['value']}")
            else:
                result["error"] = "No data available to initialize timeline"
                print(f"  ✗ Could not initialize timeline - missing enrichment data")
                return result
        else:
            print(f"→ Timeline exists with {len(timeline)} events")
        
        # Step 2: Get listing URL from enrichment data
        if not enrichment_data or "listing_url" not in enrichment_data:
            result["error"] = "No listing URL in enrichment data"
            print(f"  ✗ No listing URL found in enrichment data")
            return result
        
        listing_url = enrichment_data["listing_url"]
        print(f"→ Navigating to listing URL: {listing_url}")
        
        # Step 3: Navigate to listing URL
        is_valid, current_url = navigate_to_url(listing_url)
        
        if not is_valid:
            result["error"] = f"Failed to navigate to listing URL"
            print(f"  ✗ Navigation failed")
            return result
        
        print(f"  ✓ Navigation successful")
        
        # Step 4: Extract current HTML and parse
        print("→ Extracting current HTML...")
        html = extract_page_html()
        
        if not html:
            result["error"] = "Failed to extract HTML"
            print(f"  ✗ HTML extraction failed")
            return result
        
        print(f"  ✓ Extracted HTML ({len(html):,} chars)")
        
        # Step 5: Parse HTML for the monitored fields
        print("→ Parsing HTML for monitored fields...")
        current_data = parse_listing_html(html, address)
        current_data = clean_property_data(current_data)
        
        print(f"  ✓ Parsed current data:")
        for field in ["price", "agents_description", "inspection_times"]:
            if field in current_data:
                value = current_data[field]
                if isinstance(value, str) and len(value) > 60:
                    print(f"    • {field}: {value[:60]}...")
                else:
                    print(f"    • {field}: {value}")
        
        # Step 6: Get previous values from timeline
        previous_values = get_latest_timeline_values(timeline)
        print(f"→ Comparing with previous values...")
        
        # Step 7: Detect changes
        changes = detect_changes(current_data, previous_values)
        
        if changes:
            result["changes_detected"] = True
            result["changes"] = changes
            print(f"  ✓ Changes detected in {len(changes)} field(s):")
            
            for field, change_data in changes.items():
                old_val = change_data["old_value"]
                new_val = change_data["new_value"]
                
                # Format for display
                if isinstance(old_val, str) and len(old_val) > 40:
                    old_display = old_val[:40] + "..."
                else:
                    old_display = old_val
                
                if isinstance(new_val, str) and len(new_val) > 40:
                    new_display = new_val[:40] + "..."
                else:
                    new_display = new_val
                
                print(f"    • {field}:")
                print(f"      - Old: {old_display}")
                print(f"      - New: {new_display}")
            
            # Step 8: Create and save timeline event
            new_event = create_timeline_event(changes)
            if new_event:
                success = update_property_timeline(address, new_event)
                if success:
                    print(f"  ✓ Timeline updated in MongoDB")
                    result["success"] = True
                else:
                    result["error"] = "Failed to update timeline in MongoDB"
                    print(f"  ✗ Failed to update timeline")
        else:
            print(f"  ✓ No changes detected")
            result["success"] = True
    
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Error: {e}")
    
    end_time = datetime.now()
    result["time_seconds"] = (end_time - start_time).total_seconds()
    
    return result

def update_mongodb_after_enrichment(address, success, enrichment_data=None, error=None):
    """Update MongoDB document after enrichment attempt"""
    try:
        client, collection = get_mongodb_connection()
        
        update_doc = {
            "enrichment_attempted": True,
            "last_enriched": datetime.now()
        }
        
        if success and enrichment_data:
            update_doc["enriched"] = True
            update_doc["enrichment_data"] = enrichment_data
            update_doc["enrichment_error"] = None
        else:
            update_doc["enriched"] = False
            update_doc["enrichment_error"] = error
            # Increment retry count
            collection.update_one(
                {"address": address},
                {"$inc": {"enrichment_retry_count": 1}}
            )
        
        collection.update_one(
            {"address": address},
            {"$set": update_doc}
        )
        
        client.close()
        return True
    except Exception as e:
        print(f"  ⚠ MongoDB update error: {e}")
        return False

def generate_report(results, output_file):
    """Generate comprehensive report"""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    fixed_success = sum(1 for r in results if r["method"] == "FIXED_COORDINATES")
    direct_url_success = sum(1 for r in results if r["method"] == "DIRECT_URL")
    
    total_time = sum(r["time_seconds"] for r in results)
    avg_time = total_time / total if total > 0 else 0
    
    report = {
        "batch_info": {
            "start_time": datetime.now().isoformat(),
            "total_addresses": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            "total_time_seconds": round(total_time, 2),
            "average_time_seconds": round(avg_time, 2)
        },
        "method_breakdown": {
            "fixed_coordinates": fixed_success,
            "direct_url": direct_url_success,
            "fixed_success_rate": f"{(fixed_success/total*100):.1f}%" if total > 0 else "0%",
            "direct_url_success_rate": f"{(direct_url_success/total*100):.1f}%" if total > 0 else "0%"
        },
        "results": results
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Main batch processing workflow"""
    parser = argparse.ArgumentParser(description="Batch address processor with enrichment and monitoring modes")
    parser.add_argument('--address', help='Process a single address (e.g. "72 Woody Views Way, Robina, QLD 4226")')
    parser.add_argument('--input_json', help='Input JSON file path for batch processing')
    parser.add_argument('--mongodb', action='store_true', help='Process addresses from MongoDB (unenriched properties)')
    parser.add_argument('--monitor', action='store_true', help='Monitor mode: check all properties for changes in price, agents_description, and inspection_times')
    args = parser.parse_args()
    
    # MONITORING MODE - Track changes in property data
    if args.monitor:
        print("\n" + "=" * 80)
        print("PROPERTY CHANGE MONITORING MODE")
        print("=" * 80)
        print("\nMonitoring fields: price, agents_description, inspection_times")
        
        # Get all properties with enrichment data
        properties = get_all_properties_for_monitoring()
        
        if not properties:
            print(f"\n⚠ No properties found with enrichment data")
            print(f"Run with --mongodb flag first to enrich properties\n")
            return 0
        
        print(f"\nFound {len(properties)} properties to monitor")
        print(f"\n{'='*80}\n")
        
        # Open Chrome if not already open
        try:
            current_url = get_current_url()
            if not current_url:
                script = '''
                tell application "Google Chrome"
                    activate
                    make new window
                    set URL of active tab of front window to "about:blank"
                end tell
                '''
                run_applescript(script)
                time.sleep(1)
                maximize_chrome_window()
        except:
            pass
        
        # Process each property
        monitoring_results = []
        for i, property_doc in enumerate(properties, 1):
            result = process_property_for_monitoring(property_doc, i, len(properties))
            monitoring_results.append(result)
            
            # Brief pause between properties
            if i < len(properties):
                print(f"\n→ Waiting {BETWEEN_ADDRESS_DELAY} seconds before next property...")
                time.sleep(BETWEEN_ADDRESS_DELAY)
        
        # Generate monitoring report
        print(f"\n{'='*80}")
        print("MONITORING COMPLETE")
        print(f"{'='*80}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(RESULTS_DIR, exist_ok=True)
        report_file = os.path.join(RESULTS_DIR, f"monitoring_report_{timestamp}.json")
        
        total = len(monitoring_results)
        successful = sum(1 for r in monitoring_results if r["success"])
        timeline_initialized = sum(1 for r in monitoring_results if r["timeline_initialized"])
        changes_detected = sum(1 for r in monitoring_results if r["changes_detected"])
        failed = sum(1 for r in monitoring_results if r["error"])
        
        total_time = sum(r["time_seconds"] for r in monitoring_results)
        avg_time = total_time / total if total > 0 else 0
        
        monitoring_report = {
            "monitoring_info": {
                "timestamp": datetime.now().isoformat(),
                "total_properties": total,
                "successful": successful,
                "failed": failed,
                "timeline_initialized": timeline_initialized,
                "changes_detected": changes_detected,
                "total_time_seconds": round(total_time, 2),
                "average_time_seconds": round(avg_time, 2)
            },
            "results": monitoring_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(monitoring_report, f, indent=2)
        
        # Print summary
        print(f"\n📊 MONITORING SUMMARY:")
        print(f"  Total properties monitored: {total}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Timeline initialized: {timeline_initialized}")
        print(f"  Changes detected: {changes_detected}")
        if changes_detected > 0:
            print(f"\n  📝 Properties with changes:")
            for r in monitoring_results:
                if r["changes_detected"]:
                    print(f"    • {r['address']}")
                    for field in r["changes"].keys():
                        print(f"      - {field} changed")
        print(f"\n  Total time: {round(total_time, 2)}s")
        print(f"  Average time: {round(avg_time, 2)}s per property")
        print(f"\n📁 Report saved: {report_file}")
        print(f"\n{'='*80}\n")
        
        return 0
    
    # ENRICHMENT MODE - Original functionality
    print("\n" + "=" * 80)
    print("BATCH ADDRESS PROCESSOR")
    print("=" * 80)
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Determine addresses to process
    mongodb_mode = args.mongodb
    
    if args.mongodb:
        print(f"\n→ Running in MongoDB mode - processing unenriched properties")
        addresses = get_unenriched_addresses_from_mongodb()
        if not addresses:
            print(f"\n✓ No unenriched properties found in MongoDB")
            print(f"All properties are already enriched!\n")
            return 0
        print(f"\nFound {len(addresses)} unenriched properties to process")
    elif args.address:
        addresses = [args.address]
        print(f"\n→ Running in single-address test mode for: {args.address}")
    elif args.input_json and os.path.exists(args.input_json):
        addresses = load_addresses_from_json(args.input_json)
        print(f"\nLoaded {len(addresses)} addresses from {args.input_json}")
    else:
        # Load addresses from default JSON
        json_path = "../../Simple_Method/property_data_session_2.json"
        addresses = load_addresses_from_json(json_path)
        print(f"\nLoaded {len(addresses)} addresses from {json_path}")
    
    print(f"Results will be saved to: {RESULTS_DIR}/")
    print("\n" + "=" * 80)
    
    # Process each address
    results = []
    for i, address in enumerate(addresses, 1):
        result = process_single_address(address, i, len(addresses), mongodb_mode=mongodb_mode)
        results.append(result)
        
        # Brief pause between addresses (skip if single test)
        if not args.address and i < len(addresses):
            print(f"\n→ Waiting {BETWEEN_ADDRESS_DELAY} seconds before next address...")
            time.sleep(BETWEEN_ADDRESS_DELAY)
    
    # Generate report
    print(f"\n{'='*80}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(RESULTS_DIR, f"batch_report_{timestamp}.json")
    report = generate_report(results, report_file)
    
    # Print summary
    print(f"\n📊 SUMMARY:")
    print(f"  Total addresses: {report['batch_info']['total_addresses']}")
    print(f"  Successful: {report['batch_info']['successful']}")
    print(f"  Failed: {report['batch_info']['failed']}")
    print(f"  Success rate: {report['batch_info']['success_rate']}")
    print(f"  Total time: {report['batch_info']['total_time_seconds']}s")
    print(f"  Average time: {report['batch_info']['average_time_seconds']}s per address")
    print(f"\n📈 METHOD BREAKDOWN:")
    print(f"  Fixed coordinates: {report['method_breakdown']['fixed_coordinates']} ({report['method_breakdown']['fixed_success_rate']})")
    print(f"  Direct URL construction: {report['method_breakdown']['direct_url']} ({report['method_breakdown']['direct_url_success_rate']})")
    print(f"\n📁 Report saved: {report_file}")
    
    if mongodb_mode:
        print(f"\n📊 MongoDB Status:")
        try:
            client, collection = get_mongodb_connection()
            total_props = collection.count_documents({})
            enriched = collection.count_documents({"enriched": True})
            unenriched = collection.count_documents({"enriched": False})
            print(f"  Total properties: {total_props}")
            print(f"  Enriched: {enriched}")
            print(f"  Unenriched: {unenriched}")
            if total_props > 0:
                print(f"  Completion rate: {(enriched/total_props*100):.1f}%")
            client.close()
        except Exception as e:
            print(f"  ⚠ Could not retrieve MongoDB stats: {e}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()
