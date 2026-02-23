# Last Edit: 31/01/2026, Friday, 7:40 pm (Brisbane Time)
"""
Ollama Vision API client module for property analysis.
Replaces OpenAI GPT with locally hosted Ollama llama3.2-vision:11b model.
"""
import json
import time
import requests
import base64
from io import BytesIO
from PIL import Image
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_TOKENS, TEMPERATURE, OLLAMA_TIMEOUT, MAX_RETRIES, RETRY_DELAY
from logger import logger
from prompts import get_property_analysis_prompt

class OllamaClient:
    """Client for interacting with Ollama Vision API."""
    
    def __init__(self):
        """Initialize Ollama client."""
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.timeout = OLLAMA_TIMEOUT
        logger.info(f"Initialized Ollama client with model: {self.model} at {self.base_url}")
        
        # Verify Ollama is running and model is available
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama server is running and model is available."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            if not any(self.model in name for name in model_names):
                logger.warning(f"Model {self.model} not found in Ollama. Available models: {model_names}")
                logger.warning(f"Please run: ollama pull {self.model}")
            else:
                logger.info(f"Model {self.model} is available")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            logger.error("Please ensure Ollama is running: ollama serve")
            raise
    
    def _download_and_encode_image(self, image_url):
        """
        Download image from URL and encode to base64.
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Base64 encoded image string
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Convert to base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            return image_data
            
        except Exception as e:
            logger.error(f"Failed to download/encode image {image_url}: {e}")
            return None
    
    def analyze_property_images(self, image_urls, address, max_images=30):
        """
        Analyze property images using Ollama Vision API with automatic retry.
        
        Args:
            image_urls: List of image URLs to analyze
            address: Property address for logging
            max_images: Maximum number of images to analyze (default 30)
            
        Returns:
            Parsed JSON response with property data
        """
        # Limit number of images for Ollama
        images_to_use = image_urls[:max_images]
        logger.info(f"Analyzing {len(images_to_use)} images for {address}")
        
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                start_time = time.time()
                
                # Download and encode images
                logger.info(f"Downloading and encoding {len(images_to_use)} images...")
                encoded_images = []
                for idx, url in enumerate(images_to_use):
                    encoded = self._download_and_encode_image(url)
                    if encoded:
                        encoded_images.append(encoded)
                    else:
                        logger.warning(f"Skipping image {idx} due to download failure")
                
                if not encoded_images:
                    raise ValueError("No images could be downloaded and encoded")
                
                logger.info(f"Successfully encoded {len(encoded_images)} images")
                
                # Prepare the prompt
                prompt = get_property_analysis_prompt()
                
                # Build the Ollama API request
                # Ollama expects images as base64 strings in the images array
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "images": encoded_images,
                    "stream": False,
                    "options": {
                        "temperature": TEMPERATURE,
                        "num_predict": MAX_TOKENS
                    },
                    "format": "json"  # Request JSON output
                }
                
                # Call Ollama API
                logger.info(f"Sending request to Ollama (attempt {attempt + 1}/{MAX_RETRIES})...")
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                # Check for errors and log response
                if response.status_code != 200:
                    logger.error(f"Ollama returned status {response.status_code}")
                    logger.error(f"Response: {response.text[:500]}")
                
                response.raise_for_status()
                
                elapsed_time = time.time() - start_time
                logger.info(f"Ollama analysis complete for {address} ({elapsed_time:.1f}s)")
                
                # Parse response
                response_data = response.json()
                content = response_data.get("response", "")
                
                # Log response for debugging
                if not content or len(content.strip()) == 0:
                    logger.error(f"Empty response from Ollama for {address}")
                    logger.error(f"Full response object: {response_data}")
                    raise ValueError("Empty response from Ollama")
                
                logger.debug(f"Response length: {len(content)} characters")
                
                # Parse JSON response
                result = json.loads(content)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response as JSON: {e}")
                logger.error(f"Response content (first 1000 chars): {content[:1000] if content else 'EMPTY'}")
                logger.error(f"Response content (last 500 chars): {content[-500:] if content and len(content) > 500 else ''}")
                last_error = e
                
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    raise
                
            except requests.exceptions.Timeout as e:
                logger.error(f"Ollama request timeout for {address}: {e}")
                last_error = e
                
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    raise
                
            except Exception as e:
                logger.error(f"Ollama API error for {address}: {e}")
                last_error = e
                
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    raise
        
        # If we exhausted all attempts, raise the last error
        logger.error(f"Failed to analyze images after {MAX_RETRIES} attempts for {address}")
        raise last_error
    
    def extract_image_analysis(self, analysis_result, image_urls):
        """
        Extract image analysis data with rankings and descriptions.
        
        Args:
            analysis_result: Parsed Ollama analysis result
            image_urls: Original list of image URLs
            
        Returns:
            List of image analysis data with URLs
        """
        image_analysis = analysis_result.get("image_analysis", [])
        
        if not image_analysis:
            logger.warning("No image analysis data found in Ollama response")
            return []
        
        # Add URLs to each image analysis entry
        enriched_analysis = []
        for img_data in image_analysis:
            image_index = img_data.get("image_index")
            if image_index is not None and 0 <= image_index < len(image_urls):
                enriched_data = img_data.copy()
                enriched_data["url"] = image_urls[image_index]
                enriched_analysis.append(enriched_data)
        
        # Sort by usefulness score (highest first)
        enriched_analysis.sort(key=lambda x: x.get("usefulness_score", 0), reverse=True)
        
        logger.info(f"Analyzed {len(enriched_analysis)} images with rankings and descriptions")
        
        return enriched_analysis
    
    def extract_property_data(self, analysis_result):
        """
        Extract property valuation data from analysis result.
        
        Args:
            analysis_result: Parsed Ollama analysis result
            
        Returns:
            Dictionary of property valuation data
        """
        property_data = {
            "structural": analysis_result.get("structural", {}),
            "exterior": analysis_result.get("exterior", {}),
            "interior": analysis_result.get("interior", {}),
            "renovation": analysis_result.get("renovation", {}),
            "outdoor": analysis_result.get("outdoor", {}),
            "layout": analysis_result.get("layout", {}),
            "overall": analysis_result.get("overall", {}),
            "metadata": analysis_result.get("metadata", {})
        }
        
        # Add extraction metadata
        property_data["metadata"]["model_used"] = self.model
        property_data["metadata"]["extracted_at"] = time.time()
        property_data["metadata"]["analysis_engine"] = "ollama"
        
        return property_data
