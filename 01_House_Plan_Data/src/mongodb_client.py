"""
MongoDB client module for property valuation data extraction system.
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME
from logger import logger

class MongoDBClient:
    """MongoDB client for managing database operations."""
    
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
            
            self.db = self.client[DATABASE_NAME]
            self.collection = self.db[COLLECTION_NAME]
            
            logger.info(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_documents_with_images(self, limit=None):
        """
        Query documents that have images field populated.
        Supports both scraped_data.images and property_images formats.
        
        Args:
            limit: Maximum number of documents to return (None for all)
            
        Returns:
            Cursor of documents with images
        """
        try:
            query = {
                "$or": [
                    {
                        "scraped_data.images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    },
                    {
                        "property_images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    }
                ],
                "processing_status.images_processed": {"$ne": True}
            }
            
            if limit:
                cursor = self.collection.find(query).limit(limit)
            else:
                cursor = self.collection.find(query)
            
            count = self.collection.count_documents(query)
            logger.info(f"Found {count} documents with images to process")
            
            return cursor
            
        except OperationFailure as e:
            logger.error(f"Failed to query documents: {e}")
            raise
    
    def update_document(self, document_id, update_data):
        """
        Update a document with extracted data.
        
        Args:
            document_id: Document _id
            update_data: Dictionary containing update operations
            
        Returns:
            UpdateResult
        """
        try:
            result = self.collection.update_one(
                {"_id": document_id},
                update_data
            )
            return result
            
        except OperationFailure as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            raise
    
    def update_with_house_plans(self, document_id, house_plan_data, property_data, house_plan_urls, worker_id=None, processing_time=None):
        """
        Update document when house plans are found.
        
        Args:
            document_id: Document _id
            house_plan_data: House plan information
            property_data: Extracted property valuation data
            house_plan_urls: List of house plan URLs to remove from images
            worker_id: Worker ID that processed this document (optional)
            processing_time: Processing duration in seconds (optional)
            
        Returns:
            UpdateResult
        """
        try:
            processing_status = {
                "images_processed": True,
                "house_plans_found": True,
                "floor_size_extracted": house_plan_data.get("floor_area_sqm") is not None,
                "processed_at": datetime.utcnow()
            }
            
            if worker_id is not None:
                processing_status["worker_id"] = worker_id
            if processing_time is not None:
                processing_status["processing_duration_seconds"] = processing_time
            
            update_operation = {
                "$set": {
                    "house_plan": house_plan_data,
                    "property_valuation_data": property_data,
                    "processing_status": processing_status
                },
                "$pull": {
                    "images": {"$in": house_plan_urls}
                }
            }
            
            result = self.collection.update_one(
                {"_id": document_id},
                update_operation
            )
            
            logger.info(f"Updated document {document_id} with house plans")
            return result
            
        except OperationFailure as e:
            logger.error(f"Failed to update document with house plans: {e}")
            raise
    
    def update_without_house_plans(self, document_id, property_data, worker_id=None, processing_time=None):
        """
        Update document when no house plans are found.
        
        Args:
            document_id: Document _id
            property_data: Extracted property valuation data
            worker_id: Worker ID that processed this document (optional)
            processing_time: Processing duration in seconds (optional)
            
        Returns:
            UpdateResult
        """
        try:
            processing_status = {
                "images_processed": True,
                "house_plans_found": False,
                "processed_at": datetime.utcnow()
            }
            
            if worker_id is not None:
                processing_status["worker_id"] = worker_id
            if processing_time is not None:
                processing_status["processing_duration_seconds"] = processing_time
            
            update_operation = {
                "$set": {
                    "property_valuation_data": property_data,
                    "processing_status": processing_status
                }
            }
            
            result = self.collection.update_one(
                {"_id": document_id},
                update_operation
            )
            
            logger.info(f"Updated document {document_id} without house plans")
            return result
            
        except OperationFailure as e:
            logger.error(f"Failed to update document: {e}")
            raise
    
    def update_with_image_analysis(self, document_id, image_analysis, property_data, worker_id=None, processing_time=None):
        """
        Update document with image analysis, rankings, and descriptions.
        
        Args:
            document_id: Document _id
            image_analysis: List of image analysis data with rankings and descriptions
            property_data: Extracted property valuation data
            worker_id: Worker ID that processed this document (optional)
            processing_time: Processing duration in seconds (optional)
            
        Returns:
            UpdateResult
        """
        try:
            processing_status = {
                "images_processed": True,
                "images_analyzed": len(image_analysis),
                "processed_at": datetime.utcnow()
            }
            
            if worker_id is not None:
                processing_status["worker_id"] = worker_id
            if processing_time is not None:
                processing_status["processing_duration_seconds"] = processing_time
            
            update_operation = {
                "$set": {
                    "image_analysis": image_analysis,
                    "property_valuation_data": property_data,
                    "processing_status": processing_status
                }
            }
            
            result = self.collection.update_one(
                {"_id": document_id},
                update_operation
            )
            
            logger.info(f"Updated document {document_id} with {len(image_analysis)} analyzed images")
            return result
            
        except OperationFailure as e:
            logger.error(f"Failed to update document with image analysis: {e}")
            raise
    
    def get_total_documents(self):
        """Get total count of documents in collection."""
        try:
            return self.collection.count_documents({})
        except OperationFailure as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    def get_documents_with_images_count(self):
        """Get count of documents with images."""
        try:
            query = {
                "$or": [
                    {
                        "scraped_data.images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    },
                    {
                        "property_images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    }
                ]
            }
            return self.collection.count_documents(query)
        except OperationFailure as e:
            logger.error(f"Failed to count documents with images: {e}")
            return 0
    
    def get_unprocessed_batch(self, batch_size=100):
        """
        Get a batch of unprocessed documents atomically.
        Supports both scraped_data.images and property_images formats.
        
        Args:
            batch_size: Number of documents to retrieve
            
        Returns:
            List of documents
        """
        try:
            query = {
                "$or": [
                    {
                        "scraped_data.images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    },
                    {
                        "property_images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    }
                ],
                "processing_status.images_processed": {"$ne": True}
            }
            
            # Get batch of documents
            documents = list(self.collection.find(query).limit(batch_size))
            
            return documents
            
        except OperationFailure as e:
            logger.error(f"Failed to get unprocessed batch: {e}")
            raise
    
    def get_all_unprocessed_documents(self):
        """
        Get all unprocessed documents at once (for batch creation).
        Supports both scraped_data.images and property_images formats.
        
        Returns:
            List of all unprocessed documents
        """
        try:
            query = {
                "$or": [
                    {
                        "scraped_data.images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    },
                    {
                        "property_images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    }
                ],
                "processing_status.images_processed": {"$ne": True}
            }
            
            # Fetch all unprocessed documents
            documents = list(self.collection.find(query))
            
            return documents
            
        except OperationFailure as e:
            logger.error(f"Failed to get all unprocessed documents: {e}")
            return []
    
    def count_unprocessed_documents(self):
        """
        Count documents that need processing.
        Supports both scraped_data.images and property_images formats.
        
        Returns:
            Count of unprocessed documents
        """
        try:
            query = {
                "$or": [
                    {
                        "scraped_data.images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    },
                    {
                        "property_images": {
                            "$exists": True,
                            "$type": "array",
                            "$ne": []
                        }
                    }
                ],
                "processing_status.images_processed": {"$ne": True}
            }
            
            return self.collection.count_documents(query)
            
        except OperationFailure as e:
            logger.error(f"Failed to count unprocessed documents: {e}")
            return 0
    
    def count_processed_documents(self):
        """
        Count documents that have been processed.
        
        Returns:
            Count of processed documents
        """
        try:
            query = {
                "processing_status.images_processed": True
            }
            
            return self.collection.count_documents(query)
            
        except OperationFailure as e:
            logger.error(f"Failed to count processed documents: {e}")
            return 0
    
    def get_processing_stats(self):
        """
        Get overall processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        try:
            total = self.get_total_documents()
            processed = self.count_processed_documents()
            unprocessed = self.count_unprocessed_documents()
            
            # Count house plans found
            house_plans_query = {
                "processing_status.house_plans_found": True
            }
            house_plans_found = self.collection.count_documents(house_plans_query)
            
            # Count with floor area
            floor_area_query = {
                "processing_status.floor_size_extracted": True
            }
            with_floor_area = self.collection.count_documents(floor_area_query)
            
            # Count with water views
            water_views_query = {
                "property_valuation_data.outdoor.natural_water_view": True
            }
            with_water_views = self.collection.count_documents(water_views_query)
            
            return {
                "total_documents": total,
                "processed": processed,
                "unprocessed": unprocessed,
                "house_plans_found": house_plans_found,
                "with_floor_area": with_floor_area,
                "with_water_views": with_water_views
            }
            
        except OperationFailure as e:
            logger.error(f"Failed to get processing stats: {e}")
            return {
                "total_documents": 0,
                "processed": 0,
                "unprocessed": 0,
                "house_plans_found": 0,
                "with_floor_area": 0,
                "with_water_views": 0
            }
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
