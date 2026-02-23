#!/usr/bin/env python3
"""
MongoDB Saver for Property Data
Saves extracted property data to MongoDB
"""

from pymongo import MongoClient
from datetime import datetime
import hashlib

class MongoDBSaver:
    def __init__(self, uri="mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/", database="property_data", collection="properties_for_sale"):
        self.uri = uri
        self.database_name = database
        self.collection_name = collection
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            # Test connection
            self.client.server_info()
            print(f"✓ Connected to MongoDB: {self.database_name}.{self.collection_name}")
        except Exception as e:
            print(f"✗ Failed to connect to MongoDB: {str(e)}")
            raise
    
    def save_property(self, property_data):
        """Save property data to MongoDB"""
        try:
            # Generate unique ID based on address
            property_id = self._generate_property_id(property_data)
            property_data['_id'] = property_id
            property_data['last_updated'] = datetime.now().isoformat()
            
            # Upsert (update if exists, insert if new)
            result = self.collection.replace_one(
                {'_id': property_id},
                property_data,
                upsert=True
            )
            
            if result.upserted_id:
                print(f"✓ Inserted new property: {property_id}")
            else:
                print(f"✓ Updated existing property: {property_id}")
            
            return True
        
        except Exception as e:
            print(f"✗ Error saving property: {str(e)}")
            return False
    
    def _generate_property_id(self, property_data):
        """Generate unique property ID from address or screenshot filename"""
        # Try to use address
        address = property_data.get('address')
        if address:
            # Create hash from address
            return hashlib.md5(address.lower().encode()).hexdigest()[:16]
        
        # Fall back to screenshot filename
        screenshot_file = property_data.get('screenshot_file', '')
        if screenshot_file:
            return f"km_{screenshot_file.replace('.png', '')}"
        
        # Last resort: timestamp
        return f"km_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def get_property_count(self):
        """Get count of properties in collection"""
        try:
            return self.collection.count_documents({})
        except Exception as e:
            print(f"Error getting count: {str(e)}")
            return 0
    
    def get_properties_by_suburb(self, suburb):
        """Get all properties for a specific suburb"""
        try:
            return list(self.collection.find({'suburb': suburb.lower()}))
        except Exception as e:
            print(f"Error getting properties: {str(e)}")
            return []
    
    def clear_collection(self):
        """Clear all documents in collection"""
        try:
            result = self.collection.delete_many({})
            print(f"✓ Cleared {result.deleted_count} documents from collection")
            return True
        except Exception as e:
            print(f"✗ Error clearing collection: {str(e)}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✓ MongoDB connection closed")

# Testing and example usage
if __name__ == "__main__":
    # Test MongoDB connection and save
    saver = MongoDBSaver()
    
    # Sample property data
    test_property = {
        'address': '123 Test Street, Robina QLD 4226',
        'price': {'display': '$750,000', 'value': 750000},
        'bedrooms': 4,
        'bathrooms': 2,
        'parking': 2,
        'property_type': 'House',
        'suburb': 'robina',
        'screenshot_file': 'test_property.png',
        'scraped_at': datetime.now().isoformat(),
        'scraping_method': 'keyboard_maestro'
    }
    
    # Save test property
    success = saver.save_property(test_property)
    
    if success:
        print("\n✓ Test property saved successfully!")
        print(f"Total properties in database: {saver.get_property_count()}")
    
    saver.close()
