"""
Production runner for property enrichment pipeline.
Last Edit: 13/02/2026, 3:51 PM (Thursday) — Brisbane Time

Description: Main entry point for running the enrichment pipeline on all
2,400 properties. Includes command-line arguments for testing and configuration.

Edit History:
- 13/02/2026 3:51 PM: Initial creation for production pipeline
"""

import argparse
import sys
from datetime import datetime

from batch_processor import BatchProcessor
from mongodb_enrichment_client import MongoDBEnrichmentClient
from logger import logger


def main():
    """Main entry point for production enrichment."""
    
    parser = argparse.ArgumentParser(
        description='GPT Property Enrichment Pipeline - Production Runner'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: Process only 1 property per suburb (8 total)'
    )
    
    parser.add_argument(
        '--small-batch',
        action='store_true',
        help='Small batch: Process 10 properties per suburb (80 total)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit properties per suburb (for custom testing)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of parallel workers (default: 10)'
    )
    
    parser.add_argument(
        '--skip-enriched',
        action='store_true',
        default=True,
        help='Skip already enriched properties (default: True)'
    )
    
    parser.add_argument(
        '--force-reprocess',
        action='store_true',
        help='Force reprocess all properties (ignore existing enrichment)'
    )
    
    parser.add_argument(
        '--check-progress',
        action='store_true',
        help='Check current enrichment progress and exit'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "=" * 70)
    print("GPT PROPERTY ENRICHMENT PIPELINE")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")
    
    # Check progress only
    if args.check_progress:
        logger.info("Checking enrichment progress...")
        with MongoDBEnrichmentClient() as db_client:
            db_client.log_progress_summary()
        return 0
    
    # Determine mode
    if args.test:
        limit_per_suburb = 1
        mode = "TEST MODE (1 property per suburb = 8 total)"
    elif args.small_batch:
        limit_per_suburb = 10
        mode = "SMALL BATCH MODE (10 properties per suburb = 80 total)"
    elif args.limit:
        limit_per_suburb = args.limit
        mode = f"CUSTOM MODE ({args.limit} properties per suburb)"
    else:
        limit_per_suburb = None
        mode = "PRODUCTION MODE (ALL properties)"
    
    skip_enriched = not args.force_reprocess
    
    logger.info(f"Running in: {mode}")
    logger.info(f"Skip enriched: {skip_enriched}")
    if args.workers:
        logger.info(f"Workers: {args.workers}")
    
    # Confirm production run
    if limit_per_suburb is None and not args.force_reprocess:
        print("\n⚠️  WARNING: You are about to run PRODUCTION enrichment on ALL properties!")
        print("This will:")
        print("  - Process ~2,400 properties")
        print("  - Cost approximately $312 in API calls")
        print("  - Take several hours to complete")
        print("\nAre you sure you want to continue? (yes/no): ", end='')
        
        confirmation = input().strip().lower()
        if confirmation != 'yes':
            print("Aborted.")
            return 1
    
    # Run enrichment
    try:
        with BatchProcessor(num_workers=args.workers) as processor:
            stats = processor.process_all_properties(
                limit_per_suburb=limit_per_suburb,
                skip_enriched=skip_enriched
            )
        
        # Print final summary
        print("\n" + "=" * 70)
        print("ENRICHMENT COMPLETE")
        print("=" * 70)
        print(f"Total Properties: {stats['total']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        if stats['total'] > 0:
            print(f"Success Rate: {(stats['successful'] / stats['total'] * 100):.1f}%")
        else:
            print(f"Success Rate: N/A (no properties processed)")
        print("=" * 70)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n\nProcess interrupted by user")
        print("\n⚠️  Process interrupted. Progress has been saved.")
        print("You can resume by running the script again (already enriched properties will be skipped).")
        return 1
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
