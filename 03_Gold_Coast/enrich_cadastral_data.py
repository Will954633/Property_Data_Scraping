#!/usr/bin/env python3
"""
Gold Coast Cadastral Data Enrichment Script
Enriches MongoDB properties with data from QLD Spatial GIS API
Adds 15 critical fields including lot_area (m²), tenure, parcel types, etc.
"""

import sys
import requests
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, BulkWriteError
from datetime import datetime
import time
from typing import Dict, List, Optional
import json

# Configuration
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "Gold_Coast"
API_BASE_URL = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer"
BATCH_SIZE = 100  # Process this many properties before bulk updating
API_DELAY = 0.1  # Delay between API calls (seconds) to be respectful

# Fields to retrieve from Cadastral Parcels (Layer 4)
CADASTRAL_FIELDS = [
    'lot',
    'plan',
    'lotplan',
    'lot_area',
    'excl_area',
    'lot_volume',
    'tenure',
    'cover_typ',
    'parcel_typ',
    'acc_code',
    'surv_ind',
    'feat_name',
    'alias_name',
    'shire_name',
    'smis_map'
]

# Fields to retrieve from Addresses (Layer 0) - formatted address
ADDRESS_FIELDS = [
    'address',
    'street_full',
    'floor_number',
    'floor_type',
    'floor_suffix'
]


