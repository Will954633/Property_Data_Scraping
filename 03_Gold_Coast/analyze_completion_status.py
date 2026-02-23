#!/usr/bin/env python3
"""
Analyze Completion Status
Identifies all completed vs not completed addresses in MongoDB
Generates report and exports list of remaining addresses
"""

import json
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from typing import Dict, List
from collections import defaultdict

class CompletionAnalyzer:
    """Analyze scraping completion status across all suburbs"""
    
    def __init__(self):
        # Configuration
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
        self.db_name = 'Gold_Coast'
        self.output_file = 'remaining_addresses.json'
        
        # Initialize MongoDB
        print(f"Connecting to MongoDB...")
        try:
            self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=10000)
            self.db = self.mongo_client[self.db_name]
            self.mongo_client.admin.command('ping')
            print(f"✓ Connected to MongoDB: {self.db_name}\n")
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            sys.exit(1)
    
    def analyze_suburb(self, suburb: str) -> Dict:
        """Analyze completion status for a single suburb"""
        collection = self.db[suburb]
        
        # Count total, completed, and incomplete
        total = collection.count_documents({})
        completed = collection.count_documents({'scraped_data': {'$exists': True}})
        incomplete = total - completed
        
        completion_pct = (completed / total * 100) if total > 0 else 0
        
        return {
            'suburb': suburb,
            'total': total,
            'completed': completed,
            'incomplete': incomplete,
            'completion_pct': completion_pct
        }
    
    def get_incomplete_addresses(self, suburb: str, limit: int = None) -> List[Dict]:
        """Get list of incomplete addresses from a suburb"""
        collection = self.db[suburb]
        
        query = {'scraped_data': {'$exists': False}}
        projection = {
            'ADDRESS_PID': 1,
            'UNIT_TYPE': 1,
            'UNIT_NUMBER': 1,
            'STREET_NO_1': 1,
            'STREET_NAME': 1,
            'STREET_TYPE': 1,
            'LOCALITY': 1,
            'POSTCODE': 1,
            '_id': 1
        }
        
        cursor = collection.find(query, projection)
        
        if limit:
            cursor = cursor.limit(limit)
        
        addresses = []
        for doc in cursor:
            addresses.append({
                'suburb': suburb,
                'address_pid': doc.get('ADDRESS_PID'),
                'unit_type': doc.get('UNIT_TYPE'),
                'unit_number': doc.get('UNIT_NUMBER'),
                'street_no': doc.get('STREET_NO_1'),
                'street_name': doc.get('STREET_NAME'),
                'street_type': doc.get('STREET_TYPE'),
                'locality': doc.get('LOCALITY'),
                'postcode': doc.get('POSTCODE'),
                'mongo_id': str(doc.get('_id'))
            })
        
        return addresses
    
    def run(self):
        """Main analysis process"""
        print(f"{'='*70}")
        print(f"COMPLETION STATUS ANALYSIS")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # Get all collections
        collections = [c for c in self.db.list_collection_names() if c != 'system.indexes']
        print(f"Found {len(collections)} suburb collections\n")
        
        # Analyze each suburb
        stats = []
        total_addresses = 0
        total_completed = 0
        total_incomplete = 0
        
        print(f"{'Suburb':<30} {'Total':>8} {'Complete':>8} {'Remain':>8} {'%':>6}")
        print(f"{'-'*70}")
        
        for suburb in sorted(collections):
            result = self.analyze_suburb(suburb)
            stats.append(result)
            
            total_addresses += result['total']
            total_completed += result['completed']
            total_incomplete += result['incomplete']
            
            print(f"{suburb:<30} {result['total']:>8,} {result['completed']:>8,} "
                  f"{result['incomplete']:>8,} {result['completion_pct']:>5.1f}%")
        
        print(f"{'-'*70}")
        print(f"{'TOTAL':<30} {total_addresses:>8,} {total_completed:>8,} "
              f"{total_incomplete:>8,} {total_completed/total_addresses*100:>5.1f}%")
        print()
        
        # Sort by incomplete count
        stats_by_incomplete = sorted(stats, key=lambda x: x['incomplete'], reverse=True)
        
        print(f"\nTop 20 suburbs by remaining addresses:")
        print(f"{'Suburb':<30} {'Remaining':>10} {'% Incomplete':>12}")
        print(f"{'-'*55}")
        for stat in stats_by_incomplete[:20]:
            incomplete_pct = 100 - stat['completion_pct']
            print(f"{stat['suburb']:<30} {stat['incomplete']:>10,} {incomplete_pct:>11.1f}%")
        
        # Export remaining addresses
        print(f"\n\nExporting remaining addresses...")
        all_remaining = []
        
        for suburb in collections:
            suburb_remaining = self.get_incomplete_addresses(suburb)
            all_remaining.extend(suburb_remaining)
        
        # Save to JSON
        with open(self.output_file, 'w') as f:
            json.dump(all_remaining, f, indent=2)
        
        print(f"✓ Exported {len(all_remaining):,} remaining addresses to: {self.output_file}")
        
        # Summary statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        print(f"Total addresses:        {total_addresses:,}")
        print(f"Completed:              {total_completed:,} ({total_completed/total_addresses*100:.1f}%)")
        print(f"Remaining:              {total_incomplete:,} ({total_incomplete/total_addresses*100:.1f}%)")
        print(f"Suburbs analyzed:       {len(collections)}")
        print(f"Analysis duration:      {duration}")
        print(f"\nOutput file:            {self.output_file}")
        print(f"{'='*70}\n")
        
        # Calculate work distribution for 50 workers
        addresses_per_worker = total_incomplete // 50
        print(f"Work distribution for 50 workers:")
        print(f"  Addresses per worker:  ~{addresses_per_worker:,}")
        print(f"  At 120 addr/hr:        ~{addresses_per_worker/120:.1f} hours per worker")
        print(f"  Total processing time: ~{addresses_per_worker/120:.1f} hours (with 50 parallel)")
        print()
        
        print(f"Next steps:")
        print(f"  1. Start 50 local workers:  ./start_50_local_workers.sh")
        print(f"  2. Monitor progress:         ./monitor_local_workers.sh")
        print(f"  3. Schedule nightly runs:    ./setup_nightly_scheduler.sh")
        print()


if __name__ == "__main__":
    try:
        analyzer = CompletionAnalyzer()
        analyzer.run()
    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
