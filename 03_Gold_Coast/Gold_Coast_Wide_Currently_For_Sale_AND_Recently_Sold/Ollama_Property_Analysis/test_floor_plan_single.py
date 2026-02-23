# Last Edit: 01/02/2026, Saturday, 8:52 am (Brisbane Time)
# Test script for floor plan analysis on a single property
# Tests the complete floor plan analysis workflow

"""
Test script for floor plan analysis using Ollama Vision API.
Tests on a single property to validate the system works correctly.
"""
import json
from mongodb_floorplan_client import MongoDBFloorPlanClient
from ollama_floorplan_client import OllamaFloorPlanClient
from logger import logger

def get_property_images(property_doc):
    """Extract image URLs from property document."""
    if "scraped_data" in property_doc and "images" in property_doc["scraped_data"]:
        return property_doc["scraped_data"]["images"]
    elif "property_images" in property_doc:
        return property_doc["property_images"]
    elif "images" in property_doc:
        return property_doc["images"]
    else:
        return []

def get_property_address(property_doc):
    """Extract property address from document."""
    if "address" in property_doc:
        if isinstance(property_doc["address"], str):
            return property_doc["address"]
        elif isinstance(property_doc["address"], dict):
            return property_doc["address"].get("full_address", str(property_doc["_id"]))
    elif "scraped_data" in property_doc and "address" in property_doc["scraped_data"]:
        return property_doc["scraped_data"]["address"]
    else:
        return str(property_doc["_id"])

