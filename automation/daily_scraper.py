#!/usr/bin/env python3
"""
Daily Property Scraper Automation
Runs Script A pipeline, merges results, updates MongoDB
"""

import os
import sys
import subprocess
import json
from datetime import datetime
import logging
from pathlib import Path

# Add automation to path for mongodb_client
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mongodb_client import PropertyDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_scraper.log'),
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

def parse_session(session_num: int, simple_method_dir: str) -> dict:
    """Parse a single session's OCR output to JSON"""
    input_file = os.path.join(simple_method_dir, f"ocr_output_session_{session_num}", "raw_text_all.txt")
    output_file = os.path.join(simple_method_dir, f"property_data_session_{session_num}.json")
    
    if not os.path.exists(input_file):
        logger.warning(f"Input file not found: {input_file}")
        return {}
    
    cmd = ["python", "data_parser_multi.py", "--input", input_file, "--output", output_file]
    run_command(cmd, cwd=simple_method_dir)
    
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            data = json.load(f)
        logger.info(f"Parsed session {session_num}: {len(data.get('properties', []))} properties")
        return data
    else:
        logger.error(f"Output file not created: {output_file}")
        return {}

def merge_properties(sessions_data: list) -> list:
    """Merge properties from multiple sessions, deduplicate by address"""
    all_props = []
    address_to_prop = {}
    
    for data in sessions_data:
        props = data.get('properties', [])
        all_props.extend(props)
    
    for prop in all_props:
        addr = prop.get('address', '').lower().strip()
        if not addr:
            continue
        
        if addr not in address_to_prop:
            address_to_prop[addr] = prop
        else:
            # Merge: prefer more complete data
            current = address_to_prop[addr]
            new = prop
            # Count non-null fields
            current_count = sum(1 for k, v in current.items() if v is not None and v != '')
            new_count = sum(1 for k, v in new.items() if v is not None and v != '')
            
            if new_count > current_count:
                # Update with new if more complete
                for k, v in new.items():
                    if v and (k not in current or not current[k]):
                        current[k] = v
                logger.debug(f"Merged {addr}: kept new data (more complete)")
            else:
                logger.debug(f"Merged {addr}: kept existing data")
    
    merged = list(address_to_prop.values())
    logger.info(f"Merged {len(merged)} unique properties from {len(all_props)} total")
    return merged

def main():
    """Main daily scraper workflow"""
    # Create logs dir before logging
    os.makedirs('logs', exist_ok=True)
    
    simple_method_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '07_Undetectable_method', 'Simple_Method')
    logger.info(f"Starting daily scrape from {simple_method_dir}")
    
    try:
        db = PropertyDB()
        
        # Step 1: Run the full pipeline (screenshots + OCR)
        logger.info("Step 1: Running process_all_sessions.sh")
        run_command(['./process_all_sessions.sh'], cwd=simple_method_dir)
        
        # Step 2: Parse each session
        sessions_data = []
        for session in [1, 2, 3]:
            logger.info(f"Step 2.{session}: Parsing session {session}")
            data = parse_session(session, simple_method_dir)
            if data:
                sessions_data.append(data)
        
        if not sessions_data:
            logger.error("No session data parsed, aborting")
            return
        
        # Step 3: Merge properties
        logger.info("Step 3: Merging session data")
        merged_properties = merge_properties(sessions_data)
        
        if not merged_properties:
            logger.error("No properties to process, aborting")
            return
        
        # Step 4: Update database
        logger.info("Step 4: Updating MongoDB")
        stats = db.update_daily_list(merged_properties)
        logger.info(f"Database update complete: {stats}")
        
        db.close()
        logger.info("Daily scraper completed successfully")
        
    except Exception as e:
        logger.error(f"Daily scraper failed: {e}", exc_info=True)
        if 'db' in locals():
            db.log_error("daily_scraper", "general_error", str(e), {"error": str(e), "traceback": sys.exc_info()})
            db.close()

if __name__ == "__main__":
    main()
