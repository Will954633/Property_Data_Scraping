#!/usr/bin/env python3
"""
Multi-Session Property Data Parser
Handles OCR quirks and extracts ALL property data accurately
Supports command-line arguments for input/output files
"""

import re
import json
from datetime import datetime
import os
import argparse

def extract_bed_bath_car(text):
    """
    Extract bed/bath/car from domain.com.au OCR format
    Handles patterns like: "=\4 472 G4", "#3 672 G1", "14 472 G2"
    Format: [symbol][beds] [bath]72 G[parking]
    """
    # Domain.com.au pattern: symbol + bed + space + bath + "72" or "7" + space + G + parking
    # Examples: "=\4 472 G4", "#3 672 G1", "14 73 G2", "=\3 72 G2"
    match = re.search(r'[=#\\@]*(\d)\s*[467]?7?2\s*G(\d)', text)
    if match:
        bed = int(match.group(1))
        car = int(match.group(2))
        # Bath is usually in the middle - try to extract
        bath_match = re.search(r'[=#\\@]*\d\s*(\d)7?2\s*G\d', text)
        bath = int(bath_match.group(1)) if bath_match else 2
        return bed, bath, car
    
    # Fallback patterns
    bed_match = re.search(r'(\d+)\s*(?:bed|bd)', text, re.I)
    bath_match = re.search(r'(\d+)\s*(?:bath|ba)', text, re.I)  
    car_match = re.search(r'(\d+)\s*(?:car|parking|garage)', text, re.I)
    
    bed = int(bed_match.group(1)) if bed_match else None
    bath = int(bath_match.group(1)) if bath_match else None
    car = int(car_match.group(1)) if car_match else None
    
    return bed, bath, car

def extract_land_size(text):
    """Extract land size in sqm from domain.com.au format (e.g., 'S 441m?', 'Sf 845m2')"""
    # Pattern: S or Sf followed by number and m (with optional 2 or ?)
    match = re.search(r'S[f]?\s*(\d+,?\d*)m[2?«]?', text, re.I)
    if match:
        size_str = match.group(1).replace(',', '')
        try:
            return int(size_str)
        except:
            pass
    return None

def extract_property_type(text):
    """Extract property type from domain.com.au format (e.g., '« House')"""
    match = re.search(r'[«~-]\s*(House|Townhouse|Villa|Unit|Apartment|Duplex/semi-detached|Land)', text, re.I)
    if match:
        return match.group(1).strip()
    return None

