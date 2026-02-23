# Last Edit: 20/02/2026, Thursday (Brisbane Time)
# OpenAI GPT Vision API client for floor plan analysis (PRIMARY)
# Uses gpt-5-nano-2025-08-07 model to extract room dimensions and floor areas

"""
OpenAI GPT Vision API client module for floor plan analysis.
This is a fallback client used when Ollama fails after 2 attempts.
"""
import json
import time
import requests
import base64
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, TEMPERATURE
from logger import logger
from prompts_floorplan import get_floor_plan_basic_prompt

class OpenAIFloorPlanClient:
    """Client for analyzing floor plans using OpenAI GPT Vision API as fallback."""
    
    def __init__(self):
        """Initialize OpenAI floor plan client."""
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
        self.timeout = OPENAI_TIMEOUT
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        logger.info(f"Initialized OpenAI floor plan fallback client with model: {self.model}")
    
    def _download_and_encode_image(self, image_url):
        """
        Download image from URL and encode to base64.
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Base64 encoded image string with data URI prefix
        """
        try:
            from PIL import Image
            from io import BytesIO
            
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Open image with PIL to handle format conversion
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Save as JPEG to BytesIO (OpenAI prefers JPEG)
            jpeg_buffer = BytesIO()
            img.save(jpeg_buffer, format='JPEG', quality=95)
            jpeg_data = jpeg_buffer.getvalue()
            
            # Convert to base64 with data URI
            image_data = base64.b64encode(jpeg_data).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{image_data}"
            
            logger.info(f"Converted image to JPEG format ({len(jpeg_data)} bytes)")
            return data_uri
            
        except Exception as e:
            logger.error(f"Failed to download/encode image {image_url}: {e}")
            return None
    
    def analyze_floor_plan(self, floor_plan_url, address):
        """
        Analyze a single floor plan image using OpenAI GPT Vision API.
        
        Args:
            floor_plan_url: URL of the floor plan image
            address: Property address for logging
            
        Returns:
            Parsed JSON response with floor plan data
        """
        try:
            start_time = time.time()
            
            # Download and encode floor plan image
            logger.info(f"[OPENAI FALLBACK] Downloading floor plan image for {address}...")
            encoded_image = self._download_and_encode_image(floor_plan_url)
            
            if not encoded_image:
                raise ValueError("Failed to download and encode floor plan image")
            
            logger.info(f"[OPENAI FALLBACK] Successfully encoded floor plan image")
            
            # Prepare the prompt
            prompt = get_floor_plan_basic_prompt()
            
            # Build the OpenAI API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": encoded_image,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                # gpt-5-nano only supports temperature=1 (default), so we omit it
                "max_completion_tokens": 16384,  # Increased for gpt-5-nano reasoning model (was 4096, too low)
                "response_format": {"type": "json_object"}
            }
            
            # Call OpenAI API
            logger.info(f"[OPENAI FALLBACK] Sending floor plan to OpenAI GPT...")
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"[OPENAI FALLBACK] OpenAI returned status {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
            
            response.raise_for_status()
            
            elapsed_time = time.time() - start_time
            logger.info(f"[OPENAI FALLBACK] Floor plan analysis complete for {address} ({elapsed_time:.1f}s)")
            
            # Parse response
            response_data = response.json()
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Log response for debugging
            if not content or len(content.strip()) == 0:
                logger.error(f"[OPENAI FALLBACK] Empty response from OpenAI for {address}")
                logger.error(f"Full response object: {response_data}")
                raise ValueError("Empty response from OpenAI")
            
            logger.debug(f"Response length: {len(content)} characters")
            
            # Parse JSON response
            result = json.loads(content)
            logger.info("[OPENAI FALLBACK] JSON parsed successfully")
            
            # Add metadata to indicate this was from OpenAI fallback
            result["analysis_engine"] = "openai_fallback"
            result["model_used"] = self.model
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"[OPENAI FALLBACK] Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Response content: {content[:1000] if content else 'EMPTY'}")
            raise
            
        except requests.exceptions.Timeout as e:
            logger.error(f"[OPENAI FALLBACK] OpenAI request timeout for {address}: {e}")
            raise
            
        except Exception as e:
            logger.error(f"[OPENAI FALLBACK] OpenAI API error for {address}: {e}")
            raise
    
    def analyze_property_floor_plans(self, floor_plan_urls, address):
        """
        Analyze floor plan images for a property using OpenAI.
        
        Args:
            floor_plan_urls: List of floor plan image URLs
            address: Property address for logging
            
        Returns:
            Dictionary with floor plan analysis results
        """
        try:
            if not floor_plan_urls:
                logger.warning(f"[OPENAI FALLBACK] No floor plans provided for {address}")
                return {
                    "has_floor_plan": False,
                    "floor_plans_analyzed": 0,
                    "message": "No floor plan images provided"
                }
            
            # Analyze each floor plan
            floor_plan_analyses = []
            
            for idx, floor_plan_url in enumerate(floor_plan_urls):
                logger.info(f"[OPENAI FALLBACK] Analyzing floor plan {idx + 1}/{len(floor_plan_urls)} for {address}")
                
                analysis = self.analyze_floor_plan(floor_plan_url, address)
                
                # Add metadata
                analysis["floor_plan_url"] = floor_plan_url
                analysis["floor_plan_index"] = idx
                
                floor_plan_analyses.append(analysis)
            
            # Combine results
            result = {
                "has_floor_plan": True,
                "floor_plans_analyzed": len(floor_plan_analyses),
                "floor_plan_data": floor_plan_analyses[0] if len(floor_plan_analyses) == 1 else floor_plan_analyses,
                "model_used": self.model,
                "analysis_engine": "openai_fallback",
                "analyzed_at": time.time()
            }
            
            logger.info(f"[OPENAI FALLBACK] Successfully analyzed {len(floor_plan_analyses)} floor plan(s) for {address}")
            
            return result
            
        except Exception as e:
            logger.error(f"[OPENAI FALLBACK] Error analyzing floor plans for {address}: {e}")
            return {
                "has_floor_plan": False,
                "floor_plans_analyzed": 0,
                "error": str(e),
                "message": "Floor plan analysis failed (OpenAI fallback)"
            }
