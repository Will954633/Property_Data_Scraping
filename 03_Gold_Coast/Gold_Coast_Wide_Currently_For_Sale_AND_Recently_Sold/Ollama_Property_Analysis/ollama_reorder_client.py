# Last Edit: 01/02/2026, Saturday, 8:17 am (Brisbane Time)
# Ollama client for photo reordering - uses text-only model for JSON generation

"""
Ollama client for photo reordering.
Uses llama3.2:3b text model for fast JSON generation.
"""
import json
import requests
from typing import Dict, List, Any
from config import OLLAMA_BASE_URL, OLLAMA_TIMEOUT, MAX_RETRIES, RETRY_DELAY
from prompts_reorder import get_photo_reorder_prompt
from logger import logger
import time

class OllamaReorderClient:
    """Client for Ollama photo reordering using text model."""
    
    def __init__(self):
        """Initialize Ollama reorder client."""
        self.base_url = OLLAMA_BASE_URL
        self.model = "llama3.2:3b"  # Fast text model for JSON generation
        self.timeout = OLLAMA_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        
        logger.info(f"Initialized Ollama Reorder Client")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Model: {self.model}")
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama connection check failed: {e}")
            return False
    
    def _extract_json_from_response(self, text: str) -> Dict:
        """
        Extract JSON from Ollama response text.
        Handles cases where model includes extra text around JSON.
        """
        # Try to find JSON in the response
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("No JSON found in response")
        
        json_str = text[start_idx:end_idx + 1]
        return json.loads(json_str)
    
    def reorder_photos(self, image_analysis: List[Dict]) -> Dict[str, Any]:
        """
        Create optimal photo tour order from image analysis data.
        
        Args:
            image_analysis: List of image analysis dictionaries from ollama_image_analysis
            
        Returns:
            Dictionary with photo_tour_order and tour_metadata
        """
        if not self._check_ollama_connection():
            raise ConnectionError("Ollama is not running or not accessible")
        
        # Build the prompt with image analysis data
        prompt = get_photo_reorder_prompt()
        
        # Format image analysis data for the prompt
        images_text = "\n\nAVAILABLE IMAGES:\n"
        for img in image_analysis:
            images_text += f"\nImage {img.get('image_index', 'N/A')}:\n"
            images_text += f"  - Type: {img.get('image_type', 'unknown')}\n"
            images_text += f"  - Usefulness Score: {img.get('usefulness_score', 0)}\n"
            images_text += f"  - Description: {img.get('description', 'No description')}\n"
            images_text += f"  - URL: {img.get('url', 'No URL')}\n"
        
        full_prompt = prompt + images_text
        
        # Make request to Ollama with retries
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Requesting photo reorder from Ollama (attempt {attempt + 1}/{self.max_retries})")
                
                payload = {
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 4096
                    }
                }
                
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract the response text
                response_text = result.get('response', '')
                
                # Parse JSON from response
                reorder_data = self._extract_json_from_response(response_text)
                
                # Validate the response structure
                if 'photo_tour_order' not in reorder_data:
                    raise ValueError("Response missing 'photo_tour_order' field")
                
                if 'tour_metadata' not in reorder_data:
                    raise ValueError("Response missing 'tour_metadata' field")
                
                logger.info(f"Successfully generated photo tour with {len(reorder_data['photo_tour_order'])} photos")
                
                return reorder_data
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Ollama response (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ollama request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise
                    
            except Exception as e:
                logger.error(f"Unexpected error during photo reordering: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise
        
        raise Exception("Failed to generate photo tour after all retries")
