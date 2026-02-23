#!/usr/bin/env python3
"""
Test Enhanced Sold Detection
Tests the new detection methods against known sold properties

Last Updated: 27/01/2026, 8:40 AM (Monday) - Brisbane
- Created test script for enhanced sold detection methods
- Tests against "12 Carnoustie Court, Robina, QLD 4226" case
"""

import sys
from sold_property_monitor import SoldPropertyMonitor
from pymongo import MongoClient
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_specific_property(address: str):
    """Test detection on a specific property by address"""
    logger.info("="*80)
    logger.info(f"TESTING ENHANCED DETECTION FOR: {address}")
    logger.info("="*80)
    
    try:
        monitor = SoldPropertyMonitor()
        
        # Find the property in for_sale collection
        property_doc = monitor.for_sale_collection.find_one({"address": address})
        
        if not property_doc:
            logger.warning(f"Property not found in properties_for_sale collection: {address}")
            logger.info("Checking properties_sold collection...")
            
            property_doc = monitor.sold_collection.find_one({"address": address})
            if property_doc:
                logger.info(f"✓ Property found in properties_sold collection")
                logger.info(f"  Detection Method: {property_doc.get('detection_method', 'Unknown')}")
                logger.info(f"  Sold Date: {property_doc.get('sold_date', 'Not available')}")
                logger.info(f"  Sale Price: {property_doc.get('sale_price', 'Not disclosed')}")
                logger.info(f"  Moved to sold: {property_doc.get('moved_to_sold_date', 'Unknown')}")
                return True
            else:
                logger.error(f"Property not found in either collection: {address}")
                return False
        
        logger.info(f"✓ Property found in properties_for_sale collection")
        logger.info(f"Testing detection methods...")
        
        # Test the property
        result = monitor.monitor_property(property_doc)
        
        if result:
            logger.info("="*80)
            logger.info("✓ SUCCESS: Property was detected as SOLD and moved to properties_sold")
            logger.info("="*80)
        else:
            logger.warning("="*80)
            logger.warning("✗ FAILED: Property was NOT detected as sold")
            logger.warning("="*80)
        
        monitor.close()
        return result
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_detection_methods():
    """Test all detection methods with sample HTML"""
    logger.info("="*80)
    logger.info("TESTING DETECTION METHODS WITH SAMPLE HTML")
    logger.info("="*80)
    
    monitor = SoldPropertyMonitor()
    
    # Test 1: Breadcrumb detection
    html_breadcrumb = """
    <html>
        <nav class="breadcrumb">
            <a href="/">Home</a> > 
            <a href="/sold/">Sold</a> > 
            <a href="/sold/qld/">QLD</a> > 
            <span>Robina</span>
        </nav>
        <div class="description">
            Beautiful property in Robina
        </div>
    </html>
    """
    
    is_sold, _, _, method = monitor.check_if_sold(html_breadcrumb, "")
    logger.info(f"Test 1 - Breadcrumb Detection: {'✓ PASS' if is_sold else '✗ FAIL'} (Method: {method})")
    
    # Test 2: SOLD BY pattern detection
    html_sold_by = """
    <html>
        <meta name="description" content="SOLD BY TINA NENADIC AND JULIANNE PETERSEN - Beautiful property">
        <div class="content">
            This property has been SOLD BY TINA NENADIC
        </div>
    </html>
    """
    
    is_sold, _, _, method = monitor.check_if_sold(html_sold_by, "")
    logger.info(f"Test 2 - SOLD BY Pattern: {'✓ PASS' if is_sold else '✗ FAIL'} (Method: {method})")
    
    # Test 3: URL pattern detection
    html_simple = "<html><body>Property listing</body></html>"
    url_sold = "https://www.domain.com.au/sold/12-carnoustie-court-robina-qld-4226"
    
    is_sold, _, _, method = monitor.check_if_sold(html_simple, url_sold)
    logger.info(f"Test 3 - URL Pattern: {'✓ PASS' if is_sold else '✗ FAIL'} (Method: {method})")
    
    # Test 4: Listing tag (original method)
    html_tag = """
    <html>
        <span data-testid="listing-details__listing-tag">Sold by private treaty 25 Nov 2025</span>
    </html>
    """
    
    is_sold, _, _, method = monitor.check_if_sold(html_tag, "")
    logger.info(f"Test 4 - Listing Tag: {'✓ PASS' if is_sold else '✗ FAIL'} (Method: {method})")
    
    # Test 5: Meta tag detection
    html_meta = """
    <html>
        <meta property="og:type" content="property:sold">
    </html>
    """
    
    is_sold, _, _, method = monitor.check_if_sold(html_meta, "")
    logger.info(f"Test 5 - Meta Tag: {'✓ PASS' if is_sold else '✗ FAIL'} (Method: {method})")
    
    logger.info("="*80)
    monitor.close()


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test enhanced sold property detection')
    parser.add_argument('--address', type=str, help='Test specific property by address')
    parser.add_argument('--test-methods', action='store_true', help='Test all detection methods')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('sold_property_monitor').setLevel(logging.DEBUG)
    
    if args.test_methods:
        test_detection_methods()
    elif args.address:
        test_specific_property(args.address)
    else:
        # Default: test the known problematic property
        logger.info("Testing known problematic property: 12 Carnoustie Court, Robina, QLD 4226")
        test_specific_property("12 Carnoustie Court, Robina, QLD 4226")
        
        logger.info("\n")
        logger.info("Running detection method tests...")
        test_detection_methods()


if __name__ == "__main__":
    main()
