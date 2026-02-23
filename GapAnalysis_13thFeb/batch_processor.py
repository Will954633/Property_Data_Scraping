"""
Batch processor for parallel property enrichment.
Last Edit: 13/02/2026, 3:49 PM (Thursday) — Brisbane Time

Description: Parallel batch processing with worker pool for enriching
multiple properties simultaneously. Includes progress tracking, error handling,
and resume capability.

Edit History:
- 13/02/2026 3:49 PM: Initial creation for production pipeline
"""

import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from gpt_enrichment_client import GPTEnrichmentClient
from mongodb_enrichment_client import MongoDBEnrichmentClient
from config import NUM_WORKERS, BATCH_SIZE
from logger import logger, get_worker_logger, log_enrichment_start, log_enrichment_success, log_enrichment_error


class BatchProcessor:
    """
    Batch processor for parallel property enrichment.
    
    Features:
    - Parallel processing with configurable worker pool
    - Progress tracking and statistics
    - Error handling and retry logic
    - Resume capability (skip already enriched)
    - Thread-safe operations
    """
    
    def __init__(self, num_workers: int = None):
        """
        Initialize batch processor.
        
        Args:
            num_workers: Number of parallel workers (default from config)
        """
        self.num_workers = num_workers or NUM_WORKERS
        self.gpt_client = GPTEnrichmentClient()
        self.db_client = MongoDBEnrichmentClient()
        
        # Thread-safe counters
        self.lock = Lock()
        self.stats = {
            'total': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        logger.info(f"Initialized batch processor with {self.num_workers} workers")
    
    # ========================================================================
    # SINGLE PROPERTY ENRICHMENT
    # ========================================================================
    
    def enrich_single_property(self, property_data: Dict[str, Any], 
                               worker_id: int = 0) -> Dict[str, Any]:
        """
        Enrich a single property with all 7 enrichment methods.
        
        Args:
            property_data: Property document from MongoDB
            worker_id: Worker ID for logging
        
        Returns:
            Dictionary with enrichment results
        """
        worker_logger = get_worker_logger(worker_id)
        
        property_id = property_data.get('_id', 'unknown')
        address = property_data.get('address', 'unknown')
        suburb = property_data.get('_suburb_collection', 'unknown')
        
        worker_logger.info(f"Processing: {address}")
        log_enrichment_start(property_id, address)
        
        enrichment_results = {
            'property_id': str(property_id),
            'address': address,
            'suburb': suburb
        }
        
        try:
            # Method 1: Building Condition
            worker_logger.debug("Enriching: building_condition")
            enrichment_results['building_condition'] = self.gpt_client.enrich_building_condition(property_data)
            
            # Method 2: Building Age
            worker_logger.debug("Enriching: building_age")
            enrichment_results['building_age'] = self.gpt_client.enrich_building_age(property_data)
            
            # Method 3: Busy Road (OpenStreetMap)
            worker_logger.debug("Enriching: busy_road")
            enrichment_results['busy_road'] = self.gpt_client.enrich_busy_road(property_data)
            
            # Method 4: Corner Block (Google Maps + GPT fallback)
            worker_logger.debug("Enriching: corner_block")
            enrichment_results['corner_block'] = self.gpt_client.enrich_corner_block(property_data)
            
            # Method 5: Parking
            worker_logger.debug("Enriching: parking")
            enrichment_results['parking'] = self.gpt_client.enrich_parking(property_data)
            
            # Method 6: Outdoor Entertainment
            worker_logger.debug("Enriching: outdoor_entertainment")
            enrichment_results['outdoor_entertainment'] = self.gpt_client.enrich_outdoor_entertainment(property_data)
            
            # Method 7: Renovation Status
            worker_logger.debug("Enriching: renovation_status")
            enrichment_results['renovation_status'] = self.gpt_client.enrich_renovation_status(property_data)
            
            # Bonus: North Facing (optional)
            worker_logger.debug("Enriching: north_facing")
            enrichment_results['north_facing'] = self.gpt_client.enrich_north_facing(property_data)
            
            worker_logger.info(f"✅ Completed: {address}")
            
            return {
                'success': True,
                'property_id': str(property_id),
                'suburb': suburb,
                'enrichment_data': enrichment_results
            }
            
        except Exception as e:
            error_msg = str(e)
            worker_logger.error(f"❌ Failed: {address} - {error_msg}")
            log_enrichment_error(property_id, address, error_msg)
            
            return {
                'success': False,
                'property_id': str(property_id),
                'suburb': suburb,
                'error': error_msg
            }
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def process_batch(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of properties in parallel.
        
        Args:
            properties: List of property documents
        
        Returns:
            Dictionary with batch results and statistics
        """
        if not properties:
            logger.warning("No properties to process")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"Processing batch of {len(properties)} properties with {self.num_workers} workers")
        
        batch_results = {
            'success': 0,
            'failed': 0,
            'total': len(properties)
        }
        
        # Process properties in parallel
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all tasks
            future_to_property = {}
            for idx, property_data in enumerate(properties):
                worker_id = (idx % self.num_workers) + 1
                future = executor.submit(self.enrich_single_property, property_data, worker_id)
                future_to_property[future] = property_data
            
            # Collect results as they complete
            for future in as_completed(future_to_property):
                property_data = future_to_property[future]
                
                try:
                    result = future.result()
                    
                    if result['success']:
                        # Update MongoDB
                        success = self.db_client.update_property_enrichment(
                            result['property_id'],
                            result['suburb'],
                            result['enrichment_data']
                        )
                        
                        if success:
                            batch_results['success'] += 1
                            with self.lock:
                                self.stats['successful'] += 1
                                self.stats['processed'] += 1
                        else:
                            batch_results['failed'] += 1
                            with self.lock:
                                self.stats['failed'] += 1
                                self.stats['processed'] += 1
                    else:
                        # Mark as failed in MongoDB
                        self.db_client.mark_property_failed(
                            result['property_id'],
                            result['suburb'],
                            result.get('error', 'Unknown error')
                        )
                        
                        batch_results['failed'] += 1
                        with self.lock:
                            self.stats['failed'] += 1
                            self.stats['processed'] += 1
                
                except Exception as e:
                    logger.error(f"Error processing property: {e}")
                    batch_results['failed'] += 1
                    with self.lock:
                        self.stats['failed'] += 1
                        self.stats['processed'] += 1
        
        logger.info(
            f"Batch complete: {batch_results['success']} successful, "
            f"{batch_results['failed']} failed, "
            f"{batch_results['total']} total"
        )
        
        return batch_results
    
    # ========================================================================
    # FULL PROCESSING
    # ========================================================================
    
    def process_all_properties(self, limit_per_suburb: int = None,
                               skip_enriched: bool = True) -> Dict[str, Any]:
        """
        Process all properties from all 8 suburbs.
        
        Args:
            limit_per_suburb: Limit properties per suburb (for testing)
            skip_enriched: Skip already enriched properties
        
        Returns:
            Dictionary with overall statistics
        """
        logger.info("=" * 60)
        logger.info("STARTING FULL ENRICHMENT PROCESS")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Get all properties to enrich
        logger.info("Fetching properties from database...")
        properties = self.db_client.get_all_properties_to_enrich(
            limit_per_suburb=limit_per_suburb,
            skip_enriched=skip_enriched
        )
        
        if not properties:
            logger.warning("No properties found to enrich")
            return {'total': 0, 'successful': 0, 'failed': 0}
        
        self.stats['total'] = len(properties)
        logger.info(f"Found {len(properties)} properties to enrich")
        
        # Process in batches
        num_batches = (len(properties) + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"Processing in {num_batches} batches of {BATCH_SIZE}")
        
        for batch_num in range(num_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(properties))
            batch = properties[start_idx:end_idx]
            
            logger.info(f"\n{'='*60}")
            logger.info(f"BATCH {batch_num + 1}/{num_batches}")
            logger.info(f"Properties {start_idx + 1}-{end_idx} of {len(properties)}")
            logger.info(f"{'='*60}")
            
            self.process_batch(batch)
            
            # Log progress
            self._log_progress()
        
        # Final statistics
        elapsed_time = time.time() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("ENRICHMENT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total Properties: {self.stats['total']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Success Rate: {(self.stats['successful'] / self.stats['total'] * 100):.1f}%")
        logger.info(f"Time Elapsed: {elapsed_time:.1f}s ({elapsed_time/60:.1f} minutes)")
        logger.info(f"Average Time per Property: {elapsed_time / self.stats['total']:.2f}s")
        logger.info("=" * 60)
        
        # Log final database statistics
        self.db_client.log_progress_summary()
        
        return self.stats
    
    # ========================================================================
    # PROGRESS TRACKING
    # ========================================================================
    
    def _log_progress(self):
        """Log current progress statistics."""
        if self.stats['total'] == 0:
            return
        
        progress_pct = (self.stats['processed'] / self.stats['total']) * 100
        success_rate = (self.stats['successful'] / self.stats['processed'] * 100) if self.stats['processed'] > 0 else 0
        
        logger.info(f"\n📊 PROGRESS UPDATE:")
        logger.info(f"  Processed: {self.stats['processed']}/{self.stats['total']} ({progress_pct:.1f}%)")
        logger.info(f"  Successful: {self.stats['successful']} ({success_rate:.1f}%)")
        logger.info(f"  Failed: {self.stats['failed']}")
        logger.info(f"  Remaining: {self.stats['total'] - self.stats['processed']}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return self.stats.copy()
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    def close(self):
        """Close database connection."""
        self.db_client.close()
        logger.info("Batch processor closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
