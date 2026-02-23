"""
MongoDB enrichment client for property data enrichment.
Last Edit: 13/02/2026, 3:45 PM (Thursday) — Brisbane Time

Description: MongoDB client for reading properties from 8 suburb collections,
updating with enrichment data, and tracking progress.

Edit History:
- 13/02/2026 3:45 PM: Initial creation for production pipeline
"""

from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import time

from config import (
    COSMOS_CONNECTION_STRING, DATABASE_NAME, TARGET_SUBURBS,
    BATCH_SIZE
)
from logger import logger


class MongoDBEnrichmentClient:
    """
    Client for MongoDB operations in the enrichment pipeline.
    
    Handles:
    - Connecting to Azure Cosmos DB (MongoDB API)
    - Reading properties from 8 suburb collections
    - Updating properties with enrichment data
    - Progress tracking and resume capability
    - Error handling and retry logic
    """
    
    def __init__(self):
        """Initialize MongoDB connection."""
        if not COSMOS_CONNECTION_STRING:
            raise ValueError("COSMOS_CONNECTION_STRING not set in environment variables")
        
        self.connection_string = COSMOS_CONNECTION_STRING
        self.database_name = DATABASE_NAME
        self.client = None
        self.db = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            logger.info(f"Connecting to MongoDB database: {self.database_name}")
            
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[self.database_name]
            
            logger.info(f"✅ Successfully connected to MongoDB: {self.database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    # ========================================================================
    # PROPERTY RETRIEVAL
    # ========================================================================
    
    def get_properties_to_enrich(self, suburb: str, limit: int = None,
                                 skip_enriched: bool = True) -> List[Dict[str, Any]]:
        """
        Get properties from a suburb collection that need enrichment.
        
        Args:
            suburb: Suburb name (collection name)
            limit: Maximum number of properties to return
            skip_enriched: If True, skip properties already enriched
        
        Returns:
            List of property documents
        """
        try:
            collection = self.db[suburb]
            
            # Build query
            query = {}
            if skip_enriched:
                query['gpt_enrichment'] = {'$exists': False}
            
            # Get properties
            cursor = collection.find(query)
            
            if limit:
                cursor = cursor.limit(limit)
            
            properties = list(cursor)
            
            logger.info(f"Retrieved {len(properties)} properties from {suburb}")
            return properties
            
        except Exception as e:
            logger.error(f"Error retrieving properties from {suburb}: {e}")
            return []
    
    def get_all_properties_to_enrich(self, limit_per_suburb: int = None,
                                    skip_enriched: bool = True) -> List[Dict[str, Any]]:
        """
        Get properties from all 8 target suburbs.
        
        Args:
            limit_per_suburb: Maximum properties per suburb
            skip_enriched: If True, skip already enriched properties
        
        Returns:
            List of all properties with suburb info added
        """
        all_properties = []
        
        for suburb in TARGET_SUBURBS:
            logger.info(f"Fetching properties from {suburb}...")
            
            properties = self.get_properties_to_enrich(
                suburb, 
                limit=limit_per_suburb,
                skip_enriched=skip_enriched
            )
            
            # Add suburb info to each property
            for prop in properties:
                prop['_suburb_collection'] = suburb
            
            all_properties.extend(properties)
            
            logger.info(f"  → {len(properties)} properties from {suburb}")
        
        logger.info(f"Total properties to enrich: {len(all_properties)}")
        return all_properties
    
    def count_properties_to_enrich(self) -> Dict[str, int]:
        """
        Count properties needing enrichment in each suburb.
        
        Returns:
            Dictionary mapping suburb -> count
        """
        counts = {}
        
        for suburb in TARGET_SUBURBS:
            try:
                collection = self.db[suburb]
                count = collection.count_documents({'gpt_enrichment': {'$exists': False}})
                counts[suburb] = count
            except Exception as e:
                logger.error(f"Error counting properties in {suburb}: {e}")
                counts[suburb] = 0
        
        total = sum(counts.values())
        logger.info(f"Properties needing enrichment: {total} total")
        for suburb, count in counts.items():
            logger.info(f"  {suburb}: {count}")
        
        return counts
    
    # ========================================================================
    # PROPERTY UPDATE
    # ========================================================================
    
    def update_property_enrichment(self, property_id: str, suburb: str,
                                   gpt_enrichment: Dict[str, Any]) -> bool:
        """
        Update a property with enrichment data.
        
        Args:
            property_id: Property _id
            suburb: Suburb collection name
            gpt_enrichment: Enrichment results to store
        
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.db[suburb]
            
            # Add timestamp
            gpt_enrichment['enriched_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Update document
            result = collection.update_one(
                {'_id': property_id},
                {
                    '$set': {
                        'gpt_enrichment': enrichment_data,
                        'enrichment_status': 'completed'
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.debug(f"✅ Updated property {property_id} in {suburb}")
                return True
            else:
                logger.warning(f"No document modified for {property_id} in {suburb}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating property {property_id} in {suburb}: {e}")
            return False
    
    def mark_property_failed(self, property_id: str, suburb: str,
                            error_message: str) -> bool:
        """
        Mark a property as failed enrichment.
        
        Args:
            property_id: Property _id
            suburb: Suburb collection name
            error_message: Error description
        
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.db[suburb]
            
            result = collection.update_one(
                {'_id': property_id},
                {
                    '$set': {
                        'enrichment_status': 'failed',
                        'enrichment_error': error_message,
                        'enrichment_failed_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.debug(f"Marked property {property_id} as failed in {suburb}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error marking property {property_id} as failed: {e}")
            return False
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    def update_batch_enrichment(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple properties in batch.
        
        Args:
            updates: List of dicts with keys: property_id, suburb, gpt_enrichment
        
        Returns:
            Number of successful updates
        """
        success_count = 0
        
        for update in updates:
            property_id = update['property_id']
            suburb = update['suburb']
            gpt_enrichment = update['enrichment_data']
            
            if self.update_property_enrichment(property_id, suburb, gpt_enrichment):
                success_count += 1
        
        logger.info(f"Batch update: {success_count}/{len(updates)} successful")
        return success_count
    
    # ========================================================================
    # PROGRESS TRACKING
    # ========================================================================
    
    def get_enrichment_progress(self) -> Dict[str, Any]:
        """
        Get overall enrichment progress statistics.
        
        Returns:
            Dictionary with progress metrics
        """
        stats = {
            'by_suburb': {},
            'total_properties': 0,
            'enriched': 0,
            'failed': 0,
            'remaining': 0,
            'completion_percentage': 0.0
        }
        
        for suburb in TARGET_SUBURBS:
            try:
                collection = self.db[suburb]
                
                total = collection.count_documents({})
                enriched = collection.count_documents({'enrichment_status': 'completed'})
                failed = collection.count_documents({'enrichment_status': 'failed'})
                remaining = collection.count_documents({'gpt_enrichment': {'$exists': False}})
                
                stats['by_suburb'][suburb] = {
                    'total': total,
                    'enriched': enriched,
                    'failed': failed,
                    'remaining': remaining,
                    'completion_pct': (enriched / total * 100) if total > 0 else 0
                }
                
                stats['total_properties'] += total
                stats['enriched'] += enriched
                stats['failed'] += failed
                stats['remaining'] += remaining
                
            except Exception as e:
                logger.error(f"Error getting progress for {suburb}: {e}")
        
        if stats['total_properties'] > 0:
            stats['completion_percentage'] = (
                stats['enriched'] / stats['total_properties'] * 100
            )
        
        return stats
    
    def log_progress_summary(self):
        """Log a summary of enrichment progress."""
        stats = self.get_enrichment_progress()
        
        logger.info("=" * 60)
        logger.info("ENRICHMENT PROGRESS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Properties: {stats['total_properties']}")
        logger.info(f"Enriched: {stats['enriched']} ({stats['completion_percentage']:.1f}%)")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Remaining: {stats['remaining']}")
        logger.info("")
        logger.info("By Suburb:")
        
        for suburb, suburb_stats in stats['by_suburb'].items():
            logger.info(
                f"  {suburb:20s} | "
                f"Total: {suburb_stats['total']:4d} | "
                f"Done: {suburb_stats['enriched']:4d} | "
                f"Failed: {suburb_stats['failed']:3d} | "
                f"Remaining: {suburb_stats['remaining']:4d} | "
                f"{suburb_stats['completion_pct']:5.1f}%"
            )
        
        logger.info("=" * 60)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_property_by_id(self, property_id: str, suburb: str) -> Optional[Dict[str, Any]]:
        """
        Get a single property by ID.
        
        Args:
            property_id: Property _id
            suburb: Suburb collection name
        
        Returns:
            Property document or None
        """
        try:
            collection = self.db[suburb]
            property_doc = collection.find_one({'_id': property_id})
            return property_doc
        except Exception as e:
            logger.error(f"Error retrieving property {property_id}: {e}")
            return None
    
    def verify_collections_exist(self) -> bool:
        """
        Verify all target suburb collections exist.
        
        Returns:
            True if all collections exist, False otherwise
        """
        existing_collections = self.db.list_collection_names()
        
        missing = []
        for suburb in TARGET_SUBURBS:
            if suburb not in existing_collections:
                missing.append(suburb)
        
        if missing:
            logger.error(f"Missing collections: {missing}")
            return False
        
        logger.info(f"✅ All {len(TARGET_SUBURBS)} suburb collections exist")
        return True
    
    def get_sample_property(self, suburb: str) -> Optional[Dict[str, Any]]:
        """
        Get a sample property from a suburb for testing.
        
        Args:
            suburb: Suburb collection name
        
        Returns:
            Sample property document or None
        """
        try:
            collection = self.db[suburb]
            property_doc = collection.find_one({'gpt_enrichment': {'$exists': False}})
            return property_doc
        except Exception as e:
            logger.error(f"Error getting sample property from {suburb}: {e}")
            return None
    
    # ========================================================================
    # CONTEXT MANAGER SUPPORT
    # ========================================================================
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
