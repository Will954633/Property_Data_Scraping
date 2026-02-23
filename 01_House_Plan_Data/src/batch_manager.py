"""
Batch manager for distributing work to parallel workers.
"""
import threading
from queue import Queue, Empty
from mongodb_client import MongoDBClient
from config import PARALLEL_BATCH_SIZE, MAX_BATCHES, TEST_RUN

class BatchManager:
    """Manages distribution of document batches to workers."""
    
    def __init__(self, logger):
        """
        Initialize batch manager.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.mongo_client = MongoDBClient()
        self.batch_queue = Queue()
        self.total_batches_created = 0
        self.batches_completed = 0
        self.lock = threading.Lock()
        self.initialized = False
        
    def initialize(self):
        """Initialize the batch manager and create initial batches."""
        self.logger.info("Initializing Batch Manager...")
        
        # Get unprocessed document count
        unprocessed_count = self.mongo_client.count_unprocessed_documents()
        self.logger.info(f"Unprocessed documents: {unprocessed_count}")
        
        if unprocessed_count == 0:
            self.logger.warning("No unprocessed documents found!")
            self.initialized = True
            return
        
        # Create initial batches
        self._create_batches()
        
        self.initialized = True
        self.logger.info(f"Batch Manager initialized with {self.total_batches_created} batches in queue")
    
    def _create_batches(self):
        """Create batches from unprocessed documents."""
        max_batches = MAX_BATCHES if TEST_RUN else 0  # 0 = unlimited
        
        # Get ALL unprocessed documents at once (just IDs and necessary data)
        self.logger.info("Fetching all unprocessed documents...")
        all_documents = self.mongo_client.get_all_unprocessed_documents()
        
        if not all_documents:
            self.logger.info("No unprocessed documents found")
            return
        
        self.logger.info(f"Found {len(all_documents)} unprocessed documents")
        
        # Calculate number of batches to create
        total_batches_needed = (len(all_documents) + PARALLEL_BATCH_SIZE - 1) // PARALLEL_BATCH_SIZE
        
        # Apply batch limit if in test mode
        if max_batches > 0:
            total_batches_needed = min(total_batches_needed, max_batches)
            documents_to_process = all_documents[:max_batches * PARALLEL_BATCH_SIZE]
            self.logger.info(f"Test mode: limiting to {max_batches} batches ({len(documents_to_process)} documents)")
        else:
            documents_to_process = all_documents
        
        # Create batches
        for i in range(0, len(documents_to_process), PARALLEL_BATCH_SIZE):
            batch_documents = documents_to_process[i:i + PARALLEL_BATCH_SIZE]
            
            batch_id = f"batch_{self.total_batches_created + 1:05d}"
            batch = {
                "id": batch_id,
                "documents": batch_documents,
                "size": len(batch_documents)
            }
            
            self.batch_queue.put(batch)
            self.total_batches_created += 1
            
            self.logger.info(f"Created {batch_id} with {len(batch_documents)} documents")
        
        self.logger.info(f"Total batches created: {self.total_batches_created}")
    
    def get_next_batch(self):
        """
        Get the next batch for processing.
        
        Returns:
            Batch dictionary or None if no batches available
        """
        try:
            batch = self.batch_queue.get(block=False)
            return batch
        except Empty:
            return None
    
    def mark_batch_complete(self, batch_id):
        """
        Mark a batch as completed.
        
        Args:
            batch_id: ID of the completed batch
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
            batches_remaining = self.total_batches_created - self.batches_completed
            progress_pct = (self.batches_completed / self.total_batches_created * 100) if self.total_batches_created > 0 else 0
            
            return {
                "total_batches": self.total_batches_created,
                "completed_batches": self.batches_completed,
                "remaining_batches": batches_remaining,
                "progress_percentage": progress_pct,
                "batches_in_queue": self.batch_queue.qsize()
            }
    
    def is_complete(self):
        """
        Check if all batches have been completed.
        
        Returns:
            True if all batches are complete, False otherwise
        """
        with self.lock:
            return self.batches_completed >= self.total_batches_created and self.batch_queue.empty()
    
    def close(self):
        """Close the batch manager and MongoDB connection."""
        if self.mongo_client:
            self.mongo_client.close()
