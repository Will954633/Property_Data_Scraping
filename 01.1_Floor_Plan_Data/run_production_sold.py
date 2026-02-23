#!/usr/bin/env python
"""
Last Edit: 27/01/2026, 08:12 AM (Monday) - Brisbane
- Added --yes flag to bypass confirmation prompt for automated/orchestrator runs

Production script to process all floor plans for sold_last_6_months with 20 parallel workers.
"""
import os
import argparse

# Ensure the floor plan system targets the sold_last_6_months collection
os.environ.setdefault("DATABASE_NAME", "property_data")
os.environ["COLLECTION_NAME"] = "sold_last_6_months"

from batch_processor import FloorPlanBatchProcessor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Floor Plan Analysis - Production Run (sold_last_6_months)")
    parser.add_argument("--yes", "-y", action="store_true", 
                        help="Skip confirmation prompt (for automated/orchestrator runs)")
    args = parser.parse_args()
    
    print("=" * 80)
    print("FLOOR PLAN ANALYSIS - PRODUCTION RUN (sold_last_6_months)")
    print("=" * 80)
    print("Configuration:")
    print("  - Workers: 20")
    print("  - Worker deployment delay: 30 seconds")
    print("  - Database: property_data.sold_last_6_months")
    print("  - Model: gpt-5-nano-2025-08-07")
    print("=" * 80)

    if args.yes:
        print("\n[AUTO] Starting production processing for sold_last_6_months (--yes flag provided)...")
        processor = FloorPlanBatchProcessor(num_workers=20, worker_delay=30)
        processor.run()
    else:
        response = input("\nStart production processing for sold_last_6_months? (yes/no): ").strip().lower()

        if response in ["yes", "y"]:
            processor = FloorPlanBatchProcessor(num_workers=20, worker_delay=30)
            processor.run()
        else:
            print("Production run cancelled.")
