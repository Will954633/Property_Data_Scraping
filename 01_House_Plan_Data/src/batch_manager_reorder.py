"""
Batch Manager for Photo Reordering System
Manages batches of properties that need photo reordering.
"""
import threading
from mongodb_reorder_client import MongoDBReorderClient
from config import PARALLEL_BATCH_SIZE, TEST_RUN, MAX_BATCHES

class BatchManagerReorder:
    """Manages batches of documents for photo reordering."""
    
    def __init__(self, logger):
        """
        Initialize batch manager.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.mongo_client = None
        self.batches = []
        self.current_batch_index = 0
        self.lock = threading.Lock()
        self.total_batches_created = 0
        self.batches_completed = 0
        
    def initialize(self):
        """Initialize batch manager and create batches."""
        self.logger.info("Connecting to MongoDB...")
        self.mongo_client = MongoDBReorderClient()
        
        # Get all documents that need photo reordering
        self.logger.info("Fetching documents for photo reordering...")
        all_documents = self.mongo_client.get_all_documents_for_reordering()
        
        total_docs = len(all_documents)
        self.logger.info(f"Found {total_docs} documents to process")
        
        if total_docs == 0:
            self.logger.warning("No documents found for photo reordering")
            return
        
        # Create batches
        self.logger.info(f"Creating batches (size: {PARALLEL_BATCH_SIZE})...")
        batch_id = 1
        
        for i in range(0, len(all_documents), PARALLEL_BATCH_SIZE):
            batch_docs = all_documents[i:i + PARALLEL_BATCH_SIZE]
            
            batch = {
                "id": batch_id,
                "documents": batch_docs,
                "size": len(batch_docs)
            }
            
            self.batches.append(batch)
            batch_id += 1
            
            # Stop if we've reached max batches in test mode
            if TEST_RUN and MAX_BATCHES > 0 and len(self.batches) >= MAX_BATCHES:
                self.logger.info(f"Test mode: Limited to {MAX_BATCHES} batches")
                break
        
        self.total_batches_created = len(self.batches)
        self.logger.info(f"Created {self.total_batches_created} batches")
        
        # Log batch distribution
        total_docs_in_batches = sum(b["size"] for b in self.batches)
        self.logger.info(f"Total documents in batches: {total_docs_in_batches}")
    
    def get_next_batch(self):
        """
        Get the next batch to process (thread-safe).
        
        Returns:
            Batch dictionary or None if no more batches
        """
        with self.lock:
            if self.current_batch_index >= len(self.batches):
                return None
            
            batch = self.batches[self.current_batch_index]
            self.current_batch_index += 1
            
            return batch
    
    def mark_batch_complete(self, batch_id):
        """
        Mark a batch as complete (thread-safe).
        
        Args:
            batch_id: ID of completed batch
        """
        with self.lock:
            self.batches_completed += 1
            self.logger.info(f"Batch {batch_id} completed ({self.batches_completed}/{self.total_batches_created})")
    
    def get_progress(self):
        """
        Get current progress statistics.
        
        Returns:
            Dictionary with progress information
        """
        with self.lock:
            return {
                "total_batches": self.total_batches_created,
                "batches_completed": self.batches_completed,
                "batches_remaining": self.total_batches_created - self.batches_completed,
                "current_batch_index": self.current_batch_index
            }
    
    def close(self):
        """Close MongoDB connection."""
        if self.mongo_client:
            self.mongo_client.close()
