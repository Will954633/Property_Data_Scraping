"""
GPT enrichment client for property data enrichment.
Last Edit: 13/02/2026, 3:43 PM (Thursday) — Brisbane Time

Description: Main GPT client with all 7 enrichment methods, retry logic,
OpenStreetMap integration for busy road detection, and Google Maps integration
for corner block detection.

Edit History:
- 13/02/2026 3:43 PM: Initial creation for production pipeline
"""

import json
import time
from typing import Dict, Any, List, Optional
import requests

from openai import OpenAI
from config import (
    OPENAI_API_KEY, GPT_MODEL, MAX_TOKENS, REQUEST_TIMEOUT,
    GOOGLE_MAPS_API_KEY, MAX_RETRIES, RETRY_DELAY_BASE,
    OSM_RATE_LIMIT_DELAY, MAX_IMAGES_PER_PROPERTY, PREFERRED_IMAGE_DOMAIN
)
from logger import logger
from enrichment_prompts import (
    get_building_condition_prompt, get_building_age_prompt,
    get_parking_prompt, get_outdoor_entertainment_prompt,
    get_renovation_status_prompt, get_corner_block_prompt,
    get_north_facing_prompt
)


class GPTEnrichmentClient:
    """
    Client for enriching property data using GPT Vision API.
    
    Includes:
    - All 7 enrichment methods
    - Retry logic with exponential backoff
    - OpenStreetMap integration (busy road detection)
    - Google Maps integration (corner block detection)
    - Reliable image URL selection
    """
    
    def __init__(self):
        """Initialize OpenAI client and validate configuration."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = GPT_MODEL
        self.google_maps_available = bool(GOOGLE_MAPS_API_KEY)
        
        logger.info(f"Initialized GPT enrichment client with model: {self.model}")
        if self.google_maps_available:
            logger.info("Google Maps API available for corner block detection")
        else:
            logger.warning("Google Maps API not available - will use GPT fallback")
    
    # ========================================================================
    # IMAGE URL SELECTION
    # ========================================================================
    
    def get_reliable_image_urls(self, property_images: List[str], 
                               max_images: int = None) -> List[str]:
        """
        Select most reliable image URLs from property_images list.
        Prefer rimh2.domainstatic.com over bucket-api.domain.com.au
        
        Args:
            property_images: List of image URLs
            max_images: Maximum number of images to return
        
        Returns:
            List of reliable image URLs
        """
        if max_images is None:
            max_images = MAX_IMAGES_PER_PROPERTY
        
        # Filter for preferred domain URLs
        preferred_urls = [
            url for url in property_images 
            if PREFERRED_IMAGE_DOMAIN in url
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in preferred_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        # Return up to max_images
        selected = unique_urls[:max_images]
        logger.debug(f"Selected {len(selected)} reliable images from {len(property_images)} total")
        return selected
    
    # ========================================================================
    # CORE GPT ANALYSIS METHOD
    # ========================================================================
    
    def analyze_with_gpt(self, prompt: str, image_urls: List[str] = None,
                        description: str = None, field_name: str = "unknown") -> Dict[str, Any]:
        """
        Generic GPT analysis with retry logic.
        
        Args:
            prompt: GPT prompt text
            image_urls: Optional list of image URLs
            description: Optional property description to include
            field_name: Name of field being enriched (for logging)
        
        Returns:
            Parsed JSON response from GPT
        """
        # Build message content
        message_content = []
        
        full_prompt = prompt
        if description:
            full_prompt += f"\n\nProperty Description:\n{description}"
        
        message_content.append({"type": "text", "text": full_prompt})
        
        if image_urls:
            for url in image_urls:
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": url, "detail": "high"}
                })
        
        messages = [
            {
                "role": "system",
                "content": "You are a professional property analyst with expertise in real estate valuation and property assessment."
            },
            {"role": "user", "content": message_content}
        ]
        
        # Retry logic
        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"GPT API call for {field_name} (attempt {attempt + 1}/{MAX_RETRIES})")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_completion_tokens=MAX_TOKENS,
                    response_format={"type": "json_object"},
                    timeout=REQUEST_TIMEOUT
                )
                
                content = response.choices[0].message.content.strip()
                
                if not content:
                    raise ValueError(f"Empty response from GPT for {field_name}")
                
                result = json.loads(content)
                logger.debug(f"Successfully parsed GPT response for {field_name}")
                return result
                
            except Exception as e:
                error_msg = str(e)
                if 'Timeout' in error_msg or 'invalid_image_url' in error_msg:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY_BASE ** attempt
                        logger.warning(f"Error on attempt {attempt + 1} for {field_name}: {e}")
                        logger.info(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                logger.error(f"GPT API error for {field_name}: {e}")
                return {"error": str(e), "field": field_name}
        
        return {"error": "Max retries exceeded", "field": field_name}
    
    # ========================================================================
    # ENRICHMENT METHOD 1: BUILDING CONDITION
    # ========================================================================
    
    def enrich_building_condition(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze building condition from property photos.
        
        Returns:
            {
                "overall_condition": "excellent|good|fair|poor",
                "confidence": "high|medium|low",
                "observations": [...],
                "maintenance_level": "well-maintained|average|needs-work",
                "evidence": "..."
            }
        """
        logger.info("Enriching: building_condition")
        
        images = property_data.get('property_images', [])
        reliable_images = self.get_reliable_image_urls(images)
        
        if not reliable_images:
            logger.warning("No reliable images available for building condition")
            return {"error": "No reliable images available"}
        
        prompt = get_building_condition_prompt()
        result = self.analyze_with_gpt(prompt, reliable_images, field_name="building_condition")
        
        return result
    
    # ========================================================================
    # ENRICHMENT METHOD 2: BUILDING AGE
    # ========================================================================
    
    def enrich_building_age(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate building age from property photos.
        
        Returns:
            {
                "year_built": 2010,
                "year_range": "2008-2012",
                "confidence": "high|medium|low",
                "evidence": [...],
                "era": "modern|contemporary|established|heritage"
            }
        """
        logger.info("Enriching: building_age")
        
        images = property_data.get('property_images', [])
        reliable_images = self.get_reliable_image_urls(images)
        
        if not reliable_images:
            logger.warning("No reliable images available for building age")
            return {"error": "No reliable images available"}
        
        prompt = get_building_age_prompt()
        result = self.analyze_with_gpt(prompt, reliable_images, field_name="building_age")
        
        return result
    
    # ========================================================================
    # ENRICHMENT METHOD 3: BUSY ROAD (OpenStreetMap)
    # ========================================================================
    
    def enrich_busy_road(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if property is on a busy road using OpenStreetMap.
        
        Returns:
            {
                "is_busy": true|false,
                "confidence": "high|medium|low",
                "road_type": "...",
                "speed_limit": "...",
                "lanes": "...",
                "evidence": [...],
                "data_source": "OpenStreetMap",
                "latitude": ...,
                "longitude": ...
            }
        """
        logger.info("Enriching: busy_road (OpenStreetMap)")
        
        address = property_data.get('address', '')
        if not address:
            return {"error": "No address available"}
        
        # Step 1: Geocode address
        location = self._geocode_address_osm(address)
        if not location:
            return {"error": "Could not geocode address"}
        
        # Respect OSM rate limit
        time.sleep(OSM_RATE_LIMIT_DELAY)
        
        # Step 2: Get road data
        road_data = self._get_road_data_osm(location['lat'], location['lon'])
        if not road_data:
            return {"error": "No road data found"}
        
        # Step 3: Classify road
        result = self._classify_busy_road_osm(road_data)
        result['latitude'] = location['lat']
        result['longitude'] = location['lon']
        result['osm_raw_data'] = road_data
        
        return result
    
    def _geocode_address_osm(self, address: str) -> Optional[Dict[str, float]]:
        """Geocode address using Nominatim (OSM's free geocoding service)."""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'au'
        }
        headers = {
            'User-Agent': 'PropertyDataEnrichment/1.0'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data:
                return {
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon'])
                }
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
        
        return None
    
    def _get_road_data_osm(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """Get road classification data from OpenStreetMap Overpass API."""
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        query = f"""
        [out:json][timeout:25];
        (
          way(around:30,{lat},{lon})["highway"];
        );
        out tags;
        """
        
        try:
            response = requests.post(overpass_url, data={'data': query}, timeout=30)
            data = response.json()
            
            if data.get('elements'):
                road = data['elements'][0]
                tags = road.get('tags', {})
                
                return {
                    'highway_type': tags.get('highway', 'unknown'),
                    'name': tags.get('name', 'Unknown'),
                    'maxspeed': tags.get('maxspeed', 'unknown'),
                    'lanes': tags.get('lanes', 'unknown'),
                    'surface': tags.get('surface', 'unknown')
                }
        except Exception as e:
            logger.error(f"OSM query error: {e}")
        
        return None
    
    def _classify_busy_road_osm(self, road_data: Dict[str, str]) -> Dict[str, Any]:
        """Classify road as busy or quiet based on OSM data."""
        highway_type = road_data['highway_type']
        maxspeed = road_data['maxspeed']
        lanes = road_data['lanes']
        name = road_data['name']
        
        evidence = []
        
        # BUSY ROAD INDICATORS
        busy_types = ['motorway', 'trunk', 'primary', 'secondary']
        
        if highway_type in busy_types:
            evidence.append(f"OSM classifies as '{highway_type}' (major road)")
            
            if maxspeed != 'unknown':
                try:
                    speed = int(maxspeed)
                    if speed >= 70:
                        evidence.append(f"Speed limit {speed} km/h (high speed)")
                except:
                    pass
            
            if lanes != 'unknown':
                try:
                    num_lanes = int(lanes)
                    if num_lanes >= 4:
                        evidence.append(f"{num_lanes} lanes (multi-lane)")
                except:
                    pass
            
            return {
                'is_busy': True,
                'confidence': 'high',
                'road_type': highway_type,
                'road_name': name,
                'speed_limit': maxspeed,
                'lanes': lanes,
                'evidence': evidence,
                'data_source': 'OpenStreetMap'
            }
        
        # QUIET ROAD INDICATORS
        quiet_types = ['residential', 'service', 'unclassified', 'living_street']
        
        if highway_type in quiet_types:
            evidence.append(f"OSM classifies as '{highway_type}' (residential/local)")
            
            if maxspeed != 'unknown':
                try:
                    speed = int(maxspeed)
                    if speed <= 50:
                        evidence.append(f"Speed limit {speed} km/h (low speed)")
                except:
                    pass
            
            return {
                'is_busy': False,
                'confidence': 'high',
                'road_type': highway_type,
                'road_name': name,
                'speed_limit': maxspeed,
                'lanes': lanes,
                'evidence': evidence,
                'data_source': 'OpenStreetMap'
            }
        
        # MEDIUM ROADS
        evidence.append(f"OSM classifies as '{highway_type}' (medium traffic)")
        
        return {
            'is_busy': False,
            'confidence': 'medium',
            'road_type': highway_type,
            'road_name': name,
            'speed_limit': maxspeed,
            'lanes': lanes,
            'evidence': evidence,
            'data_source': 'OpenStreetMap'
        }
    
    # ========================================================================
    # ENRICHMENT METHOD 4: CORNER BLOCK (Google Maps)
    # ========================================================================
    
    def enrich_corner_block(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if property is on a corner block using Google Maps.
        Falls back to GPT if Google Maps unavailable.
        
        Returns:
            {
                "is_corner": true|false,
                "confidence": "high|medium|low",
                "evidence": "...",
                "data_source": "Google Maps|GPT Vision"
            }
        """
        logger.info("Enriching: corner_block")
        
        address = property_data.get('address', '')
        if not address:
            return {"error": "No address available"}
        
        # Try Google Maps first
        if self.google_maps_available:
            result = self._check_corner_block_google_maps(address)
            if result:
                return result
            logger.warning("Google Maps failed, falling back to GPT")
        
        # Fallback to GPT
        return self._check_corner_block_gpt(property_data)
    
    def _check_corner_block_google_maps(self, address: str) -> Optional[Dict[str, Any]]:
        """Use Google Maps to verify corner block position."""
        try:
            import googlemaps
            
            gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
            
            # Geocode address
            geocode_result = gmaps.geocode(address)
            if not geocode_result:
                return None
            
            location = geocode_result[0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            
            # Search for nearby roads
            nearby_roads = gmaps.nearest_roads(
                points=[
                    (lat, lng),
                    (lat + 0.0001, lng),  # North
                    (lat, lng + 0.0001),  # East
                    (lat - 0.0001, lng),  # South
                    (lat, lng - 0.0001),  # West
                ]
            )
            
            # Count unique roads
            unique_roads = set()
            if 'snappedPoints' in nearby_roads:
                for point in nearby_roads['snappedPoints']:
                    place_id = point.get('placeId')
                    if place_id:
                        try:
                            place = gmaps.place(place_id)
                            road_name = place.get('result', {}).get('name')
                            if road_name:
                                unique_roads.add(road_name)
                        except:
                            pass
            
            # If 2+ roads nearby, likely corner block
            if len(unique_roads) >= 2:
                return {
                    'is_corner': True,
                    'confidence': 'high',
                    'evidence': f'Property at intersection of {len(unique_roads)} roads',
                    'streets': list(unique_roads),
                    'data_source': 'Google Maps'
                }
            
            return {
                'is_corner': False,
                'confidence': 'high',
                'evidence': 'Only one road detected nearby',
                'data_source': 'Google Maps'
            }
            
        except ImportError:
            logger.error("googlemaps library not installed")
            return None
        except Exception as e:
            logger.error(f"Google Maps error: {e}")
            return None
    
    def _check_corner_block_gpt(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Use GPT to detect corner block."""
        address = property_data.get('address', '')
        description = property_data.get('agents_description', '')
        
        images = property_data.get('property_images', [])
        reliable_images = self.get_reliable_image_urls(images)
        
        prompt = get_corner_block_prompt()
        result = self.analyze_with_gpt(prompt, reliable_images, description, field_name="corner_block")
        result['data_source'] = 'GPT Vision'
        
        return result
    
    # ========================================================================
    # ENRICHMENT METHOD 5: PARKING
    # ========================================================================
    
    def enrich_parking(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify parking type and capacity from photos.
        
        Returns:
            {
                "type": "garage|carport|open|mixed",
                "garage_spaces": 2,
                "carport_spaces": 0,
                "total_spaces": 2,
                "garage_type": "single|double|triple|tandem",
                "confidence": "high|medium|low"
            }
        """
        logger.info("Enriching: parking")
        
        images = property_data.get('property_images', [])
        reliable_images = self.get_reliable_image_urls(images)
        
        if not reliable_images:
            logger.warning("No reliable images available for parking")
            return {"error": "No reliable images available"}
        
        prompt = get_parking_prompt()
        result = self.analyze_with_gpt(prompt, reliable_images, field_name="parking")
        
        return result
    
    # ========================================================================
    # ENRICHMENT METHOD 6: OUTDOOR ENTERTAINMENT
    # ========================================================================
    
    def enrich_outdoor_entertainment(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rate outdoor entertainment areas (0-10).
        
        Returns:
            {
                "score": 8,
                "size": "small|medium|large",
                "features": [...],
                "quality": "basic|standard|premium",
                "confidence": "high|medium|low"
            }
        """
        logger.info("Enriching: outdoor_entertainment")
        
        images = property_data.get('property_images', [])
        reliable_images = self.get_reliable_image_urls(images)
        
        if not reliable_images:
            logger.warning("No reliable images available for outdoor entertainment")
            return {"error": "No reliable images available"}
        
        prompt = get_outdoor_entertainment_prompt()
        result = self.analyze_with_gpt(prompt, reliable_images, field_name="outdoor_entertainment")
        
        return result
    
    # ========================================================================
    # ENRICHMENT METHOD 7: RENOVATION STATUS
    # ========================================================================
    
    def enrich_renovation_status(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess renovation status and quality.
        
        Returns:
            {
                "status": "original|partially-renovated|fully-renovated|new",
                "renovated_areas": [...],
                "quality": "budget|standard|high-end",
                "age": "recent|moderate|dated",
                "confidence": "high|medium|low"
            }
        """
        logger.info("Enriching: renovation_status")
        
        images = property_data.get('property_images', [])
        reliable_images = self.get_reliable_image_urls(images)
        
        if not reliable_images:
            logger.warning("No reliable images available for renovation status")
            return {"error": "No reliable images available"}
        
        prompt = get_renovation_status_prompt()
        result = self.analyze_with_gpt(prompt, reliable_images, field_name="renovation_status")
        
        return result
    
    # ========================================================================
    # BONUS METHOD: NORTH FACING
    # ========================================================================
    
    def enrich_north_facing(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if property has north-facing living areas.
        
        Returns:
            {
                "north_facing": true|false|unknown,
                "confidence": "high|medium|low",
                "evidence": [...],
                "living_areas": [...]
            }
        """
        logger.info("Enriching: north_facing")
        
        images = property_data.get('property_images', [])
        description = property_data.get('agents_description', '')
        reliable_images = self.get_reliable_image_urls(images)
        
        if not reliable_images:
            logger.warning("No reliable images available for north facing")
            return {"error": "No reliable images available"}
        
        prompt = get_north_facing_prompt()
        result = self.analyze_with_gpt(prompt, reliable_images, description, field_name="north_facing")
        
        return result
