"""
Photo Reordering System for Property Virtual Tours
Processes properties_for_sale collection to create optimal photo ordering
for virtual property tours following a logical flow.
"""
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

from config import (
    NUM_WORKERS, TEST_RUN, PARALLEL_BATCH_SIZE, MAX_BATCHES, 
    WORKER_STARTUP_DELAY, OPENAI_API_KEY, GPT_MODEL
)
from worker_logger import (
    setup_run_directory, setup_coordinator_logger,
    setup_worker_logger, setup_progress_logger
)
from batch_manager_reorder import BatchManagerReorder
from progress_monitor import ProgressMonitor
from worker_reorder import WorkerReorder

class PhotoReorderCoordinator:
    """Coordinates parallel processing of photo reordering."""
    
    def __init__(self):
        """Initialize the parallel coordinator."""
        # Set up timestamped log directory
        self.run_dir = setup_run_directory()
        
        # Set up loggers
        self.coordinator_logger = setup_coordinator_logger(self.run_dir)
        self.progress_logger = setup_progress_logger(self.run_dir)
        
        # Initialize components
        self.batch_manager = None
        self.progress_monitor = None
        self.workers = []
        self.worker_threads = []
        
        self.coordinator_logger.info(f"Run directory: {self.run_dir}")
        
    def initialize(self):
        """Initialize all components."""
        self.coordinator_logger.info("="*60)
        self.coordinator_logger.info("PHOTO REORDERING SYSTEM FOR VIRTUAL TOURS")
        self.coordinator_logger.info("="*60)
        self.coordinator_logger.info(f"Database: property_data")
        self.coordinator_logger.info(f"Collection: properties_for_sale")
        self.coordinator_logger.info(f"Workers: {NUM_WORKERS}")
        self.coordinator_logger.info(f"Batch Size: {PARALLEL_BATCH_SIZE}")
        self.coordinator_logger.info(f"Test Run: {TEST_RUN}")
        if TEST_RUN:
            self.coordinator_logger.info(f"Max Batches: {MAX_BATCHES}")
        self.coordinator_logger.info("="*60)
        
        # Initialize batch manager
        self.coordinator_logger.info("Initializing Batch Manager...")
        self.batch_manager = BatchManagerReorder(self.coordinator_logger)
        self.batch_manager.initialize()
        
        if self.batch_manager.total_batches_created == 0:
            self.coordinator_logger.warning("No batches to process. Exiting.")
            return False
        
        # Initialize progress monitor
        self.coordinator_logger.info("Initializing Progress Monitor...")
        self.progress_monitor = ProgressMonitor(
            self.progress_logger,
            self.batch_manager,
            NUM_WORKERS
        )
        
        return True
    
    def spawn_workers(self):
        """Spawn worker threads with staggered startup."""
        self.coordinator_logger.info(f"Spawning {NUM_WORKERS} workers...")
        if WORKER_STARTUP_DELAY > 0:
            self.coordinator_logger.info(f"Using staggered startup with {WORKER_STARTUP_DELAY}s delay between workers")
        
        for worker_id in range(1, NUM_WORKERS + 1):
            # Set up worker logger
            worker_logger = setup_worker_logger(worker_id, self.run_dir)
            
            # Create worker instance
            worker = WorkerReorder(worker_id, worker_logger, self.batch_manager)
            self.workers.append(worker)
            
            # Create and start worker thread
            worker_thread = threading.Thread(
                target=worker.run,
                name=f"Worker-{worker_id:02d}"
            )
            worker_thread.start()
            self.worker_threads.append(worker_thread)
            
            self.coordinator_logger.info(f"Worker {worker_id} started")
            
            # Staggered startup: wait before starting next worker (except for the last one)
            if WORKER_STARTUP_DELAY > 0 and worker_id < NUM_WORKERS:
                self.coordinator_logger.info(f"Waiting {WORKER_STARTUP_DELAY}s before starting next worker...")
                time.sleep(WORKER_STARTUP_DELAY)
        
        self.coordinator_logger.info(f"All {NUM_WORKERS} workers spawned")
    
    def wait_for_completion(self):
        """Wait for all workers to complete."""
        self.coordinator_logger.info("Waiting for workers to complete...")
        
        # Start progress monitoring
        self.progress_monitor.start()
        
        # Wait for all worker threads to finish
        for i, thread in enumerate(self.worker_threads, 1):
            thread.join()
            self.coordinator_logger.info(f"Worker {i} finished")
        
        # Stop progress monitoring
        self.progress_monitor.stop()
        
        self.coordinator_logger.info("All workers completed")
    
    def collect_stats(self):
        """Collect statistics from all workers."""
        total_stats = {
            "documents_processed": 0,
            "photos_reordered": 0,
            "errors": 0,
            "total_processing_time": 0,
            "batches_processed": 0
        }
        
        for worker in self.workers:
            worker_stats = worker.get_stats()
            for key in total_stats:
                total_stats[key] += worker_stats.get(key, 0)
        
        return total_stats
    
    def log_final_summary(self, total_stats):
        """Log final summary of processing."""
        self.coordinator_logger.info("\n" + "="*60)
        self.coordinator_logger.info("PROCESSING COMPLETE")
        self.coordinator_logger.info("="*60)
        self.coordinator_logger.info(f"Workers Used: {NUM_WORKERS}")
        self.coordinator_logger.info(f"Batches Processed: {total_stats['batches_processed']}")
        self.coordinator_logger.info(f"Documents Processed: {total_stats['documents_processed']}")
        self.coordinator_logger.info(f"Photos Reordered: {total_stats['photos_reordered']}")
        self.coordinator_logger.info(f"Errors: {total_stats['errors']}")
        
        if total_stats['documents_processed'] > 0:
            avg_time = total_stats['total_processing_time'] / total_stats['documents_processed']
            self.coordinator_logger.info(f"Avg Processing Time: {avg_time:.1f}s/document")
        
        self.coordinator_logger.info("="*60)
        
        # Also log from progress monitor
        self.progress_monitor.log_final_summary()
    
    def run(self):
        """Main execution method."""
        try:
            # Initialize
            if not self.initialize():
                return False
            
            # Spawn workers
            self.spawn_workers()
            
            # Wait for completion
            self.wait_for_completion()
            
            # Collect and log stats
            total_stats = self.collect_stats()
            self.log_final_summary(total_stats)
            
            # Cleanup
            if self.batch_manager:
                self.batch_manager.close()
            if self.progress_monitor:
                self.progress_monitor.close()
            
            self.coordinator_logger.info("Photo reordering completed successfully")
            return True
            
        except KeyboardInterrupt:
            self.coordinator_logger.warning("Interrupted by user")
            return False
        except Exception as e:
            self.coordinator_logger.error(f"Fatal error: {e}", exc_info=True)
            return False

def main():
    """Main entry point."""
    print("="*60)
    print("PHOTO REORDERING FOR VIRTUAL PROPERTY TOURS")
    print("="*60)
    print(f"Starting with {NUM_WORKERS} workers...")
    print()
    
    coordinator = PhotoReorderCoordinator()
    success = coordinator.run()
    
    if success:
        print("\n" + "="*60)
        print("✓ Photo reordering completed successfully!")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("✗ Processing failed or was interrupted")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
