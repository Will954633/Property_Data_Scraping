#!/usr/bin/env python3
"""
Test script to verify the auction property false positive fix

Last Updated: 27/01/2026, 10:17 AM (Monday) - Brisbane
- Created to test the fix for auction properties being incorrectly marked as sold
- Tests the specific property: 330 Ron Penhaligon Way, Robina, QLD 4226
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sold_property_monitor_selenium import SoldPropertyMonitor
from pymongo import MongoClient
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_auction_property():
    """Test that the auction property is not incorrectly marked as sold"""
    
    logger.info("="*80)
    logger.info("TESTING AUCTION PROPERTY FIX")
    logger.info("="*80)
    
    # Connect to MongoDB
    client = MongoClient('mongodb://REDACTED:REDACTED@REDACTED.mongo.cosmos.azure.com:10255/')
    db = client['property_data']
    
    # Get the specific property
    test_address = '330 Ron Penhaligon Way, Robina, QLD 4226'
    property_doc = db.properties_for_sale.find_one({'address': test_address})
    
    if not property_doc:
        logger.error(f"❌ Test property not found in for_sale collection: {test_address}")
        return False
    
    logger.info(f"✓ Found test property: {test_address}")
    
    # Initialize monitor
    monitor = SoldPropertyMonitor(headless=True)
    
    try:
        # Test the property
        logger.info("\nTesting property detection...")
        was_moved = monitor.monitor_property(property_doc)
        
        # Check result
        if was_moved:
            logger.error("❌ TEST FAILED: Auction property was incorrectly marked as sold!")
            logger.error("   The fix did not work as expected.")
            return False
        else:
            logger.info("✅ TEST PASSED: Auction property was correctly identified and NOT marked as sold")
            logger.info("   The fix is working correctly!")
            return True
            
    finally:
        monitor.close()
        client.close()

if __name__ == "__main__":
    success = test_auction_property()
    sys.exit(0 if success else 1)
