#!/usr/bin/env python3
"""
Analyze Gold Coast suburbs in MongoDB to determine processing status
"""

from pymongo import MongoClient
import json

# Connect to MongoDB
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['Gold_Coast']

# Get all collection names (each collection is a suburb)
collections = db.list_collection_names()
print(f'Found {len(collections)} collections (suburbs)\n')

# Analyze each suburb
suburb_stats = []
total_addresses = 0
total_scraped = 0
total_unscraped = 0

print('Collection Statistics:')
print('='*90)
print(f'{"Suburb":30s} | {"Total":>8s} | {"Scraped":>8s} | {"Unscraped":>8s} | {"Progress":>8s}')
print('='*90)

for coll_name in sorted(collections):
    coll = db[coll_name]
    total = coll.count_documents({})
    scraped = coll.count_documents({'scraped_data': {'$exists': True}})
    unscraped = total - scraped
    progress = (scraped/total*100) if total > 0 else 0
    
    suburb_stats.append({
        'suburb': coll_name,
        'total': total,
        'scraped': scraped,
        'unscraped': unscraped,
        'progress': progress
    })
    
    total_addresses += total
    total_scraped += scraped
    total_unscraped += unscraped
    
    print(f'{coll_name:30s} | {total:8,d} | {scraped:8,d} | {unscraped:8,d} | {progress:7.1f}%')

print('='*90)
print(f'{"TOTAL":30s} | {total_addresses:8,d} | {total_scraped:8,d} | {total_unscraped:8,d} | {(total_scraped/total_addresses*100) if total_addresses > 0 else 0:7.1f}%')
print('='*90)
print()

# Sort by unscraped count (largest first) to prioritize
suburb_stats_sorted = sorted(suburb_stats, key=lambda x: x['unscraped'], reverse=True)

print('\nTop 20 Suburbs by Unscraped Count:')
print('='*90)
print(f'{"Rank":>4s} | {"Suburb":30s} | {"Unscraped":>10s} | {"Total":>8s} | {"Progress":>8s}')
print('='*90)

for i, stat in enumerate(suburb_stats_sorted[:20], 1):
    print(f'{i:4d} | {stat["suburb"]:30s} | {stat["unscraped"]:10,d} | {stat["total"]:8,d} | {stat["progress"]:7.1f}%')

print('='*90)
print()

# Calculate 30% target
target_percentage = 30
target_addresses = int(total_unscraped * target_percentage / 100)

print(f'\n30% TARGET CALCULATION:')
print('='*90)
print(f'Total unscraped addresses:     {total_unscraped:,}')
print(f'30% target:                    {target_addresses:,} addresses')
print(f'With 50 workers @ 120/hr:      {target_addresses / (50 * 120):.1f} hours ({target_addresses / (50 * 120 * 24):.1f} days)')
print('='*90)
print()

# Calculate which suburbs to include to reach 30%
selected_suburbs = []
cumulative_count = 0

for stat in suburb_stats_sorted:
    if cumulative_count < target_addresses:
        selected_suburbs.append(stat)
        cumulative_count += stat['unscraped']

print(f'\nSUBURBS TO PROCESS (to reach ~30% target):')
print('='*90)
print(f'{"Suburb":30s} | {"Unscraped":>10s} | {"Cumulative":>12s} | {"% of Total":>10s}')
print('='*90)

for stat in selected_suburbs:
    cumulative_for_this = sum(s['unscraped'] for s in selected_suburbs[:selected_suburbs.index(stat)+1])
    pct_of_total = (cumulative_for_this / total_unscraped * 100) if total_unscraped > 0 else 0
    print(f'{stat["suburb"]:30s} | {stat["unscraped"]:10,d} | {cumulative_for_this:12,d} | {pct_of_total:9.1f}%')

print('='*90)
print(f'Total suburbs selected:        {len(selected_suburbs)}')
print(f'Total addresses to scrape:     {cumulative_count:,}')
print(f'Percentage of unscraped:       {(cumulative_count/total_unscraped*100) if total_unscraped > 0 else 0:.1f}%')
print('='*90)
print()

# Save results to JSON for use by the scraper
results = {
    'total_suburbs': len(collections),
    'total_addresses': total_addresses,
    'total_scraped': total_scraped,
    'total_unscraped': total_unscraped,
    'target_percentage': target_percentage,
    'target_addresses': target_addresses,
    'selected_suburbs': [s['suburb'] for s in selected_suburbs],
    'selected_suburbs_count': len(selected_suburbs),
    'selected_addresses_count': cumulative_count,
    'all_suburbs': suburb_stats_sorted
}

with open('suburb_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print('✓ Analysis saved to suburb_analysis.json\n')