def parse_properties_best(text):
    """
    Best parser for domain.com.au format
    """
    properties = []
    lines = text.split('\n')
    
    # Address pattern for domain.com.au format
    # Matches: "4 Sawgrass Place," or "2/128 Cottesloe Drive,"
    address_pattern = r'(\d+[-/]?\d*\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Court|Ct|Place|Pl|Circuit|Cct|Way|Lane|Ln|Terrace|Tce|Crescent|Cres|Close|Boulevard|Blvd|Parade|Pde)),'
    
    # Price patterns
    price_patterns = [
        (r'\$[\d,]+,\d{3,6}(?:\+)?', 'exact'),
        (r'\$[\d,]+-\s*\$[\d,]+', 'range'),
        (r'Offers?\s+[Oo]ver\s+\$[\d,.]+[kKmM]?', 'offers_over'),
        (r'\$[\d.]+[mM]', 'millions'),
        (r'UNDER\s+OFFER|Under\s+offer', 'under_offer'),
        (r'MUST\s+BE\s+SOLD', 'must_sell'),
        (r'Auction\s+Coming\s+Soon', 'auction_coming'),
        (r'Auction', 'auction'),
        (r'Contact\s+(?:Agent|Crasto\s+Collective)|CONTACT\s+AGENT', 'contact_agent'),
        (r'Expressions?\s+[Oo]f\s+[Ii]nterest', 'eoi'),
        (r'Just\s+Listed', 'just_listed'),
    ]
    
    # Agency/Agent patterns - domain.com.au agencies
    agency_pattern = r'(Professionals|RayWhite|Ray\s*White|McGrath|Harcourts|REMAX|RE/?MAX|COASTAL|Astras?\.?\s*S\.?|MARSH|crasto|Crasto\s+Collective|COMPANY\s*RE|WELCOME\s*CHANGE)'
    
    # Other patterns - domain.com.au uses uppercase
    url_pattern = r'https://www\.domain\.com\.au/[\w\-]+-qld-\d+'
    inspection_pattern = r'INSPECTION:\s+(?:SAT|SUN|MON|TUE|WED|THU|FRI)\s+\d+\s+[A-Z]+,?\s+\d+:\d+[AP]M'
    auction_pattern = r'Auction\s+(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri|tomorrow)\s+\d+\s+\w+(?:\s+\d+:\d+\s+[ap]m)?'
    added_pattern = r'Added\s+(?:\d+\s+(?:hours?|days?)\s+ago|yesterday|today)'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip sold properties
        if re.search(r'®?\s*Sold\s+\d+\s+\w+\s+\d{4}', line):
            i += 1
            continue
        
        # Look for address
        addr_match = re.search(address_pattern, line, re.IGNORECASE)
        
        if addr_match:
            property_data = {
                'address': addr_match.group(1).strip()
            }
            
            # Get extended context
            context_start = max(0, i - 15)
            context_end = min(len(lines), i + 20)
            context = '\n'.join(lines[context_start:context_end])
            
            # Extract bed/bath/car
            bed, bath, car = extract_bed_bath_car(context)
            if bed: property_data['bedrooms'] = bed
            if bath: property_data['bathrooms'] = bath
            if car: property_data['parking'] = car
            
            # Extract land size
            land = extract_land_size(context)
            if land: property_data['land_size_sqm'] = land
            
            # Extract property type
            prop_type = extract_property_type(context)
            if prop_type: property_data['property_type'] = prop_type
            
            # Extract price
            for pattern, price_type in price_patterns:
                price_match = re.search(pattern, context, re.IGNORECASE)
                if price_match:
                    property_data['price'] = price_match.group(0).strip()
                    property_data['price_type'] = price_type
                    break
            
            # Extract agency
            agency_match = re.search(agency_pattern, context, re.IGNORECASE)
            if agency_match:
                property_data['agency'] = agency_match.group(1).strip().replace(' ', '').replace('/', '')
            
            # Extract agent name
            agent_names = []
            name_matches = re.findall(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,2})\b', context)
            excluded = {'Agent', 'Contact', 'McGrath', 'Harcourts', 'RayWhite', 'REMAX', 'COASTAL',
                       'Featured', 'Inspection', 'Auction', 'House', 'Property', 'Listed', 'Under',
                       'Offer', 'Coming', 'Soon', 'Must', 'Sell', 'Sold', 'Robina', 'Added',
                       'Present', 'Expressions', 'Interest', 'Owner', 'Bought', 'Drive', 'Court',
                       'Place', 'Street', 'Avenue', 'Close', 'Terrace', 'Crescent', 'Boulevard',
                       'Research', 'Guide', 'Market', 'View', 'Price', 'Showing'}
            
            for name in name_matches:
                if name not in excluded and len(name) > 3:
                    parts = name.split()
                    if len(parts) >= 2 or (len(parts) == 1 and len(name) > 5):
                        if name not in agent_names:
                            agent_names.append(name)
                            if len(agent_names) >= 2:
                                break
            
            if agent_names:
                property_data['agent'] = ' & '.join(agent_names[:2])
            
            # Extract URL
            url_match = re.search(url_pattern, context)
            if url_match:
                property_data['listing_url'] = url_match.group(0).strip()
            
            # Extract inspection
            insp_match = re.search(inspection_pattern, context, re.IGNORECASE)
            if insp_match:
                property_data['inspection'] = insp_match.group(0).strip()
            
            # Extract auction date
            auction_match = re.search(auction_pattern, context, re.IGNORECASE)
            if auction_match:
                property_data['auction_date'] = auction_match.group(0).strip()
            
            # Extract added date
            added_match = re.search(added_pattern, context, re.IGNORECASE)
            if added_match:
                property_data['added'] = added_match.group(0).strip()
            
            # Determine selling method and under offer status
            price_type = property_data.get('price_type', 'unknown')
            under_offer = bool(re.search(r'[Uu]nder\s+[Oo]ffer|UNDER\s+OFFER', context))
            property_data['under_offer'] = under_offer
            
            if 'auction' in price_type or re.search(r'Auction', context, re.IGNORECASE):
                property_data['selling_method'] = 'Auction'
            elif price_type == 'exact' or price_type == 'offers_over' or price_type == 'range':
                property_data['selling_method'] = 'Private Treaty'
            else:
                property_data['selling_method'] = 'Unknown'
            
            # Extract selling description
            selling_desc_patterns = [
                r'((?:Submit|Present)\s+[Aa]ll?\s+[Oo]ffers?)',
                r'(MUST\s+BE\s+SOLD(?:\s+[-–]\s*)?(?:PRESENT\s+OFFERS)?)',
                r'([Oo]wner\s+[Hh]as\s+[Bb]ought\s+[-–]?\s*[Mm]ust\s+[Ss]ell)',
                r'(Contact\s+(?:Agent|Crasto\s+Collective)\s+[Ff]or\s+[Pp]rice\s+[Gg]uide)',
                r'(Contact\s+Agent)',
                r'(Expressions?\s+[Oo]f\s+[Ii]nterest)',
                r'(Offers?\s+[Oo]ver\s+\$[\d,.]+[kKmM]?)',
                r'(Just\s+Listed)',
                r'(Auction\s+Coming\s+Soon)',
            ]
            
            selling_desc = []
            for pattern in selling_desc_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match and match.group(1) not in selling_desc:
                    selling_desc.append(match.group(1).strip())
            
            if selling_desc:
                property_data['selling_description'] = ', '.join(selling_desc)
            else:
                property_data['selling_description'] = property_data.get('price', 'Unknown')
            
            properties.append(property_data)
        
        i += 1
    
    return properties

