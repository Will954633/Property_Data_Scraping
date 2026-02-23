# Last Edit: 06/02/2026, Thursday, 9:40 AM (Brisbane Time)
# Ollama Vision API client for floor plan analysis with OpenAI GPT fallback
# OPTIMIZED: Now uses simplified prompt to avoid timeouts
# Uses llama3.2-vision:11b model to extract room dimensions and floor areas
# FALLBACK: After 2 Ollama failures, falls back to OpenAI GPT-4o for analysis

"""
Ollama Vision API client module for floor plan analysis.
Uses locally hosted Ollama llama3.2-vision:11b model.
Falls back to OpenAI GPT-4o after 2 Ollama failures.
"""
import json
import time
import requests
import base64
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_TOKENS, TEMPERATURE, OLLAMA_TIMEOUT, MAX_RETRIES, RETRY_DELAY, OPENAI_FALLBACK_ENABLED, USE_OPENAI_PRIMARY
from logger import logger
from prompts_floorplan import get_floor_plan_basic_prompt

class OllamaFloorPlanClient:
    """Client for analyzing floor plans using Ollama Vision API."""
    
    def __init__(self):
        """Initialize Ollama floor plan client."""
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.timeout = OLLAMA_TIMEOUT
        if USE_OPENAI_PRIMARY:
            logger.info("USE_OPENAI_PRIMARY=True: skipping Ollama connection check, using OpenAI directly")
            return

        logger.info(f"Initialized Ollama floor plan client with model: {self.model} at {self.base_url}")

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
                logger.info(f"Model {self.model} is available for floor plan analysis")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            logger.error("Please ensure Ollama is running: ollama serve")
            raise
    
    def _download_and_encode_image(self, image_url):
        """
        Download image from URL, convert to PNG if needed, and encode to base64.
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Base64 encoded image string (PNG format)
        """
        try:
            from PIL import Image
            from io import BytesIO
            
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Open image with PIL to handle format conversion
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary (handles RGBA, P mode, etc.)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Save as PNG to BytesIO
            png_buffer = BytesIO()
            img.save(png_buffer, format='PNG')
            png_data = png_buffer.getvalue()
            
            # Convert to base64
            image_data = base64.b64encode(png_data).decode('utf-8')
            
            logger.info(f"Converted image to PNG format ({len(png_data)} bytes)")
            return image_data
            
        except Exception as e:
            logger.error(f"Failed to download/encode image {image_url}: {e}")
            return None
    
    def _identify_floor_plan_images(self, image_urls, image_analysis=None, floor_plans_field=None):
        """
        Identify which images are floor plans.
        
        Args:
            image_urls: List of all image URLs
            image_analysis: Optional existing image analysis data with image types
            floor_plans_field: Optional dedicated floor_plans array from property document
            
        Returns:
            List of floor plan image URLs
        """
        floor_plan_urls = []
        
        # PRIORITY 1: Check dedicated floor_plans field (most reliable)
        if floor_plans_field and isinstance(floor_plans_field, list) and len(floor_plans_field) > 0:
            logger.info(f"Found {len(floor_plans_field)} floor plan(s) in dedicated floor_plans field")
            floor_plan_urls = floor_plans_field
            return floor_plan_urls
        
        # PRIORITY 2: If we have image analysis data, use it to identify floor plans
        if image_analysis:
            for img_data in image_analysis:
                image_type = img_data.get("image_type", "").lower()
                if "floor" in image_type or "plan" in image_type or "floorplan" in image_type:
                    image_index = img_data.get("image_index")
                    if image_index is not None and 0 <= image_index < len(image_urls):
                        floor_plan_urls.append(image_urls[image_index])
                        logger.info(f"Identified floor plan at index {image_index}: {image_type}")
        
        # PRIORITY 3: If no floor plans found via analysis, check URL patterns
        if not floor_plan_urls:
            logger.info("No floor plans identified from image analysis, checking URL patterns...")
            for url in image_urls:
                url_lower = url.lower()
                if any(keyword in url_lower for keyword in ['floor', 'plan', 'floorplan', 'layout']):
                    floor_plan_urls.append(url)
                    logger.info(f"Identified potential floor plan from URL: {url}")
        
        logger.info(f"Found {len(floor_plan_urls)} floor plan image(s)")
        return floor_plan_urls
    
    def analyze_floor_plan(self, floor_plan_url, address):
        """
        Analyze a single floor plan image using Ollama Vision API.
        
        Args:
            floor_plan_url: URL of the floor plan image
            address: Property address for logging
            
        Returns:
            Parsed JSON response with floor plan data
        """
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                start_time = time.time()
                
                # Download and encode floor plan image
                logger.info(f"Downloading floor plan image for {address}...")
                encoded_image = self._download_and_encode_image(floor_plan_url)
                
                if not encoded_image:
                    raise ValueError("Failed to download and encode floor plan image")
                
                logger.info(f"Successfully encoded floor plan image")
                
                # Prepare the prompt (using simplified version to avoid timeouts)
                prompt = get_floor_plan_basic_prompt()
                
                # Build the Ollama API request
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "images": [encoded_image],  # Single floor plan image
                    "stream": False,
                    "options": {
                        "temperature": TEMPERATURE,
                        "num_predict": -1  # -1 = unlimited, let model generate complete response
                    },
                    "format": "json"  # Request JSON output
                }
                
                # Call Ollama API
                logger.info(f"Sending floor plan to Ollama (attempt {attempt + 1}/{MAX_RETRIES})...")
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                # Check for errors
                if response.status_code != 200:
                    logger.error(f"Ollama returned status {response.status_code}")
                    logger.error(f"Response: {response.text[:500]}")
                
                response.raise_for_status()
                
                elapsed_time = time.time() - start_time
                logger.info(f"Floor plan analysis complete for {address} ({elapsed_time:.1f}s)")
                
                # Parse response
                response_data = response.json()
                content = response_data.get("response", "")
                
                # Log response for debugging
                if not content or len(content.strip()) == 0:
                    logger.error(f"Empty response from Ollama for {address}")
                    logger.error(f"Full response object: {response_data}")
                    raise ValueError("Empty response from Ollama")
                
                logger.debug(f"Response length: {len(content)} characters")
                
                # Try to parse JSON response
                try:
                    result = json.loads(content)
                    logger.info("JSON parsed successfully on first attempt")
                    return result
                except json.JSONDecodeError as json_error:
                    # Try to repair common JSON issues
                    logger.warning(f"Initial JSON parse failed: {json_error}")
                    logger.warning(f"Attempting repair strategies...")
                    
                    # Strategy 1: Remove trailing incomplete content
                    repaired_content = content.strip()
                    logger.info(f"Strategy 1: Stripped whitespace, length: {len(repaired_content)}")
                    
                    # Strategy 2: Find the last complete closing brace
                    last_brace = repaired_content.rfind('}')
                    logger.info(f"Strategy 2: Last closing brace found at position {last_brace}")
                    if last_brace > 0:
                        # Try truncating to last complete brace
                        truncated = repaired_content[:last_brace + 1]
                        logger.info(f"Attempting to parse truncated JSON (length: {len(truncated)})")
                        try:
                            result = json.loads(truncated)
                            logger.info("✓ Successfully repaired JSON by truncating to last complete brace!")
                            return result
                        except json.JSONDecodeError as e:
                            logger.warning(f"Truncation strategy failed: {e}")
                    
                    # Strategy 3: Count and balance braces
                    open_braces = repaired_content.count('{')
                    close_braces = repaired_content.count('}')
                    missing_braces = open_braces - close_braces
                    logger.info(f"Strategy 3: Open braces: {open_braces}, Close braces: {close_braces}, Missing: {missing_braces}")
                    
                    if missing_braces > 0:
                        logger.info(f"Attempting to balance by adding {missing_braces} closing braces")
                        balanced = repaired_content + ('}' * missing_braces)
                        
                        try:
                            result = json.loads(balanced)
                            logger.info("✓ Successfully repaired JSON by balancing braces!")
                            return result
                        except json.JSONDecodeError as e:
                            logger.warning(f"Balancing strategy failed: {e}")
                    
                    # Strategy 4: Try to extract valid JSON from the beginning
                    # Look for the first complete object
                    logger.info("Strategy 4: Attempting to extract first complete JSON object")
                    try:
                        # Find first { and try to parse incrementally
                        start = repaired_content.find('{')
                        if start >= 0:
                            depth = 0
                            for i in range(start, len(repaired_content)):
                                if repaired_content[i] == '{':
                                    depth += 1
                                elif repaired_content[i] == '}':
                                    depth -= 1
                                    if depth == 0:
                                        # Found complete object
                                        complete_json = repaired_content[start:i+1]
                                        logger.info(f"Found complete object at position {i}, attempting parse")
                                        result = json.loads(complete_json)
                                        logger.info("✓ Successfully extracted complete JSON object!")
                                        return result
                    except Exception as e:
                        logger.warning(f"Extraction strategy failed: {e}")
                    
                    # If all repair strategies failed, raise the original error
                    logger.error("✗ All 4 JSON repair strategies failed")
                    logger.error(f"Original error: {json_error}")
                    raise json_error
                
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
        logger.error(f"Failed to analyze floor plan after {MAX_RETRIES} attempts for {address}")
        raise last_error
    
    def analyze_property_floor_plans(self, image_urls, address, image_analysis=None, floor_plans_field=None):
        """
        Identify and analyze all floor plan images for a property.
        Falls back to OpenAI GPT after 2 Ollama failures.
        
        Args:
            image_urls: List of all property image URLs
            address: Property address for logging
            image_analysis: Optional existing image analysis data
            floor_plans_field: Optional dedicated floor_plans array from property document
            
        Returns:
            Dictionary with floor plan analysis results
        """
        ollama_attempts = 0
        max_ollama_attempts = 0 if USE_OPENAI_PRIMARY else 2  # Skip Ollama if USE_OPENAI_PRIMARY is True
        
        try:
            # Identify floor plan images
            floor_plan_urls = self._identify_floor_plan_images(image_urls, image_analysis, floor_plans_field)
            
            if not floor_plan_urls:
                logger.warning(f"No floor plans found for {address}")
                return {
                    "has_floor_plan": False,
                    "floor_plans_analyzed": 0,
                    "message": "No floor plan images identified"
                }
            
            # Check if we should skip Ollama and go straight to OpenAI
            if USE_OPENAI_PRIMARY:
                logger.info(f"🚀 USE_OPENAI_PRIMARY=True, skipping Ollama and using OpenAI directly for {address}")
                try:
                    from openai_floorplan_client import OpenAIFloorPlanClient
                    
                    openai_client = OpenAIFloorPlanClient()
                    result = openai_client.analyze_property_floor_plans(floor_plan_urls, address)
                    result["ollama_attempts"] = 0
                    result["primary_engine"] = "openai"
                    
                    logger.info(f"✓ Successfully analyzed floor plan(s) with OpenAI (primary) for {address}")
                    return result
                    
                except Exception as openai_error:
                    logger.error(f"❌ OpenAI (primary) failed for {address}: {openai_error}")
                    return {
                        "has_floor_plan": False,
                        "floor_plans_analyzed": 0,
                        "error": f"OpenAI primary failed: {openai_error}",
                        "message": "Floor plan analysis failed (OpenAI primary)",
                        "ollama_attempts": 0
                    }
            
            # Try Ollama first (up to 2 attempts)
            while ollama_attempts < max_ollama_attempts:
                ollama_attempts += 1
                try:
                    logger.info(f"Attempting Ollama analysis (attempt {ollama_attempts}/{max_ollama_attempts}) for {address}")
                    
                    # Analyze each floor plan (usually just one, but could be multiple levels)
                    floor_plan_analyses = []
                    
                    for idx, floor_plan_url in enumerate(floor_plan_urls):
                        logger.info(f"Analyzing floor plan {idx + 1}/{len(floor_plan_urls)} for {address}")
                        
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
                        "analysis_engine": "ollama",
                        "analyzed_at": time.time(),
                        "ollama_attempts": ollama_attempts
                    }
                    
                    logger.info(f"✓ Successfully analyzed {len(floor_plan_analyses)} floor plan(s) with Ollama for {address}")
                    return result
                    
                except Exception as ollama_error:
                    logger.error(f"Ollama attempt {ollama_attempts} failed for {address}: {ollama_error}")
                    
                    if ollama_attempts < max_ollama_attempts:
                        logger.info(f"Retrying with Ollama (attempt {ollama_attempts + 1}/{max_ollama_attempts})...")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        # After 2 Ollama failures, try OpenAI fallback
                        if OPENAI_FALLBACK_ENABLED:
                            logger.warning(f"⚠️  Ollama failed after {max_ollama_attempts} attempts for {address}")
                            logger.info(f"🔄 Falling back to OpenAI GPT for {address}...")
                            
                            try:
                                # Import OpenAI client only when needed
                                from openai_floorplan_client import OpenAIFloorPlanClient
                                
                                openai_client = OpenAIFloorPlanClient()
                                result = openai_client.analyze_property_floor_plans(floor_plan_urls, address)
                                result["ollama_attempts"] = ollama_attempts
                                result["fallback_used"] = True
                                
                                logger.info(f"✓ Successfully analyzed floor plan(s) with OpenAI fallback for {address}")
                                return result
                                
                            except Exception as openai_error:
                                logger.error(f"❌ OpenAI fallback also failed for {address}: {openai_error}")
                                return {
                                    "has_floor_plan": False,
                                    "floor_plans_analyzed": 0,
                                    "error": f"Both Ollama and OpenAI failed. Ollama: {ollama_error}, OpenAI: {openai_error}",
                                    "message": "Floor plan analysis failed (both engines)",
                                    "ollama_attempts": ollama_attempts,
                                    "fallback_attempted": True
                                }
                        else:
                            logger.error(f"❌ Ollama failed and OpenAI fallback is disabled")
                            return {
                                "has_floor_plan": False,
                                "floor_plans_analyzed": 0,
                                "error": str(ollama_error),
                                "message": "Floor plan analysis failed (Ollama only)",
                                "ollama_attempts": ollama_attempts
                            }
            
        except Exception as e:
            logger.error(f"Error analyzing floor plans for {address}: {e}")
            return {
                "has_floor_plan": False,
                "floor_plans_analyzed": 0,
                "error": str(e),
                "message": "Floor plan analysis failed",
                "ollama_attempts": ollama_attempts
            }
