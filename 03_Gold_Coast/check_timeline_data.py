#!/usr/bin/env python3
import json

print('='*80)
print('TIMELINE DATA ANALYSIS')
print('='*80)

files = [
    ('test_results_fresh/test_data/broadbeach/1844889.json', 'U 3018/2633 Broadbeach'),
    ('test_results_fresh/test_data/broadbeach/1844892.json', 'U 3023/2633 Broadbeach'),
    ('test_results_fresh/test_data/woongoolba/1389886.json', '1199 Stapylton Jacobs Well Rd'),
    ('test_results_fresh/test_data/woongoolba/441615.json', '41 New Norwell Rd'),
]

for filepath, short_name in files:
    try:
        with open(filepath) as f:
            data = json.load(f)
        
        timeline = data.get('property_timeline', [])
        print(f'\nProperty: {short_name}')
        print(f'Full Address: {data["address"]}')
        print(f'URL: {data["url"]}')
        print(f'Timeline Events: {len(timeline)}')
        
        if len(timeline) == 0:
            print('  ⚠ WARNING: NO TIMELINE DATA EXTRACTED')
        else:
            print(f'  ✓ Has {len(timeline)} timeline events')
            for i, event in enumerate(timeline[:3], 1):
                price = event.get('price')
                price_str = f'${price:,}' if price else 'N/A'
                print(f'    {i}. {event["date"]}: {event["category"]} - {price_str}')
    except FileNotFoundError:
        print(f'\nProperty: {short_name}')
        print('  ✗ FILE NOT FOUND')

print('\n' + '='*80)
print('SUMMARY')
print('='*80)
print('If timeline data exists on domain.com.au but not in extracted data,')
print('this indicates the retry mechanism may not be working correctly.')
