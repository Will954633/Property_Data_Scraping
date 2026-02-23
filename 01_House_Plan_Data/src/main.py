"""
Main execution script for property valuation data extraction system.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from config import (
    TEST_MODE, STOP_AT_FIRST_HOUSE_PLAN, BATCH_SIZE,
    MAX_IMAGES_PER_PROPERTY, OUTPUT_DIR
)
from logger import logger
from mongodb_client import MongoDBClient
from gpt_client import GPTClient

class PropertyValuationExtractor:
    """Main orchestrator for property valuation data extraction."""
    
    def __init__(self):
        """Initialize extractor components."""
        self.mongo_client = None
        self.gpt_client = None
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_documents_queried": 0,
            "documents_with_images": 0,
            "documents_processed": 0,
            "house_plans_found": 0,
            "first_house_plan_address": None,
            "first_house_plan_document": None,
            "processed_documents": []
        }
    
    def initialize(self):
        """Initialize MongoDB and GPT clients."""
        logger.info("Initializing Property Valuation Extractor")
        logger.info(f"TEST_MODE: {TEST_MODE}")
        logger.info(f"STOP_AT_FIRST_HOUSE_PLAN: {STOP_AT_FIRST_HOUSE_PLAN}")
        
        try:
            self.mongo_client = MongoDBClient()
            self.gpt_client = GPTClient()
            logger.info("Initialization complete")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    def process_document(self, document):
        """
        Process a single document.
        
        Args:
            document: MongoDB document
            
        Returns:
            dict with processing results
        """
        doc_id = document.get("_id")
        # Try multiple paths for address
        address = (document.get("complete_address") or 
                  document.get("address") or 
                  document.get("scraped_data", {}).get("address") or
                  "Unknown Address")
        
        # Images can be in scraped_data.images OR property_images
        scraped_data = document.get("scraped_data", {})
        images = scraped_data.get("images", [])
        
        # If no images in scraped_data, check property_images
        if not images:
            images = document.get("property_images", [])
        
        logger.info(f"Processing document: {address}")
        logger.info(f"Images found: {len(images)}")
        
        process_start = time.time()
        
        try:
            # Extract URLs from image objects
            # Images can be stored as: [{"url": "...", "index": 0, "date": "..."}] or ["url1", "url2", ...]
            if images and isinstance(images[0], dict):
                image_urls = [img.get("url") for img in images if img.get("url")]
            else:
                # Simple string array format (property_images)
                image_urls = images
            
            # Clean URLs - remove trailing backslashes and filter out invalid URLs
            cleaned_urls = []
            for url in image_urls:
                if url:
                    # Remove trailing backslashes
                    cleaned_url = url.rstrip('\\')
                    # Only include valid URLs (not empty after cleaning)
                    if cleaned_url and not cleaned_url.endswith('\\'):
                        cleaned_urls.append(cleaned_url)
            
            # Limit number of images
            images_to_analyze = cleaned_urls[:MAX_IMAGES_PER_PROPERTY]
            
            # Call GPT API
            analysis_result = self.gpt_client.analyze_property_images(
                images_to_analyze, 
                address
            )
            
            # Extract image analysis with rankings and descriptions
            image_analysis = self.gpt_client.extract_image_analysis(
                analysis_result,
                images_to_analyze
            )
            
            # Extract property valuation data
            property_data = self.gpt_client.extract_property_data(analysis_result)
            
            # Update MongoDB with image analysis
            self.mongo_client.update_with_image_analysis(
                doc_id,
                image_analysis,
                property_data
            )
            
            process_time = time.time() - process_start
            logger.info(f"Document processed successfully ({process_time:.1f}s)")
            
            # Build result
            result = {
                "address": address,
                "document_id": str(doc_id),
                "images_count": len(images),
                "images_analyzed": len(image_analysis),
                "processing_time_seconds": round(process_time, 1),
                "processed_at": datetime.utcnow().isoformat(),
                "image_analysis": image_analysis,
                "property_data": property_data
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {address}: {e}")
            return {
                "address": address,
                "document_id": str(doc_id),
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }
    
    def save_results(self):
        """Save processing results to output files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save test run summary
        summary_file = Path(OUTPUT_DIR) / f"test_run_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        logger.info(f"Saved test run summary to {summary_file}")
        
        # Save first house plan details if found
        if self.stats["first_house_plan_document"]:
            first_plan_file = Path(OUTPUT_DIR) / f"first_house_plan_{timestamp}.json"
            with open(first_plan_file, 'w') as f:
                json.dump(self.stats["first_house_plan_document"], f, indent=2, default=str)
            logger.info(f"Saved first house plan details to {first_plan_file}")
    
    def run(self):
        """Execute the main processing pipeline."""
        if not self.initialize():
            logger.error("Failed to initialize. Exiting.")
            return False
        
        self.stats["start_time"] = datetime.utcnow().isoformat()
        
        try:
            # Get document statistics
            total_docs = self.mongo_client.get_total_documents()
            docs_with_images = self.mongo_client.get_documents_with_images_count()
            
            self.stats["total_documents_queried"] = total_docs
            self.stats["documents_with_images"] = docs_with_images
            
            logger.info(f"Total documents in collection: {total_docs}")
            logger.info(f"Documents with images: {docs_with_images}")
            logger.info("Starting processing...")
            
            # Get documents to process
            documents = self.mongo_client.get_documents_with_images()
            
            # Process documents
            for document in documents:
                result = self.process_document(document)
                
                self.stats["documents_processed"] += 1
                self.stats["processed_documents"].append(result)
                
                # Log image analysis results
                images_analyzed = result.get("images_analyzed", 0)
                if images_analyzed > 0:
                    logger.info(f"Analyzed {images_analyzed} images with rankings and descriptions")
                
                # In test mode with batch size 1, process one at a time
                if TEST_MODE and BATCH_SIZE == 1:
                    logger.info(f"Processed {self.stats['documents_processed']} document(s)")
            
            self.stats["end_time"] = datetime.utcnow().isoformat()
            
            # Log final summary
            logger.info("")
            logger.info("=" * 50)
            logger.info("Processing Summary:")
            logger.info("=" * 50)
            logger.info(f"Documents processed: {self.stats['documents_processed']}")
            logger.info("=" * 50)
            
            # Save results
            self.save_results()
            
            logger.info("Processing complete!")
            return True
            
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            return False
            
        finally:
            if self.mongo_client:
                self.mongo_client.close()

def main():
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("GPT-Powered Property Valuation Data Extraction")
    logger.info("=" * 50)
    
    extractor = PropertyValuationExtractor()
    success = extractor.run()
    
    if success:
        logger.info("Execution completed successfully")
        return 0
    else:
        logger.error("Execution failed")
        return 1

if __name__ == "__main__":
    exit(main())
