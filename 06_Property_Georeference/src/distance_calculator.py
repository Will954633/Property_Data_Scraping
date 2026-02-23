# src/distance_calculator.py

import math
from typing import Tuple, Dict, List

class DistanceCalculator:
    """Calculate distances between geographic coordinates"""
    
    # Gold Coast specific hardcoded locations
    GOLD_COAST_AIRPORT = {"latitude": -28.164444, "longitude": 153.504722}
    
    MAJOR_BEACHES = {
        "Surfers Paradise Beach": {"latitude": -28.0023, "longitude": 153.4295},
        "Broadbeach": {"latitude": -28.0264, "longitude": 153.4294},
        "Burleigh Heads": {"latitude": -28.1003, "longitude": 153.4508},
        "Coolangatta Beach": {"latitude": -28.1682, "longitude": 153.5376},
        "Main Beach": {"latitude": -27.9605, "longitude": 153.4278}
    }
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance between two points on earth.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
        
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return round(c * r, 2)
    
    @staticmethod
    def distance_to_airport(property_lat: float, property_lon: float) -> Dict:
        """Calculate distance to Gold Coast Airport"""
        distance_km = DistanceCalculator.haversine_distance(
            property_lat, property_lon,
            DistanceCalculator.GOLD_COAST_AIRPORT["latitude"],
            DistanceCalculator.GOLD_COAST_AIRPORT["longitude"]
        )
        
        return {
            "name": "Gold Coast Airport",
            "distance_meters": int(distance_km * 1000),
            "distance_km": distance_km,
            "coordinates": DistanceCalculator.GOLD_COAST_AIRPORT
        }
    
    @staticmethod
    def distances_to_beaches(property_lat: float, property_lon: float) -> List[Dict]:
        """Calculate distances to all major beaches"""
        beach_distances = []
        
        for beach_name, coords in DistanceCalculator.MAJOR_BEACHES.items():
            distance_km = DistanceCalculator.haversine_distance(
                property_lat, property_lon,
                coords["latitude"], coords["longitude"]
            )
            
            beach_distances.append({
                "name": beach_name,
                "distance_meters": int(distance_km * 1000),
                "distance_km": distance_km,
                "coordinates": coords
            })
        
        # Sort by distance
        beach_distances.sort(key=lambda x: x["distance_km"])
        
        return beach_distances[:3]  # Return top 3 closest
