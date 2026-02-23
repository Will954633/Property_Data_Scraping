#!/usr/bin/env python3
"""
Test GCS to MongoDB Import Matching Logic
Tests with 5 sample addresses from Robina to verify correct matching
"""

import json
import os
import sys
from pymongo import MongoClient
from google.cloud import storage

class ImportMatchingTester:
    """Test the import matching logic with sample data"""
    
    def __init__(self):
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
        self.bucket_name = 'property-scraper-production-data-477306'
        self.db_name = 'Gold_Coast'
        
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=10000)
        self.db = self.mongo_client[self.db_name]
        self.mongo_client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {self.db_name}\n")
        
        # Connect to GCS
        print("Connecting to Google Cloud Storage...")
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)
        print(f"✓ Connected to GCS: {self.bucket_name}\n")
    
    def build_address_from_doc(self, doc) -> str:
        """Build full address string from MongoDB document"""
        parts = []
        
        # Unit prefix
        if doc.get('UNIT_TYPE') and doc.get('UNIT_NUMBER'):
            parts.append(f"{doc['UNIT_TYPE']} {doc['UNIT_NUMBER']}/")
        
        # Street number
        if doc.get('STREET_NO_1'):
            parts.append(str(doc['STREET_NO_1']))
        
        # Street name and type
        if doc.get('STREET_NAME'):
            street = str(doc['STREET_NAME'])
            if doc.get('STREET_TYPE'):
                street += f" {doc['STREET_TYPE']}"
            parts.append(street)
        
        # Locality, state, postcode
        if doc.get('LOCALITY'):
            locality = f"{doc['LOCALITY']} QLD"
            if doc.get('POSTCODE'):
                locality += f" {doc['POSTCODE']}"
            parts.append(locality)
        
        address = ' '.join(parts)
        address = address.replace(' /', '/').replace('/ ', '/')
        return address.upper()
    
    def normalize_address(self, address: str) -> str:
        """Normalize address for comparison"""
        # Convert to uppercase
        addr = address.upper().strip()
        # Remove extra spaces
        addr = ' '.join(addr.split())
        # Remove commas
        addr = addr.replace(',', '')
        return addr
    
    def sample_robina_addresses(self, count=5):
        """Get sample addresses from Robina collection"""
        print(f"Sampling {count} addresses from 'robina' collection...")
        
        collection = self.db['robina']
        
        # Get some addresses (mix of scraped and unscraped)
        unscraped = list(collection.find({'scraped_data': {'$exists': False}}).limit(3))
        scraped = list(collection.find({'scraped_data': {'$exists': True}}).limit(2))
        
        samples = unscraped + scraped
        
        print(f"✓ Found {len(samples)} sample documents:")
        print(f"  - {len(unscraped)} unscraped")
        print(f"  - {len(scraped)} already scraped\n")
        
        return samples
    
    def search_gcs_for_address(self, address: str):
        """Search GCS for JSON file matching this address"""
        print(f"  Searching GCS for: {address}")
        
        # Normalize address for filename matching
        normalized = self.normalize_address(address)
        
        # Try to find matching JSON file
        # GCS files are named like: "1-2-3-street-name-suburb-qld-postcode.json"
        search_slug = normalized.lower().replace(' ', '-').replace('/', '-')
        
        # List files that might match
        blobs = self.bucket.list_blobs(prefix='scraped_data/')
        
        for blob in blobs:
            if blob.name.endswith('.json'):
                # Download and check if address matches
                try:
                    json_content = blob.download_as_text()
                    data = json.loads(json_content)
                    json_address = self.normalize_address(data.get('address', ''))
                    
                    if json_address == normalized:
                        return blob.name, data
                except:
                    continue
        
        return None, None
    
    def test_matching(self):
        """Main test process"""
        print("="*70)
        print("TESTING IMPORT MATCHING LOGIC")
        print("="*70)
        print()
        
        # Sample addresses
        samples = self.sample_robina_addresses(5)
        
        if not samples:
            print("No sample addresses found in robina collection")
            return
        
        # Test each address
        matches = []
        no_matches = []
        
        for i, doc in enumerate(samples, 1):
            print(f"\n{'─'*70}")
            print(f"Test {i}/{len(samples)}")
            print(f"{'─'*70}")
            
            # Build address from MongoDB document
            db_address = self.build_address_from_doc(doc)
            print(f"MongoDB Address: {db_address}")
            print(f"ADDRESS_PID: {doc.get('ADDRESS_PID', 'N/A')}")
            print(f"Has scraped_data: {doc.get('scraped_data') is not None}")
            
            # Search GCS
            blob_name, json_data = self.search_gcs_for_address(db_address)
            
            if blob_name:
                print(f"✓ MATCH FOUND in GCS!")
                print(f"  GCS File: {blob_name}")
                print(f"  GCS Address: {json_data.get('address')}")
                print(f"  Property Type: {json_data.get('features', {}).get('property_type')}")
                print(f"  Bedrooms: {json_data.get('features', {}).get('bedrooms')}")
                print(f"  Timeline Events: {len(json_data.get('property_timeline', []))}")
                matches.append((doc, blob_name, json_data))
            else:
                print(f"✗ NO MATCH found in GCS")
                no_matches.append(doc)
        
        # Summary
        print(f"\n{'='*70}")
        print(f"MATCHING TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total tested:     {len(samples)}")
        print(f"Matches found:    {len(matches)}")
        print(f"No matches:       {len(no_matches)}")
        print(f"Success rate:     {len(matches)/len(samples)*100:.1f}%")
        print()
        
        if len(matches) > 0:
            print(f"✓ Matching logic appears to work!")
            print(f"  The script can find GCS files that correspond to MongoDB addresses")
            print()
            print(f"Next step: Review the matching strategy and run full import")
        else:
            print(f"✗ Warning: No matches found!")
            print(f"  This suggests either:")
            print(f"  1. The GCS files don't exist for these addresses")
            print(f"  2. The address format doesn't match")
            print(f"  3. The matching logic needs adjustment")
        
        return matches, no_matches


if __name__ == "__main__":
    try:
        tester = ImportMatchingTester()
        matches, no_matches = tester.test_matching()
        
        print(f"\nDone! Found {len(matches)} matches out of 5 test addresses.")
        
    except KeyboardInterrupt:
        print("\n\nTest cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
