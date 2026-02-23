"""
MongoDB client for photo reordering system.
Handles database operations for properties_for_sale collection.
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson import ObjectId
from datetime import datetime
from config import MONGODB_URI
from logger import logger

class MongoDBReorderClient:
    """MongoDB client for photo reordering operations."""
    
    def __init__(self):
        """Initialize MongoDB client."""
        self.client = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB."""
        try:
            logger.info(f"Connecting to MongoDB at {MONGODB_URI}")
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client["property_data"]
            self.collection = self.db["properties_for_sale"]
            
            logger.info(f"Connected to MongoDB: property_data.properties_for_sale")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_all_documents_for_reordering(self):
        """
        Get all documents that have image_analysis but no photo_tour_order.
        
        Returns:
            List of documents that need photo reordering
        """
        try:
            query = {
                "image_analysis": {
                    "$exists": True,
                    "$type": "array",
                    "$ne": []
                },
                "photo_tour_order": {"$exists": False}
            }
            
            # Fetch all documents that need reordering
            documents = list(self.collection.find(query))
            
            logger.info(f"Found {len(documents)} documents for photo reordering")
            
            return documents
            
        except OperationFailure as e:
            logger.error(f"Failed to get documents for reordering: {e}")
            return []
    
    def update_with_photo_tour_order(self, document_id, photo_tour_order, worker_id=None, processing_time=None):
        """
        Update document with photo tour order.
        
        Args:
            document_id: Document _id
            photo_tour_order: List of photos in tour order with reorder_position
            worker_id: Worker ID that processed this document (optional)
            processing_time: Processing duration in seconds (optional)
            
        Returns:
            UpdateResult
        """
        try:
            reorder_status = {
                "photo_tour_created": True,
                "photos_in_tour": len(photo_tour_order),
                "reordered_at": datetime.utcnow()
            }
            
            if worker_id is not None:
                reorder_status["worker_id"] = worker_id
            if processing_time is not None:
                reorder_status["processing_duration_seconds"] = processing_time
            
            update_operation = {
                "$set": {
                    "photo_tour_order": photo_tour_order,
                    "photo_reorder_status": reorder_status
                }
            }
            
            result = self.collection.update_one(
                {"_id": document_id},
                update_operation
            )
            
            logger.info(f"Updated document {document_id} with {len(photo_tour_order)} photos in tour order")
            return result
            
        except OperationFailure as e:
            logger.error(f"Failed to update document with photo tour order: {e}")
            raise
    
    def count_documents_for_reordering(self):
        """
        Count documents that need photo reordering.
        
        Returns:
            Count of documents
        """
        try:
            query = {
                "image_analysis": {
                    "$exists": True,
                    "$type": "array",
                    "$ne": []
                },
                "photo_tour_order": {"$exists": False}
            }
            
            return self.collection.count_documents(query)
            
        except OperationFailure as e:
            logger.error(f"Failed to count documents for reordering: {e}")
            return 0
    
    def count_reordered_documents(self):
        """
        Count documents that have been reordered.
        
        Returns:
            Count of reordered documents
        """
        try:
            query = {
                "photo_tour_order": {"$exists": True}
            }
            
            return self.collection.count_documents(query)
            
        except OperationFailure as e:
            logger.error(f"Failed to count reordered documents: {e}")
            return 0
    
    def get_reordering_stats(self):
        """
        Get overall reordering statistics.
        
        Returns:
            Dictionary with reordering statistics
        """
        try:
            total = self.collection.count_documents({})
            reordered = self.count_reordered_documents()
            needs_reordering = self.count_documents_for_reordering()
            
            return {
                "total_documents": total,
                "reordered": reordered,
                "needs_reordering": needs_reordering
            }
            
        except OperationFailure as e:
            logger.error(f"Failed to get reordering stats: {e}")
            return {
                "total_documents": 0,
                "reordered": 0,
                "needs_reordering": 0
            }

    def get_document_by_id(self, object_id_str):
        """Retrieve a single document by its MongoDB _id.

        Args:
            object_id_str: 24-character hex string ObjectId

        Returns:
            Document dict or None
        """
        try:
            object_id = ObjectId(object_id_str)
            doc = self.collection.find_one({"_id": object_id})
            if doc:
                logger.info(f"Retrieved document with _id={object_id_str}")
            else:
                logger.warning(f"No document found with _id={object_id_str}")
            return doc
        except Exception as e:
            logger.error(f"Failed to retrieve document by _id={object_id_str}: {e}")
            return None

    def get_single_document_for_reordering(self):
        """Get a single document that requires photo reordering.

        This uses the same filter as get_all_documents_for_reordering
        but only returns the first matching document.
        """
        try:
            query = {
                "image_analysis": {
                    "$exists": True,
                    "$type": "array",
                    "$ne": []
                },
                "photo_tour_order": {"$exists": False}
            }

            doc = self.collection.find_one(query)
            if doc:
                logger.info(
                    "Retrieved one document that needs photo reordering: "
                    f"_id={doc.get('_id')}"
                )
            else:
                logger.info("No documents found that need photo reordering")
            return doc
        except OperationFailure as e:
            logger.error(f"Failed to retrieve document for reordering: {e}")
            return None
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
