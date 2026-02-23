# Last Edit: 01/02/2026, Thursday, 8:52 pm (Brisbane Time)
# Main script for Ollama-based photo reordering system
# FIXED: Address field handling - address can be string or dict

"""
Ollama Photo Reordering System for Gold Coast Properties
Creates optimal photo tour sequences from existing ollama_image_analysis data.
"""
import sys
import time
from datetime import datetime
from mongodb_reorder_client import MongoDBReorderClient
from ollama_reorder_client import OllamaReorderClient
from logger import logger

class OllamaPhotoReorder:
    """Main coordinator for photo reordering."""
    
    def __init__(self):
        """Initialize the photo reorder system."""
        self.db_client = None
        self.ollama_client = None
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "total_processing_time": 0
        }
    
    def initialize(self):
        """Initialize database and Ollama clients."""
        logger.info("="*60)
        logger.info("OLLAMA PHOTO REORDERING SYSTEM")
        logger.info("="*60)
        logger.info(f"Database: Gold_Coast_Currently_For_Sale")
        logger.info(f"Model: llama3.2:3b (text-only)")
        logger.info("="*60)
        
        try:
            # Initialize MongoDB client
            logger.info("Initializing MongoDB client...")
            self.db_client = MongoDBReorderClient()
            
            # Initialize Ollama client
            logger.info("Initializing Ollama client...")
            self.ollama_client = OllamaReorderClient()
            
            # Get initial stats
            stats = self.db_client.get_reordering_stats()
            logger.info(f"\nInitial Statistics:")
            logger.info(f"  Properties with analysis: {stats['properties_with_analysis']}")
            logger.info(f"  Properties with tours: {stats['properties_with_tours']}")
            logger.info(f"  Properties needing reorder: {stats['properties_needing_reorder']}")
            
            if stats['properties_needing_reorder'] == 0:
                logger.warning("No properties need reordering. Exiting.")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}", exc_info=True)
            return False
    
    def process_property(self, property_doc):
        """
        Process a single property to create photo tour.
        
        Args:
            property_doc: Property document from MongoDB
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_id = property_doc.get('_id')
            collection_name = property_doc.get('_collection')
            address = property_doc.get('address', {})
            
            # Handle address being either string or dict
            if isinstance(address, str):
                display_address = address
            elif isinstance(address, dict):
                display_address = address.get('display_address', str(doc_id))
            else:
                display_address = str(doc_id)
            
            logger.info(f"\nProcessing property: {display_address}")
            logger.info(f"Collection: {collection_name}")
            
            # Get image analysis data
            image_analysis = property_doc.get('ollama_image_analysis', [])
            
            if not image_analysis:
                logger.warning(f"No image analysis data found for {doc_id}")
                return False
            
            logger.info(f"Found {len(image_analysis)} analyzed images")
            
            # Generate photo tour order
            start_time = time.time()
            
            reorder_data = self.ollama_client.reorder_photos(image_analysis)
            
            processing_time = time.time() - start_time
            
            # Extract photo tour and metadata
            photo_tour_order = reorder_data.get('photo_tour_order', [])
            tour_metadata = reorder_data.get('tour_metadata', {})
            
            logger.info(f"Generated tour with {len(photo_tour_order)} photos in {processing_time:.1f}s")
            logger.info(f"Tour completeness score: {tour_metadata.get('tour_completeness_score', 'N/A')}")
            
            # Update database
            success = self.db_client.update_with_photo_tour(
                doc_id,
                collection_name,
                photo_tour_order,
                tour_metadata,
                processing_time
            )
            
            if success:
                self.stats['successful'] += 1
                self.stats['total_processing_time'] += processing_time
                logger.info(f"✓ Successfully created photo tour for {doc_id}")
                return True
            else:
                self.stats['failed'] += 1
                logger.error(f"✗ Failed to update database for {doc_id}")
                return False
            
        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"Error processing property: {e}", exc_info=True)
            return False
        finally:
            self.stats['processed'] += 1
    
    def run(self, limit=None):
        """
        Main execution method.
        
        Args:
            limit: Maximum number of properties to process (None for all)
        """
        try:
            if not self.initialize():
                return False
            
            # Get properties for reordering
            logger.info("\nFetching properties for reordering...")
            properties = self.db_client.get_properties_for_reordering()
            
            if not properties:
                logger.warning("No properties found for reordering")
                return False
            
            # Apply limit if specified
            if limit:
                properties = properties[:limit]
                logger.info(f"Processing limited to {limit} properties")
            
            logger.info(f"Processing {len(properties)} properties...")
            logger.info("="*60)
            
            # Process each property
            for i, prop in enumerate(properties, 1):
                logger.info(f"\n[{i}/{len(properties)}] Processing property...")
                self.process_property(prop)
                
                # Log progress every 10 properties
                if i % 10 == 0:
                    self.log_progress()
            
            # Final summary
            self.log_final_summary()
            
            return True
            
        except KeyboardInterrupt:
            logger.warning("\nInterrupted by user")
            self.log_final_summary()
            return False
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            return False
        finally:
            if self.db_client:
                self.db_client.close()
    
    def log_progress(self):
        """Log current progress."""
        logger.info("\n" + "-"*60)
        logger.info("PROGRESS UPDATE")
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        if self.stats['successful'] > 0:
            avg_time = self.stats['total_processing_time'] / self.stats['successful']
            logger.info(f"Avg processing time: {avg_time:.1f}s")
        logger.info("-"*60)
    
    def log_final_summary(self):
        """Log final summary of processing."""
        logger.info("\n" + "="*60)
        logger.info("PROCESSING COMPLETE")
        logger.info("="*60)
        logger.info(f"Total Processed: {self.stats['processed']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        if self.stats['successful'] > 0:
            avg_time = self.stats['total_processing_time'] / self.stats['successful']
            logger.info(f"Average Processing Time: {avg_time:.1f}s/property")
            logger.info(f"Total Processing Time: {self.stats['total_processing_time']:.1f}s")
        
        # Get final stats
        if self.db_client:
            final_stats = self.db_client.get_reordering_stats()
            logger.info(f"\nFinal Statistics:")
            logger.info(f"  Properties with tours: {final_stats['properties_with_tours']}")
            logger.info(f"  Properties still needing reorder: {final_stats['properties_needing_reorder']}")
        
        logger.info("="*60)

def main():
    """Main entry point."""
    print("="*60)
    print("OLLAMA PHOTO REORDERING SYSTEM")
    print("="*60)
    print("Creating optimal photo tours for Gold Coast properties")
    print()
    
    # Check for limit argument
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"Processing limit: {limit} properties")
        except ValueError:
            print("Invalid limit argument. Processing all properties.")
    
    reorder_system = OllamaPhotoReorder()
    success = reorder_system.run(limit=limit)
    
    if success:
        print("\n" + "="*60)
        print("✓ Photo reordering completed successfully!")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("✗ Processing failed or was interrupted")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
