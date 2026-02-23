#!/usr/bin/env python3
"""
Add complete_address field to all MongoDB documents
Builds standardized address from cadastral components
"""

import os
import sys
from pymongo import MongoClient
from datetime import datetime

class AddressFieldBuilder:
    """Add complete_address field to all documents"""
    
    def __init__(self):
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
        self.db_name = 'Gold_Coast'
        
        # Connect to MongoDB
        print(f"Connecting to MongoDB...")
        self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=10000)
        self.db = self.mongo_client[self.db_name]
        self.mongo_client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {self.db_name}\n")
    
    def build_complete_address(self, doc) -> str:
        """Build standardized complete address from cadastral fields"""
        parts = []
        
        # Unit number (if present)
        if doc.get('UNIT_NUMBER'):
            parts.append(f"{doc['UNIT_NUMBER']}/")
        
        # Street number
        if doc.get('STREET_NO_1'):
            parts.append(str(doc['STREET_NO_1']))
        
        # Street name and type
        if doc.get('STREET_NAME'):
            street = str(doc['STREET_NAME'])
            if doc.get('STREET_TYPE'):
                street += f" {doc['STREET_TYPE']}"
            parts.append(street)
        
        # Locality
        if doc.get('LOCALITY'):
            parts.append(doc['LOCALITY'])
        
        # State
        parts.append("QLD")
        
        # Postcode
        if doc.get('POSTCODE'):
            parts.append(str(doc['POSTCODE']))
        
        # Join and normalize
        address = ' '.join(parts)
        address = address.replace(' /', '/').replace('/ ', '/')
        address = ' '.join(address.split())  # Remove extra spaces
        return address.upper()
    
    def process_collection(self, collection_name):
        """Add complete_address to all documents in a collection"""
        collection = self.db[collection_name]
        
        # Get total count
        total = collection.count_documents({})
        
        if total == 0:
            return {'collection': collection_name, 'total': 0, 'updated': 0}
        
        print(f"\nProcessing: {collection_name} ({total:,} documents)")
        
        # Get all documents
        updated_count = 0
        for i, doc in enumerate(collection.find(), 1):
            # Build complete address
            complete_address = self.build_complete_address(doc)
            
            # Update document
            collection.update_one(
                {'_id': doc['_id']},
                {'$set': {'complete_address': complete_address}}
            )
            updated_count += 1
            
            # Progress updates
            if i % 1000 == 0 or i == total:
                percent = (i / total * 100)
                print(f"  Progress: {i:,}/{total:,} ({percent:.1f}%)")
        
        print(f"  ✓ Updated {updated_count:,} documents")
        
        return {
            'collection': collection_name,
            'total': total,
            'updated': updated_count
        }
    
    def run(self):
        """Main process"""
        print(f"{'='*70}")
        print(f"ADDING complete_address FIELD TO ALL DOCUMENTS")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # Get all collections
        collections = [c for c in self.db.list_collection_names() if c != 'system.indexes']
        print(f"Found {len(collections)} collections\n")
        
        # Process each collection
        results = []
        for coll in sorted(collections):
            result = self.process_collection(coll)
            results.append(result)
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        total_docs = sum(r['total'] for r in results)
        total_updated = sum(r['updated'] for r in results)
        
        print(f"\n{'='*70}")
        print(f"COMPLETE")
        print(f"{'='*70}")
        print(f"Collections processed: {len(collections)}")
        print(f"Total documents:       {total_docs:,}")
        print(f"Documents updated:     {total_updated:,}")
        print(f"Duration:              {duration}")
        print(f"{'='*70}\n")
        
        # Sample addresses
        print("Sample complete_address values:")
        print("="*70)
        for coll in collections[:3]:
            sample = self.db[coll].find_one({'complete_address': {'$exists': True}})
            if sample:
                print(f"{coll}: {sample.get('complete_address')}")
        
        print(f"\n✓ All documents now have complete_address field")
        print(f"✓ Ready for GCS import matching")


if __name__ == "__main__":
    try:
        builder = AddressFieldBuilder()
        builder.run()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
