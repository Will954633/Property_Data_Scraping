#!/usr/bin/env python3
"""
MongoDB Property Uploader with Auto-Enrichment Trigger
Uploads property data to MongoDB and automatically triggers enrichment for new properties
UPDATED: Now supports both Selenium and OCR (legacy) formats
"""

import pymongo
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import json
import os
import sys
import subprocess
import glob
import argparse
from typing import Dict, List, Tuple

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "properties_for_sale"

# Paths
BATCH_PROCESSOR_PATH = "../00_Production_System/02_Individual_Property_Google_Search/batch_processor.py"


class MongoDBUploader:
    def __init__(self, mongodb_uri: str = MONGODB_URI, db_name: str = DATABASE_NAME):
        """Initialize MongoDB connection"""
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.collection = self.db[COLLECTION_NAME]
        self.ensure_indexes()
    
    def ensure_indexes(self):
        """Create necessary indexes for performance"""
        self.collection.create_index("address", unique=True)
        self.collection.create_index("enriched")
        self.collection.create_index("first_seen")
        self.collection.create_index("last_updated")
        print("✓ MongoDB indexes ensured")
    
    def load_session_files(self, pattern: str = "property_data_session_*.json") -> List[Dict]:
        """Load session JSON files (OCR-based legacy format)"""
        all_properties = []
        session_files = sorted(glob.glob(pattern))
        
        if not session_files:
            return []
        
        print(f"\n→ Loading session files (OCR format)...")
        for filepath in session_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    properties = data.get('properties', [])
                    all_properties.extend(properties)
                    print(f"  ✓ {filepath}: {len(properties)} properties")
            except Exception as e:
                print(f"  ✗ Error loading {filepath}: {e}")
        
        print(f"  → Total properties loaded: {len(all_properties)}")
        return all_properties
    
    def load_selenium_scrape_reports(self, directory: str = "property_data") -> List[Dict]:
        """Load Selenium scrape report files (new format)"""
        all_properties = []
        
        # Check if directory exists
        if not os.path.exists(directory):
            return []
        
        # Find all scrape report files
        pattern = os.path.join(directory, "property_scrape_report_*.json")
        report_files = sorted(glob.glob(pattern))
        
        if not report_files:
            return []
        
        # Get most recent report file
        latest_report = max(report_files, key=os.path.getmtime)
        
        print(f"\n→ Loading Selenium scrape report...")
        print(f"  ℹ Using latest report: {os.path.basename(latest_report)}")
        
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract property data from successful results
            results = data.get('results', [])
            for result in results:
                if result.get('success') and result.get('property_data'):
                    prop = result['property_data']
                    # Ensure address field exists
                    if 'address' in prop:
                        all_properties.append(prop)
            
            print(f"  ✓ Loaded {len(all_properties)} successful properties")
            
            # Print scrape info if available
            if 'scrape_info' in data:
                info = data['scrape_info']
                print(f"  ℹ Scrape info:")
                print(f"    • Total scraped: {info.get('total_properties', 'N/A')}")
                print(f"    • Successful: {info.get('successful', 'N/A')}")
                print(f"    • Failed: {info.get('failed', 'N/A')}")
                print(f"    • Success rate: {info.get('success_rate', 'N/A')}")
        
        except Exception as e:
            print(f"  ✗ Error loading {latest_report}: {e}")
        
        return all_properties
    
    def upload_properties(self, properties: List[Dict], source: str = "selenium_scraper") -> Tuple[int, int, int]:
        """
        Upload properties to MongoDB using upsert
        Returns: (new_count, updated_count, total_count)
        """
        if not properties:
            print("⚠ No properties to upload")
            return 0, 0, 0
        
        now = datetime.now()
        new_count = 0
        updated_count = 0
        
        print(f"\n→ Uploading {len(properties)} properties to MongoDB...")
        
        for prop in properties:
            address = prop.get('address')
            if not address:
                continue
            
            # Check if property exists
            existing = self.collection.find_one({"address": address})
            
            if existing:
                # Update existing property
                update_doc = {
                    "$set": {
                        **prop,
                        "last_updated": now
                    }
                }
                self.collection.update_one({"address": address}, update_doc)
                updated_count += 1
            else:
                # Insert new property with enrichment tracking fields
                insert_doc = {
                    **prop,
                    "enriched": False,
                    "enrichment_attempted": False,
                    "enrichment_retry_count": 0,
                    "enrichment_error": None,
                    "first_seen": now,
                    "last_updated": now,
                    "last_enriched": None,
                    "source": source,
                    "enrichment_data": None
                }
                self.collection.insert_one(insert_doc)
                new_count += 1
        
        total_count = new_count + updated_count
        
        print(f"  ✓ Upload complete:")
        print(f"    • New properties: {new_count}")
        print(f"    • Updated properties: {updated_count}")
        print(f"    • Total processed: {total_count}")
        
        return new_count, updated_count, total_count
    
    def get_unenriched_count(self) -> int:
        """Count properties that need enrichment"""
        return self.collection.count_documents({
            "enriched": False,
            "enrichment_attempted": {"$ne": True}
        })
    
    def get_unenriched_addresses(self) -> List[str]:
        """Get list of addresses that need enrichment"""
        cursor = self.collection.find(
            {"enriched": False, "enrichment_attempted": {"$ne": True}},
            {"address": 1}
        )
        return [doc["address"] for doc in cursor]
    
    def trigger_enrichment(self, auto_trigger: bool = True) -> bool:
        """Trigger batch_processor.py to enrich unenriched properties"""
        unenriched_count = self.get_unenriched_count()
        
        if unenriched_count == 0:
            print(f"\n✓ All properties are enriched - no action needed")
            return True
        
        print(f"\n→ Found {unenriched_count} properties needing enrichment")
        
        if not auto_trigger:
            print(f"  ⚠ Auto-trigger disabled - skipping enrichment")
            return False
        
        # Get absolute path to batch_processor.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        batch_processor_abs = os.path.join(script_dir, BATCH_PROCESSOR_PATH)
        
        if not os.path.exists(batch_processor_abs):
            print(f"  ✗ batch_processor.py not found at: {batch_processor_abs}")
            return False
        
        print(f"  → Triggering enrichment: {batch_processor_abs}")
        print(f"  → Processing {unenriched_count} properties...")
        print(f"\n{'='*80}")
        print(f"STARTING ENRICHMENT PROCESS")
        print(f"{'='*80}\n")
        
        try:
            # Call batch_processor.py with --mongodb flag
            result = subprocess.run(
                ['python3', batch_processor_abs, '--mongodb'],
                cwd=os.path.dirname(batch_processor_abs),
                capture_output=False,
                text=True
            )
            
            print(f"\n{'='*80}")
            print(f"ENRICHMENT PROCESS COMPLETE")
            print(f"{'='*80}\n")
            
            if result.returncode == 0:
                print(f"✓ Enrichment completed successfully")
                return True
            else:
                print(f"⚠ Enrichment completed with return code: {result.returncode}")
                return False
        
        except Exception as e:
            print(f"✗ Error triggering enrichment: {e}")
            return False
    
    def print_summary(self):
        """Print summary statistics"""
        total = self.collection.count_documents({})
        enriched_count = self.collection.count_documents({"enriched": True})
        unenriched_count = self.collection.count_documents({"enriched": False})
        
        print(f"\n{'='*80}")
        print(f"MONGODB SUMMARY")
        print(f"{'='*80}")
        print(f"  Database: {DATABASE_NAME}")
        print(f"  Collection: {COLLECTION_NAME}")
        print(f"  Total properties: {total}")
        print(f"  Enriched: {enriched_count}")
        print(f"  Unenriched: {unenriched_count}")
        if total > 0:
            print(f"  Enrichment rate: {(enriched_count/total*100):.1f}%")
        print(f"{'='*80}\n")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Upload property data to MongoDB and trigger enrichment')
    parser.add_argument('--pattern', default='property_data_session_*.json', 
                       help='Pattern for session JSON files (OCR format - legacy)')
    parser.add_argument('--selenium', action='store_true',
                       help='Force load from Selenium scrape reports (new format)')
    parser.add_argument('--no-auto-enrich', action='store_true',
                       help='Disable automatic enrichment trigger')
    parser.add_argument('--mongodb-uri', default=MONGODB_URI,
                       help=f'MongoDB connection URI (default: {MONGODB_URI})')
    
    args = parser.parse_args()
    
    print("="*80)
    print("MONGODB PROPERTY UPLOADER")
    print("="*80)
    
    try:
        # Initialize uploader
        uploader = MongoDBUploader(mongodb_uri=args.mongodb_uri)
        
        # Load properties - auto-detect format
        properties = []
        source = "unknown"
        
        # First try Selenium format (NEW - preferred)
        selenium_props = uploader.load_selenium_scrape_reports()
        if selenium_props:
            properties = selenium_props
            source = "selenium_forsale_scraper"
            print(f"  ℹ Using Selenium scrape format (NEW)")
        
        # Fallback to OCR session files (OLD) if --selenium not specified and no Selenium data
        if not properties and not args.selenium:
            ocr_props = uploader.load_session_files(pattern=args.pattern)
            if ocr_props:
                properties = ocr_props
                source = "ocr_session_scraper"
                print(f"  ℹ Using OCR session format (LEGACY)")
        
        if not properties:
            print("\n✗ No properties found to upload")
            print("  • Check that scraping completed successfully")
            print("  • For Selenium (NEW): property_data/property_scrape_report_*.json")
            print("  • For OCR (LEGACY): property_data_session_*.json")
            uploader.close()
            return 1
        
        # Upload to MongoDB
        new_count, updated_count, total_count = uploader.upload_properties(properties, source=source)
        
        # Print current summary
        uploader.print_summary()
        
        # Trigger enrichment if there are unenriched properties
        auto_trigger = not args.no_auto_enrich
        if new_count > 0 or uploader.get_unenriched_count() > 0:
            uploader.trigger_enrichment(auto_trigger=auto_trigger)
        
        # Final summary
        uploader.print_summary()
        
        # Close connection
        uploader.close()
        
        print("✓ Upload process complete\n")
        return 0
    
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
