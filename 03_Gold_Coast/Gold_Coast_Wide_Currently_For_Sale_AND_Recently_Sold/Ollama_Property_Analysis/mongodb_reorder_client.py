# Last Edit: 01/02/2026, Saturday, 8:18 am (Brisbane Time)
# MongoDB client for photo reordering operations

"""
MongoDB client for photo reordering operations.
Handles querying properties with ollama_image_analysis and updating with photo tours.
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime
from typing import List, Dict, Any
from config import MONGODB_URI, DATABASE_NAME, TARGET_SUBURBS
from logger import logger

class MongoDBReorderClient:
    """MongoDB client for photo reordering operations."""
    
    def __init__(self):
        """Initialize MongoDB client."""
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB."""
        try:
            logger.info(f"Connecting to MongoDB at {MONGODB_URI}")
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[DATABASE_NAME]
            
            logger.info(f"Connected to MongoDB: {DATABASE_NAME}")
            logger.info(f"Target suburbs: {', '.join(TARGET_SUBURBS)}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _build_suburb_query(self):
        """Build MongoDB query to filter by target suburbs."""
        return {
            "$or": [
                {"suburb": {"$in": TARGET_SUBURBS}},
                {"address.suburb": {"$in": TARGET_SUBURBS}},
                {"property_details.suburb": {"$in": TARGET_SUBURBS}},
                {"scraped_data.suburb": {"$in": TARGET_SUBURBS}}
            ]
        }
    
    def get_properties_for_reordering(self) -> List[Dict]:
        """
        Get properties that have ollama_image_analysis but no photo tour yet.
        
        Returns:
            List of properties ready for photo reordering
        """
        try:
            # Simple query - no suburb filter needed since we query each collection separately
            query = {
                "ollama_image_analysis": {
                    "$exists": True,
                    "$type": "array",
                    "$ne": []
                },
                "ollama_photo_tour_order": {"$exists": False}
            }
            
            # Get all matching properties from all suburb collections
            all_properties = []
            
            for suburb in TARGET_SUBURBS:
                try:
                    collection = self.db[suburb]
                    properties = list(collection.find(query))
                    
                    # Add suburb info to each property
                    for prop in properties:
                        prop['_collection'] = suburb
                    
                    all_properties.extend(properties)
                    logger.info(f"Found {len(properties)} properties for reordering in {suburb}")
                    
                except Exception as e:
                    logger.warning(f"Error querying {suburb}: {e}")
                    continue
            
            logger.info(f"Total properties for reordering: {len(all_properties)}")
            return all_properties
            
        except OperationFailure as e:
            logger.error(f"Failed to get properties for reordering: {e}")
            return []
    
    def count_properties_for_reordering(self) -> int:
        """
        Count properties that need photo reordering.
        
        Returns:
            Count of properties ready for reordering
        """
        try:
            query = {
                "ollama_image_analysis": {
                    "$exists": True,
                    "$type": "array",
                    "$ne": []
                },
                "ollama_photo_tour_order": {"$exists": False}
            }
            
            total_count = 0
            for suburb in TARGET_SUBURBS:
                try:
                    collection = self.db[suburb]
                    count = collection.count_documents(query)
                    total_count += count
                except Exception as e:
                    logger.warning(f"Error counting in {suburb}: {e}")
                    continue
            
            logger.info(f"Properties needing reordering: {total_count}")
            return total_count
            
        except OperationFailure as e:
            logger.error(f"Failed to count properties for reordering: {e}")
            return 0
    
    def count_properties_with_tours(self) -> int:
        """
        Count properties that already have photo tours.
        
        Returns:
            Count of properties with photo tours
        """
        try:
            query = {"ollama_photo_tour_order": {"$exists": True}}
            
            total_count = 0
            for suburb in TARGET_SUBURBS:
                try:
                    collection = self.db[suburb]
                    count = collection.count_documents(query)
                    total_count += count
                except Exception as e:
                    logger.warning(f"Error counting in {suburb}: {e}")
                    continue
            
            return total_count
            
        except OperationFailure as e:
            logger.error(f"Failed to count properties with tours: {e}")
            return 0
    
    def update_with_photo_tour(self, document_id, collection_name: str, 
                               photo_tour_order: List[Dict], 
                               tour_metadata: Dict,
                               processing_time: float = None) -> bool:
        """
        Update property with photo tour order.
        
        Args:
            document_id: Document _id
            collection_name: Name of the collection (suburb)
            photo_tour_order: List of ordered photos
            tour_metadata: Tour metadata
            processing_time: Processing duration in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.db[collection_name]
            
            reorder_status = {
                "photo_tour_created": True,
                "photos_in_tour": len(photo_tour_order),
                "reordered_at": datetime.utcnow(),
                "model": "llama3.2:3b",
                "engine": "ollama"
            }
            
            if processing_time is not None:
                reorder_status["processing_duration_seconds"] = processing_time
            
            # Add metadata to each photo in tour
            for photo in photo_tour_order:
                photo["tour_metadata"] = tour_metadata
            
            update_operation = {
                "$set": {
                    "ollama_photo_tour_order": photo_tour_order,
                    "ollama_photo_reorder_status": reorder_status
                }
            }
            
            result = collection.update_one(
                {"_id": document_id},
                update_operation
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated {collection_name} document {document_id} with photo tour ({len(photo_tour_order)} photos)")
                return True
            else:
                logger.warning(f"No document updated for {document_id} in {collection_name}")
                return False
            
        except OperationFailure as e:
            logger.error(f"Failed to update document with photo tour: {e}")
            return False
    
    def get_reordering_stats(self) -> Dict[str, Any]:
        """
        Get statistics about photo reordering progress.
        
        Returns:
            Dictionary with reordering statistics
        """
        try:
            stats = {
                "properties_with_analysis": 0,
                "properties_with_tours": 0,
                "properties_needing_reorder": 0,
                "by_suburb": {}
            }
            
            for suburb in TARGET_SUBURBS:
                try:
                    collection = self.db[suburb]
                    
                    # Count with analysis
                    with_analysis = collection.count_documents({
                        "ollama_image_analysis": {"$exists": True, "$ne": []}
                    })
                    
                    # Count with tours
                    with_tours = collection.count_documents({
                        "ollama_photo_tour_order": {"$exists": True}
                    })
                    
                    # Count needing reorder
                    needing_reorder = collection.count_documents({
                        "ollama_image_analysis": {"$exists": True, "$ne": []},
                        "ollama_photo_tour_order": {"$exists": False}
                    })
                    
                    stats["properties_with_analysis"] += with_analysis
                    stats["properties_with_tours"] += with_tours
                    stats["properties_needing_reorder"] += needing_reorder
                    
                    stats["by_suburb"][suburb] = {
                        "with_analysis": with_analysis,
                        "with_tours": with_tours,
                        "needing_reorder": needing_reorder
                    }
                    
                except Exception as e:
                    logger.warning(f"Error getting stats for {suburb}: {e}")
                    continue
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get reordering stats: {e}")
            return {
                "properties_with_analysis": 0,
                "properties_with_tours": 0,
                "properties_needing_reorder": 0,
                "by_suburb": {}
            }
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
