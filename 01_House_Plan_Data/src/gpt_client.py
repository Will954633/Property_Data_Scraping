"""
GPT Vision API client module for property analysis.
"""
import json
import time
from openai import OpenAI
from retry import retry
from config import OPENAI_API_KEY, GPT_MODEL, MAX_TOKENS, TEMPERATURE, MAX_RETRIES, RETRY_DELAY
from logger import logger
from prompts import get_property_analysis_prompt

class GPTClient:
    """Client for interacting with OpenAI GPT Vision API."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = GPT_MODEL
        logger.info(f"Initialized GPT client with model: {self.model}")
    
    def analyze_property_images(self, image_urls, address, max_images=50):
        """
        Analyze property images using GPT Vision API with automatic retry on size limit.
        
        Args:
            image_urls: List of image URLs to analyze
            address: Property address for logging
            max_images: Maximum number of images to analyze (default 50)
            
        Returns:
            Parsed JSON response with property data
        """
        # Try with full set first, then reduce if size limit exceeded
        attempts = [
            (max_images, "high"),      # Try with high detail first
            (max_images, "low"),       # If size limit, try low detail
            (max_images // 2, "low"),  # If still too big, try half the images
            (max_images // 4, "low"),  # If still too big, try quarter
            (10, "low")                # Last resort: 10 images
        ]
        
        last_error = None
        
        for num_images, detail_level in attempts:
            try:
                images_to_use = image_urls[:num_images]
                logger.info(f"Analyzing {len(images_to_use)} images for {address} (detail: {detail_level})")
                start_time = time.time()
                
                # Prepare messages with images
                message_content = [
                    {
                        "type": "text",
                        "text": get_property_analysis_prompt()
                    }
                ]
                
                # Add images to message
                for url in images_to_use:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": url,
                            "detail": detail_level
                        }
                    })
            
                messages = [
                    {
                        "role": "system",
                        "content": "You are a property valuation expert with extensive knowledge of real estate assessment and floor plan analysis."
                    },
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
                
                # Call GPT API
                # Note: gpt-5-nano only supports default temperature=1, so we omit the parameter
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_completion_tokens=MAX_TOKENS,  # gpt-5-nano uses max_completion_tokens instead of max_tokens
                    response_format={"type": "json_object"}
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"GPT analysis complete for {address} ({elapsed_time:.1f}s)")
                
                # Parse response
                content = response.choices[0].message.content
                
                # Log response for debugging
                if not content or len(content.strip()) == 0:
                    logger.error(f"Empty response from GPT for {address}")
                    logger.error(f"Full response object: {response}")
                    raise ValueError("Empty response from GPT")
                
                logger.debug(f"Response length: {len(content)} characters")
                
                result = json.loads(content)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {e}")
                logger.error(f"Response content (first 1000 chars): {content[:1000] if content else 'EMPTY'}")
                logger.error(f"Response content (last 500 chars): {content[-500:] if content and len(content) > 500 else ''}")
                raise
                
            except Exception as e:
                error_str = str(e)
                last_error = e
                
                # Check if it's a size limit error
                if "exceeds the allowed limit" in error_str or "Total image size" in error_str:
                    logger.warning(f"Image size limit exceeded, trying with fewer images/lower detail...")
                    continue
                
                # Check if it's a timeout error downloading an image
                elif "Timeout while downloading" in error_str or "Error while downloading" in error_str:
                    logger.warning(f"Image download timeout/error, retrying with different settings...")
                    continue
                
                # For other errors, raise immediately
                else:
                    logger.error(f"GPT API error for {address}: {e}")
                    raise
        
        # If we exhausted all attempts, raise the last error
        logger.error(f"Failed to analyze images after all attempts for {address}")
        raise last_error
    
    def extract_image_analysis(self, analysis_result, image_urls):
        """
        Extract image analysis data with rankings and descriptions.
        
        Args:
            analysis_result: Parsed GPT analysis result
            image_urls: Original list of image URLs
            
        Returns:
            List of image analysis data with URLs
        """
        image_analysis = analysis_result.get("image_analysis", [])
        
        if not image_analysis:
            logger.warning("No image analysis data found in GPT response")
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
            analysis_result: Parsed GPT analysis result
            
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
        
        return property_data
