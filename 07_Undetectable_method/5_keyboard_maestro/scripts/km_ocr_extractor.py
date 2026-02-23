#!/usr/bin/env python3
"""
Property Data Extractor from OCR Text
Extracts structured property data from OCR text
"""

import re
from datetime import datetime

class PropertyExtractor:
    def __init__(self):
        self.patterns = {
            'address': [
                r'(\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Court|Ct|Place|Pl|Terrace|Tce|Boulevard|Blvd|Lane|Ln|Way|Close|Cl|Circuit|Cct|Parade|Pde|Crescent|Cres|Highway|Hwy)[,\s]+[A-Za-z\s]+QLD\s+\d{4})',
                r'(\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Court|Ct)[,\s]+[A-Za-z\s]+)',
                r'(\d+[A-Za-z]?\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave))'
            ],
            'price': [
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'Price:\s*\$(\d{1,3}(?:,\d{3})*)',
                r'Offers over \$(\d{1,3}(?:,\d{3})*)'
            ],
            'bedrooms': [
                r'(\d+)\s*(?:bed(?:room)?s?)',
                r'(?:bed(?:room)?s?:?\s*)(\d+)',
                r'🛏\s*(\d+)'
            ],
            'bathrooms': [
                r'(\d+)\s*(?:bath(?:room)?s?)',
                r'(?:bath(?:room)?s?:?\s*)(\d+)',
                r'🚿\s*(\d+)'
            ],
            'parking': [
                r'(\d+)\s*(?:car|parking|garage)',
                r'(?:car|parking|garage):?\s*(\d+)',
                r'🚗\s*(\d+)'
            ],
            'land_size': [
                r'(\d+(?:,\d+)?)\s*(?:m²|sqm|square metres)',
                r'Land:\s*(\d+(?:,\d+)?)\s*m²'
            ],
            'property_type': [
                r'\b(House|Townhouse|Apartment|Unit|Villa|Duplex)\b'
            ]
        }
    
    def extract_property_info(self, ocr_text):
        """Extract all property information from OCR text"""
        data = {
            'raw_ocr_text': ocr_text[:500],  # Store first 500 chars for debugging
            'extraction_confidence': 'low'
        }
        
        # Extract each field
        data['address'] = self._extract_field(ocr_text, 'address')
        data['price'] = self._extract_price(ocr_text)
        data['bedrooms'] = self._extract_number(ocr_text, 'bedrooms')
        data['bathrooms'] = self._extract_number(ocr_text, 'bathrooms')
        data['parking'] = self._extract_number(ocr_text, 'parking')
        data['land_size'] = self._extract_field(ocr_text, 'land_size')
        data['property_type'] = self._extract_field(ocr_text, 'property_type')
        
        # Parse address components if address found
        if data['address']:
            address_parts = self._parse_address(data['address'])
            data['address_components'] = address_parts
        
        # Calculate confidence score
        data['extraction_confidence'] = self._calculate_confidence(data)
        
        return data
    
    def _extract_field(self, text, field_name):
        """Extract a field using multiple patterns"""
        patterns = self.patterns.get(field_name, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        
        return None
    
    def _extract_number(self, text, field_name):
        """Extract numeric field and convert to integer"""
        value = self._extract_field(text, field_name)
        if value:
            try:
                return int(value)
            except ValueError:
                return None
        return None
    
    def _extract_price(self, text):
        """Extract and parse price"""
        patterns = self.patterns['price']
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1) if match.groups() else match.group(0)
                # Remove commas and convert to integer
                try:
                    price_value = int(price_str.replace(',', ''))
                    return {
                        'display': f"${price_str}",
                        'value': price_value
                    }
                except ValueError:
                    return {'display': f"${price_str}", 'value': None}
        
        return None
    
    def _parse_address(self, full_address):
        """Parse address into components"""
        components = {
            'full': full_address,
            'street': None,
            'suburb': None,
            'state': None,
            'postcode': None
        }
        
        # Extract postcode (4 digits)
        postcode_match = re.search(r'\b(\d{4})\b', full_address)
        if postcode_match:
            components['postcode'] = postcode_match.group(1)
        
        # Extract state (QLD)
        state_match = re.search(r'\b(QLD|NSW|VIC|SA|WA|TAS|NT|ACT)\b', full_address)
        if state_match:
            components['state'] = state_match.group(1)
        
        # Try to extract suburb (word before state)
        if components['state']:
            suburb_match = re.search(r'([A-Za-z\s]+)\s+' + components['state'], full_address)
            if suburb_match:
                components['suburb'] = suburb_match.group(1).strip()
        
        # Extract street (everything before suburb)
        if components['suburb']:
            parts = full_address.split(components['suburb'])
            if parts:
                components['street'] = parts[0].strip().rstrip(',')
        
        return components
    
    def _calculate_confidence(self, data):
        """Calculate extraction confidence based on number of fields extracted"""
        fields_extracted = 0
        total_fields = 7  # address, price, bed, bath, parking, land, type
        
        if data.get('address'):
            fields_extracted += 1
        if data.get('price'):
            fields_extracted += 1
        if data.get('bedrooms'):
            fields_extracted += 1
        if data.get('bathrooms'):
            fields_extracted += 1
        if data.get('parking') is not None:  # Allow 0
            fields_extracted += 1
        if data.get('land_size'):
            fields_extracted += 1
        if data.get('property_type'):
            fields_extracted += 1
        
        confidence_score = fields_extracted / total_fields
        
        if confidence_score >= 0.7:
            return 'high'
        elif confidence_score >= 0.5:
            return 'medium'
        else:
            return 'low'

# Example usage and testing
if __name__ == "__main__":
    extractor = PropertyExtractor()
    
    # Test with sample OCR text
    sample_text = """
    123 Main Street, Robina QLD 4226
    
    $750,000
    
    4 bedrooms
    2 bathrooms
    2 car spaces
    
    House
    600 m² land
    
    Beautiful family home in prime location
    """
    
    result = extractor.extract_property_info(sample_text)
    
    print("Extracted Property Data:")
    print(f"Address: {result.get('address')}")
    print(f"Price: {result.get('price')}")
    print(f"Bedrooms: {result.get('bedrooms')}")
    print(f"Bathrooms: {result.get('bathrooms')}")
    print(f"Parking: {result.get('parking')}")
    print(f"Land Size: {result.get('land_size')}")
    print(f"Property Type: {result.get('property_type')}")
    print(f"Confidence: {result.get('extraction_confidence')}")
