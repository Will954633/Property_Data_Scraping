#!/usr/bin/env python3
"""
Verify dateListed Extraction
Last Updated: 31/01/2026, 10:51 am (Brisbane Time)

PURPOSE:
Quick test to verify the dateListed field extraction works correctly
"""

import re
from datetime import datetime

# Sample HTML snippet with dateListed field (from our analysis)
sample_html = '''
<script>
{
  "dateListed": "2025-08-11T15:31:46.000",
  "property": "test"
}
</script>
'''

def extract_first_listed_date(html: str) -> dict:
    """Extract dateListed from HTML"""
    result = {
        'first_listed_date': None,
        'first_listed_year': None,
        'first_listed_full': None,
        'first_listed_timestamp': None,
        'days_on_domain': None,
    }
    
    # Extract from "dateListed" JSON field
    date_listed_pattern = r'"dateListed"\s*:\s*"([^"]+)"'
    date_match = re.search(date_listed_pattern, html)
    
    if date_match:
        timestamp_str = date_match.group(1)
        result['first_listed_timestamp'] = timestamp_str
        
        try:
            # Parse the ISO timestamp
            listed_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').split('.')[0])
            
            # Format for display
            result['first_listed_date'] = listed_date.strftime('%d %B')
            result['first_listed_year'] = listed_date.year
            result['first_listed_full'] = listed_date.strftime('%d %B %Y')
            
            # Calculate days on domain
            current_date = datetime.now()
            days_diff = (current_date - listed_date).days
            result['days_on_domain'] = days_diff
            
        except Exception as e:
            print(f"Error: {e}")
    
    return result

print("="*80)
print("VERIFICATION TEST: dateListed Extraction")
print("="*80)

result = extract_first_listed_date(sample_html)

print("\n✅ EXTRACTION RESULTS:")
print(f"  Timestamp: {result['first_listed_timestamp']}")
print(f"  Date: {result['first_listed_date']}")
print(f"  Year: {result['first_listed_year']}")
print(f"  Full: {result['first_listed_full']}")
print(f"  Days on Domain: {result['days_on_domain']}")

print("\n" + "="*80)
if result['first_listed_timestamp']:
    print("✅ SUCCESS - Extraction working correctly!")
    print("\nThe script will now:")
    print("  1. Extract dateListed timestamp from property HTML")
    print("  2. Parse it into readable date format")
    print("  3. Calculate days on market automatically")
    print("  4. Store all data in MongoDB")
else:
    print("❌ FAILED - Could not extract dateListed")

print("="*80)
