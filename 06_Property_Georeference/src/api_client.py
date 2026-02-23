# src/api_client.py

import requests
import time
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GooglePlacesClient:
    """Client for Google Places API (New)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://places.googleapis.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': 'places.displayName,places.id,places.location,places.rating,places.userRatingCount'
        })
    
    def search_nearby(
        self, 
        latitude: float, 
        longitude: float, 
        included_types: List[str],
        radius_meters: int = 5000,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for places near a location
        
        Args:
            latitude: Property latitude
            longitude: Property longitude
            included_types: List of place types to search for
            radius_meters: Search radius
            max_results: Maximum results to return
        
        Returns:
            List of place dictionaries
        """
        url = f"{self.base_url}/places:searchNearby"
        
        payload = {
            "includedTypes": included_types,
            "maxResultCount": max_results,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": radius_meters
                }
            },
            "rankPreference": "DISTANCE"
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            places = data.get('places', [])
            
            # Process and format results
            formatted_places = []
            for place in places:
                location = place.get('location', {})
                formatted_places.append({
                    'name': place.get('displayName', {}).get('text', 'Unknown'),
                    'place_id': place.get('id', ''),
                    'coordinates': {
                        'latitude': location.get('latitude'),
                        'longitude': location.get('longitude')
                    },
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('userRatingCount', 0)
                })
            
            logger.info(f"Found {len(formatted_places)} places for types {included_types}")
            return formatted_places
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def search_by_category_group(
        self,
        latitude: float,
        longitude: float,
        category_groups: Dict[str, List[str]],
        radius_meters: int = 5000
    ) -> Dict[str, List[Dict]]:
        """
        Search for multiple POI categories with optimized API calls
        
        Args:
            latitude: Property latitude
            longitude: Property longitude
            category_groups: Dict mapping category names to place type lists
            radius_meters: Search radius
        
        Returns:
            Dict mapping category names to place lists
        """
        results = {}
        
        for category_name, place_types in category_groups.items():
            try:
                places = self.search_nearby(
                    latitude, longitude, place_types, radius_meters
                )
                results[category_name] = places
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to search {category_name}: {e}")
                results[category_name] = []
        
        return results
