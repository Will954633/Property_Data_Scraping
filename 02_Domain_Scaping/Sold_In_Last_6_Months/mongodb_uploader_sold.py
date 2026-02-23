#!/usr/bin/env python3
"""
MongoDB Uploader for SOLD Properties (Last 6 Months)
Uploads sold property data to MongoDB with intelligent stop conditions:
- Stop Condition A: 3 consecutive properties with sale dates >6 months old
- Stop Condition B: 3 consecutive properties already in database
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

# MongoDB Configuration
MONGODB_URI = "mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/"
DATABASE_NAME = "property_data"
COLLECTION_NAME = "sold_last_6_months"


class SoldPropertyUploader:
    def __init__(self, mongodb_uri: str = MONGODB_URI, db_name: str = DATABASE_NAME):
        """Initialize MongoDB connection"""
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.collection = self.db[COLLECTION_NAME]
        self.ensure_indexes()
    
    def ensure_indexes(self):
        """Create necessary indexes for performance"""
        self.collection.create_index("address", unique=True)
        self.collection.create_index("sale_date")
        self.collection.create_index("suburb_scraped")
        self.collection.create_index("first_seen")
        self.collection.create_index("last_updated")
        print("✓ MongoDB indexes ensured")
    
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
    
    def upload_suburb_properties(self, suburb_name: str, properties: List[Dict]) -> Tuple[int, int, str]:
        """
        Upload properties for a suburb with stop conditions
        
        Returns: (uploaded_count, updated_count, stop_reason)
        """
        if not properties:
            return 0, 0, "NO_DATA: No properties to upload"
        
        consecutive_old = 0
        consecutive_duplicate = 0
        uploaded_count = 0
        updated_count = 0
        skipped_no_date = 0
        
        six_months_ago = datetime.now() - timedelta(days=182)  # ~6 months
        
        print(f"\n  Processing {len(properties)} properties...")
        print(f"  Six months cutoff: {six_months_ago.strftime('%Y-%m-%d')}")
        
        for i, prop in enumerate(properties, 1):
            address = prop.get('address')
            sale_date_str = prop.get('sale_date')
            
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
            
            # STOP CONDITION A: Check if sale date > 6 months
            if sale_date < six_months_ago:
                consecutive_old += 1
                print(f"  [{i}/{len(properties)}] ⚠ Property sold >6 months ago: {address}")
                print(f"    Sale date: {sale_date_str} (>{(datetime.now() - sale_date).days} days ago)")
                print(f"    Consecutive old: {consecutive_old}/3")
                
                if consecutive_old >= 3:
                    stop_reason = f"STOP_A: 3 consecutive properties >6 months old (last: {address})"
                    print(f"\n  🛑 {stop_reason}")
                    return uploaded_count, updated_count, stop_reason
            else:
                consecutive_old = 0  # Reset counter
            
            # STOP CONDITION B: Check if already in database
            existing = self.collection.find_one({"address": address})
            
            if existing:
                consecutive_duplicate += 1
                print(f"  [{i}/{len(properties)}] ⚠ Duplicate property: {address}")
                print(f"    Consecutive duplicates: {consecutive_duplicate}/3")
                
                if consecutive_duplicate >= 3:
                    stop_reason = f"STOP_B: 3 consecutive duplicate properties (last: {address})"
                    print(f"\n  🛑 {stop_reason}")
                    return uploaded_count, updated_count, stop_reason
                
                # Update existing record
                self.collection.update_one(
                    {"address": address},
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
                    "source": "selenium_sold_scraper"
                }
                self.collection.insert_one(insert_doc)
                uploaded_count += 1
                print(f"  [{i}/{len(properties)}] ✓ Inserted: {address} (sold: {sale_date_str})")
        
        # If we got here, all properties were processed
        stop_reason = f"COMPLETE: All {len(properties)} properties processed"
        if skipped_no_date > 0:
            stop_reason += f" ({skipped_no_date} skipped - no sale date)"
        
        return uploaded_count, updated_count, stop_reason
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        total = self.collection.count_documents({})
        
        # Count by suburb
        pipeline = [
            {"$group": {"_id": "$suburb_scraped", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_suburb = list(self.collection.aggregate(pipeline))
        
        # Recent sales (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent_sales = self.collection.count_documents({
            "sale_date": {"$gte": thirty_days_ago}
        })
        
        return {
            "total_properties": total,
            "by_suburb": {item["_id"]: item["count"] for item in by_suburb},
            "recent_sales_30_days": recent_sales
        }
    
    def print_summary(self):
        """Print summary statistics"""
        stats = self.get_collection_stats()
        
        print(f"\n{'='*80}")
        print(f"MONGODB COLLECTION SUMMARY")
        print(f"{'='*80}")
        print(f"  Database: {DATABASE_NAME}")
        print(f"  Collection: {COLLECTION_NAME}")
        print(f"  Total properties: {stats['total_properties']}")
        print(f"  Recent sales (30 days): {stats['recent_sales_30_days']}")
        
        if stats['by_suburb']:
            print(f"\n  By suburb:")
            for suburb, count in stats['by_suburb'].items():
                print(f"    • {suburb}: {count} properties")
        
        print(f"{'='*80}\n")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()


def main():
    """Main execution"""
    print("="*80)
    print("MONGODB UPLOADER - SOLD PROPERTIES (Last 6 Months)")
    print("="*80)
    
    # Suburbs to process (in order)
    suburbs = ['robina', 'mudgeeraba', 'varsity-lakes', 'reedy-creek', 'burleigh-waters']
    
    try:
        # Initialize uploader
        uploader = SoldPropertyUploader()
        
        # Print initial state
        print("\n→ Initial collection state:")
        uploader.print_summary()
        
        # Process each suburb sequentially
        all_results = []
        
        for suburb in suburbs:
            print(f"\n{'#'*80}")
            print(f"# PROCESSING SUBURB: {suburb.upper()}")
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
            print(f"    • {result['suburb']}: {result['uploaded']} new, {result['updated']} updated")
            if result['stop_reason'].startswith('STOP'):
                print(f"      ⚠ {result['stop_reason']}")
        
        # Save results log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"upload_log_{timestamp}.json"
        with open(log_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_uploaded": total_uploaded,
                "total_updated": total_updated,
                "suburbs": all_results
            }, f, indent=2)
        print(f"\n📁 Upload log saved: {log_file}")
        
        # Final collection summary
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
