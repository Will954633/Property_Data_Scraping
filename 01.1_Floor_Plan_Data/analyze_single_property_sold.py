"""
Script to analyze floor plans for a single property in the sold_last_6_months collection.
This is for testing and manual review of the analysis quality.
"""
import json
import os
import sys

# Ensure we target the sold_last_6_months collection
os.environ.setdefault("DATABASE_NAME", "property_data")
os.environ["COLLECTION_NAME"] = "sold_last_6_months"

from gpt_client import GPTFloorPlanClient
from mongodb_client import MongoDBFloorPlanClient
from logger import logger


def analyze_single_property_sold(address=None):
    """Analyze floor plans for a single sold property.

    Args:
        address: Optional specific address. If None, will get first property with floor plans.
    """
    # Initialize clients
    logger.info("=" * 80)
    logger.info("FLOOR PLAN ANALYSIS - SINGLE SOLD PROPERTY TEST (sold_last_6_months)")
    logger.info("=" * 80)

    mongo_client = MongoDBFloorPlanClient()
    gpt_client = GPTFloorPlanClient()

    try:
        # Get property
        if address:
            property_doc = mongo_client.get_property_by_address(address)
            if not property_doc or not property_doc.get("floor_plans"):
                logger.error(f"Property {address} not found or has no floor plans")
                return
        else:
            property_doc = mongo_client.get_property_with_floor_plans()
            if not property_doc:
                logger.error("No properties with floor plans found in sold_last_6_months")
                return

        address = property_doc.get("address", "Unknown")
        floor_plans = property_doc.get("floor_plans", [])

        logger.info(f"\nProperty: {address}")
        logger.info(f"Floor plans found: {len(floor_plans)}")
        for i, url in enumerate(floor_plans, 1):
            logger.info(f"  {i}. {url}")

        # Analyze floor plans
        logger.info("\nStarting GPT analysis...")
        analysis_result = gpt_client.analyze_floor_plans(floor_plans, address)

        if not analysis_result:
            logger.error("Analysis failed - no result returned")
            return

        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS RESULTS")
        logger.info("=" * 80)

        # Pretty print the JSON result
        print(json.dumps(analysis_result, indent=2))

        # Save to output file
        output_file = f"output/floor_plan_analysis_sold_{address.replace('/', '_').replace(' ', '_')}.json"
        with open(output_file, "w") as f:
            json.dump(analysis_result, f, indent=2)
        logger.info(f"\nAnalysis saved to: {output_file}")

        # Ask user if they want to save to database
        logger.info("\n" + "=" * 80)
        response = input("\nSave this analysis to MongoDB (sold_last_6_months)? (yes/no): ").strip().lower()

        if response in ["yes", "y"]:
            success = mongo_client.update_floor_plan_analysis(address, analysis_result)
            if success:
                logger.info("✓ Analysis saved to database successfully!")
            else:
                logger.error("✗ Failed to save analysis to database")
        else:
            logger.info("Analysis not saved to database (user declined)")

        # Display summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)

        if "total_floor_area" in analysis_result:
            area = analysis_result["total_floor_area"]
            logger.info(
                f"Total Floor Area: {area.get('value')} {area.get('unit')} (confidence: {area.get('confidence')})"
            )

        if "bedrooms" in analysis_result:
            bedrooms = analysis_result["bedrooms"]
            logger.info(f"Bedrooms: {bedrooms.get('total_count')}")

        if "bathrooms" in analysis_result:
            bathrooms = analysis_result["bathrooms"]
            logger.info(f"Bathrooms: {bathrooms.get('total_count')}")

        if "parking" in analysis_result:
            parking = analysis_result["parking"]
            logger.info(f"Parking: {parking.get('total_spaces')} spaces")

        if "rooms" in analysis_result:
            logger.info(f"Total Rooms Identified: {len(analysis_result['rooms'])}")

        if "orientation_analysis" in analysis_result:
            orientation = analysis_result["orientation_analysis"]
            logger.info(f"Orientation Confidence: {orientation.get('confidence')}")
            logger.info(f"Methodology: {orientation.get('methodology')}")

        if "data_quality" in analysis_result:
            quality = analysis_result["data_quality"]
            logger.info(f"Overall Confidence: {quality.get('confidence_overall')}")
            logger.info(f"Floor Plan Clarity: {quality.get('floor_plan_clarity')}")

        logger.info("\n" + "=" * 80)
        logger.info("Analysis complete! Please review the results above.")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise

    finally:
        mongo_client.close()


if __name__ == "__main__":
    # Check if address provided as command line argument
    if len(sys.argv) > 1:
        address = " ".join(sys.argv[1:])
        logger.info(f"Analyzing specific sold property: {address}")
        analyze_single_property_sold(address)
    else:
        logger.info("No address specified - will analyze first sold property with floor plans")
        analyze_single_property_sold()
