#!/usr/bin/env python3
"""
Improved Property Data Parser
Analyzes OCR text and extracts property listings with all details
"""

import re
import json
from datetime import datetime
import os

# Configuration
OCR_INPUT_FILE = "ocr_output/raw_text_all.txt"
OUTPUT_FILE = "property_data_improved.json"

def extract_property_details(detail_line):
    """
    Parse property detail line like: 'A4 42 &2 (934m? - House'
    Returns: {bedrooms, bathrooms, parking, land_size, property_type}
    """
    details = {}
    
    # Property details pattern: A/B followed by numbers for bed/bath/parking
    # Example: "A4 42 &2 (934m? - House" or "B5 43 &2 10 842m? - House"
    match = re.search(r'[AB](\d+)\s*[&]?\s*(\d+)\s*[&@](\d+)(?:\s+[!1]?[0Oo]?\s*(\d+,?\d*))?m?\??\s*-\s*(\w+)', detail_line)
    
    if match:
        details['bedrooms'] = int(match.group(1))
        details['bathrooms'] = int(match.group(2))
        details['parking'] = int(match.group(3))
        
        if match.group(4):
            # Clean land size
            land_size = match.group(4).replace(',', '')
            try:
                details['land_size_sqm'] = int(land_size)
            except:
                pass
        
        details['property_type'] = match.group(5).strip()
    
    return details

def parse_properties_improved(text):
    """
    Improved parsing that captures all property data
    """
    properties = []
    lines = text.split('\n')
    
    # Patterns
    # Address must contain ", Robina" and street/court/drive etc
    address_pattern = r'(\d+[-/]?\d*\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Court|Ct|Place|Pl|Circuit|Cct|Way|Lane|Ln|Terrace|Tce|Crescent|Cres|Close|Boulevard|Blvd|Parade|Pde),\s*Robina)'
    
    # Property details pattern
    detail_pattern = r'[AB]\d+\s*[&]?\s*\d+\s*[&@]\d+.*?-\s*(?:House|Townhouse|Unit|Apartment|Duplex)'
    
    # Price patterns - comprehensive
    price_patterns = {
        'exact': r'\$[\d,]+(?:\.\d+)?[kKmM]?',
        'range': r'\$[\d,]+\s*-\s*\$[\d,]+',
        'offers_over': r'Offers?\s+[Oo]ver\s+\$[\d,]+(?:\.\d+)?[kKmM]?',
        'contact': r'Contact\s+Agent|CONTACT\s+AGENT',
        'auction': r'Auction',
        'eoi': r'Expressions?\s+[Oo]f\s+[Ii]nterest',
        'must_sell': r'MUST\s+BE\s+SOLD',
        'under_offer': r'[Uu]nder\s+offer|UNDER\s+OFFER'
    }
    
    # Agent pattern
    agent_pattern = r'(RayWhite|Ray\s*White|McGrath|Harcourts|REMAX|COASTAL|Astras?|MARSH|crasto|COMPANY\s*RE)[.\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    
    # URL pattern
    url_pattern = r'https://www\.realestate\.com\.au/property-[a-z]+-qld-robina-\d+'
    
    # Inspection pattern
    inspection_pattern = r'Inspection\s+(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri|tomorrow)\s+\d+\s+\w+(?:\s+\d+:\d+\s+[ap]m)?'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for address
        addr_match = re.search(address_pattern, line, re.IGNORECASE)
        
        if addr_match:
            property_data = {
                'address': addr_match.group(1).strip()
            }
            
            # Look at surrounding lines for more data (check 5 lines before and after)
            context_start = max(0, i - 5)
            context_end = min(len(lines), i + 10)
            context = '\n'.join(lines[context_start:context_end])
            
            # Extract property details (bed/bath/parking)
            detail_match = re.search(detail_pattern, context, re.IGNORECASE)
            if detail_match:
                details = extract_property_details(detail_match.group(0))
                property_data.update(details)
            
            # Extract price (try all patterns)
            for price_type, pattern in price_patterns.items():
                price_match = re.search(pattern, context, re.IGNORECASE)
                if price_match and 'price' not in property_data:
                    property_data['price'] = price_match.group(0).strip()
                    property_data['price_type'] = price_type
                    break
            
            # Extract agent
            agent_match = re.search(agent_pattern, context, re.IGNORECASE)
            if agent_match:
                agency = agent_match.group(1).strip().replace(' ', '')
                agent_name = agent_match.group(2).strip() if agent_match.group(2) else ''
                property_data['agency'] = agency
                if agent_name:
                    property_data['agent'] = agent_name
            
            # Extract URL
            url_match = re.search(url_pattern, context)
            if url_match:
                property_data['listing_url'] = url_match.group(0).strip()
            
            # Extract inspection
            insp_match = re.search(inspection_pattern, context, re.IGNORECASE)
            if insp_match:
                property_data['inspection'] = insp_match.group(0).strip()
            
            # Store raw context for debugging
            property_data['raw_context'] = context
            
            properties.append(property_data)
        
        i += 1
    
    return properties

