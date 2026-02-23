#!/usr/bin/env python3
"""
Download JSON files from Google Cloud Storage to local MongoDB
Imports all scraped property data from GCS bucket into Gold_Coast collection
"""

import json
import os
import sys
from datetime import datetime
from google.cloud import storage
from pymongo import MongoClient
from typing import Dict, List

class GCSToMongoDBImporter:
    """Import GCS JSON data into MongoDB"""
    
    def __init__(self):
        # Configuration
        self.project_id = os.getenv('GCP_PROJECT_ID', 'property-data-scraping-477306')
        self.bucket_name = os.getenv('GCS_BUCKET', 'property-scraper-production-data-477306')
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
        self.db_name = 'Gold_Coast'
        
        # Initialize GCS client
        print(f"Connecting to Google Cloud Storage...")
        try:
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            print(f"✓ Connected to gs://{self.bucket_name}")
        except Exception as e:
            print(f"✗ GCS connection failed: {e}")
            print(f"\nMake sure you're authenticated:")
            print(f"  gcloud auth application-default login")
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
    
    def list_gcs_json_files(self) -> List[Dict]:
        """List all JSON files in GCS scraped_data folder"""
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
        
        print(f"✓ Found {len(json_files):,} JSON files")
        return json_files
    
    def extract_suburb_from_address(self, address: str) -> str:
        """Extract suburb from address string"""
        # Address format: "UNIT X/123 Street Name SUBURB QLD 4XXX"
        parts = address.upper().split()
        
        # Find QLD and extract suburb before it
        try:
            qld_idx = parts.index('QLD')
            if qld_idx > 0:
                suburb = parts[qld_idx - 1].lower()
                return suburb.replace(',', '')
        except (ValueError, IndexError):
            pass
        
        # Fallback: use last part before QLD/postcode
        for i, part in enumerate(parts):
            if part == 'QLD' or part.isdigit():
                if i > 0:
                    return parts[i-1].lower().replace(',', '')
        
        return 'unknown_suburb'
    
    def download_and_import_file(self, blob_name: str) -> bool:
        """Download a single JSON file and import to MongoDB"""
        try:
            # Download JSON
            blob = self.bucket.blob(blob_name)
            json_content = blob.download_as_text()
            property_data = json.loads(json_content)
            
            # Extract address and suburb
            address = property_data.get('address', '')
            suburb = self.extract_suburb_from_address(address)
            
            if not address:
                print(f"  ⚠ No address in {blob_name}")
                return False
            
            # Get collection for suburb
            collection = self.db[suburb]
            
            # Try to find existing document by address match
            # Since we may not have ADDRESS_PID, we'll match on address string
            query = {'scraped_data.address': address}
            
            # Check if already imported
            existing = collection.find_one(query)
            
            if existing and existing.get('scraped_data'):
                # Already imported
                return None  # Signal: already exists
            
            # Update or insert
            if existing:
                # Update existing document
                result = collection.update_one(
                    {'_id': existing['_id']},
                    {'$set': {
                        'scraped_data': property_data,
                        'scraped_at': datetime.now(),
                        'imported_from_gcs': True,
                        'gcs_blob': blob_name
                    }}
                )
                return result.modified_count > 0
            else:
                # Insert new document (GCS-only data, no cadastral info)
                document = {
                    'scraped_data': property_data,
                    'scraped_at': datetime.now(),
                    'imported_from_gcs': True,
                    'gcs_blob': blob_name,
                    'address_string': address,
                    'suburb': suburb
                }
                collection.insert_one(document)
                return True
                
        except Exception as e:
            print(f"  ✗ Error importing {blob_name}: {e}")
            return False
    
    def run(self):
        """Main import process"""
        print(f"\n{'='*70}")
        print(f"GCS TO MONGODB IMPORT")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # List files
        json_files = self.list_gcs_json_files()
        
        if not json_files:
            print("No files to import")
            return
        
        # Import files
        print(f"\nImporting {len(json_files):,} files to MongoDB...")
        print(f"Database: {self.db_name}")
        print(f"Collections: suburb-based\n")
        
        successful = 0
        skipped = 0
        failed = 0
        
        for i, file_info in enumerate(json_files, 1):
            blob_name = file_info['name']
            
            if i % 100 == 0 or i == 1:
                print(f"[{i:,}/{len(json_files):,}] {blob_name}")
            
            result = self.download_and_import_file(blob_name)
            
            if result is True:
                successful += 1
            elif result is None:
                skipped += 1
            else:
                failed += 1
            
            # Progress update every 500 files
            if i % 500 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = i / elapsed
                remaining = (len(json_files) - i) / rate
                print(f"\n  Progress: {i:,}/{len(json_files):,} ({i/len(json_files)*100:.1f}%)")
                print(f"  Imported: {successful:,} | Skipped: {skipped:,} | Failed: {failed:,}")
                print(f"  Rate: {rate:.1f} files/sec | Est. remaining: {remaining/60:.1f} min\n")
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"IMPORT COMPLETE")
        print(f"{'='*70}")
        print(f"Total files:     {len(json_files):,}")
        print(f"Imported:        {successful:,} ({successful/len(json_files)*100:.1f}%)")
        print(f"Skipped:         {skipped:,} (already existed)")
        print(f"Failed:          {failed:,}")
        print(f"Duration:        {duration}")
        print(f"Rate:            {len(json_files) / duration.total_seconds():.1f} files/second")
        print(f"{'='*70}\n")
        
        # Collection statistics
        print("Collection statistics:")
        collections = self.db.list_collection_names()
        for coll_name in sorted(collections):
            if coll_name == 'system.indexes':
                continue
            count = self.db[coll_name].count_documents({})
            scraped_count = self.db[coll_name].count_documents({'scraped_data': {'$exists': True}})
            print(f"  {coll_name:30s}: {count:6,} total | {scraped_count:6,} scraped")
        
        print(f"\nNext step: Analyze completion status")
        print(f"  ./analyze_completion_status.py")


if __name__ == "__main__":
    try:
        importer = GCSToMongoDBImporter()
        importer.run()
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
