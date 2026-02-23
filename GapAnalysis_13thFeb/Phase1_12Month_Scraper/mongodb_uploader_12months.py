#!/usr/bin/env python3
"""
MongoDB Uploader for SOLD Properties (Last 12 Months)
Last Edit: 13/02/2026, 11:45 AM (Thursday) — Brisbane Time

Modified from 6-month uploader to:
- Target Gold_Coast_Recently_Sold database (Azure Cosmos DB)
- Use 12-month cutoff instead of 6 months
- Support all 8 target market suburbs
- Upload to suburb-specific collections (e.g., Robina, Mudgeeraba, etc.)

Uploads sold property data to MongoDB with intelligent stop conditions:
- Stop Condition A: 5 consecutive properties with sale dates >12 months old
- Stop Condition B: 5 consecutive properties already in database
Processes suburbs sequentially
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
import os
import sys
import glob
from typing import Dict, List, Tuple

# MongoDB Configuration - AZURE COSMOS DB
# Connection string should be set in environment variable or .env file
MONGODB_URI = os.getenv("COSMOS_CONNECTION_STRING", "mongodb://127.0.0.1:27017/")
DATABASE_NAME = "Gold_Coast_Recently_Sold"

# Suburb name mapping (URL slug -> Collection name)
SUBURB_COLLECTION_MAP = {
    "robina": "Robina",
    "mudgeeraba": "Mudgeeraba",
    "varsity-lakes": "Varsity_Lakes",
    "reedy-creek": "Reedy_Creek",
    "burleigh-waters": "Burleigh_Waters",
    "carrara": "Carrara",
    "merrimac": "Merrimac",
    "worongary": "Worongary"
}


class SoldPropertyUploader:
    def __init__(self, mongodb_uri: str = MONGODB_URI, db_name: str = DATABASE_NAME):
        """Initialize MongoDB connection"""
        print(f"→ Connecting to MongoDB...")
        print(f"  Database: {db_name}")
        
        try:
            self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            print(f"  ✓ Connected successfully")
        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
            raise
        
        self.db = self.client[db_name]
        self.collections = {}  # Cache of collection objects
    
    def get_collection(self, suburb_slug: str):
        """Get or create collection for a suburb"""
        collection_name = SUBURB_COLLECTION_MAP.get(suburb_slug)
        if not collection_name:
            raise ValueError(f"Unknown suburb: {suburb_slug}")
        
        if collection_name not in self.collections:
            self.collections[collection_name] = self.db[collection_name]
            self.ensure_indexes(self.collections[collection_name])
        
        return self.collections[collection_name]
    
    def ensure_indexes(self, collection):
        """Create necessary indexes for performance"""
        try:
            collection.create_index("address", unique=True)
            collection.create_index("sale_date")
            collection.create_index("suburb")
            collection.create_index("first_seen")
            collection.create_index("last_updated")
            collection.create_index("property_url", unique=True)
            print(f"  ✓ Indexes ensured for {collection.name}")
        except Exception as e:
            print(f"  ⚠ Index creation warning: {e}")
    
    def load_suburb_scrape_data(self, suburb_name: str) -> List[Dict]:
        """Load scraped data for a specific suburb"""
        pattern = f"property_data/sold_scrape_{suburb_name}_*.json"
        files = glob.glob(pattern)
        
        if not files:
            print(f"  ⚠ No scrape data found for {suburb_name}")
            return []
        
        # Get most recent file
        latest_file = max(files, key=os.path.getmtime)
        print(f"  → Loading: {os.path.basename(latest_file)}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract property data from successful results
            properties = []
            results = data.get('results', [])
            for result in results:
                if result.get('success') and result.get('property_data'):
                    prop = result['property_data']
                    # Ensure address field exists
                    if 'address' in prop:
                        properties.append(prop)
            
            print(f"  ✓ Loaded {len(properties)} properties")
            return properties
        
        except Exception as e:
            print(f"  ✗ Error loading {latest_file}: {e}")
            return []
    
    def upload_suburb_properties(self, suburb_slug: str, properties: List[Dict]) -> Tuple[int, int, str]:
        """
        Upload properties for a suburb with stop conditions
        
        Returns: (uploaded_count, updated_count, stop_reason)
        """
        if not properties:
            return 0, 0, "NO_DATA: No properties to upload"
        
        collection = self.get_collection(suburb_slug)
        
        consecutive_old = 0
        consecutive_duplicate = 0
        uploaded_count = 0
        updated_count = 0
        skipped_no_date = 0
        
        twelve_months_ago = datetime.now() - timedelta(days=365)  # 12 months
        
        print(f"\n  Processing {len(properties)} properties...")
        print(f"  Twelve months cutoff: {twelve_months_ago.strftime('%Y-%m-%d')}")
        
        for i, prop in enumerate(properties, 1):
            address = prop.get('address')
            sale_date_str = prop.get('sale_date')
            property_url = prop.get('property_url', '')
            
            # Skip properties without sale date
            if not sale_date_str:
                print(f"  [{i}/{len(properties)}] ⚠ No sale date for {address}, skipping")
                skipped_no_date += 1
                continue
            
            # Parse sale date
            try:
                sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d')
            except:
                print(f"  [{i}/{len(properties)}] ⚠ Invalid sale date format for {address}: {sale_date_str}, skipping")
                skipped_no_date += 1
                continue
            
            # STOP CONDITION A: Check if sale date > 12 months
            if sale_date < twelve_months_ago:
                consecutive_old += 1
                print(f"  [{i}/{len(properties)}] ⚠ Property sold >12 months ago: {address}")
                print(f"    Sale date: {sale_date_str} (>{(datetime.now() - sale_date).days} days ago)")
                print(f"    Consecutive old: {consecutive_old}/5")
                
                if consecutive_old >= 5:
                    stop_reason = f"STOP_A: 5 consecutive properties >12 months old (last: {address})"
                    print(f"\n  🛑 {stop_reason}")
                    return uploaded_count, updated_count, stop_reason
            else:
                consecutive_old = 0  # Reset counter
            
            # STOP CONDITION B: Check if already in database
            # Try both address and property_url for deduplication
            existing = None
            if property_url:
                existing = collection.find_one({"property_url": property_url})
            if not existing and address:
                existing = collection.find_one({"address": address})
            
            if existing:
                consecutive_duplicate += 1
                print(f"  [{i}/{len(properties)}] ⚠ Duplicate property: {address}")
                print(f"    Consecutive duplicates: {consecutive_duplicate}/5")
                
                if consecutive_duplicate >= 5:
                    stop_reason = f"STOP_B: 5 consecutive duplicate properties (last: {address})"
                    print(f"\n  🛑 {stop_reason}")
                    return uploaded_count, updated_count, stop_reason
                
                # Update existing record
                update_filter = {"property_url": property_url} if property_url else {"address": address}
                collection.update_one(
                    update_filter,
                    {"$set": {**prop, "last_updated": datetime.now()}}
                )
                updated_count += 1
                print(f"  [{i}/{len(properties)}] ↻ Updated: {address}")
            else:
                consecutive_duplicate = 0  # Reset counter
                
                # Insert new property
                insert_doc = {
                    **prop,
                    "first_seen": datetime.now(),
                    "last_updated": datetime.now(),
                    "source": "selenium_sold_scraper_12months",
                    "scraper_version": "12month_v1.0"
                }
                
                try:
                    collection.insert_one(insert_doc)
                    uploaded_count += 1
                    print(f"  [{i}/{len(properties)}] ✓ Inserted: {address} (sold: {sale_date_str})")
                except pymongo.errors.DuplicateKeyError:
                    # Handle race condition or duplicate key
                    print(f"  [{i}/{len(properties)}] ⚠ Duplicate key error for: {address}, updating instead")
                    update_filter = {"property_url": property_url} if property_url else {"address": address}
                    collection.update_one(
                        update_filter,
                        {"$set": {**prop, "last_updated": datetime.now()}},
                        upsert=True
                    )
                    updated_count += 1
        
        # If we got here, all properties were processed
        stop_reason = f"COMPLETE: All {len(properties)} properties processed"
        if skipped_no_date > 0:
            stop_reason += f" ({skipped_no_date} skipped - no sale date)"
        
        return uploaded_count, updated_count, stop_reason
    
    def get_collection_stats(self, suburb_slug: str = None) -> Dict:
        """Get statistics about a collection or all collections"""
        if suburb_slug:
            # Stats for single suburb
            collection = self.get_collection(suburb_slug)
            total = collection.count_documents({})
            
            # Recent sales (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            recent_sales = collection.count_documents({
                "sale_date": {"$gte": thirty_days_ago}
            })
            
            return {
                "suburb": suburb_slug,
                "collection": SUBURB_COLLECTION_MAP[suburb_slug],
                "total_properties": total,
                "recent_sales_30_days": recent_sales
            }
        else:
            # Stats for all suburbs
            all_stats = {}
            total_all = 0
            
            for suburb_slug, collection_name in SUBURB_COLLECTION_MAP.items():
                try:
                    collection = self.db[collection_name]
                    count = collection.count_documents({})
                    all_stats[suburb_slug] = count
                    total_all += count
                except:
                    all_stats[suburb_slug] = 0
            
            return {
                "total_properties": total_all,
                "by_suburb": all_stats
            }
    
    def print_summary(self, suburb_slug: str = None):
        """Print summary statistics"""
        if suburb_slug:
            stats = self.get_collection_stats(suburb_slug)
            print(f"\n{'='*80}")
            print(f"COLLECTION SUMMARY: {stats['collection']}")
            print(f"{'='*80}")
            print(f"  Database: {DATABASE_NAME}")
            print(f"  Collection: {stats['collection']}")
            print(f"  Total properties: {stats['total_properties']}")
            print(f"  Recent sales (30 days): {stats['recent_sales_30_days']}")
            print(f"{'='*80}\n")
        else:
            stats = self.get_collection_stats()
            print(f"\n{'='*80}")
            print(f"DATABASE SUMMARY: {DATABASE_NAME}")
            print(f"{'='*80}")
            print(f"  Total properties: {stats['total_properties']}")
            
            if stats['by_suburb']:
                print(f"\n  By suburb:")
                for suburb, count in sorted(stats['by_suburb'].items()):
                    collection_name = SUBURB_COLLECTION_MAP[suburb]
                    print(f"    • {collection_name}: {count} properties")
            
            print(f"{'='*80}\n")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()


def main():
    """Main execution"""
    print("="*80)
    print("MONGODB UPLOADER - SOLD PROPERTIES (Last 12 Months)")
    print("="*80)
    print(f"Target Database: {DATABASE_NAME} (Azure Cosmos DB)")
    
    # All 8 target market suburbs (in order)
    suburbs = [
        'robina', 'mudgeeraba', 'varsity-lakes', 'reedy-creek', 
        'burleigh-waters', 'carrara', 'merrimac', 'worongary'
    ]
    
    try:
        # Initialize uploader
        uploader = SoldPropertyUploader()
        
        # Print initial state
        print("\n→ Initial database state:")
        uploader.print_summary()
        
        # Process each suburb sequentially
        all_results = []
        
        for suburb in suburbs:
            print(f"\n{'#'*80}")
            print(f"# PROCESSING SUBURB: {suburb.upper()}")
            print(f"# Collection: {SUBURB_COLLECTION_MAP[suburb]}")
            print(f"{'#'*80}")
            
            # Load scraped data for this suburb
            properties = uploader.load_suburb_scrape_data(suburb)
            
            if not properties:
                print(f"  ⚠ Skipping {suburb} - no data found")
                all_results.append({
                    "suburb": suburb,
                    "uploaded": 0,
                    "updated": 0,
                    "stop_reason": "NO_DATA"
                })
                continue
            
            # Upload with stop conditions
            uploaded, updated, stop_reason = uploader.upload_suburb_properties(suburb, properties)
            
            result = {
                "suburb": suburb,
                "collection": SUBURB_COLLECTION_MAP[suburb],
                "uploaded": uploaded,
                "updated": updated,
                "total_processed": uploaded + updated,
                "stop_reason": stop_reason
            }
            all_results.append(result)
            
            print(f"\n  📊 {suburb.upper()} RESULTS:")
            print(f"    New properties: {uploaded}")
            print(f"    Updated properties: {updated}")
            print(f"    Total processed: {uploaded + updated}")
            print(f"    Stop reason: {stop_reason}")
        
        # Generate overall summary
        print(f"\n{'='*80}")
        print(f"UPLOAD COMPLETE - ALL SUBURBS")
        print(f"{'='*80}")
        
        total_uploaded = sum(r["uploaded"] for r in all_results)
        total_updated = sum(r["updated"] for r in all_results)
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"  Total new properties: {total_uploaded}")
        print(f"  Total updated properties: {total_updated}")
        print(f"  Total processed: {total_uploaded + total_updated}")
        
        print(f"\n  By suburb:")
        for result in all_results:
            print(f"    • {result['suburb']} ({result['collection']}): {result['uploaded']} new, {result['updated']} updated")
            if result['stop_reason'].startswith('STOP'):
                print(f"      ⚠ {result['stop_reason']}")
        
        # Save results log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"upload_log_12months_{timestamp}.json"
        with open(log_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "database": DATABASE_NAME,
                "total_uploaded": total_uploaded,
                "total_updated": total_updated,
                "suburbs": all_results
            }, f, indent=2)
        print(f"\n📁 Upload log saved: {log_file}")
        
        # Final database summary
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
