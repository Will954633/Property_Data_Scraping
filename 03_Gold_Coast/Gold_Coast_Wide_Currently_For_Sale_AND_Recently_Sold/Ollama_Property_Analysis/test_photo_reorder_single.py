# Last Edit: 01/02/2026, Saturday, 8:20 am (Brisbane Time)
# Test script for photo reordering - tests with a single property

"""
Test script for Ollama photo reordering system.
Tests with a single property to verify functionality.
"""
import sys
from mongodb_reorder_client import MongoDBReorderClient
from ollama_reorder_client import OllamaReorderClient
from logger import logger
import json
import time

def test_single_property():
    """Test photo reordering with a single property."""
    
    print("="*60)
    print("TESTING OLLAMA PHOTO REORDERING - SINGLE PROPERTY")
    print("="*60)
    
    try:
        # Initialize clients
        print("\n1. Initializing MongoDB client...")
        db_client = MongoDBReorderClient()
        
        print("2. Initializing Ollama client...")
        ollama_client = OllamaReorderClient()
        
        # Get stats
        print("\n3. Getting statistics...")
        stats = db_client.get_reordering_stats()
        print(f"   Properties with analysis: {stats['properties_with_analysis']}")
        print(f"   Properties with tours: {stats['properties_with_tours']}")
        print(f"   Properties needing reorder: {stats['properties_needing_reorder']}")
        
        if stats['properties_needing_reorder'] == 0:
            print("\n✗ No properties available for testing")
            return False
        
        # Get one property
        print("\n4. Fetching a property for testing...")
        properties = db_client.get_properties_for_reordering()
        
        if not properties:
            print("✗ No properties found")
            return False
        
        test_property = properties[0]
        doc_id = test_property.get('_id')
        collection_name = test_property.get('_collection')
        address = test_property.get('address', {})
        
        # Handle address being either dict or string
        if isinstance(address, dict):
            address_str = address.get('display_address', str(address))
        else:
            address_str = str(address)
        
        print(f"\n   Selected property:")
        print(f"   - ID: {doc_id}")
        print(f"   - Collection: {collection_name}")
        print(f"   - Address: {address_str}")
        
        # Get image analysis
        image_analysis = test_property.get('ollama_image_analysis', [])
        print(f"   - Images analyzed: {len(image_analysis)}")
        
        if not image_analysis:
            print("\n✗ No image analysis data found")
            return False
        
        # Show sample of image analysis
        print("\n5. Sample of image analysis data:")
        for i, img in enumerate(image_analysis[:3], 1):
            print(f"   Image {i}:")
            print(f"     - Index: {img.get('image_index')}")
            print(f"     - Type: {img.get('image_type')}")
            print(f"     - Usefulness: {img.get('usefulness_score')}/10")
            print(f"     - Description: {img.get('description', 'N/A')[:60]}...")
        
        if len(image_analysis) > 3:
            print(f"   ... and {len(image_analysis) - 3} more images")
        
        # Generate photo tour
        print("\n6. Generating photo tour order...")
        start_time = time.time()
        
        reorder_data = ollama_client.reorder_photos(image_analysis)
        
        processing_time = time.time() - start_time
        
        print(f"   ✓ Generated in {processing_time:.1f}s")
        
        # Display results
        photo_tour_order = reorder_data.get('photo_tour_order', [])
        tour_metadata = reorder_data.get('tour_metadata', {})
        
        print(f"\n7. Photo Tour Results:")
        print(f"   - Photos in tour: {len(photo_tour_order)}")
        print(f"   - Sections included: {', '.join(tour_metadata.get('sections_included', []))}")
        print(f"   - Sections missing: {', '.join(tour_metadata.get('sections_missing', []))}")
        print(f"   - Average usefulness: {tour_metadata.get('average_usefulness_score', 'N/A')}")
        print(f"   - Tour completeness: {tour_metadata.get('tour_completeness_score', 'N/A')}/10")
        
        print(f"\n8. Photo Tour Sequence:")
        for photo in photo_tour_order:
            print(f"   {photo['reorder_position']}. {photo['tour_section']}")
            print(f"      - Image index: {photo['image_index']}")
            print(f"      - Usefulness: {photo['usefulness_score']}/10")
            print(f"      - Reason: {photo['selection_reason'][:60]}...")
        
        # Update database
        print(f"\n9. Updating database...")
        success = db_client.update_with_photo_tour(
            doc_id,
            collection_name,
            photo_tour_order,
            tour_metadata,
            processing_time
        )
        
        if success:
            print("   ✓ Database updated successfully")
        else:
            print("   ✗ Failed to update database")
            return False
        
        # Verify update
        print("\n10. Verifying update...")
        final_stats = db_client.get_reordering_stats()
        print(f"    Properties with tours: {final_stats['properties_with_tours']}")
        print(f"    Properties needing reorder: {final_stats['properties_needing_reorder']}")
        
        # Close connection
        db_client.close()
        
        print("\n" + "="*60)
        print("✓ TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"\nThe photo tour has been created and saved to:")
        print(f"  Database: Gold_Coast_Currently_For_Sale")
        print(f"  Collection: {collection_name}")
        print(f"  Document ID: {doc_id}")
        print(f"\nFields added:")
        print(f"  - ollama_photo_tour_order (array of {len(photo_tour_order)} photos)")
        print(f"  - ollama_photo_reorder_status (metadata)")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_single_property()
    sys.exit(0 if success else 1)
