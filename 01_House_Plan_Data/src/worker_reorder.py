"""
Worker process for parallel photo reordering.
"""
import time
from datetime import datetime
from mongodb_reorder_client import MongoDBReorderClient
from gpt_reorder_client import GPTReorderClient

class WorkerReorder:
    """Worker process for processing photo reordering."""
    
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
            "photos_reordered": 0,
            "errors": 0,
            "total_processing_time": 0,
            "batches_processed": 0
        }
        
    def initialize(self):
        """Initialize worker connections."""
        self.logger.info(f"Worker {self.worker_id} initializing...")
        
        try:
            self.mongo_client = MongoDBReorderClient()
            self.gpt_client = GPTReorderClient()
            self.logger.info(f"Worker {self.worker_id} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Worker {self.worker_id} failed to initialize: {e}")
            return False
    
    def process_document(self, document):
        """
        Process a single document for photo reordering.
        
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
        
        # Get existing image analysis
        image_analysis = document.get("image_analysis", [])
        
        if not image_analysis:
            self.logger.warning(f"No image analysis found for {address}, skipping")
            return {
                "success": False,
                "address": address,
                "error": "No image analysis available"
            }
        
        self.logger.info(f"Processing: {address} ({len(image_analysis)} images)")
        
        process_start = time.time()
        
        try:
            # Call GPT API to create photo tour order
            reorder_result = self.gpt_client.create_photo_tour_order(
                image_analysis,
                address
            )
            
            # Extract photo tour order
            photo_tour_order = self.gpt_client.extract_photo_tour_order(reorder_result)
            
            # Get tour metadata
            tour_metadata = self.gpt_client.get_tour_metadata(reorder_result)
            
            # Add metadata to each photo in tour order
            for photo in photo_tour_order:
                photo["tour_metadata"] = tour_metadata
            
            process_time = time.time() - process_start
            
            # Update MongoDB with photo tour order
            self.mongo_client.update_with_photo_tour_order(
                doc_id,
                photo_tour_order,
                worker_id=self.worker_id,
                processing_time=process_time
            )
            
            # Update stats
            self.stats["documents_processed"] += 1
            self.stats["photos_reordered"] += len(photo_tour_order)
            self.stats["total_processing_time"] += process_time
            
            self.logger.info(f"Completed: {address} - {len(photo_tour_order)} photos in tour ({process_time:.1f}s)")
            
            return {
                "success": True,
                "address": address,
                "processing_time": process_time,
                "photos_in_tour": len(photo_tour_order)
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
        self.logger.info(f"  Photos reordered: {self.stats['photos_reordered']}")
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
