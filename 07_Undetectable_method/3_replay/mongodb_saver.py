#!/usr/bin/env python3
"""
MongoDB Saver - Handles saving property data to MongoDB

Database: property_data
Collection: properties_for_sale
"""

import sys
from pathlib import Path
from datetime import datetime
import hashlib
from pymongo import MongoClient, errors
from typing import Dict, List, Optional
import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class MongoDBSaver:
    """Handles MongoDB operations for property data"""
    
    def __init__(self, config_path="../config.yaml"):
        self.config = self._load_config(config_path)
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _load_config(self, config_path):
        """Load configuration"""
        # Get the project root (07_Undetectable_method)
        project_root = Path(__file__).parent.parent
        config_file = project_root / "config.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _connect(self):
        """Connect to MongoDB"""
        mongo_config = self.config['mongodb']
        
        try:
            self.client = MongoClient(
                mongo_config['uri'],
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            self.client.server_info()
            
            self.db = self.client[mongo_config['database']]
            self.collection = self.db[mongo_config['collection']]
            
            print(f"✅ Connected to MongoDB: {mongo_config['database']}.{mongo_config['collection']}")
            
        except errors.ServerSelectionTimeoutError:
            print(f"❌ Error: Could not connect to MongoDB at {mongo_config['uri']}")
            print("   Make sure MongoDB is running:")
            print("   brew services start mongodb-community")
            raise
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            raise
    
    def _generate_id(self, property_url: str) -> str:
        """Generate unique ID from property URL"""
        return hashlib.md5(property_url.encode()).hexdigest()
    
    def save_property(self, property_data: Dict) -> bool:
        """
        Save a single property to MongoDB
        
        Args:
            property_data: Property dictionary
            
        Returns:
            bool: True if saved successfully
        """
        if not property_data.get('property_url'):
            print("⚠️  Warning: Property missing URL, cannot save")
            return False
        
        # Generate unique ID
        property_id = self._generate_id(property_data['property_url'])
        property_data['_id'] = property_id
        
        # Add timestamp
        property_data['scraped_at'] = datetime.now().isoformat()
        
        try:
            # Insert or update (upsert)
            result = self.collection.replace_one(
                {'_id': property_id},
                property_data,
                upsert=True
            )
            
            if result.upserted_id:
                print(f"  ✓ Saved new property: {property_data.get('address', {}).get('full', 'Unknown')}")
            else:
                print(f"  ↻ Updated property: {property_data.get('address', {}).get('full', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Error saving property: {e}")
            return False
    
    def save_properties(self, properties: List[Dict]) -> int:
        """
        Save multiple properties to MongoDB
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            int: Number of properties saved successfully
        """
        saved_count = 0
        
        for prop in properties:
            if self.save_property(prop):
                saved_count += 1
        
        return saved_count
    
    def get_property_count(self) -> int:
        """Get total number of properties in collection"""
        return self.collection.count_documents({})
    
    def get_properties_by_suburb(self, suburb: str) -> List[Dict]:
        """Get all properties for a specific suburb"""
        return list(self.collection.find({'suburb': suburb.lower()}))
    
    def clear_collection(self) -> int:
        """
        Clear all documents from the collection
        
        Returns:
            int: Number of documents deleted
        """
        result = self.collection.delete_many({})
        return result.deleted_count
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✓ MongoDB connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def test_connection():
    """Test MongoDB connection"""
    print("\n" + "="*70)
    print("  TESTING MONGODB CONNECTION")
    print("="*70)
    
    try:
        with MongoDBSaver() as saver:
            print(f"\n✅ Successfully connected!")
            print(f"📊 Current property count: {saver.get_property_count()}")
            
            # Test saving a sample property
            test_property = {
                'property_url': 'https://test.com/property/123',
                'address': {
                    'full': 'Test Address, Test Suburb QLD 4000',
                    'suburb': 'Test Suburb'
                },
                'price': {
                    'display': '$500,000',
                    'value': 500000
                },
                'suburb': 'test',
                'session_used': 'test_session'
            }
            
            print("\n📝 Testing property save...")
            if saver.save_property(test_property):
                print("✅ Test property saved successfully!")
                
                # Delete test property
                saver.collection.delete_one({'_id': saver._generate_id(test_property['property_url'])})
                print("✓ Test property cleaned up")
            
            print("\n" + "="*70)
            print("✅ MONGODB TEST PASSED")
            print("="*70)
            
    except Exception as e:
        print(f"\n❌ MongoDB test failed: {e}")
        print("\nMake sure MongoDB is running:")
        print("  brew services start mongodb-community")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()
