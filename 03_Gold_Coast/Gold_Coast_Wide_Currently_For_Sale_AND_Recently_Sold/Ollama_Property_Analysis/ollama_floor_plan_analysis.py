# Last Edit: 01/02/2026, Saturday, 8:51 am (Brisbane Time)
# Main floor plan analysis script using Ollama Vision API
# Processes properties that have been analyzed but need floor plan extraction

"""
Main script for analyzing floor plans using Ollama Vision API.
Processes properties from Gold Coast suburbs that have ollama_image_analysis
but don't have floor plan analysis yet.
"""
import time
from mongodb_floorplan_client import MongoDBFloorPlanClient
from ollama_floorplan_client import OllamaFloorPlanClient
from logger import logger

def get_property_images(property_doc):
    """
    Extract image URLs from property document.
    
    Args:
        property_doc: Property document from MongoDB
        
    Returns:
        List of image URLs
    """
    # Try different possible image field locations
    if "scraped_data" in property_doc and "images" in property_doc["scraped_data"]:
        return property_doc["scraped_data"]["images"]
    elif "property_images" in property_doc:
        return property_doc["property_images"]
    elif "images" in property_doc:
        return property_doc["images"]
    else:
        return []

def get_property_address(property_doc):
    """
    Extract property address from document.
    
    Args:
        property_doc: Property document from MongoDB
        
    Returns:
        Property address string
    """
    # Try different possible address field locations
    if "address" in property_doc:
        if isinstance(property_doc["address"], str):
            return property_doc["address"]
        elif isinstance(property_doc["address"], dict):
            return property_doc["address"].get("full_address", str(property_doc["_id"]))
    elif "scraped_data" in property_doc and "address" in property_doc["scraped_data"]:
        return property_doc["scraped_data"]["address"]
    else:
        return str(property_doc["_id"])

def get_property_suburb(property_doc):
    """
    Extract suburb from property document.
    
    Args:
        property_doc: Property document from MongoDB
        
    Returns:
        Suburb name
    """
    # Try different possible suburb field locations
    if "suburb" in property_doc:
        return property_doc["suburb"]
    elif "address" in property_doc and isinstance(property_doc["address"], dict):
        return property_doc["address"].get("suburb", "unknown")
    elif "scraped_data" in property_doc and "suburb" in property_doc["scraped_data"]:
        return property_doc["scraped_data"]["suburb"]
    else:
        return "unknown"

def process_property(property_doc, ollama_client, mongo_client):
    """
    Process a single property for floor plan analysis.
    
    Args:
        property_doc: Property document from MongoDB
        ollama_client: OllamaFloorPlanClient instance
        mongo_client: MongoDBFloorPlanClient instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        start_time = time.time()
        
        # Extract property information
        property_id = property_doc["_id"]
        address = get_property_address(property_doc)
        suburb = get_property_suburb(property_doc)
        image_urls = get_property_images(property_doc)
        
        logger.info(f"Processing property: {address}")
        logger.info(f"  Suburb: {suburb}")
        logger.info(f"  Total images: {len(image_urls)}")
        
        if not image_urls:
            logger.warning(f"No images found for {address}")
            return False
        
        # Get existing image analysis if available
        image_analysis = property_doc.get("ollama_image_analysis", [])
        
        # Get dedicated floor_plans field if available
        floor_plans_field = property_doc.get("floor_plans", [])
        
        # Analyze floor plans
        floor_plan_analysis = ollama_client.analyze_property_floor_plans(
            image_urls=image_urls,
            address=address,
            image_analysis=image_analysis,
            floor_plans_field=floor_plans_field
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Update database
        mongo_client.update_with_floor_plan_analysis(
            document_id=property_id,
            suburb=suburb,
            floor_plan_analysis=floor_plan_analysis,
            processing_time=processing_time
        )
        
        if floor_plan_analysis.get("has_floor_plan"):
            logger.info(f"✓ Successfully analyzed floor plan for {address} ({processing_time:.1f}s)")
        else:
            logger.info(f"○ No floor plan found for {address} ({processing_time:.1f}s)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error processing property {address}: {e}", exc_info=True)
        return False

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("OLLAMA FLOOR PLAN ANALYSIS")
    logger.info("=" * 80)
    
    # Initialize clients
    logger.info("Initializing clients...")
    mongo_client = MongoDBFloorPlanClient()
    ollama_client = OllamaFloorPlanClient()
    
    # Get initial statistics
    logger.info("\nInitial Statistics:")
    stats = mongo_client.get_floor_plan_stats()
    logger.info(f"  Total properties with floor plan analysis: {stats['total_with_floor_plans']}")
    logger.info(f"  Total properties needing analysis: {stats['total_needing_analysis']}")
    
    for suburb, suburb_stats in stats["by_suburb"].items():
        if suburb_stats["needing_analysis"] > 0:
            logger.info(f"    {suburb}: {suburb_stats['needing_analysis']} properties")
    
    # Get properties needing analysis
    logger.info("\nFetching properties needing floor plan analysis...")
    properties = mongo_client.get_properties_needing_floor_plan_analysis()
    
    if not properties:
        logger.info("No properties need floor plan analysis!")
        mongo_client.close()
        return
    
    logger.info(f"Found {len(properties)} properties to process")
    logger.info("=" * 80)
    
    # Process each property
    start_time = time.time()
    success_count = 0
    error_count = 0
    floor_plans_found = 0
    
    for idx, property_doc in enumerate(properties, 1):
        logger.info(f"\n[{idx}/{len(properties)}] Processing property...")
        
        success = process_property(property_doc, ollama_client, mongo_client)
        
        if success:
            success_count += 1
            # Check if floor plan was found
            address = get_property_address(property_doc)
            suburb = get_property_suburb(property_doc)
            
            # Re-fetch to check if floor plan was found
            collection = mongo_client.db[suburb]
            updated_doc = collection.find_one({"_id": property_doc["_id"]})
            if updated_doc and updated_doc.get("ollama_floor_plan_analysis", {}).get("has_floor_plan"):
                floor_plans_found += 1
        else:
            error_count += 1
        
        # Progress update every 10 properties
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / idx
            remaining = (len(properties) - idx) * avg_time
            logger.info(f"\nProgress: {idx}/{len(properties)} ({idx/len(properties)*100:.1f}%)")
            logger.info(f"  Success: {success_count}, Errors: {error_count}, Floor plans found: {floor_plans_found}")
            logger.info(f"  Elapsed: {elapsed/60:.1f}min, Est. remaining: {remaining/60:.1f}min")
    
    # Final statistics
    total_time = time.time() - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total properties processed: {len(properties)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Floor plans found: {floor_plans_found}")
    logger.info(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    logger.info(f"Average per property: {total_time/len(properties):.1f}s")
    logger.info("=" * 80)
    
    # Get final statistics
    logger.info("\nFinal Statistics:")
    final_stats = mongo_client.get_floor_plan_stats()
    logger.info(f"  Total properties with floor plan analysis: {final_stats['total_with_floor_plans']}")
    logger.info(f"  Total properties needing analysis: {final_stats['total_needing_analysis']}")
    
    for suburb, suburb_stats in final_stats["by_suburb"].items():
        logger.info(f"    {suburb}: {suburb_stats['with_floor_plan_analysis']} analyzed, {suburb_stats['needing_analysis']} remaining")
    
    # Close connections
    mongo_client.close()
    logger.info("\nFloor plan analysis complete!")

if __name__ == "__main__":
    main()