def deduplicate(properties):
    """Remove duplicates"""
    seen = {}
    unique = []
    
    for prop in properties:
        addr = prop.get('address', '').lower().strip()
        if addr and addr not in seen:
            seen[addr] = True
            unique.append(prop)
    
    return unique

def calculate_stats(properties):
    """Calculate statistics"""
    total = len(properties)
    stats = {
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
        'with_auction_date': len([p for p in properties if p.get('auction_date')]),
        'with_added': len([p for p in properties if p.get('added')]),
        'price_types': {}
    }
    
    for prop in properties:
        pt = prop.get('price_type', 'none')
        stats['price_types'][pt] = stats['price_types'].get(pt, 0) + 1
    
    return stats

def main():
    """Main"""
    parser = argparse.ArgumentParser(description='Parse property data from OCR text')
    parser.add_argument('--input', required=True, help='Input OCR text file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--url', default='', help='Source URL (optional)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("MULTI-SESSION PROPERTY DATA PARSER")
    print("=" * 70)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    
    if not os.path.exists(args.input):
        print(f"\n✗ File not found: {args.input}")
        return
    
    print(f"\n→ Reading OCR text...")
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f"  ✓ {len(text):,} characters")
    
    print("\n→ Parsing properties...")
    props = parse_properties_best(text)
    print(f"  ✓ Found {len(props)} properties")
    
    print("\n→ Deduplicating...")
    unique = deduplicate(props)
    print(f"  ✓ {len(unique)} unique")
    
    stats = calculate_stats(unique)
    
    output = {
        "extraction_date": datetime.now().isoformat(),
        "source": "domain.com.au - Robina QLD 4226 houses",
        "search_url": args.url if args.url else "Multiple sessions",
        "total_properties": len(unique),
        "properties": unique,
        "statistics": stats
    }
    
    print(f"\n→ Saving to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ PARSING COMPLETE")
    print("=" * 70)
    print(f"Total: {stats['total']} properties\n")
    print("Data Completeness:")
    for field in ['price', 'bedrooms', 'bathrooms', 'parking', 'land_size', 
                  'property_type', 'agency', 'agent', 'url', 'inspection']:
        count = stats.get(f'with_{field}', 0)
        pct = (count / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {field:15s}: {count:2d}/{stats['total']:2d} ({pct:3.0f}%)")
    
    print(f"\nPrice types: {stats['price_types']}")
    print(f"\nSaved to: {args.output}")
    print("=" * 70)

if __name__ == "__main__":
    main()
