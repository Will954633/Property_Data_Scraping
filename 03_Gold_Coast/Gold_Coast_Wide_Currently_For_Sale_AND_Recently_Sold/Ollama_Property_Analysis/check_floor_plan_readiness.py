# Last Edit: 01/02/2026, Saturday, 8:52 am (Brisbane Time)
# Check if properties are ready for floor plan analysis
# Verifies database state and property analysis completion

"""
Check database readiness for floor plan analysis.
"""
from mongodb_floorplan_client import MongoDBFloorPlanClient
from config import TARGET_SUBURBS
from logger import logger

def main():
    """Check database state."""
    logger.info("=" * 80)
    logger.info("FLOOR PLAN ANALYSIS READINESS CHECK")
    logger.info("=" * 80)
    
    mongo_client = MongoDBFloorPlanClient()
    
    logger.info("\nChecking each suburb collection...")
    
    for suburb in TARGET_SUBURBS:
        collection = mongo_client.db[suburb]
        
        # Total properties
        total = collection.count_documents({})
        
        # Properties with ollama_image_analysis
        with_analysis = collection.count_documents({
            "ollama_image_analysis": {"$exists": True, "$ne": []}
        })
        
        # Properties with floor plan analysis
        with_floor_plan = collection.count_documents({
            "ollama_floor_plan_analysis.has_floor_plan": True
        })
        
        # Properties ready for floor plan analysis
        ready = collection.count_documents({
            "$and": [
                {"ollama_image_analysis": {"$exists": True, "$ne": []}},
                {"ollama_floor_plan_analysis.has_floor_plan": {"$ne": True}}
            ]
        })
        
        logger.info(f"\n{suburb}:")
        logger.info(f"  Total properties: {total}")
        logger.info(f"  With ollama_image_analysis: {with_analysis}")
        logger.info(f"  With floor plan analysis: {with_floor_plan}")
        logger.info(f"  Ready for floor plan analysis: {ready}")
        
        # Count properties with dedicated floor_plans field
        with_floor_plans_field = collection.count_documents({
            "floor_plans": {"$exists": True, "$ne": []}
        })
        
        logger.info(f"  Properties with floor_plans field: {with_floor_plans_field}")
        
        # Sample a property with ollama_image_analysis if available
        if with_analysis > 0:
            sample = collection.find_one({
                "ollama_image_analysis": {"$exists": True, "$ne": []}
            })
            
            if sample:
                address = sample.get("address", str(sample["_id"]))
                if isinstance(address, dict):
                    address = address.get("full_address", str(sample["_id"]))
                
                image_analysis = sample.get("ollama_image_analysis", [])
                floor_plans_field = sample.get("floor_plans", [])
                
                # Check for floor plans in image analysis
                floor_plans_in_analysis = [img for img in image_analysis if "floor" in img.get("image_type", "").lower() or "plan" in img.get("image_type", "").lower()]
                
                logger.info(f"  Sample property: {address}")
                logger.info(f"    Images analyzed: {len(image_analysis)}")
                logger.info(f"    Has floor_plans field: {len(floor_plans_field) > 0}")
                logger.info(f"    Floor plans in dedicated field: {len(floor_plans_field)}")
                logger.info(f"    Floor plans in image analysis: {len(floor_plans_in_analysis)}")
    
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    
    stats = mongo_client.get_floor_plan_stats()
    logger.info(f"Total properties ready for floor plan analysis: {stats['total_needing_analysis']}")
    logger.info(f"Total properties with floor plan analysis: {stats['total_with_floor_plans']}")
    
    if stats['total_needing_analysis'] == 0:
        logger.info("\n⚠️  No properties are ready for floor plan analysis yet.")
        logger.info("This means either:")
        logger.info("  1. Property analysis (run_production.py) hasn't completed yet")
        logger.info("  2. No properties have ollama_image_analysis field")
        logger.info("\nNext steps:")
        logger.info("  - Wait for property analysis to complete")
        logger.info("  - Or run: python3 run_production.py")
    else:
        logger.info(f"\n✓ {stats['total_needing_analysis']} properties are ready for floor plan analysis!")
        logger.info("\nTo analyze floor plans, run:")
        logger.info("  python3 test_floor_plan_single.py  # Test on one property")
        logger.info("  python3 ollama_floor_plan_analysis.py  # Process all properties")
    
    mongo_client.close()

if __name__ == "__main__":
    main()