def main():
    """Main test function."""
    logger.info("=" * 80)
    logger.info("FLOOR PLAN ANALYSIS - SINGLE PROPERTY TEST")
    logger.info("=" * 80)
    
    # Initialize clients
    logger.info("Initializing clients...")
    mongo_client = MongoDBFloorPlanClient()
    ollama_client = OllamaFloorPlanClient()
    
    # Get statistics
    logger.info("\nCurrent Statistics:")
    stats = mongo_client.get_floor_plan_stats()
    logger.info(f"  Total properties with floor plan analysis: {stats['total_with_floor_plans']}")
    logger.info(f"  Total properties needing analysis: {stats['total_needing_analysis']}")
    
    # Get one property for testing
    logger.info("\nFetching a test property...")
    properties = mongo_client.get_properties_needing_floor_plan_analysis()
    
    if not properties:
        logger.info("No properties available for testing!")
        logger.info("All properties have been analyzed or no properties have ollama_image_analysis yet.")
        mongo_client.close()
        return
    
    # Use the first property
    test_property = properties[0]
    property_id = test_property["_id"]
    address = get_property_address(test_property)
    suburb = test_property.get("suburb", "unknown")
    image_urls = get_property_images(test_property)
    image_analysis = test_property.get("ollama_image_analysis", [])
    floor_plans_field = test_property.get("floor_plans", [])
    
    logger.info(f"\nTest Property:")
    logger.info(f"  Address: {address}")
    logger.info(f"  Suburb: {suburb}")
    logger.info(f"  Total images: {len(image_urls)}")
    logger.info(f"  Has image analysis: {len(image_analysis) > 0}")
    logger.info(f"  Has dedicated floor_plans field: {len(floor_plans_field) > 0}")
    
    if floor_plans_field:
        logger.info(f"  Floor plans in dedicated field: {len(floor_plans_field)}")
        for idx, fp_url in enumerate(floor_plans_field):
            logger.info(f"    - Floor plan {idx + 1}: {fp_url[:80]}...")
    
    if image_analysis:
        # Check if any images are identified as floor plans
        floor_plan_images = [img for img in image_analysis if "floor" in img.get("image_type", "").lower() or "plan" in img.get("image_type", "").lower()]
        logger.info(f"  Floor plans identified in image analysis: {len(floor_plan_images)}")
        
        if floor_plan_images:
            for fp in floor_plan_images:
                logger.info(f"    - Image {fp.get('image_index')}: {fp.get('image_type')}")
    
    logger.info("\n" + "=" * 80)
    logger.info("STARTING FLOOR PLAN ANALYSIS")
    logger.info("=" * 80)
    
    # Analyze floor plans
    import time
    start_time = time.time()
    
    try:
        floor_plan_analysis = ollama_client.analyze_property_floor_plans(
            image_urls=image_urls,
            address=address,
            image_analysis=image_analysis,
            floor_plans_field=floor_plans_field
        )
        
        processing_time = time.time() - start_time
        
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS RESULTS")
        logger.info("=" * 80)
        logger.info(f"Processing time: {processing_time:.1f}s")
        logger.info(f"Has floor plan: {floor_plan_analysis.get('has_floor_plan')}")
        logger.info(f"Floor plans analyzed: {floor_plan_analysis.get('floor_plans_analyzed', 0)}")
        
        if floor_plan_analysis.get("has_floor_plan"):
            logger.info("\nFloor Plan Data:")
            floor_plan_data = floor_plan_analysis.get("floor_plan_data", {})
            
            # Display key information
            if "internal_floor_area" in floor_plan_data:
                internal_area = floor_plan_data["internal_floor_area"]
                logger.info(f"  Internal Floor Area: {internal_area.get('value')} {internal_area.get('unit')} (confidence: {internal_area.get('confidence')})")
            
            if "total_floor_area" in floor_plan_data:
                total_area = floor_plan_data["total_floor_area"]
                logger.info(f"  Total Floor Area: {total_area.get('value')} {total_area.get('unit')} (confidence: {total_area.get('confidence')})")
            
            if "bedrooms" in floor_plan_data:
                bedrooms = floor_plan_data["bedrooms"]
                logger.info(f"  Bedrooms: {bedrooms.get('total_count')}")
            
            if "bathrooms" in floor_plan_data:
                bathrooms = floor_plan_data["bathrooms"]
                logger.info(f"  Bathrooms: {bathrooms.get('total_count')} (Full: {bathrooms.get('full_bathrooms')}, Ensuites: {bathrooms.get('ensuites')})")
            
            if "parking" in floor_plan_data:
                parking = floor_plan_data["parking"]
                logger.info(f"  Parking: {parking.get('total_spaces')} spaces ({parking.get('garage_type', 'N/A')})")
            
            if "rooms" in floor_plan_data:
                rooms = floor_plan_data["rooms"]
                logger.info(f"  Total rooms extracted: {len(rooms)}")
            
            # Display full JSON for inspection
            logger.info("\nFull Floor Plan Analysis (JSON):")
            logger.info(json.dumps(floor_plan_analysis, indent=2))
        else:
            logger.info(f"\nMessage: {floor_plan_analysis.get('message', 'No floor plan found')}")
        
        # Save to database
        logger.info("\n" + "=" * 80)
        logger.info("SAVING TO DATABASE")
        logger.info("=" * 80)
        
        mongo_client.update_with_floor_plan_analysis(
            document_id=property_id,
            suburb=suburb,
            floor_plan_analysis=floor_plan_analysis,
            processing_time=processing_time
        )
        
        logger.info("✓ Successfully saved floor plan analysis to database")
        
        # Verify it was saved
        collection = mongo_client.db[suburb]
        updated_doc = collection.find_one({"_id": property_id})
        
        if updated_doc and "ollama_floor_plan_analysis" in updated_doc:
            logger.info("✓ Verified: Floor plan analysis field exists in database")
            saved_analysis = updated_doc["ollama_floor_plan_analysis"]
            logger.info(f"  Has floor plan: {saved_analysis.get('has_floor_plan')}")
            logger.info(f"  Processed at: {saved_analysis.get('processed_at')}")
        else:
            logger.warning("⚠ Warning: Could not verify floor plan analysis in database")
        
    except Exception as e:
        logger.error(f"✗ Error during floor plan analysis: {e}", exc_info=True)
    
    # Final statistics
    logger.info("\n" + "=" * 80)
    logger.info("FINAL STATISTICS")
    logger.info("=" * 80)
    
    final_stats = mongo_client.get_floor_plan_stats()
    logger.info(f"  Total properties with floor plan analysis: {final_stats['total_with_floor_plans']}")
    logger.info(f"  Total properties needing analysis: {final_stats['total_needing_analysis']}")
    
    # Close connections
    mongo_client.close()
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
