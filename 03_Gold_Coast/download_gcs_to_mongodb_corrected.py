#!/usr/bin/env python3
"""
CORRECTED: Download JSON files from Google Cloud Storage to local MongoDB
Properly matches GCS JSON data to existing MongoDB cadastral records
"""

import json
import os
import sys
import re
from datetime import datetime
from google.cloud import storage
from pymongo import MongoClient
from typing import Dict, List, Optional

class GCSToMongoDBImporterCorrected:
    """Import GCS JSON data into MongoDB with CORRECT address matching"""
    
    def __init__(self, test_mode=False, test_limit=5):
        # Configuration
        self.project_id = os.getenv('GCP_PROJECT_ID', 'property-data-scraping-477306')
        self.bucket_name = os.getenv('GCS_BUCKET', 'property-scraper-production-data-477306')
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
        self.db_name = 'Gold_Coast'
        self.test_mode = test_mode
        self.test_limit = test_limit
        
        # Initialize GCS client
        print(f"Connecting to Google Cloud Storage...")
        try:
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            print(f"✓ Connected to gs://{self.bucket_name}")
        except Exception as e:
            print(f"✗ GCS connection failed: {e}")
            sys.exit(1)
        
        # Initialize MongoDB client
        print(f"\nConnecting to MongoDB...")
        try:
            self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=10000)
            self.db = self.mongo_client[self.db_name]
            self.mongo_client.admin.command('ping')
            print(f"✓ Connected to MongoDB: {self.db_name}")
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            sys.exit(1)
    
    def normalize_address(self, address: str) -> str:
        """Normalize address for comparison"""
        addr = address.upper().strip()
        addr = ' '.join(addr.split())  # Remove extra spaces
        addr = addr.replace(',', '')  # Remove commas
        addr = re.sub(r'\s+', ' ', addr)  # Single spaces
        return addr
    
    def build_address_from_doc(self, doc: Dict) -> str:
        """Build full address string from MongoDB cadastral document"""
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
        return self.normalize_address(address)
    
    def extract_suburb_from_address(self, address: str) -> str:
        """Extract suburb from address string and convert to collection name format"""
        parts = address.upper().split()
        
        try:
            qld_idx = parts.index('QLD')
            if qld_idx > 0:
                # Check for multi-word suburbs (e.g., "PALM BEACH", "BIGGERA WATERS")
                # Try 2 words first, then 1 word
                if qld_idx >= 2:
                    # Try two words before QLD
                    two_word = f"{parts[qld_idx - 2]}_{parts[qld_idx - 1]}".lower()
                    # Check if this collection exists
                    if two_word in self.db.list_collection_names():
                        return two_word
                
                # Fall back to single word
                return parts[qld_idx - 1].lower().replace(',', '')
        except (ValueError, IndexError):
            pass
        
        return 'unknown_suburb'
    
    def find_matching_mongodb_doc(self, json_address: str, suburb: str) -> Optional[Dict]:
        """
        Find MongoDB document that matches the GCS JSON address
        Uses the pre-built complete_address field for efficient matching
        """
        collection = self.db[suburb]
        normalized_json_addr = self.normalize_address(json_address)
        
        # Direct query using complete_address field (MUCH faster!)
        query = {
            'complete_address': normalized_json_addr,
            'scraped_data': {'$exists': False}
        }
        
        return collection.find_one(query)
    
    def list_gcs_json_files(self, limit: Optional[int] = None) -> List[Dict]:
        """List JSON files in GCS (optionally limited for testing)"""
        print(f"\nScanning GCS bucket for JSON files...")
        
        blobs = self.bucket.list_blobs(prefix='scraped_data/')
        json_files = []
        
        for blob in blobs:
            if blob.name.endswith('.json'):
                json_files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'updated': blob.updated
                })
                
                if limit and len(json_files) >= limit:
                    break
        
        print(f"✓ Found {len(json_files):,} JSON files" + 
              (f" (limited to {limit} for testing)" if limit else ""))
        return json_files
    
    def import_single_file(self, blob_name: str, file_num: int, total: int) -> Dict:
        """Import a single JSON file and return detailed results"""
        result = {
            'blob_name': blob_name,
            'status': 'unknown',
            'message': '',
            'json_address': None,
            'db_address': None,
            'suburb': None,
            'matched': False
        }
        
        try:
            # Download JSON
            blob = self.bucket.blob(blob_name)
            json_content = blob.download_as_text()
            property_data = json.loads(json_content)
            
            # Extract address and suburb from JSON
            json_address = property_data.get('address')
            
            # If address is null, extract from URL
            if not json_address:
                url = property_data.get('url', '')
                if url:
                    # URL format: https://www.domain.com.au/property-profile/1-108-cypress-terrace-palm-beach-qld-4221
                    # Extract slug and convert to address
                    import re
                    match = re.search(r'/property-profile/(.+)$', url)
                    if match:
                        slug = match.group(1)
                        # Convert slug to address: "1-108-cypress-terrace-palm-beach-qld-4221" -> "1/108 CYPRESS TERRACE PALM BEACH QLD 4221"
                        json_address = slug.replace('-', ' ').upper()
                        # Fix unit format: "1 108" -> "1/108" at the start
                        parts = json_address.split()
                        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                            json_address = f"{parts[0]}/{parts[1]} {' '.join(parts[2:])}"
            
            result['json_address'] = json_address
            
            if not json_address:
                result['status'] = 'skip'
                result['message'] = 'No address in JSON or URL'
                return result
            
            suburb = self.extract_suburb_from_address(json_address)
            result['suburb'] = suburb
            
            # Find matching MongoDB document
            print(f"\n[{file_num}/{total}] Processing: {blob_name}")
            print(f"  JSON Address: {json_address}")
            print(f"  Suburb: {suburb}")
            print(f"  Searching for matching cadastral record...")
            
            matching_doc = self.find_matching_mongodb_doc(json_address, suburb)
            
            if matching_doc:
                result['matched'] = True
                result['db_address'] = self.build_address_from_doc(matching_doc)
                
                print(f"  ✓ MATCH FOUND!")
                print(f"    DB Address: {result['db_address']}")
                print(f"    ADDRESS_PID: {matching_doc.get('ADDRESS_PID')}")
                
                # Check if already has scraped_data
                if matching_doc.get('scraped_data'):
                    result['status'] = 'already_scraped'
                    result['message'] = 'Document already has scraped_data'
                    print(f"    Status: Already scraped (skipping)")
                else:
                    # Update the document
                    collection = self.db[suburb]
                    update_result = collection.update_one(
                        {'_id': matching_doc['_id']},
                        {'$set': {
                            'scraped_data': property_data,
                            'scraped_at': datetime.now(),
                            'imported_from_gcs': True,
                            'gcs_blob': blob_name
                        }}
                    )
                    
                    if update_result.modified_count > 0:
                        result['status'] = 'success'
                        result['message'] = 'Successfully updated'
                        print(f"    Status: ✓ Successfully updated MongoDB document")
                    else:
                        result['status'] = 'update_failed'
                        result['message'] = 'Update returned 0 modified'
                        print(f"    Status: ✗ Update failed")
            else:
                result['status'] = 'no_match'
                result['message'] = 'No matching cadastral record found in MongoDB'
                print(f"  ✗ NO MATCH found in MongoDB")
                print(f"    This address may not exist in cadastral database")
                
        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)
            print(f"  ✗ Error: {e}")
        
        return result
    
    def run(self):
        """Main import process"""
        print(f"\n{'='*70}")
        print(f"GCS TO MONGODB IMPORT - CORRECTED VERSION")
        if self.test_mode:
            print(f"TEST MODE: Processing only {self.test_limit} files")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # List files
        limit = self.test_limit if self.test_mode else None
        json_files = self.list_gcs_json_files(limit=limit)
        
        if not json_files:
            print("No files to import")
            return
        
        # Import files
        print(f"\nImporting {len(json_files):,} files...")
        print(f"Database: {self.db_name}")
        print(f"Matching: By normalized address comparison\n")
        
        results = []
        stats = {
            'success': 0,
            'already_scraped': 0,
            'no_match': 0,
            'skip': 0,
            'error': 0,
            'update_failed': 0
        }
        
        for i, file_info in enumerate(json_files, 1):
            result = self.import_single_file(file_info['name'], i, len(json_files))
            results.append(result)
            
            status = result['status']
            if status in stats:
                stats[status] += 1
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"IMPORT COMPLETE")
        print(f"{'='*70}")
        print(f"Total files:         {len(json_files):,}")
        print(f"Successfully updated: {stats['success']:,}")
        print(f"Already scraped:     {stats['already_scraped']:,}")
        print(f"No match found:      {stats['no_match']:,}")
        print(f"Skipped:             {stats['skip']:,}")
        print(f"Update failed:       {stats['update_failed']:,}")
        print(f"Errors:              {stats['error']:,}")
        print(f"Duration:            {duration}")
        print(f"{'='*70}\n")
        
        # Show detailed results for test mode
        if self.test_mode:
            print("DETAILED TEST RESULTS:")
            print("="*70)
            for i, result in enumerate(results, 1):
                print(f"\nFile {i}: {result['blob_name']}")
                print(f"  Status: {result['status']}")
                print(f"  JSON Address: {result['json_address']}")
                print(f"  DB Address: {result['db_address']}")
                print(f"  Matched: {result['matched']}")
                print(f"  Message: {result['message']}")
        
        return results


if __name__ == "__main__":
    # Check for test mode
    test_mode = '--test' in sys.argv or len(sys.argv) == 1  # Default to test mode
    test_limit = 50  # Test with 50 files for better statistics
    
    if '--full' in sys.argv:
        test_mode = False
    
    try:
        importer = GCSToMongoDBImporterCorrected(test_mode=test_mode, test_limit=test_limit)
        results = importer.run()
        
        if test_mode:
            print(f"\n✓ Test completed with {test_limit} files")
            print(f"\nTo run full import, use: python3 {sys.argv[0]} --full")
        
    except KeyboardInterrupt:
        print("\n\nImport cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        print(f"{e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
