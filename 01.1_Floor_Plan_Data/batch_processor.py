"""
Batch processor for floor plan analysis with parallel workers.
"""
import time
import multiprocessing as mp
from mongodb_client import MongoDBFloorPlanClient
from logger import logger


class FloorPlanBatchProcessor:
    """Manages batch processing of floor plans across multiple workers."""
    
    def __init__(self, num_workers=20, worker_delay=30):
        """
        Initialize batch processor.
        
        Args:
            num_workers: Number of parallel workers
            worker_delay: Delay in seconds between starting workers
        """
        self.num_workers = num_workers
        self.worker_delay = worker_delay
    
    def get_properties_to_process(self):
        """
        Get all properties that need floor plan analysis.
        
        Returns:
            List of property addresses
        """
        # Create temporary MongoDB client
        mongo_client = MongoDBFloorPlanClient()
        
        # Get properties with floor plans but no analysis
        properties = mongo_client.collection.find(
            {
                "floor_plans": {"$exists": True, "$ne": []},
                "floor_plan_analysis": {"$exists": False}
            },
            {"address": 1}
        )
        
        addresses = [prop["address"] for prop in properties]
        logger.info(f"Found {len(addresses)} properties to process")
        
        mongo_client.close()
        return addresses
    
    def divide_work(self, addresses):
        """
        Divide addresses among workers.
        
        Args:
            addresses: List of property addresses
            
        Returns:
            List of address batches, one per worker
        """
        total = len(addresses)
        batch_size = (total + self.num_workers - 1) // self.num_workers  # Ceiling division
        
        batches = []
        for i in range(0, total, batch_size):
            batch = addresses[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"Divided {total} properties into {len(batches)} batches")
        for i, batch in enumerate(batches, 1):
            logger.info(f"  Worker {i}: {len(batch)} properties")
        
        return batches
    
    def start_workers(self, batches):
        """
        Start worker processes with staggered deployment.
        
        Args:
            batches: List of address batches
            
        Returns:
            List of worker processes
        """
        processes = []
        
        for worker_id, batch in enumerate(batches, 1):
            if not batch:
                continue
            
            logger.info(f"Starting Worker {worker_id} with {len(batch)} properties...")
            
            # Start worker process
            process = mp.Process(
                target=self._worker_process,
                args=(worker_id, batch)
            )
            process.start()
            processes.append(process)
            
            # Wait before starting next worker (except for the last one)
            if worker_id < len(batches):
                logger.info(f"Waiting {self.worker_delay} seconds before starting next worker...")
                time.sleep(self.worker_delay)
        
        logger.info(f"All {len(processes)} workers started")
        return processes
    
    def _worker_process(self, worker_id, addresses):
        """
        Worker process that analyzes floor plans.
        
        Args:
            worker_id: Worker identifier
            addresses: List of addresses to process
        """
        from gpt_client import GPTFloorPlanClient
        from mongodb_client import MongoDBFloorPlanClient
        
        # Each worker needs its own clients
        mongo_client = MongoDBFloorPlanClient()
        gpt_client = GPTFloorPlanClient()
        
        logger.info(f"[Worker {worker_id}] Started processing {len(addresses)} properties")
        
        success_count = 0
        error_count = 0
        
        for idx, address in enumerate(addresses, 1):
            try:
                logger.info(f"[Worker {worker_id}] Processing {idx}/{len(addresses)}: {address}")
                
                # Get property
                property_doc = mongo_client.get_property_by_address(address)
                if not property_doc:
                    logger.warning(f"[Worker {worker_id}] Property not found: {address}")
                    error_count += 1
                    continue
                
                floor_plans = property_doc.get("floor_plans", [])
                if not floor_plans:
                    logger.warning(f"[Worker {worker_id}] No floor plans for: {address}")
                    error_count += 1
                    continue
                
                # Analyze floor plans
                analysis_result = gpt_client.analyze_floor_plans(floor_plans, address)
                
                if analysis_result:
                    # Save to database
                    success = mongo_client.update_floor_plan_analysis(address, analysis_result)
                    if success:
                        success_count += 1
                        logger.info(f"[Worker {worker_id}] ✓ Completed {idx}/{len(addresses)}: {address}")
                    else:
                        error_count += 1
                        logger.error(f"[Worker {worker_id}] ✗ Failed to save: {address}")
                else:
                    error_count += 1
                    logger.error(f"[Worker {worker_id}] ✗ Analysis failed: {address}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"[Worker {worker_id}] ✗ Error processing {address}: {e}", exc_info=True)
        
        logger.info(f"[Worker {worker_id}] Completed: {success_count} successful, {error_count} errors")
        mongo_client.close()
    
    def wait_for_completion(self, processes):
        """
        Wait for all worker processes to complete.
        
        Args:
            processes: List of worker processes
        """
        logger.info("Waiting for all workers to complete...")
        
        for i, process in enumerate(processes, 1):
            process.join()
            logger.info(f"Worker {i} completed")
        
        logger.info("All workers completed!")
    
    def run(self):
        """Run the complete batch processing workflow."""
        logger.info("=" * 80)
        logger.info("FLOOR PLAN BATCH PROCESSOR")
        logger.info("=" * 80)
        logger.info(f"Workers: {self.num_workers}")
        logger.info(f"Worker delay: {self.worker_delay} seconds")
        logger.info("=" * 80)
        
        # Get properties to process
        addresses = self.get_properties_to_process()
        
        if not addresses:
            logger.info("No properties to process!")
            return
        
        # Divide work among workers
        batches = self.divide_work(addresses)
        
        # Start workers with staggered deployment
        start_time = time.time()
        processes = self.start_workers(batches)
        
        # Wait for completion
        self.wait_for_completion(processes)
        
        # Summary
        elapsed_time = time.time() - start_time
        logger.info("=" * 80)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total properties: {len(addresses)}")
        logger.info(f"Total time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        logger.info(f"Average per property: {elapsed_time/len(addresses):.1f} seconds")
        logger.info("=" * 80)
        
        # Check final status
        mongo_client = MongoDBFloorPlanClient()
        mongo_client.count_properties_with_analysis()
        mongo_client.close()


if __name__ == "__main__":
    processor = FloorPlanBatchProcessor(num_workers=20, worker_delay=30)
    processor.run()
