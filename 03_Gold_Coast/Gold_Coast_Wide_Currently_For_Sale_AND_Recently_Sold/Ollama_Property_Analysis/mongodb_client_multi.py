# Last Edit: 31/01/2026, Friday, 7:54 pm (Brisbane Time)
"""
MongoDB client module for Ollama property analysis system.
Handles multiple collections (one per suburb).
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime
from config import MONGODB_URI, DATABASE_NAME, TARGET_SUBURBS, OPENAI_MODEL
from logger import logger

class MongoDBClientMulti:
    """MongoDB client for managing multiple suburb collections."""
    
    def __init__(self):
        """Initialize MongoDB client."""
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB."""
        try:
            logger.info(f"Connecting to MongoDB at {MONGODB_URI}")
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, retryWrites=False)
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[DATABASE_NAME]
            
            logger.info(f"Connected to MongoDB: {DATABASE_NAME}")
            logger.info(f"Target suburb collections: {', '.join(TARGET_SUBURBS)}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_all_unprocessed_documents(self):
        """
        Get all unprocessed documents from all target suburb collections.
        
        Returns:
            List of tuples: (suburb_name, document)
        """
        all_documents = []
        
        for suburb in TARGET_SUBURBS:
            try:
                collection = self.db[suburb]
                
                # Query for unprocessed documents with images
                query = {
                    "$and": [
                        {
                            "$or": [
                                {"scraped_data.images": {"$exists": True, "$type": "array", "$ne": []}},
                                {"property_images": {"$exists": True, "$type": "array", "$ne": []}},
                                {"images": {"$exists": True, "$type": "array", "$ne": []}}
                            ]
                        },
                        {
                            "ollama_analysis.processed": {"$ne": True}
                        }
                    ]
                }
                
                documents = list(collection.find(query))
                logger.info(f"Found {len(documents)} unprocessed documents in {suburb}")
                
                # Add suburb name to each document tuple
                for doc in documents:
                    all_documents.append((suburb, doc))
                    
            except OperationFailure as e:
                logger.error(f"Failed to query {suburb} collection: {e}")
                continue
        
        logger.info(f"Total unprocessed documents across all suburbs: {len(all_documents)}")
        return all_documents
    
    def count_unprocessed_documents(self):
        """Count total unprocessed documents across all suburb collections."""
        total = 0
        for suburb in TARGET_SUBURBS:
            try:
                collection = self.db[suburb]
                query = {
                    "$and": [
                        {
                            "$or": [
                                {"scraped_data.images": {"$exists": True, "$type": "array", "$ne": []}},
                                {"property_images": {"$exists": True, "$type": "array", "$ne": []}},
                                {"images": {"$exists": True, "$type": "array", "$ne": []}}
                            ]
                        },
                        {"ollama_analysis.processed": {"$ne": True}}
                    ]
                }
                count = collection.count_documents(query)
                total += count
            except OperationFailure as e:
                logger.error(f"Failed to count documents in {suburb}: {e}")
                continue
        
        return total
    
    def count_processed_documents(self):
        """Count total processed documents across all suburb collections."""
        total = 0
        for suburb in TARGET_SUBURBS:
            try:
                collection = self.db[suburb]
                count = collection.count_documents({"ollama_analysis.processed": True})
                total += count
            except OperationFailure as e:
                logger.error(f"Failed to count processed documents in {suburb}: {e}")
                continue
        
        return total
    
    def update_with_ollama_analysis(self, suburb, document_id, image_analysis, property_data, worker_id=None, processing_time=None):
        """
        Update document with Ollama analysis results.
        
        Args:
            suburb: Suburb collection name
            document_id: Document _id
            image_analysis: List of image analysis data
            property_data: Extracted property valuation data
            worker_id: Worker ID (optional)
            processing_time: Processing duration in seconds (optional)
        """
        try:
            collection = self.db[suburb]
            
            ollama_analysis = {
                "processed": True,
                "images_analyzed": len(image_analysis),
                "processed_at": datetime.utcnow(),
                "model": OPENAI_MODEL,
                "engine": "openai"
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
            
            result = collection.update_one({"_id": document_id}, update_operation)
            
            logger.info(f"Updated document {document_id} in {suburb} with Ollama analysis")
            return result
            
        except OperationFailure as e:
            logger.error(f"Failed to update document in {suburb}: {e}")
            raise
    
    def get_processing_stats(self):
        """Get processing statistics for all suburb collections."""
        stats = {
            "total_documents_in_target_suburbs": 0,
            "processed": 0,
            "unprocessed": 0,
            "with_water_views": 0,
            "by_suburb": {}
        }
        
        for suburb in TARGET_SUBURBS:
            try:
                collection = self.db[suburb]
                
                total = collection.count_documents({})
                processed = collection.count_documents({"ollama_analysis.processed": True})
                water_views = collection.count_documents({"ollama_property_data.outdoor.natural_water_view": True})
                
                stats["total_documents_in_target_suburbs"] += total
                stats["processed"] += processed
                stats["with_water_views"] += water_views
                stats["by_suburb"][suburb] = total
                
            except OperationFailure as e:
                logger.error(f"Failed to get stats for {suburb}: {e}")
                stats["by_suburb"][suburb] = 0
                continue
        
        stats["unprocessed"] = self.count_unprocessed_documents()
        
        return stats
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
