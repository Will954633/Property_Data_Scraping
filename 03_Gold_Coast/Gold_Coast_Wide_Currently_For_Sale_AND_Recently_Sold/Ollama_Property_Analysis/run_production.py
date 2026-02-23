#!/usr/bin/env python3
# Last Edit: 31/01/2026, Friday, 7:43 pm (Brisbane Time)
"""
Production runner for Ollama property analysis.
Processes properties from Gold_Coast_Currently_For_Sale database.
Target suburbs: Robina, Mudgeeraba, Varsity Lakes, Reedy Creek, Burleigh Waters, Merimac, Warongary
"""
import time
from mongodb_client_multi import MongoDBClientMulti
from worker_multi import PropertyWorkerMulti
from logger import logger
from config import PARALLEL_BATCH_SIZE, TEST_RUN, MAX_BATCHES

def main():
    """Main execution function."""
    start_time = time.time()
    
    logger.info("=" * 80)
    logger.info("OLLAMA PROPERTY ANALYSIS - PRODUCTION RUN")
    logger.info("=" * 80)
    logger.info(f"Mode: {'TEST' if TEST_RUN else 'PRODUCTION'}")
    logger.info(f"Batch size: {PARALLEL_BATCH_SIZE}")
    if TEST_RUN:
        logger.info(f"Max batches: {MAX_BATCHES}")
    
    # Initialize MongoDB client
    mongo_client = MongoDBClientMulti()
    
    try:
        # Get initial stats
        logger.info("\n" + "=" * 80)
        logger.info("INITIAL STATISTICS")
        logger.info("=" * 80)
        stats = mongo_client.get_processing_stats()
        logger.info(f"Total documents in target suburbs: {stats['total_documents_in_target_suburbs']}")
        logger.info(f"Already processed: {stats['processed']}")
        logger.info(f"Unprocessed: {stats['unprocessed']}")
        logger.info(f"Properties with water views: {stats['with_water_views']}")
        logger.info("\nBy suburb:")
        for suburb, count in stats['by_suburb'].items():
            logger.info(f"  {suburb}: {count} properties")
        
        if stats['unprocessed'] == 0:
            logger.info("\nNo unprocessed documents found. Exiting.")
            return
        
        # Get all unprocessed documents
        logger.info("\n" + "=" * 80)
        logger.info("FETCHING UNPROCESSED DOCUMENTS")
        logger.info("=" * 80)
        all_documents = mongo_client.get_all_unprocessed_documents()
        
        if not all_documents:
            logger.info("No documents to process. Exiting.")
            return
        
        # Apply test mode limits if enabled
        if TEST_RUN and MAX_BATCHES > 0:
            max_docs = MAX_BATCHES * PARALLEL_BATCH_SIZE
            if len(all_documents) > max_docs:
                logger.info(f"TEST MODE: Limiting to {max_docs} documents ({MAX_BATCHES} batches)")
                all_documents = all_documents[:max_docs]
        
        logger.info(f"Processing {len(all_documents)} documents")
        
        # Create batches
        batches = []
        for i in range(0, len(all_documents), PARALLEL_BATCH_SIZE):
            batch = all_documents[i:i + PARALLEL_BATCH_SIZE]
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} batches")
        
        # Initialize worker
        logger.info("\n" + "=" * 80)
        logger.info("STARTING PROCESSING")
        logger.info("=" * 80)
        worker = PropertyWorkerMulti(worker_id="main_worker")
        
        # Process batches
        total_successful = 0
        total_failed = 0
        
        for batch_num, batch in enumerate(batches, 1):
            logger.info(f"\n--- Processing Batch {batch_num}/{len(batches)} ({len(batch)} documents) ---")
            
            batch_stats = worker.process_batch(batch)
            
            total_successful += batch_stats['successful']
            total_failed += batch_stats['failed']
            
            logger.info(f"Batch {batch_num} complete: {batch_stats['successful']} successful, {batch_stats['failed']} failed")
            logger.info(f"Average time per property: {batch_stats['avg_time_per_property']:.1f}s")
            logger.info(f"Overall progress: {total_successful + total_failed}/{len(all_documents)} documents processed")
        
        # Clean up worker only (keep mongo_client open for final stats)
        worker.close()

        # Final statistics
        elapsed_time = time.time() - start_time

        logger.info("\n" + "=" * 80)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total documents processed: {total_successful + total_failed}")
        logger.info(f"Successful: {total_successful}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Total time: {elapsed_time:.1f}s ({elapsed_time/60:.1f} minutes)")
        if total_successful > 0:
            logger.info(f"Average time per property: {elapsed_time/total_successful:.1f}s")

        # Get final stats
        logger.info("\n" + "=" * 80)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 80)
        final_stats = mongo_client.get_processing_stats()
        logger.info(f"Total documents in target suburbs: {final_stats['total_documents_in_target_suburbs']}")
        logger.info(f"Processed: {final_stats['processed']}")
        logger.info(f"Remaining unprocessed: {final_stats['unprocessed']}")
        logger.info(f"Properties with water views: {final_stats['with_water_views']}")

        logger.info("\n" + "=" * 80)
        logger.info("DONE!")
        logger.info("=" * 80)

        # Clean up mongo client after final stats
        mongo_client.close()
        
    except KeyboardInterrupt:
        logger.info("\n\nProcessing interrupted by user")
        mongo_client.close()
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}", exc_info=True)
        mongo_client.close()
        raise

if __name__ == "__main__":
    main()
