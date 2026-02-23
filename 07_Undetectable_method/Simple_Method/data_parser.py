#!/usr/bin/env python3
"""
Property Data Parser
Parses OCR extracted text and structures property data into JSON
"""

import re
import json
from datetime import datetime
import os

# Configuration
OCR_INPUT_FILE = "ocr_output/raw_text_all.txt"
OUTPUT_FILE = "property_data.json"

def parse_property_data(text):
    """
    Parse property listings from OCR text
    Returns list of property dictionaries
    """
    properties = []
    
    # Split text into lines for processing
    lines = text.split('\n')
    
    # Patterns for matching
    # Address patterns - QLD addresses
    address_pattern = r'(\d+[A-Za-z]?\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Court|Ct|Place|Pl|Circuit|Cct|Way|Lane|Ln|Terrace|Tce|Crescent|Cres|Close|Boulevard|Blvd|Parade|Pde),?\s*(?:Robina|[A-Za-z\s]+),?\s*(?:QLD|Queensland)?\s*\d{4})'
    
    # Price patterns
    price_patterns = [
        r'\$[\d,]+(?:\.\d{2})?[kKmM]?',  # $850,000 or $1.2M
        r'[\d,]+(?:\.\d{2})?\s*million',  # 1.2 million
        r'Offers?\s+[Oo]ver\s+\$[\d,]+',  # Offers over $...
        r'From\s+\$[\d,]+',  # From $...
        r'Contact\s+[Aa]gent',  # Contact agent
        r'Price\s+[Ww]ithheld',  # Price withheld
    ]
    
    # Bedroom pattern
    bed_pattern = r'(\d+)\s*(?:bed(?:room)?s?|bd|BR)'
    
    # Bathroom pattern
    bath_pattern = r'(\d+)\s*(?:bath(?:room)?s?|ba)'
    
    # Parking/Garage pattern
    parking_pattern = r'(\d+)\s*(?:car|garage|parking)'
    
    # Property type pattern
    type_pattern = r'\b(House|Townhouse|Villa|Unit|Apartment|Land|Duplex)\b'
    
    # Process text line by line
    current_property = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Try to find address
        address_match = re.search(address_pattern, line, re.IGNORECASE)
        if address_match:
            # Start new property if we have data for previous one
            if current_property.get('address'):
                properties.append(current_property)
                current_property = {}
            
            current_property['address'] = address_match.group(0).strip()
            current_property['raw_text'] = line
        
        # Look for price
        if not current_property.get('price'):
            for pattern in price_patterns:
                price_match = re.search(pattern, line, re.IGNORECASE)
                if price_match:
                    current_property['price'] = price_match.group(0).strip()
                    break
        
        # Look for bedrooms
        if not current_property.get('bedrooms'):
            bed_match = re.search(bed_pattern, line, re.IGNORECASE)
            if bed_match:
                current_property['bedrooms'] = int(bed_match.group(1))
        
        # Look for bathrooms
        if not current_property.get('bathrooms'):
            bath_match = re.search(bath_pattern, line, re.IGNORECASE)
            if bath_match:
                current_property['bathrooms'] = int(bath_match.group(1))
        
        # Look for parking
        if not current_property.get('parking'):
            parking_match = re.search(parking_pattern, line, re.IGNORECASE)
            if parking_match:
                current_property['parking'] = int(parking_match.group(1))
        
        # Look for property type
        if not current_property.get('property_type'):
            type_match = re.search(type_pattern, line, re.IGNORECASE)
            if type_match:
                current_property['property_type'] = type_match.group(1).title()
    
    # Add last property if exists
    if current_property.get('address'):
        properties.append(current_property)
    
    return properties

def deduplicate_properties(properties):
    """
    Remove duplicate properties based on address
    """
    seen_addresses = set()
    unique_properties = []
    
    for prop in properties:
        address = prop.get('address', '').lower().strip()
        if address and address not in seen_addresses:
            seen_addresses.add(address)
            unique_properties.append(prop)
    
    return unique_properties

def main():
    """Main function"""
    print("=" * 70)
    print("PROPERTY DATA PARSER")
    print("=" * 70)
    
    # Check if OCR file exists
    if not os.path.exists(OCR_INPUT_FILE):
        print(f"\n✗ OCR file not found: {OCR_INPUT_FILE}")
        print("  Run ocr_extractor.py first to extract text from screenshots")
        return
    
    # Read OCR text
    print(f"\n→ Reading OCR text from {OCR_INPUT_FILE}...")
    with open(OCR_INPUT_FILE, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    print(f"  ✓ Read {len(ocr_text):,} characters")
    
    # Parse property data
    print("\n→ Parsing property data...")
    properties = parse_property_data(ocr_text)
    print(f"  ✓ Found {len(properties)} potential properties")
    
    # Deduplicate
    print("\n→ Removing duplicates...")
    unique_properties = deduplicate_properties(properties)
    print(f"  ✓ {len(unique_properties)} unique properties")
    
    # Create output structure
    output_data = {
        "extraction_date": datetime.now().isoformat(),
        "total_properties": len(unique_properties),
        "properties": unique_properties,
        "statistics": {
            "with_price": len([p for p in unique_properties if p.get('price')]),
            "with_bedrooms": len([p for p in unique_properties if p.get('bedrooms')]),
            "with_bathrooms": len([p for p in unique_properties if p.get('bathrooms')]),
            "with_parking": len([p for p in unique_properties if p.get('parking')]),
            "with_type": len([p for p in unique_properties if p.get('property_type')])
        }
    }
    
    # Save to JSON
    print(f"\n→ Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Display summary
    print("\n" + "=" * 70)
    print("✅ PARSING COMPLETE")
    print("=" * 70)
    print(f"Total properties found: {output_data['total_properties']}")
    print(f"\nData completeness:")
    print(f"  • Addresses: {output_data['total_properties']}")
    print(f"  • Prices: {output_data['statistics']['with_price']}")
    print(f"  • Bedrooms: {output_data['statistics']['with_bedrooms']}")
    print(f"  • Bathrooms: {output_data['statistics']['with_bathrooms']}")
    print(f"  • Parking: {output_data['statistics']['with_parking']}")
    print(f"  • Property type: {output_data['statistics']['with_type']}")
    print(f"\nOutput saved to: {OUTPUT_FILE}")
    
    # Show sample properties
    if unique_properties:
        print(f"\n📋 Sample properties:")
        for i, prop in enumerate(unique_properties[:3], 1):
            print(f"\n  Property {i}:")
            print(f"    Address: {prop.get('address', 'N/A')}")
            print(f"    Price: {prop.get('price', 'N/A')}")
            print(f"    Beds: {prop.get('bedrooms', 'N/A')}")
            print(f"    Baths: {prop.get('bathrooms', 'N/A')}")
            print(f"    Parking: {prop.get('parking', 'N/A')}")
            print(f"    Type: {prop.get('property_type', 'N/A')}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
