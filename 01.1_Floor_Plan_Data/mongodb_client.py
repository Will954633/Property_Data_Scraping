"""
MongoDB client module for floor plan analysis system.
"""
from pymongo import MongoClient
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME
from logger import logger


class MongoDBFloorPlanClient:
    """Client for MongoDB operations related to floor plan analysis."""
    
    def __init__(self):
        """Initialize MongoDB client."""
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        logger.info(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def get_property_with_floor_plans(self, address=None):
        """
        Get a single property that has floor plans.
        
        Args:
            address: Optional specific address to retrieve
            
        Returns:
            Property document or None
        """
        query = {"floor_plans": {"$exists": True, "$ne": []}}
        
        if address:
            query["address"] = address
        
        property_doc = self.collection.find_one(query)
        
        if property_doc:
            logger.info(f"Retrieved property: {property_doc.get('address', 'Unknown')}")
        else:
            logger.warning("No property with floor plans found")
        
        return property_doc
    
    def get_all_properties_with_floor_plans(self):
        """
        Get all properties that have floor plans.
        
        Returns:
            List of property documents
        """
        query = {"floor_plans": {"$exists": True, "$ne": []}}
        properties = list(self.collection.find(query))
        logger.info(f"Retrieved {len(properties)} properties with floor plans")
        return properties
    
    def update_floor_plan_analysis(self, address, analysis_data):
        """
        Update a property document with floor plan analysis data.
        
        Args:
            address: Property address
            analysis_data: Floor plan analysis data to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"address": address},
                {"$set": {"floor_plan_analysis": analysis_data}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated floor plan analysis for {address}")
                return True
            else:
                logger.warning(f"No document modified for {address}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating floor plan analysis for {address}: {e}")
            return False
    
    def get_property_by_address(self, address):
        """
        Get a property by its address.
        
        Args:
            address: Property address
            
        Returns:
            Property document or None
        """
        property_doc = self.collection.find_one({"address": address})
        
        if property_doc:
            logger.info(f"Retrieved property: {address}")
        else:
            logger.warning(f"Property not found: {address}")
        
        return property_doc
    
    def count_properties_with_floor_plans(self):
        """
        Count properties that have floor plans.
        
        Returns:
            Count of properties
        """
        count = self.collection.count_documents({"floor_plans": {"$exists": True, "$ne": []}})
        logger.info(f"Total properties with floor plans: {count}")
        return count
    
    def count_properties_with_analysis(self):
        """
        Count properties that have floor plan analysis.
        
        Returns:
            Count of properties
        """
        count = self.collection.count_documents({"floor_plan_analysis": {"$exists": True}})
        logger.info(f"Total properties with floor plan analysis: {count}")
        return count
    
    def close(self):
        """Close MongoDB connection."""
        self.client.close()
        logger.info("MongoDB connection closed")
