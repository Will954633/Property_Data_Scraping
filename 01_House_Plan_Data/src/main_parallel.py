"""
Main parallel coordinator for property valuation data extraction system.
Spawns and manages multiple worker threads for parallel processing.
"""
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

from config import (
    NUM_WORKERS, TEST_RUN, DATABASE_NAME, COLLECTION_NAME,
    PARALLEL_BATCH_SIZE, MAX_BATCHES, WORKER_STARTUP_DELAY
)
from worker_logger import (
    setup_run_directory, setup_coordinator_logger,
    setup_worker_logger, setup_progress_logger
)
from batch_manager import BatchManager
from progress_monitor import ProgressMonitor
from worker import Worker

class ParallelCoordinator:
    """Coordinates parallel processing of property documents."""
    
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
        self.coordinator_logger.info("PARALLEL PROPERTY VALUATION EXTRACTION SYSTEM")
        self.coordinator_logger.info("="*60)
        self.coordinator_logger.info(f"Database: {DATABASE_NAME}")
        self.coordinator_logger.info(f"Collection: {COLLECTION_NAME}")
        self.coordinator_logger.info(f"Workers: {NUM_WORKERS}")
        self.coordinator_logger.info(f"Batch Size: {PARALLEL_BATCH_SIZE}")
        self.coordinator_logger.info(f"Test Run: {TEST_RUN}")
        if TEST_RUN:
            self.coordinator_logger.info(f"Max Batches: {MAX_BATCHES}")
        self.coordinator_logger.info("="*60)
        
        # Initialize batch manager
        self.coordinator_logger.info("Initializing Batch Manager...")
        self.batch_manager = BatchManager(self.coordinator_logger)
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
            worker = Worker(worker_id, worker_logger, self.batch_manager)
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
            "house_plans_found": 0,
            "with_floor_area": 0,
            "with_water_views": 0,
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
        self.coordinator_logger.info(f"House Plans Found: {total_stats['house_plans_found']}")
        self.coordinator_logger.info(f"With Floor Area: {total_stats['with_floor_area']}")
        self.coordinator_logger.info(f"With Water Views: {total_stats['with_water_views']}")
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
            
            self.coordinator_logger.info("Parallel processing completed successfully")
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
    print("PARALLEL PROPERTY VALUATION DATA EXTRACTION")
    print("="*60)
    print(f"Starting with {NUM_WORKERS} workers...")
    print()
    
    coordinator = ParallelCoordinator()
    success = coordinator.run()
    
    if success:
        print("\n" + "="*60)
        print("✓ Processing completed successfully!")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("✗ Processing failed or was interrupted")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
