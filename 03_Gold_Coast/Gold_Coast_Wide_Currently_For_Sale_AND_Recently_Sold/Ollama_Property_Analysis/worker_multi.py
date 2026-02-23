# Last Edit: 31/01/2026, Friday, 7:55 pm (Brisbane Time)
"""
Worker module for processing property documents with Ollama.
Handles multiple suburb collections.
"""
import time
from ollama_client_single_image import OllamaClientSingleImage
from mongodb_client_multi import MongoDBClientMulti
from logger import logger
from config import MAX_IMAGES_PER_PROPERTY

class PropertyWorkerMulti:
    """Worker for processing individual property documents across multiple collections."""
    
    def __init__(self, worker_id):
        """
        Initialize worker.
        
        Args:
            worker_id: Unique identifier for this worker
        """
        self.worker_id = worker_id
        self.ollama_client = OllamaClientSingleImage()
        self.mongo_client = MongoDBClientMulti()
        self.properties_processed = 0
        logger.info(f"Worker {worker_id} initialized")
    
    def _extract_images(self, document):
        """Extract image URLs from document (supports multiple formats)."""
        images = []
        
        if "scraped_data" in document and "images" in document["scraped_data"]:
            images = document["scraped_data"]["images"]
        elif "property_images" in document:
            images = document["property_images"]
        elif "images" in document:
            images = document["images"]
        
        if not isinstance(images, list):
            images = []
        
        # Clean URLs - remove trailing backslashes that cause 404 errors
        cleaned_images = []
        for url in images:
            if isinstance(url, str):
                # Remove trailing backslash
                cleaned_url = url.rstrip('\\')
                cleaned_images.append(cleaned_url)
        
        return cleaned_images
    
    def _extract_address(self, document):
        """Extract property address from document."""
        if "address" in document:
            if isinstance(document["address"], str):
                return document["address"]
            elif isinstance(document["address"], dict):
                parts = []
                for key in ["street", "suburb", "state", "postcode"]:
                    if key in document["address"]:
                        parts.append(str(document["address"][key]))
                return ", ".join(parts) if parts else "Unknown Address"
        
        if "scraped_data" in document and "address" in document["scraped_data"]:
            return document["scraped_data"]["address"]
        
        if "property_details" in document and "address" in document["property_details"]:
            return document["property_details"]["address"]
        
        return f"Property {document.get('_id', 'Unknown')}"
    
    def process_document(self, suburb, document):
        """
        Process a single property document.
        
        Args:
            suburb: Suburb collection name
            document: MongoDB document to process
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        document_id = document.get("_id")
        address = self._extract_address(document)
        
        try:
            logger.info(f"Worker {self.worker_id}: Processing {address} ({suburb})")
            
            # Extract images
            image_urls = self._extract_images(document)
            
            if not image_urls:
                logger.warning(f"Worker {self.worker_id}: No images found for {address}")
                return False
            
            logger.info(f"Worker {self.worker_id}: Found {len(image_urls)} images")
            
            # Analyze with Ollama
            analysis_result = self.ollama_client.analyze_property_images(
                image_urls,
                address,
                max_images=MAX_IMAGES_PER_PROPERTY
            )
            
            # Extract structured data
            image_analysis = self.ollama_client.extract_image_analysis(analysis_result, image_urls)
            property_data = self.ollama_client.extract_property_data(analysis_result)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update MongoDB (pass suburb parameter)
            self.mongo_client.update_with_ollama_analysis(
                suburb,
                document_id,
                image_analysis,
                property_data,
                worker_id=self.worker_id,
                processing_time=processing_time
            )
            
            self.properties_processed += 1
            logger.info(f"Worker {self.worker_id}: Successfully processed {address} ({processing_time:.1f}s)")
            
            return True
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Failed to process {address}: {e}")
            return False
    
    def process_batch(self, documents_with_suburbs):
        """
        Process a batch of documents.
        
        Args:
            documents_with_suburbs: List of tuples (suburb, document)
            
        Returns:
            Dictionary with processing statistics
        """
        batch_start = time.time()
        successful = 0
        failed = 0
        
        for suburb, doc in documents_with_suburbs:
            if self.process_document(suburb, doc):
                successful += 1
            else:
                failed += 1
        
        batch_time = time.time() - batch_start
        
        stats = {
            "worker_id": self.worker_id,
            "total": len(documents_with_suburbs),
            "successful": successful,
            "failed": failed,
            "batch_time": batch_time,
            "avg_time_per_property": batch_time / len(documents_with_suburbs) if documents_with_suburbs else 0
        }
        
        logger.info(f"Worker {self.worker_id}: Batch complete - {successful}/{len(documents_with_suburbs)} successful ({batch_time:.1f}s)")
        
        return stats
    
    def close(self):
        """Clean up resources."""
        if self.mongo_client:
            self.mongo_client.close()
        logger.info(f"Worker {self.worker_id} closed ({self.properties_processed} properties processed)")
