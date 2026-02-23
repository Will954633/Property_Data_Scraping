"""
Progress monitoring module for parallel processing.
"""
import time
import threading
from datetime import datetime, timedelta
from mongodb_client import MongoDBClient

class ProgressMonitor:
    """Monitors and displays processing progress."""
    
    def __init__(self, logger, batch_manager, num_workers):
        """
        Initialize progress monitor.
        
        Args:
            logger: Logger instance
            batch_manager: Batch manager instance
            num_workers: Number of workers
        """
        self.logger = logger
        self.batch_manager = batch_manager
        self.num_workers = num_workers
        self.mongo_client = MongoDBClient()
        self.start_time = None
        self.running = False
        self.monitor_thread = None
        
    def start(self):
        """Start the progress monitor."""
        self.start_time = datetime.now()
        self.running = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Progress monitor started")
    
    def stop(self):
        """Stop the progress monitor."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Progress monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop - updates progress every 10 seconds."""
        while self.running:
            try:
                self._log_progress()
                time.sleep(10)  # Update every 10 seconds
            except Exception as e:
                self.logger.error(f"Error in progress monitor: {e}")
    
    def _log_progress(self):
        """Log current progress."""
        try:
            # Get batch progress
            batch_progress = self.batch_manager.get_progress()
            
            # Get MongoDB stats
            stats = self.mongo_client.get_processing_stats()
            
            # Calculate time metrics
            elapsed = datetime.now() - self.start_time
            elapsed_seconds = elapsed.total_seconds()
            
            # Calculate rate
            docs_processed = stats["processed"]
            rate = docs_processed / elapsed_seconds if elapsed_seconds > 0 else 0
            
            # Estimate completion
            remaining = stats["unprocessed"]
            if rate > 0:
                eta_seconds = remaining / rate
                eta = timedelta(seconds=int(eta_seconds))
            else:
                eta = "Unknown"
            
            # Log progress
            progress_msg = (
                f"\n{'='*50}\n"
                f"PROGRESS UPDATE - {datetime.now().strftime('%H:%M:%S')}\n"
                f"{'='*50}\n"
                f"Batches: {batch_progress['completed_batches']}/{batch_progress['total_batches']} "
                f"({batch_progress['progress_percentage']:.1f}%)\n"
                f"Documents: {docs_processed} processed, {remaining} remaining\n"
                f"House Plans: {stats['house_plans_found']} total, {stats['with_floor_area']} with area\n"
                f"Water Views: {stats['with_water_views']} properties\n"
                f"Rate: {rate:.1f} docs/min\n"
                f"Elapsed: {str(elapsed).split('.')[0]}\n"
                f"ETA: {eta}\n"
                f"{'='*50}"
            )
            
            self.logger.info(progress_msg)
            
        except Exception as e:
            self.logger.error(f"Error logging progress: {e}")
    
    def log_final_summary(self):
        """Log final processing summary."""
        try:
            stats = self.mongo_client.get_processing_stats()
            elapsed = datetime.now() - self.start_time
            
            summary = (
                f"\n{'='*50}\n"
                f"FINAL SUMMARY\n"
                f"{'='*50}\n"
                f"Total Runtime: {str(elapsed).split('.')[0]}\n"
                f"Documents Processed: {stats['processed']}\n"
                f"House Plans Found: {stats['house_plans_found']}\n"
                f"With Floor Area: {stats['with_floor_area']}\n"
                f"With Water Views: {stats['with_water_views']}\n"
                f"Workers Used: {self.num_workers}\n"
                f"{'='*50}"
            )
            
            self.logger.info(summary)
            print(summary)
            
        except Exception as e:
            self.logger.error(f"Error logging final summary: {e}")
    
    def close(self):
        """Close the progress monitor and MongoDB connection."""
        self.stop()
        if self.mongo_client:
            self.mongo_client.close()
