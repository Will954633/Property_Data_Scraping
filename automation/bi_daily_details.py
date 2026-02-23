#!/usr/bin/env python3
"""
Bi-Daily Detailed Property Data Collector
Runs Script B on active properties, stores snapshots, detects changes
"""

import os
import sys
import subprocess
import json
import glob
from datetime import datetime
import logging
from pathlib import Path

# Add automation to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mongodb_client import PropertyDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bi_daily_details.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd, cwd=None, check=True):
    """Run shell command and log output"""
    logger.info(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd} in {cwd or os.getcwd()}")
    try:
        if isinstance(cmd, list):
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)
        else:
            result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=check)
        if result.stdout:
            logger.info(f"Output: {result.stdout.strip()}")
        if result.stderr:
            logger.warning(f"Errors: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise

def get_active_addresses_json(db: PropertyDB, temp_file: str):
    """Get active addresses from DB and save to temp JSON"""
    addresses = db.get_all_active_addresses()
    temp_data = {
        "extraction_date": datetime.now().isoformat(),
        "source": "mongodb_active_properties",
        "properties": [{"address": addr} for addr in addresses]
    }
    with open(temp_file, 'w') as f:
        json.dump(temp_data, f, indent=2)
    logger.info(f"Saved {len(addresses)} active addresses to {temp_file}")
    return len(addresses)

def run_batch_processor(batch_dir: str, input_json: str):
    """Run batch_processor.py with input JSON"""
    logger.info("Running batch_processor.py")
    cmd = ["python", "batch_processor.py", "--input_json", input_json]
    result = run_command(cmd, cwd=batch_dir)
    if result.returncode == 0:
        logger.info("Batch processor completed successfully")
        return True
    else:
        logger.error("Batch processor failed")
        return False

def process_detailed_results(batch_dir: str, db: PropertyDB):
    """Process the generated property_data_*.json files, store snapshots, detect changes"""
    pattern = os.path.join(batch_dir, "batch_results", "property_data_*.json")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning("No property_data files found")
        return
    
    logger.info(f"Processing {len(files)} detailed result files")
    
    processed = 0
    errors = 0
    
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            address = data.get("address_searched")
            if not address:
                logger.warning(f"No address in {file_path}")
                continue
            
            property_data = data.get("property_data", {})
            if not property_data:
                logger.warning(f"No property data in {file_path}")
                continue
            
            # Get property document from DB to get _id
            prop_doc = db.properties.find_one({"address": address})
            if not prop_doc:
                logger.warning(f"Property not found in DB: {address}")
                continue
            
            property_id = str(prop_doc["_id"])
            
            # Store snapshot
            snapshot_id = db.store_detailed_snapshot(address, property_data, property_id)
            
            # Detect and log changes
            db.detect_and_log_changes(address, property_data, property_id)
            
            processed += 1
            logger.info(f"Processed {address} (snapshot: {snapshot_id})")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            db.log_error(address if 'address' in locals() else "unknown", "processing_error", str(e), {"file": file_path})
            errors += 1
    
    logger.info(f"Processed {processed} properties, {errors} errors")

def main():
    """Main bi-daily workflow"""
    # Create logs dir
    os.makedirs('logs', exist_ok=True)
    
    batch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '07_Undetectable_method', '00_Production_System', '02_Individual_Property_Google_Search')
    temp_json = "temp_active_addresses.json"
    
    logger.info(f"Starting bi-daily details collection from {batch_dir}")
    
    try:
        db = PropertyDB()
        
        # Step 1: Get active addresses and create temp JSON
        num_addresses = get_active_addresses_json(db, temp_json)
        if num_addresses == 0:
            logger.info("No active properties to process")
            os.remove(temp_json)
            db.close()
            return
        
        # Step 2: Run batch_processor
        success = run_batch_processor(batch_dir, os.path.abspath(temp_json))
        if not success:
            logger.error("Batch processor failed, aborting")
            os.remove(temp_json)
            db.close()
            return
        
        # Step 3: Process results
        process_detailed_results(batch_dir, db)
        
        # Cleanup temp file
        os.remove(temp_json)
        
        db.close()
        logger.info("Bi-daily details collection completed successfully")
        
    except Exception as e:
        logger.error(f"Bi-daily workflow failed: {e}", exc_info=True)
        if os.path.exists(temp_json):
            os.remove(temp_json)
        if 'db' in locals():
            db.log_error("bi_daily", "general_error", str(e), {"error": str(e)})
            db.close()

if __name__ == "__main__":
    main()
