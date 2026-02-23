# Last Edit: 31/01/2026, Friday, 7:42 pm (Brisbane Time)
"""
MongoDB client module for Ollama property analysis system.
Includes suburb filtering for target Gold Coast suburbs.
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME, TARGET_SUBURBS
from logger import logger

class MongoDBClient:
    """MongoDB client for managing database operations with suburb filtering."""
    
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
            logger.info(f"Target suburbs (collections): {', '.join(TARGET_SUBURBS)}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _build_suburb_query(self):
        """
        Build MongoDB query to filter by target suburbs.
        
        Returns:
            Dictionary with suburb filter query
        """
        # Try multiple possible field names for suburb
        return {
            "$or": [
                {"suburb": {"$in": TARGET_SUBURBS}},
                {"address.suburb": {"$in": TARGET_SUBURBS}},
                {"property_details.suburb": {"$in": TARGET_SUBURBS}},
                {"scraped_data.suburb": {"$in": TARGET_SUBURBS}}
            ]
        }
    
    def get_all_unprocessed_documents(self):
        """
        Get all unprocessed documents from target suburbs.
        Supports multiple image field formats.
        
        Returns:
            List of all unprocessed documents from target suburbs
        """
        try:
            # Build query for unprocessed documents with images in target suburbs
            suburb_query = self._build_suburb_query()
            
            query = {
                "$and": [
                    suburb_query,
                    {
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
                            },
                            {
                                "images": {
                                    "$exists": True,
                                    "$type": "array",
                                    "$ne": []
                                }
                            }
                        ]
                    },
                    {
                        "ollama_analysis.processed": {"$ne": True}
                    }
                ]
            }
            
            # Fetch all unprocessed documents
            documents = list(self.collection.find(query))
            
            logger.info(f"Found {len(documents)} unprocessed documents in target suburbs")
            
            return documents
            
        except OperationFailure as e:
            logger.error(f"Failed to get all unprocessed documents: {e}")
            return []
    
    def count_unprocessed_documents(self):
        """
        Count documents that need processing in target suburbs.
        
        Returns:
            Count of unprocessed documents
        """
        try:
            suburb_query = self._build_suburb_query()
            
            query = {
                "$and": [
                    suburb_query,
                    {
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
                            },
                            {
                                "images": {
                                    "$exists": True,
                                    "$type": "array",
                                    "$ne": []
                                }
                            }
                        ]
                    },
                    {
                        "ollama_analysis.processed": {"$ne": True}
                    }
                ]
            }
            
            count = self.collection.count_documents(query)
            logger.info(f"Unprocessed documents in target suburbs: {count}")
            
            return count
            
        except OperationFailure as e:
            logger.error(f"Failed to count unprocessed documents: {e}")
            return 0
    
    def count_processed_documents(self):
        """
        Count documents that have been processed by Ollama.
        
        Returns:
            Count of processed documents
        """
        try:
            suburb_query = self._build_suburb_query()
            
            query = {
                "$and": [
                    suburb_query,
                    {
                        "ollama_analysis.processed": True
                    }
                ]
            }
            
            return self.collection.count_documents(query)
            
        except OperationFailure as e:
            logger.error(f"Failed to count processed documents: {e}")
            return 0
    
    def update_with_ollama_analysis(self, document_id, image_analysis, property_data, worker_id=None, processing_time=None):
        """
        Update document with Ollama analysis results.
        
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
            ollama_analysis = {
                "processed": True,
                "images_analyzed": len(image_analysis),
                "processed_at": datetime.utcnow(),
                "model": "llama3.2-vision:11b",
                "engine": "ollama"
            }
            
            if worker_id is not None:
                ollama_analysis["worker_id"] = worker_id
            if processing_time is not None:
                ollama_analysis["processing_duration_seconds"] = processing_time
            
            update_operation = {
                "$set": {
                    "ollama_analysis": ollama_analysis,
                    "ollama_image_analysis": image_analysis,
                    "ollama_property_data": property_data
                }
            }
            
            result = self.collection.update_one(
                {"_id": document_id},
                update_operation
            )
            
            logger.info(f"Updated document {document_id} with Ollama analysis ({len(image_analysis)} images)")
            return result
            
        except OperationFailure as e:
            logger.error(f"Failed to update document with Ollama analysis: {e}")
            raise
    
    def get_processing_stats(self):
        """
        Get overall processing statistics for target suburbs.
        
        Returns:
            Dictionary with processing statistics
        """
        try:
            suburb_query = self._build_suburb_query()
            
            # Total documents in target suburbs
            total = self.collection.count_documents(suburb_query)
            
            # Processed by Ollama
            processed_query = {
                "$and": [
                    suburb_query,
                    {"ollama_analysis.processed": True}
                ]
            }
            processed = self.collection.count_documents(processed_query)
            
            # Unprocessed
            unprocessed = self.count_unprocessed_documents()
            
            # Count with water views
            water_views_query = {
                "$and": [
                    suburb_query,
                    {"ollama_property_data.outdoor.natural_water_view": True}
                ]
            }
            with_water_views = self.collection.count_documents(water_views_query)
            
            # Count by suburb
            suburb_counts = {}
            for suburb in TARGET_SUBURBS:
                suburb_specific_query = {
                    "$or": [
                        {"suburb": suburb},
                        {"address.suburb": suburb},
                        {"property_details.suburb": suburb},
                        {"scraped_data.suburb": suburb}
                    ]
                }
                count = self.collection.count_documents(suburb_specific_query)
                suburb_counts[suburb] = count
            
            return {
                "total_documents_in_target_suburbs": total,
                "processed": processed,
                "unprocessed": unprocessed,
                "with_water_views": with_water_views,
                "by_suburb": suburb_counts
            }
            
        except OperationFailure as e:
            logger.error(f"Failed to get processing stats: {e}")
            return {
                "total_documents_in_target_suburbs": 0,
                "processed": 0,
                "unprocessed": 0,
                "with_water_views": 0,
                "by_suburb": {}
            }
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
