"""
Worker process for parallel property valuation extraction.
"""
import time
from datetime import datetime
from mongodb_client import MongoDBClient
from gpt_client import GPTClient
from config import MAX_IMAGES_PER_PROPERTY

class Worker:
    """Worker process for processing property documents."""
    
    def __init__(self, worker_id, logger, batch_manager):
        """
        Initialize worker.
        
        Args:
            worker_id: Unique worker identifier
            logger: Logger instance for this worker
            batch_manager: Shared batch manager instance
        """
        self.worker_id = worker_id
        self.logger = logger
        self.batch_manager = batch_manager
        self.mongo_client = None
        self.gpt_client = None
        self.stats = {
            "documents_processed": 0,
            "with_water_views": 0,
            "errors": 0,
            "total_processing_time": 0,
            "batches_processed": 0
        }
        
    def initialize(self):
        """Initialize worker connections."""
        self.logger.info(f"Worker {self.worker_id} initializing...")
        
        try:
            self.mongo_client = MongoDBClient()
            self.gpt_client = GPTClient()
            self.logger.info(f"Worker {self.worker_id} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Worker {self.worker_id} failed to initialize: {e}")
            return False
    
    def process_document(self, document):
        """
        Process a single document.
        
        Args:
            document: MongoDB document
            
        Returns:
            dict with processing results
        """
        doc_id = document.get("_id")
        address = (document.get("complete_address") or 
                  document.get("address") or 
                  document.get("scraped_data", {}).get("address") or
                  "Unknown Address")
        
        # Images can be in scraped_data.images OR property_images
        scraped_data = document.get("scraped_data", {})
        images = scraped_data.get("images", [])
        
        # If no images in scraped_data, check property_images
        if not images:
            images = document.get("property_images", [])
        
        self.logger.info(f"Processing: {address} ({len(images)} images)")
        
        process_start = time.time()
        
        try:
            # Extract URLs from image objects
            # Images can be stored as: [{"url": "...", "index": 0, "date": "..."}] or ["url1", "url2", ...]
            if images and isinstance(images[0], dict):
                image_urls = [img.get("url") for img in images if img.get("url")]
            else:
                # Simple string array format (property_images)
                image_urls = images
            
            # Clean URLs - remove trailing backslashes and filter out invalid URLs
            cleaned_urls = []
            for url in image_urls:
                if url:
                    # Remove trailing backslashes
                    cleaned_url = url.rstrip('\\')
                    # Only include valid URLs (not empty after cleaning)
                    if cleaned_url and not cleaned_url.endswith('\\'):
                        cleaned_urls.append(cleaned_url)
            
            # Limit number of images
            images_to_analyze = cleaned_urls[:MAX_IMAGES_PER_PROPERTY]
            
            # Call GPT API
            analysis_result = self.gpt_client.analyze_property_images(
                images_to_analyze, 
                address
            )
            
            # Extract image analysis with rankings and descriptions
            image_analysis = self.gpt_client.extract_image_analysis(
                analysis_result,
                images_to_analyze
            )
            
            # Extract property valuation data
            property_data = self.gpt_client.extract_property_data(analysis_result)
            
            process_time = time.time() - process_start
            
            # Update MongoDB with image analysis
            self.mongo_client.update_with_image_analysis(
                doc_id,
                image_analysis,
                property_data,
                worker_id=self.worker_id,
                processing_time=process_time
            )
            
            # Check for water views
            has_water_views = property_data.get("outdoor", {}).get("natural_water_view", False)
            
            # Update stats
            self.stats["documents_processed"] += 1
            self.stats["total_processing_time"] += process_time
            if has_water_views:
                self.stats["with_water_views"] += 1
            
            self.logger.info(f"Completed: {address} - {len(image_analysis)} images analyzed ({process_time:.1f}s)")
            
            return {
                "success": True,
                "address": address,
                "processing_time": process_time,
                "images_analyzed": len(image_analysis),
                "has_water_views": has_water_views
            }
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Error processing {address}: {e}")
            return {
                "success": False,
                "address": address,
                "error": str(e)
            }
    
    def process_batch(self, batch):
        """
        Process a batch of documents.
        
        Args:
            batch: Batch dictionary with documents
            
        Returns:
            List of processing results
        """
        batch_id = batch["id"]
        documents = batch["documents"]
        
        self.logger.info(f"Starting batch {batch_id} ({len(documents)} documents)")
        batch_start = time.time()
        
        results = []
        for doc in documents:
            result = self.process_document(doc)
            results.append(result)
        
        batch_time = time.time() - batch_start
        self.stats["batches_processed"] += 1
        
        self.logger.info(f"Completed batch {batch_id} in {batch_time:.1f}s")
        
        return results
    
    def run(self):
        """Main worker loop - process batches until none remain."""
        if not self.initialize():
            self.logger.error(f"Worker {self.worker_id} failed to initialize")
            return
        
        self.logger.info(f"Worker {self.worker_id} starting processing loop")
        
        while True:
            # Get next batch
            batch = self.batch_manager.get_next_batch()
            
            if batch is None:
                self.logger.info(f"Worker {self.worker_id} - No more batches available")
                break
            
            # Process the batch
            self.process_batch(batch)
            
            # Mark batch as complete
            self.batch_manager.mark_batch_complete(batch["id"])
        
        # Log final stats
        self.logger.info(f"Worker {self.worker_id} completed:")
        self.logger.info(f"  Documents processed: {self.stats['documents_processed']}")
        self.logger.info(f"  With water views: {self.stats['with_water_views']}")
        self.logger.info(f"  Errors: {self.stats['errors']}")
        self.logger.info(f"  Batches processed: {self.stats['batches_processed']}")
        
        avg_time = self.stats["total_processing_time"] / self.stats["documents_processed"] if self.stats["documents_processed"] > 0 else 0
        self.logger.info(f"  Avg time/doc: {avg_time:.1f}s")
        
        # Close connections
        if self.mongo_client:
            self.mongo_client.close()
    
    def get_stats(self):
        """Get current worker statistics."""
        return self.stats.copy()
