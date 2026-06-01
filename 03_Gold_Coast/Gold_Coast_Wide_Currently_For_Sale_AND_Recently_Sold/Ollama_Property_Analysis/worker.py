# Last Edit: 31/01/2026, Friday, 7:42 pm (Brisbane Time)
"""
Worker module for processing property documents with Ollama.
"""
import time
from ollama_client import OllamaClient
from mongodb_client_multi import MongoDBClientMulti
from logger import logger
from config import MAX_IMAGES_PER_PROPERTY

class PropertyWorker:
    """Worker for processing individual property documents."""
    
    def __init__(self, worker_id):
        """
        Initialize worker.
        
        Args:
            worker_id: Unique identifier for this worker
        """
        self.worker_id = worker_id
        self.ollama_client = OllamaClient()
        self.mongo_client = MongoDBClient()
        self.properties_processed = 0
        logger.info(f"Worker {worker_id} initialized")
    
    @staticmethod
    def _coerce_url_list(items):
        """Normalize a mixed image payload into a list of URL strings.

        Handles both plain string URLs and dict entries of the form
        {"url"/"src"/"image_url": "..."} — the scraper switched
        ``scraped_data.images`` to dict entries, which the old code passed
        through unchanged (dicts then read as "no images").
        """
        if not isinstance(items, list):
            return []

        urls = []
        for item in items:
            if isinstance(item, str) and item.strip():
                urls.append(item.strip().rstrip('\\'))
            elif isinstance(item, dict):
                for key in ("url", "src", "image_url"):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        urls.append(value.strip().rstrip('\\'))
                        break
        return urls

    def _extract_images(self, document):
        """
        Extract image URLs from document (supports multiple formats).

        Args:
            document: MongoDB document

        Returns:
            List of image URLs

        Accumulates across every known source with fallback rather than
        stopping at the first source whose key exists — a dict-shaped
        ``scraped_data.images`` previously short-circuited the elif chain.
        """
        scraped = document.get("scraped_data")
        scraped_images = scraped.get("images") if isinstance(scraped, dict) else None

        for source in (scraped_images, document.get("property_images"), document.get("images")):
            cleaned = self._coerce_url_list(source)
            if cleaned:
                return cleaned

        return []
    
    def _extract_address(self, document):
        """
        Extract property address from document.
        
        Args:
            document: MongoDB document
            
        Returns:
            Address string
        """
        # Try different possible locations for address
        if "address" in document:
            if isinstance(document["address"], str):
                return document["address"]
            elif isinstance(document["address"], dict):
                # Build address from components
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
    
    def process_document(self, document):
        """
        Process a single property document.
        
        Args:
            document: MongoDB document to process
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        document_id = document.get("_id")
        address = self._extract_address(document)
        
        try:
            logger.info(f"Worker {self.worker_id}: Processing {address}")
            
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
            
            # Update MongoDB
            self.mongo_client.update_with_ollama_analysis(
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
    
    def process_batch(self, documents):
        """
        Process a batch of documents.
        
        Args:
            documents: List of MongoDB documents
            
        Returns:
            Dictionary with processing statistics
        """
        batch_start = time.time()
        successful = 0
        failed = 0
        
        for doc in documents:
            if self.process_document(doc):
                successful += 1
            else:
                failed += 1
        
        batch_time = time.time() - batch_start
        
        stats = {
            "worker_id": self.worker_id,
            "total": len(documents),
            "successful": successful,
            "failed": failed,
            "batch_time": batch_time,
            "avg_time_per_property": batch_time / len(documents) if documents else 0
        }
        
        logger.info(f"Worker {self.worker_id}: Batch complete - {successful}/{len(documents)} successful ({batch_time:.1f}s)")
        
        return stats
    
    def close(self):
        """Clean up resources."""
        if self.mongo_client:
            self.mongo_client.close()
        logger.info(f"Worker {self.worker_id} closed ({self.properties_processed} properties processed)")