def connect_to_mongodb():
    """Establish connection to MongoDB."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB at {MONGODB_URI}")
        return client
    except ConnectionFailure as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        sys.exit(1)


def query_cadastral_data(lot: str, plan: str) -> Optional[Dict]:
    """
    Query QLD Spatial GIS API for cadastral data using lot and plan.
    
    Args:
        lot: Lot number
        plan: Plan number
        
    Returns:
        Dictionary with cadastral data or None if not found
    """
    try:
        # Build query URL for Layer 4 (Cadastral Parcels)
        where_clause = f"lot='{lot}' AND plan='{plan}'"
        params = {
            'where': where_clause,
            'outFields': ','.join(CADASTRAL_FIELDS),
            'f': 'json',
            'returnGeometry': 'false'
        }
        
        url = f"{API_BASE_URL}/4/query"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('features') and len(data['features']) > 0:
            attributes = data['features'][0]['attributes']
            
            # Clean up None values and convert to appropriate types
            cleaned_data = {}
            for key, value in attributes.items():
                if value is not None:
                    # Convert empty strings to None
                    if isinstance(value, str) and value.strip() == '':
                        cleaned_data[key] = None
                    else:
                        cleaned_data[key] = value
                else:
                    cleaned_data[key] = None
            
            return cleaned_data
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"    ⚠ API request failed for lot={lot}, plan={plan}: {e}")
        return None
    except Exception as e:
        print(f"    ⚠ Error processing lot={lot}, plan={plan}: {e}")
        return None


def query_address_data(address_pid: int) -> Optional[Dict]:
    """
    Query QLD Spatial GIS API for address data using ADDRESS_PID.
    
    Args:
        address_pid: Address point ID
        
    Returns:
        Dictionary with address data or None if not found
    """
    try:
        # Build query URL for Layer 0 (Addresses)
        where_clause = f"address_pid={address_pid}"
        params = {
            'where': where_clause,
            'outFields': ','.join(ADDRESS_FIELDS),
            'f': 'json',
            'returnGeometry': 'false'
        }
        
        url = f"{API_BASE_URL}/0/query"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('features') and len(data['features']) > 0:
            attributes = data['features'][0]['attributes']
            
            # Clean up data
            cleaned_data = {}
            for key, value in attributes.items():
                if value is not None:
                    if isinstance(value, str) and value.strip() == '':
                        cleaned_data[key] = None
                    else:
                        cleaned_data[key] = value
                else:
                    cleaned_data[key] = None
            
            return cleaned_data
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"    ⚠ API request failed for address_pid={address_pid}: {e}")
        return None
    except Exception as e:
        print(f"    ⚠ Error processing address_pid={address_pid}: {e}")
        return None


def enrich_collection(collection, stats: Dict) -> None:
    """
    Enrich a single collection (suburb) with cadastral data.
    
    Args:
        collection: MongoDB collection object
        stats: Statistics dictionary to update
    """
    collection_name = collection.name
    total_docs = collection.count_documents({})
    
    print(f"\n  Processing: {collection_name} ({total_docs:,} properties)")
    
    # Check if already enriched (has lot_area field)
    enriched_count = collection.count_documents({'lot_area': {'$exists': True}})
    if enriched_count == total_docs:
        print(f"    ℹ Already enriched ({enriched_count}/{total_docs})")
        stats['collections_skipped'] += 1
        stats['total_properties'] += total_docs
        stats['already_enriched'] += total_docs
        return
    
    # Get properties that need enrichment
    cursor = collection.find({
        'lot_area': {'$exists': False},
        'LOT': {'$exists': True, '$ne': None},
        'PLAN': {'$exists': True, '$ne': None}
    })
    
    updates = []
    processed = 0
    enriched = 0
    failed = 0
    
    for doc in cursor:
        lot = doc.get('LOT')
        plan = doc.get('PLAN')
        address_pid = doc.get('ADDRESS_PID')
        
        if not lot or not plan:
            failed += 1
            continue
        
        # Query cadastral data
        cadastral_data = query_cadastral_data(lot, plan)
        
        # Query address data if ADDRESS_PID is available
        address_data = None
        if address_pid:
            address_data = query_address_data(address_pid)
        
        # Combine the data
        update_fields = {}
        
        if cadastral_data:
            # Add all cadastral fields
            update_fields.update(cadastral_data)
            enriched += 1
        
        if address_data:
            # Add address fields (prefixed to avoid conflicts with existing fields)
            for key, value in address_data.items():
                if key not in ['lot', 'plan', 'lotplan']:  # Skip duplicates
                    update_fields[f'API_{key}'] = value
        
        if update_fields:
            # Add enrichment metadata
            update_fields['enriched_at'] = datetime.utcnow()
            update_fields['enriched_source'] = 'QLD_Spatial_GIS_API'
            
            # Create update operation
            updates.append(
                UpdateOne(
                    {'_id': doc['_id']},
                    {'$set': update_fields}
                )
            )
        else:
            failed += 1
        
        processed += 1
        
        # Bulk update when batch is full
        if len(updates) >= BATCH_SIZE:
            try:
                result = collection.bulk_write(updates, ordered=False)
                print(f"    ✓ Updated {result.modified_count} properties (batch)")
                updates = []
            except BulkWriteError as e:
                print(f"    ⚠ Bulk write error: {e.details.get('nModified', 0)} updated")
                updates = []
        
        # Progress indicator
        if processed % 100 == 0:
            print(f"    Progress: {processed:,}/{enriched_count:,} | Enriched: {enriched} | Failed: {failed}")
        
        # Respectful delay between API calls
        time.sleep(API_DELAY)
    
    # Update remaining batch
    if updates:
        try:
            result = collection.bulk_write(updates, ordered=False)
            print(f"    ✓ Updated {result.modified_count} properties (final batch)")
        except BulkWriteError as e:
            print(f"    ⚠ Bulk write error: {e.details.get('nModified', 0)} updated")
    
    # Update statistics
    stats['total_properties'] += total_docs
    stats['properties_processed'] += processed
    stats['properties_enriched'] += enriched
    stats['properties_failed'] += failed
    stats['collections_processed'] += 1
    
    print(f"    ✓ Completed: {enriched} enriched, {failed} failed")


def main():
    """Main enrichment function."""
    start_time = datetime.now()
    
    print(f"\n{'='*70}")
    print("Gold Coast Cadastral Data Enrichment")
    print(f"{'='*70}\n")
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    
    # Get all collections (suburbs)
    collections = sorted(db.list_collection_names())
    print(f"✓ Found {len(collections)} suburbs to process")
    
    # Statistics
    stats = {
        'total_properties': 0,
        'properties_processed': 0,
        'properties_enriched': 0,
        'properties_failed': 0,
        'already_enriched': 0,
        'collections_processed': 0,
        'collections_skipped': 0
    }
    
    # Process each collection
    print(f"\n{'='*70}")
    print("Processing Collections")
    print(f"{'='*70}")
    
    for i, collection_name in enumerate(collections, 1):
        print(f"\n[{i}/{len(collections)}]", end=" ")
        collection = db[collection_name]
        
        try:
            enrich_collection(collection, stats)
        except Exception as e:
            print(f"    ✗ Error processing collection: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*70}")
    print("Enrichment Summary")
    print(f"{'='*70}\n")
    print(f"Collections processed:     {stats['collections_processed']:,}")
    print(f"Collections skipped:       {stats['collections_skipped']:,}")
    print(f"Total properties:          {stats['total_properties']:,}")
    print(f"Properties processed:      {stats['properties_processed']:,}")
    print(f"Properties enriched:       {stats['properties_enriched']:,}")
    print(f"Properties failed:         {stats['properties_failed']:,}")
    print(f"Already enriched:          {stats['already_enriched']:,}")
    print(f"Duration:                  {duration}")
    
    if stats['properties_enriched'] > 0:
        success_rate = (stats['properties_enriched'] / stats['properties_processed']) * 100
        print(f"Success rate:              {success_rate:.1f}%")
    
    # Show sample enriched document
    print(f"\n{'='*70}")
    print("Sample Enriched Property")
    print(f"{'='*70}\n")
    
    for collection_name in collections:
        collection = db[collection_name]
        sample = collection.find_one({'lot_area': {'$exists': True}})
        if sample:
            # Remove _id for cleaner output
            sample.pop('_id', None)
            
            # Show new fields only
            new_fields = {
                k: v for k, v in sample.items() 
                if k in CADASTRAL_FIELDS + ADDRESS_FIELDS + ['enriched_at', 'enriched_source']
                or k.startswith('API_')
            }
            
            print(f"From collection: {collection_name}")
            print(f"Address: {sample.get('STREET_NO_1', '')} {sample.get('STREET_NAME', '')} {sample.get('STREET_TYPE', '')}, {sample.get('LOCALITY', '')}")
            print(f"\nNew fields added:")
            print(json.dumps(new_fields, indent=2, default=str))
            break
    
    print(f"\n{'='*70}")
    print("✓ Enrichment completed!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Enrichment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