def deduplicate_properties(properties):
    """Remove duplicates based on address"""
    seen = set()
    unique = []
    
    for prop in properties:
        addr = prop.get('address', '').lower().strip()
        if addr and addr not in seen and 'Sold' not in prop.get('address', ''):
            seen.add(addr)
            unique.append(prop)
    
    return unique

def calculate_stats(properties):
    """Calculate statistics about data completeness"""
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
        'with_inspection': len([p for p in properties if p.get('inspection')])
    }

def main():
    """Main function"""
    print("=" * 70)
    print("IMPROVED PROPERTY DATA PARSER")
    print("=" * 70)
    
    # Check if OCR file exists
    if not os.path.exists(OCR_INPUT_FILE):
        print(f"\n✗ OCR file not found: {OCR_INPUT_FILE}")
        print("  Run: python ocr_extractor.py first")
        return
    
    # Read OCR text
    print(f"\n→ Reading OCR text from {OCR_INPUT_FILE}...")
    with open(OCR_INPUT_FILE, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    print(f"  ✓ Read {len(ocr_text):,} characters")
    
    # Parse properties
    print("\n→ Parsing property listings...")
    properties = parse_properties_improved(ocr_text)
    print(f"  ✓ Found {len(properties)} potential properties")
    
    # Deduplicate
    print("\n→ Removing duplicates and sold properties...")
    unique_properties = deduplicate_properties(properties)
    print(f"  ✓ {len(unique_properties)} unique for-sale properties")
    
    # Calculate statistics
    stats = calculate_stats(unique_properties)
    
    # Create output
    output_data = {
        "extraction_date": datetime.now().isoformat(),
        "source": "realestate.com.au - Robina, QLD 4226",
        "total_properties": len(unique_properties),
        "properties": unique_properties,
        "statistics": stats
    }
    
    # Save to JSON
    print(f"\n→ Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Display summary
    print("\n" + "=" * 70)
    print("✅ IMPROVED PARSING COMPLETE")
    print("=" * 70)
    print(f"Total properties found: {stats['total']}")
    print(f"\nData completeness:")
    print(f"  • Addresses:      {stats['total']}")
    print(f"  • Prices:         {stats['with_price']}")
    print(f"  • Bedrooms:       {stats['with_bedrooms']}")
    print(f"  • Bathrooms:      {stats['with_bathrooms']}")
    print(f"  • Parking:        {stats['with_parking']}")
    print(f"  • Land size:      {stats['with_land_size']}")
    print(f"  • Property type:  {stats['with_property_type']}")
    print(f"  • Agent name:     {stats['with_agent']}")
    print(f"  • Agency:         {stats['with_agency']}")
    print(f"  • Listing URL:    {stats['with_url']}")
    print(f"  • Inspection:     {stats['with_inspection']}")
    print(f"\nOutput saved to: {OUTPUT_FILE}")
    
    # Show sample properties
    if unique_properties:
        print(f"\n📋 Sample properties (first 5):")
        for i, prop in enumerate(unique_properties[:5], 1):
            print(f"\n  Property {i}:")
            print(f"    Address:      {prop.get('address', 'N/A')}")
            print(f"    Price:        {prop.get('price', 'N/A')}")
            print(f"    Beds/Bath/Car: {prop.get('bedrooms', '?')}/{prop.get('bathrooms', '?')}/{prop.get('parking', '?')}")
            print(f"    Land:         {prop.get('land_size_sqm', 'N/A')} sqm")
            print(f"    Type:         {prop.get('property_type', 'N/A')}")
            print(f"    Agent:        {prop.get('agent', 'N/A')} ({prop.get('agency', 'N/A')})")
            if prop.get('listing_url'):
                print(f"    URL:          {prop.get('listing_url')[:60]}...")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
