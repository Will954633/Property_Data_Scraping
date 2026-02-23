#!/usr/bin/env python3
"""
Final Optimized Property Data Parser
Captures ALL property data accurately from OCR text
"""

import re
import json
from datetime import datetime
import os

# Configuration
OCR_INPUT_FILE = "ocr_output/raw_text_all.txt"
OUTPUT_FILE = "property_data_final.json"

def extract_property_details(context):
    """
    Enhanced extraction of bed/bath/parking/land/type from context
    Handles variations like: A4 42 &2 (934m?, B5 43 @2 10 842m?, etc.
    """
    details = {}
    
    # Multiple pattern attempts for flexibility
    patterns = [
        # Pattern 1: A4 42 &2 506m? - House
        r'[AB](\d+)\s+(\d+)\s*[&@]\s*(\d+)\s+(?:[!1]?[0Oo]?\s*)?(\d+,?\d*)m?\??\s*-\s*(\w+)',
        # Pattern 2: A4 42 &2 10 506m? - House (with extra number)
        r'[AB](\d+)\s+(\d+)\s*[&@](\d+)\s+[1!][0Oo]\s+(\d+,?\d*)m?\??\s*-\s*(\w+)',
        # Pattern 3: Simpler A4 32 82 - House
        r'[AB](\d+)\s+(\d+)\s+(\d+).*?-\s*(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            details['bedrooms'] = int(match.group(1))
            
            # Handle bathroom (sometimes shows as 42 meaning 4 bath + 2 something)
            bath_str = match.group(2)
            if len(bath_str) == 2:
                details['bathrooms'] = int(bath_str[0])  # First digit
            else:
                details['bathrooms'] = int(bath_str)
            
            details['parking'] = int(match.group(3))
            
            # Land size (if present)
            if len(match.groups()) >= 5 and match.group(4):
                land_str = match.group(4).replace(',', '')
                try:
                    details['land_size_sqm'] = int(land_str)
                except:
                    pass
            
            # Property type
            type_idx =len(match.groups())
            details['property_type'] = match.group(type_idx).strip()
            break
    
    return details

def parse_properties_final(text):
    """
    Final optimized parser
    """
    properties = []
    lines = text.split('\n')
    
    # Address pattern - must have number + street name + Robina
    address_pattern = r'(\d+[-/]?\d*\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Court|Ct|Place|Pl|Circuit|Cct|Way|Lane|Ln|Terrace|Tce|Crescent|Cres|Close|Boulevard|Blvd|Parade|Pde),\s*Robina)'
    
    # Price patterns
    price_patterns = [
        (r'\$[\d,]+,\d{3}', 'exact'),  # $1,369,000
        (r'\$[\d.]+[mM]', 'millions'),  # $1.3m
        (r'\$\d+', 'basic'),  # $850000
        (r'Offers?\s+[Oo]ver\s+\$[\d,]+', 'offers_over'),
        (r'UNDER\s+OFFER|Under\s+offer', 'under_offer'),
        (r'MUST\s+BE\s+SOLD|Must\s+sell', 'must_sell'),
        (r'Contact\s+Agent|CONTACT\s+AGENT', 'contact_agent'),
        (r'Auction\s+Coming\s+Soon|Auction', 'auction'),
        (r'Expressions?\s+[Oo]f\s+[Ii]nterest', 'eoi'),
        (r'Just\s+Listed', 'just_listed'),
    ]
    
    # Agency patterns
    agency_pattern = r'(RayWhite|Ray\s*White|McGrath|Harcourts|REMAX|COASTAL|Astras?\.?|MARSH|crasto|COMPANY\s*RE|WELCOME\s*CHANGE)'
    
    # Agent name pattern (capital letter followed by lowercase)
    agent_name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
    
    # URL pattern
    url_pattern = r'https://www\.realestate\.com\.au/property-[a-z]+-qld-robina-\d+'
    
    # Inspection pattern
    inspection_pattern = r'[Ii]nspection\s+(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri|tomorrow)\s+\d+\s+\w+(?:\s+\d+:\d+\s+[ap]m)?'
    
    # Auction pattern
    auction_pattern = r'Auction\s+(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri|tomorrow)\s+\d+\s+\w+(?:\s+\d+:\d+\s+[ap]m)?'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip sold properties and dates
        if re.search(r'Sold\s+\d+\s+\w+\s+\d{4}', line):
            i += 1
            continue
        
        # Look for address
        addr_match = re.search(address_pattern, line, re.IGNORECASE)
        
        if addr_match:
            property_data = {
                'address': addr_match.group(1).strip()
            }
            
            # Get surrounding context (10 lines before/after)
            context_start = max(0, i - 10)
            context_end = min(len(lines), i + 15)
            context = '\n'.join(lines[context_start:context_end])
            
            # Extract property details
            details = extract_property_details(context)
            property_data.update(details)
            
            # Extract price (try all patterns in order)
            for pattern, price_type in price_patterns:
                price_match = re.search(pattern, context, re.IGNORECASE)
                if price_match:
                    property_data['price'] = price_match.group(0).strip()
                    property_data['price_type'] = price_type
                    break
            
            # Extract agency
            agency_match = re.search(agency_pattern, context, re.IGNORECASE)
            if agency_match:
                property_data['agency'] = agency_match.group(1).strip().replace(' ', '')
                
                # Try to find agent name near agency
                agency_pos = context.find(agency_match.group(0))
                nearby_text = context[max(0, agency_pos-50):min(len(context), agency_pos+100)]
                
                # Find agent names (capitalized words)
                agent_names = re.findall(agent_name_pattern, nearby_text)
                # Filter out common words
                excluded = {'Agent', 'Contact', 'McGrath', 'Harcourts', 'RayWhite', 'REMAX', 
                            'Featured', 'Inspection', 'Auction', 'House', 'Property', 'Listed',
                            'Under', 'Offer', 'Coming', 'Soon', 'Must', 'Sell', 'Sold'}
                valid_names = [n for n in agent_names if n not in excluded and len(n) > 2]
                if valid_names:
                    property_data['agent'] = ' '.join(valid_names[:2])  # Take first 1-2 names
            
            # Extract URL
            url_match = re.search(url_pattern, context)
            if url_match:
                property_data['listing_url'] = url_match.group(0).strip()
            
            # Extract inspection
            insp_match = re.search(inspection_pattern, context, re.IGNORECASE)
            if insp_match:
                property_data['inspection'] = insp_match.group(0).strip()
            
            # Extract auction
            auction_match = re.search(auction_pattern, context, re.IGNORECASE)
            if auction_match:
                property_data['auction'] = auction_match.group(0).strip()
            
            properties.append(property_data)
        
        i += 1
    
    return properties

def deduplicate_properties(properties):
    """Remove duplicates"""
    seen = set()
    unique = []
    
    for prop in properties:
        addr = prop.get('address', '').lower().strip()
        if addr and addr not in seen:
            seen.add(addr)
            unique.append(prop)
    
    return unique

def calculate_stats(properties):
    """Calculate comprehensive statistics"""
    total = len(properties)
    return {
        'total': total,
        'with_price': len([p for p in properties if p.get('price')]),
        'with_bedrooms': len([p for p in properties if p.get('bedrooms')]),
        'with_bathrooms': len([p for p in properties if p.get('bathrooms')]),
        'with_parking': len([p for p in properties if p.get('parking')]),
        'with_land_size': len([p for p in properties if p.get('land_size_sqm')]),
        'with_property_type': len([p for p in properties if p.get('property_type')]),
        'with_agent': len([p for p in properties if p.get('agent')]),
        'with_agency': len([p for p in properties if p.get('agency')]),
        'with_url': len([p for p in properties if p.get('listing_url')]),
        'with_inspection': len([p for p in properties if p.get('inspection')]),
        'with_auction': len([p for p in properties if p.get('auction')]),
        'price_types': {}
    }
    
    # Count price types
    for prop in properties:
        price_type = prop.get('price_type', 'unknown')
        stats['price_types'][price_type] = stats['price_types'].get(price_type, 0) + 1
    
    return stats

def main():
    """Main function"""
    print("=" * 70)
    print("FINAL OPTIMIZED PROPERTY DATA PARSER")
    print("=" * 70)
    
    # Check if OCR file exists
    if not os.path.exists(OCR_INPUT_FILE):
        print(f"\n✗ OCR file not found: {OCR_INPUT_FILE}")
        print("  Run: python ocr_extractor.py first")
        return
    
    # Read OCR text
    print(f"\n→ Reading OCR text...")
    with open(OCR_INPUT_FILE, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    print(f"  ✓ Read {len(ocr_text):,} characters")
    
    # Parse properties
    print("\n→ Parsing property listings...")
    properties = parse_properties_final(ocr_text)
    print(f"  ✓ Found {len(properties)} properties")
    
    # Deduplicate
    print("\n→ Removing duplicates...")
    unique_properties = deduplicate_properties(properties)
    print(f"  ✓ {len(unique_properties)} unique properties")
    
    # Calculate stats
    stats = calculate_stats(unique_properties)
    
    # Create output
    output_data = {
        "extraction_date": datetime.now().isoformat(),
        "source": "realestate.com.au - Houses for sale in Robina, QLD 4226",
        "search_url": "https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-1",
        "total_properties": len(unique_properties),
        "properties": unique_properties,
        "statistics": stats
    }
    
    # Save to JSON
    print(f"\n→ Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Display detailed summary
    print("\n" + "=" * 70)
    print("✅ FINAL PARSING COMPLETE")
    print("=" * 70)
    print(f"Total properties: {stats['total']}")
    print(f"\nData Completeness:")
    print(f"  • Addresses:      {stats['total']:3d} / {stats['total']} (100%)")
    print(f"  • Prices:         {stats['with_price']:3d} / {stats['total']} ({stats['with_price']/stats['total']*100:.0f}%)")
    print(f"  • Bedrooms:       {stats['with_bedrooms']:3d} / {stats['total']} ({stats['with_bedrooms']/stats['total']*100:.0f}%)")
    print(f"  • Bathrooms:      {stats['with_bathrooms']:3d} / {stats['total']} ({stats['with_bathrooms']/stats['total']*100:.0f}%)")
    print(f"  • Parking:        {stats['with_parking']:3d} / {stats['total']} ({stats['with_parking']/stats['total']*100:.0f}%)")
    print(f"  • Land size:      {stats['with_land_size']:3d} / {stats['total']} ({stats['with_land_size']/stats['total']*100:.0f}%)")
    print(f"  • Property type:  {stats['with_property_type']:3d} / {stats['total']} ({stats['with_property_type']/stats['total']*100:.0f}%)")
    print(f"  • Agency:         {stats['with_agency']:3d} / {stats['total']} ({stats['with_agency']/stats['total']*100:.0f}%)")
    print(f"  • Agent name:     {stats['with_agent']:3d} / {stats['total']} ({stats['with_agent']/stats['total']*100:.0f}%)")
    print(f"  • Listing URL:    {stats['with_url']:3d} / {stats['total']} ({stats['with_url']/stats['total']*100:.0f}%)")
    print(f"  • Inspection:     {stats['with_inspection']:3d} / {stats['total']} ({stats['with_inspection']/stats['total']*100:.0f}%)")
    print(f"\nPrice Types:")
    for price_type, count in sorted(stats['price_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {price_type:20s}: {count}")
    
    print(f"\nOutput saved to: {OUTPUT_FILE}")
    
    # Show ALL properties in summary
    if unique_properties:
        print(f"\n📋 ALL {len(unique_properties)} PROPERTIES:")
        for i, prop in enumerate(unique_properties, 1):
            print(f"\n  {i:2d}. {prop.get('address', 'N/A')}")
            print(f"      Price: {prop.get('price', 'N/A'):30s}  Beds/Bath/Car: {prop.get('bedrooms', '?')}/{prop.get('bathrooms', '?')}/{prop.get('parking', '?')}")
            print(f"      Type:  {prop.get('property_type', 'N/A'):30s}  Land: {prop.get('land_size_sqm', 'N/A')} sqm")
            if prop.get('agent'):
                print(f"      Agent: {prop.get('agent')} @ {prop.get('agency', 'N/A')}")
            if prop.get('inspection'):
                print(f"      {prop.get('inspection')}")
            if prop.get('listing_url'):
                print(f"      URL:   ...{prop.get('listing_url')[-40:]}")
    
    print("\n" + "=" * 70)
    print(f"\n✅ Use 'python' (not 'python3') to run scripts")
    print(f"✅ View full data: cat {OUTPUT_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    main()
