"""
Test script for single property enrichment.
Last Edit: 13/02/2026, 3:52 PM (Thursday) — Brisbane Time

Description: Test the enrichment pipeline on a single property to verify
all methods are working correctly before running production.

Edit History:
- 13/02/2026 3:52 PM: Initial creation for testing
"""

import json
from mongodb_enrichment_client import MongoDBEnrichmentClient
from gpt_enrichment_client import GPTEnrichmentClient
from logger import logger


def test_single_property():
    """Test enrichment on a single property."""
    
    print("\n" + "=" * 70)
    print("SINGLE PROPERTY ENRICHMENT TEST")
    print("=" * 70 + "\n")
    
    # Connect to database
    logger.info("Connecting to database...")
    db_client = MongoDBEnrichmentClient()
    
    # Verify collections exist
    if not db_client.verify_collections_exist():
        logger.error("Missing collections - cannot proceed")
        return
    
    # Get a sample property
    logger.info("Fetching sample property from Robina...")
    property_data = db_client.get_sample_property('Robina')
    
    if not property_data:
        logger.error("No sample property found")
        return
    
    address = property_data.get('address', 'Unknown')
    property_id = property_data.get('_id', 'Unknown')
    
    print(f"\n📍 Testing Property:")
    print(f"   Address: {address}")
    print(f"   ID: {property_id}")
    print(f"   Suburb: Robina")
    print("\n" + "-" * 70 + "\n")
    
    # Initialize GPT client
    gpt_client = GPTEnrichmentClient()
    
    # Test each enrichment method
    results = {}
    
    print("🔍 Testing Enrichment Methods:\n")
    
    # 1. Building Condition
    print("1️⃣  Building Condition...")
    try:
        results['building_condition'] = gpt_client.enrich_building_condition(property_data)
        print(f"   ✅ Success: {results['building_condition'].get('overall_condition', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['building_condition'] = {'error': str(e)}
    
    # 2. Building Age
    print("2️⃣  Building Age...")
    try:
        results['building_age'] = gpt_client.enrich_building_age(property_data)
        print(f"   ✅ Success: {results['building_age'].get('year_built', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['building_age'] = {'error': str(e)}
    
    # 3. Busy Road
    print("3️⃣  Busy Road (OpenStreetMap)...")
    try:
        results['busy_road'] = gpt_client.enrich_busy_road(property_data)
        is_busy = results['busy_road'].get('is_busy', 'N/A')
        road_type = results['busy_road'].get('road_type', 'N/A')
        print(f"   ✅ Success: Busy={is_busy}, Type={road_type}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['busy_road'] = {'error': str(e)}
    
    # 4. Corner Block
    print("4️⃣  Corner Block...")
    try:
        results['corner_block'] = gpt_client.enrich_corner_block(property_data)
        is_corner = results['corner_block'].get('is_corner', 'N/A')
        source = results['corner_block'].get('data_source', 'N/A')
        print(f"   ✅ Success: Corner={is_corner}, Source={source}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['corner_block'] = {'error': str(e)}
    
    # 5. Parking
    print("5️⃣  Parking...")
    try:
        results['parking'] = gpt_client.enrich_parking(property_data)
        parking_type = results['parking'].get('type', 'N/A')
        spaces = results['parking'].get('total_spaces', 'N/A')
        print(f"   ✅ Success: Type={parking_type}, Spaces={spaces}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['parking'] = {'error': str(e)}
    
    # 6. Outdoor Entertainment
    print("6️⃣  Outdoor Entertainment...")
    try:
        results['outdoor_entertainment'] = gpt_client.enrich_outdoor_entertainment(property_data)
        score = results['outdoor_entertainment'].get('score', 'N/A')
        print(f"   ✅ Success: Score={score}/10")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['outdoor_entertainment'] = {'error': str(e)}
    
    # 7. Renovation Status
    print("7️⃣  Renovation Status...")
    try:
        results['renovation_status'] = gpt_client.enrich_renovation_status(property_data)
        status = results['renovation_status'].get('status', 'N/A')
        quality = results['renovation_status'].get('quality', 'N/A')
        print(f"   ✅ Success: Status={status}, Quality={quality}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['renovation_status'] = {'error': str(e)}
    
    # 8. North Facing (Bonus)
    print("8️⃣  North Facing...")
    try:
        results['north_facing'] = gpt_client.enrich_north_facing(property_data)
        north_facing = results['north_facing'].get('north_facing', 'N/A')
        print(f"   ✅ Success: North Facing={north_facing}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['north_facing'] = {'error': str(e)}
    
    # Summary
    print("\n" + "-" * 70)
    print("\n📊 TEST SUMMARY:\n")
    
    success_count = sum(1 for r in results.values() if 'error' not in r)
    total_count = len(results)
    
    print(f"   Successful: {success_count}/{total_count}")
    print(f"   Failed: {total_count - success_count}/{total_count}")
    print(f"   Success Rate: {(success_count / total_count * 100):.1f}%")
    
    # Save results
    output_file = 'test_single_property_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'property_id': str(property_id),
            'address': address,
            'enrichment_results': results
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Close connection
    db_client.close()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70 + "\n")
    
    if success_count == total_count:
        print("✅ All enrichment methods working correctly!")
        print("   Ready for production run.")
    else:
        print("⚠️  Some enrichment methods failed.")
        print("   Review errors before running production.")


if __name__ == "__main__":
    test_single_property()
