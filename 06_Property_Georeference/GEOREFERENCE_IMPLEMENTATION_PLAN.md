# Property Georeference Implementation Plan

## Executive Summary

This document outlines the comprehensive plan to calculate and store distances from ~6,950 qualifying property locations to significant geographic points of interest (POIs) that are relevant for family homebuyers in the 1-3M dollar price range. This data will enhance property valuation models and provide insights for property sales analysis.

---

## 1. Project Scope

### 1.1 Target Properties
- **Count**: ~6,950 properties (houses sold in last 12 months)
- **Property Type**: Family houses only (no units, villas, or apartments)
- **Price Range**: $1M - $3M
- **Geographic Area**: Gold Coast, QLD
- **Selection Criteria**: As defined in `count_all_qualifying_properties.py`:
  - Houses (addresses without "/" character)
  - Properties with timeline data
  - Sold within the last 12 months

### 1.2 Data Requirements
- **Input**: Property coordinates stored as `LATITUDE` and `LONGITUDE` in MongoDB
- **Output**: Distance (in meters/km) to various POI categories
- **Storage**: MongoDB property documents with nested georeference data

---

## 2. Google Places API (New) Overview

### 2.1 API Capabilities
The Google Places API (New) provides:
- **Nearby Search**: Find places within a specified radius
- **Text Search**: Search for places using text queries
- **Place Details**: Get detailed information about specific places
- **Distance Calculation**: Calculate distances between coordinates

### 2.2 Relevant API Endpoints
1. **Nearby Search (New)**: `places.googleapis.com/v1/places:searchNearby`
   - Best for finding closest POIs by category
   - Returns places sorted by distance
   - Supports multiple place types in single request
   
2. **Distance Matrix API**: For precise distance calculations
   - Road distance vs straight-line distance
   - Multiple origins and destinations in single request
   - Consider traffic patterns (optional)

### 2.3 Pricing Structure (as of 2024)
- **Nearby Search**: $32 per 1,000 requests (Basic Data)
- **Place Details**: $17 per 1,000 requests (Basic Data)
- **Distance Matrix**: $5 per 1,000 elements (origins × destinations)
- **Monthly Credit**: $200 free credit per month

### 2.4 Cost Estimation - TWO APPROACHES

#### Approach A: Per-Property API Calls (Original)
For 6,950 properties with 10 POI categories:
- **Nearby Search**: 6,950 × 10 categories = 69,500 requests
  - Cost: 69.5 × $32 = **$2,224**
- **Alternative** (optimized): Use single request with multiple types
  - 6,950 requests × 1 = 6,950 requests
  - Cost: 6.95 × $32 = **$222.40**

#### Approach B: Build POI Database Once (RECOMMENDED)
**Phase 1: One-time POI Collection**
- Search Gold Coast region (~70km × 50km area) for all POIs
- Grid-based search: ~100-200 API calls to cover entire region
- Cost: 0.2 × $32 = **~$6.40**
- Store all POIs in MongoDB (reusable for all properties)

**Phase 2: Calculate Distances Locally**
- For each property: Query local POI database (FREE)
- Calculate straight-line distance using Haversine formula (FREE)
- Identify closest POIs per category (FREE)

**Phase 3: Optional Drive Distance Calculation**
- For top 3 closest POIs per category: Calculate drive distance
- Distance Matrix API: 6,950 properties × 3 POIs × 10 categories = 208,500 elements
- BUT with batching: Can do 25 origins × 25 destinations per request
- Actual requests: ~350 requests (batched)
- Cost: 208,500 elements × $0.005 per element = **~$1,042.50**

**Total Cost for Approach B**:
- POI Database Creation: ~$10
- Straight-line distances: $0 (calculated locally)
- Drive distances (optional): ~$1,000
- **Recommended Budget**: $10-50 (without drive distance) or $50-1,100 (with drive distance)

### 2.5 Distance Matrix API for Drive Distances

The Distance Matrix API provides:
- **Driving distance**: Actual road distance in meters/km
- **Driving time**: Estimated travel time (with/without traffic)
- **Travel modes**: DRIVE, WALK, BICYCLE, TRANSIT
- **Alternative routes**: Can consider traffic and road conditions

**API Endpoint**: `routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix`

**Pricing**: $5 per 1,000 elements (where 1 element = 1 origin × 1 destination)

**Batching Capability**: 
- Up to 25 origins × 25 destinations per request = 625 elements
- Significantly reduces number of API calls needed

---

## 3. Points of Interest (POI) Categories

### 3.1 Essential Family-Oriented POIs

Based on family homebuyer priorities:

| Category | Google Places Type | Priority | Typical Count |
|----------|-------------------|----------|---------------|
| **Primary Schools** | `primary_school` | HIGH | Top 5 closest |
| **Secondary Schools** | `secondary_school` | HIGH | Top 3 closest |
| **Childcare Centers** | `child_care` | HIGH | Top 5 closest |
| **Shopping Centers** | `shopping_mall` | HIGH | Top 3 closest |
| **Supermarkets** | `supermarket` | HIGH | Top 5 closest |
| **Beaches** | `beach` or custom | HIGH | Top 3 closest |
| **Hospitals** | `hospital` | MEDIUM | Top 2 closest |
| **Medical Centers** | `medical_center` | MEDIUM | Top 3 closest |
| **Parks** | `park` | MEDIUM | Top 5 closest |
| **Public Transport** | `bus_station`, `train_station` | MEDIUM | Top 3 closest |
| **Airports** | `airport` | LOW | Nearest airport |
| **Pharmacies** | `pharmacy` | LOW | Top 3 closest |

### 3.2 Gold Coast Specific Locations

For beaches and airport, we may want to hardcode known locations:
- **Gold Coast Airport (OOL)**: `-28.164444, 153.504722`
- **Major Beaches**: 
  - Surfers Paradise Beach: `-28.0023, 153.4295`
  - Broadbeach: `-28.0264, 153.4294`
  - Burleigh Heads: `-28.1003, 153.4508`
  - Coolangatta Beach: `-28.1682, 153.5376`
  - Main Beach: `-27.9605, 153.4278`

---

## 4. MongoDB Schema Design

### 4.1 Proposed Document Structure

Add a new field `georeference_data` to existing property documents:

```javascript
{
  // Existing fields...
  "complete_address": "123 Smith Street, Robina QLD 4226",
  "LATITUDE": -28.11028046,
  "LONGITUDE": 153.40707093,
  "scraped_data": { ... },
  
  // NEW FIELD
  "georeference_data": {
    "last_updated": ISODate("2025-11-09T06:41:00Z"),
    "coordinates": {
      "latitude": -28.11028046,
      "longitude": 153.40707093
    },
    "distances": {
      "primary_schools": [
        {
          "name": "Robina State Primary School",
          "place_id": "ChIJ...",
          "distance_meters": 850,
          "distance_km": 0.85,
          "coordinates": {
            "latitude": -28.1145,
            "longitude": 153.4089
          },
          "rating": 4.2,
          "user_ratings_total": 156
        },
        // ... top 5 schools
      ],
      "secondary_schools": [ ... ],
      "childcare_centers": [ ... ],
      "supermarkets": [ ... ],
      "shopping_malls": [ ... ],
      "beaches": [
        {
          "name": "Burleigh Heads Beach",
          "distance_meters": 5200,
          "distance_km": 5.2,
          "coordinates": {
            "latitude": -28.1003,
            "longitude": 153.4508
          }
        }
      ],
      "hospitals": [ ... ],
      "medical_centers": [ ... ],
      "parks": [ ... ],
      "public_transport": [ ... ],
      "airport": {
        "name": "Gold Coast Airport",
        "distance_meters": 15400,
        "distance_km": 15.4,
        "coordinates": {
          "latitude": -28.164444,
          "longitude": 153.504722
        }
      },
      "pharmacies": [ ... ]
    },
    "summary_stats": {
      "closest_primary_school_km": 0.85,
      "closest_secondary_school_km": 1.2,
      "closest_childcare_km": 0.6,
      "closest_supermarket_km": 1.5,
      "closest_beach_km": 5.2,
      "closest_hospital_km": 3.8,
      "airport_distance_km": 15.4,
      "total_amenities_within_1km": 12,
      "total_amenities_within_2km": 28,
      "total_amenities_within_5km": 67
    },
    "api_stats": {
      "api_calls_made": 12,
      "processing_time_seconds": 4.5,
      "errors": []
    }
  }
}
```

### 4.2 Index Requirements

Create indexes for efficient querying:
```javascript
// For geospatial queries
db.collection.createIndex({ "georeference_data.coordinates": "2dsphere" })

// For finding properties by specific distance ranges
db.collection.createIndex({ "georeference_data.summary_stats.closest_beach_km": 1 })
db.collection.createIndex({ "georeference_data.summary_stats.closest_primary_school_km": 1 })
```

---

## 5. Implementation Approach

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MongoDB Database                         │
│  Collections: [Robina, Burleigh, Surfers_Paradise, ...]    │
│  ~6,950 qualifying properties with LATITUDE/LONGITUDE       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               Batch Processing Controller                    │
│  - Fetches properties in batches (e.g., 100 at a time)     │
│  - Manages worker distribution                               │
│  - Tracks progress and handles errors                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Worker Pool (10-20 workers)                │
│  Each worker:                                               │
│  1. Receives property with coordinates                       │
│  2. Calls Google Places API for each POI category           │
│  3. Calculates distances                                     │
│  4. Updates MongoDB with georeference_data                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Places API (New)                         │
│  - Nearby Search for POIs                                   │
│  - Rate limiting: 1000 requests/second                      │
│  - Quota management                                          │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Processing Workflow

**Phase 1: Setup & Validation**
1. Validate Google API credentials
2. Test API calls with sample property
3. Verify MongoDB connection
4. Create backup of database

**Phase 2: Batch Processing**
1. Query MongoDB for qualifying properties (6,950 total)
2. Filter properties that don't already have `georeference_data` (or need updates)
3. Divide properties into batches (e.g., 100 properties per batch)
4. Process batches in parallel using worker pool

**Phase 3: POI Discovery per Property**
For each property:
1. Extract coordinates (LATITUDE, LONGITUDE)
2. For each POI category:
   - Call Places API Nearby Search
   - Search radius: Start with 5km, expand to 10km if needed
   - Request top N results (e.g., 5 for schools, 3 for hospitals)
   - Extract: name, place_id, distance, coordinates, rating
3. For hardcoded locations (airport, major beaches):
   - Calculate straight-line distance using Haversine formula
4. Compile all results into `georeference_data` structure
5. Calculate summary statistics
6. Update MongoDB document

**Phase 4: Verification & Quality Control**
1. Verify all 6,950 properties processed
2. Check for any API errors or missing data
3. Validate distance calculations
4. Generate processing report

### 5.3 Optimization Strategies

#### Strategy 1: Batch API Requests
- Use `includedTypes` parameter to search multiple POI types in single request
- Reduces API calls from 10 per property to 2-3 per property
- Example: Group `[primary_school, secondary_school, child_care]` in one request

#### Strategy 2: Caching & Deduplication
- Cache nearby POIs within grid cells (e.g., 1km squares)
- Properties close together will likely share POIs
- Reduces redundant API calls by ~60-70%

#### Strategy 3: Progressive Processing
- Process high-priority POIs first (schools, supermarkets)
- Lower-priority POIs (pharmacies) can be processed in second pass
- Allows early analysis while remaining data processes

#### Strategy 4: Rate Limiting
- Implement exponential backoff for API rate limits
- Stay well below 1000 requests/second limit
- Target: 100-200 requests/second for safety

#### Strategy 5: Resume Capability
- Track processing progress in separate MongoDB collection
- If process crashes, resume from last checkpoint
- Store: `property_id`, `status`, `timestamp`, `retry_count`

---

## 5A. OPTIMIZED APPROACH: Build POI Database Once (RECOMMENDED)

This section details the **significantly more cost-effective** approach of building a reusable POI database for the entire Gold Coast region, then calculating distances locally for each property.

### 5A.1 Three-Phase Strategy

```
PHASE 1: Build POI Database (One-Time)
┌─────────────────────────────────────────────────────────┐
│  Grid-Based API Collection (~100-200 API calls)        │
│  - Cover entire Gold Coast region                       │
│  - Store all POIs in MongoDB "gold_coast_pois"         │
│  - Cost: ~$6-10 (one time only)                        │
│  - Reusable for ALL properties forever                  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
PHASE 2: Calculate Straight-Line Distances (FREE)
┌─────────────────────────────────────────────────────────┐
│  For each of 6,950 properties:                          │
│  - Query local POI database                              │
│  - Calculate Haversine distance                          │
│  - Identify closest POIs per category                    │
│  - Cost: $0 (all local calculations)                    │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
PHASE 3: Calculate Drive Distances (OPTIONAL)
┌─────────────────────────────────────────────────────────┐
│  Distance Matrix API (Batched)                          │
│  - For top 3-5 POIs per category                        │
│  - Batch 25×25 origins/destinations                     │
│  - Cost: ~$1,000 (if needed for all properties)        │
└─────────────────────────────────────────────────────────┘
```

### 5A.2 Phase 1: Building the POI Database

#### Gold Coast Region Coverage Strategy

**Geographic Bounds:**
- North: Ormeau/Pimpama (-27.75)
- South: Coolangatta/Tweed Border (-28.20)
- West: Hinterland (-153.25)
- East: Pacific Ocean (-153.55)
- **Area**: ~70km × 40km = 2,800 km²

#### Grid-Based Search Pattern

Divide region into overlapping search circles:
- Each circle: 5km radius (covers ~78.5 km² area)
- Grid spacing: 8km between centers (ensures overlap)
- Number of grid points: ~9 × 5 = **45 grid points**
- POI categories: 10-12 types
- **Total API calls**: 45 grid points × 12 categories = **540 calls** (worst case)
- **Optimized**: Group categories → 45 grid points × 3 requests = **135 calls**

**Cost for Phase 1**: 135 calls × $0.032 per call = **$4.32**

#### Implementation: POI Database Schema

Create new MongoDB collection: `gold_coast_pois`

```javascript
{
  "_id": ObjectId("..."),
  "poi_type": "primary_school",
  "name": "Robina State Primary School",
  "place_id": "ChIJ...",
  "coordinates": {
    "type": "Point",
    "coordinates": [153.4089, -28.1145]  // [longitude, latitude] for 2dsphere
  },
  "latitude": -28.1145,
  "longitude": 153.4089,
  "rating": 4.2,
  "user_ratings_total": 156,
  "address": "University Drive, Robina QLD 4226",
  "last_updated": ISODate("2025-11-09T06:00:00Z"),
  "grid_cell": "grid_3_2"  // For tracking coverage
}
```

**Indexes for POI Database:**
```javascript
// Geospatial index for proximity queries
db.gold_coast_pois.createIndex({ "coordinates": "2dsphere" })

// Category index for filtering
db.gold_coast_pois.createIndex({ "poi_type": 1 })

// Compound index for category + location queries
db.gold_coast_pois.createIndex({ "poi_type": 1, "coordinates": "2dsphere" })
```

### 5A.3 Phase 2: Local Distance Calculation

For each of 6,950 properties:

1. **Query POI Database** (using MongoDB geospatial query):
```javascript
// Find schools within 10km radius
db.gold_coast_pois.find({
  poi_type: "primary_school",
  coordinates: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [153.407, -28.110]  // Property location
      },
      $maxDistance: 10000  // 10km in meters
    }
  }
}).limit(20)  // Get top 20 to ensure we have closest ones
```

2. **Calculate Exact Haversine Distance** (in Python):
```python
def find_closest_pois(property_lat, property_lon, poi_type, max_count=5):
    """
    Find closest POIs to property from local database
    
    Args:
        property_lat: Property latitude
        property_lon: Property longitude
        poi_type: Type of POI (e.g., 'primary_school')
        max_count: Number of closest POIs to return
    
    Returns:
        List of closest POIs with calculated distances
    """
    # Query MongoDB for nearby POIs
    nearby_pois = poi_collection.find({
        'poi_type': poi_type,
        'coordinates': {
            '$near': {
                '$geometry': {
                    'type': 'Point',
                    'coordinates': [property_lon, property_lat]
                },
                '$maxDistance': 10000  # 10km
            }
        }
    }).limit(20)
    
    # Calculate exact distances
    poi_distances = []
    for poi in nearby_pois:
        distance_km = haversine_distance(
            property_lat, property_lon,
            poi['latitude'], poi['longitude']
        )
        
        poi_distances.append({
            'name': poi['name'],
            'place_id': poi['place_id'],
            'distance_meters': int(distance_km * 1000),
            'distance_km': distance_km,
            'coordinates': {
                'latitude': poi['latitude'],
                'longitude': poi['longitude']
            },
            'rating': poi.get('rating'),
            'user_ratings_total': poi.get('user_ratings_total', 0)
        })
    
    # Sort and return closest N
    poi_distances.sort(key=lambda x: x['distance_km'])
    return poi_distances[:max_count]
```

**Phase 2 Performance:**
- Time per property: < 0.1 seconds (local database query)
- Total time for 6,950 properties: < 12 minutes
- **Cost: $0** (all local calculations)

### 5A.4 Phase 3: Drive Distance Calculation (Optional)

**When to Calculate Drive Distances:**
- For property valuation models (more accurate)
- For schools (parents care about drive time)
- For hospitals (emergency access)
- For shopping centers

**When Straight-Line Distance is Sufficient:**
- Beaches (typically straight access)
- Parks (walking distance)
- Initial filtering/sorting

#### Distance Matrix API Batching Strategy

The Distance Matrix API allows **25 origins × 25 destinations** per request = 625 elements per request.

**Batch Calculation Example:**

For 6,950 properties, calculating drive distance to top 3 schools:
```python
def calculate_drive_distances_batch(properties, pois):
    """
    Calculate drive distances using Distance Matrix API with batching
    
    Args:
        properties: List of property locations
        pois: List of POI locations
    
    Returns:
        Matrix of driving distances and times
    """
    batch_size_origins = 25
    batch_size_destinations = 25
    
    results = {}
    
    for i in range(0, len(properties), batch_size_origins):
        property_batch = properties[i:i+batch_size_origins]
        
        for j in range(0, len(pois), batch_size_destinations):
            poi_batch = pois[j:j+batch_size_destinations]
            
            # Call Distance Matrix API
            response = compute_route_matrix(property_batch, poi_batch)
            
            # Process results
            for origin_idx, destination_results in enumerate(response):
                property_id = property_batch[origin_idx]['id']
                results[property_id] = destination_results
            
            # Rate limiting
            time.sleep(0.1)
    
    return results

def compute_route_matrix(origins, destinations):
    """
    Call Google Distance Matrix API
    
    API Endpoint: routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix
    """
    url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    
    payload = {
        "origins": [
            {
                "waypoint": {
                    "location": {
                        "latLng": {
                            "latitude": prop['latitude'],
                            "longitude": prop['longitude']
                        }
                    }
                }
            }
            for prop in origins
        ],
        "destinations": [
            {
                "waypoint": {
                    "location": {
                        "latLng": {
                            "latitude": poi['latitude'],
                            "longitude": poi['longitude']
                        }
                    }
                }
            }
            for poi in destinations
        ],
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_UNAWARE"  # Or TRAFFIC_AWARE for current conditions
    }
    
    headers = {
        'X-Goog-Api-Key': GOOGLE_API_KEY,
        'X-Goog-FieldMask': 'originIndex,destinationIndex,distanceMeters,duration'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

**Phase 3 Cost Calculation:**

Assuming we want drive distance for top 3 POIs in 5 high-priority categories:
- Properties: 6,950
- POIs per property: 3 POIs × 5 categories = 15 POIs
- Total elements: 6,950 × 15 = **104,250 elements**
- Requests needed: 104,250 ÷ 625 = **167 requests**
- **Cost**: 104,250 × $0.005 = **$521.25**

**Selective Drive Distance** (More Cost-Effective):
Only calculate drive distance for top 3 schools per property:
- Elements: 6,950 × 3 = 20,850
- **Cost**: 20,850 × $0.005 = **$104.25**

### 5A.5 Cost Comparison: Approach A vs Approach B

| Phase | Approach A (Per-Property) | Approach B (POI Database) | Savings |
|-------|---------------------------|---------------------------|---------|
| **POI Discovery** | $222 (6,950 API calls) | $5-10 (135 API calls) | **$212** |
| **Straight-Line Distance** | Included in API | $0 (local calculation) | $0 |
| **Drive Distance (Full)** | ~$1,042 | ~$521 | **$521** |
| **Drive Distance (Selective)** | ~$417 | ~$104 | **$313** |
| | | | |
| **Total (No Drive Distance)** | $222 | $5-10 | **Save $212** |
| **Total (Full Drive Distance)** | $1,264 | $526-531 | **Save $733** |
| **Total (Selective Drive)** | $639 | $109-114 | **Save $525** |

**Recommendation**: Use Approach B with selective drive distance calculation
- **Estimated Total Cost**: **$110-150**
- **Savings**: **~$500-525**

### 5A.6 Implementation Scripts for Approach B

#### Script 1: Build POI Database (`build_poi_database.py`)

```python
#!/usr/bin/env python3
"""
Build comprehensive POI database for Gold Coast region
One-time execution to collect all POIs
"""

import os
from pymongo import MongoClient
from google_places_client import GooglePlacesClient
from datetime import datetime
import time

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')

# Gold Coast bounds
NORTH = -27.75
SOUTH = -28.20
WEST = 153.25
EAST = 153.55

# Grid configuration
GRID_SPACING = 0.08  # ~8km spacing
SEARCH_RADIUS = 5000  # 5km radius

# POI Categories
POI_CATEGORIES = {
    'primary_school': ['primary_school'],
    'secondary_school': ['secondary_school'],
    'childcare': ['child_care'],
    'supermarket': ['supermarket'],
    'shopping_mall': ['shopping_mall'],
    'hospital': ['hospital'],
    'medical_center': ['medical_center'],
    'park': ['park'],
    'pharmacy': ['pharmacy'],
    'public_transport': ['bus_station', 'train_station', 'light_rail_station']
}

def generate_grid_points():
    """Generate grid of search points covering Gold Coast"""
    grid_points = []
    
    lat = NORTH
    grid_row = 0
    
    while lat >= SOUTH:
        lon = WEST
        grid_col = 0
        
        while lon <= EAST:
            grid_points.append({
                'latitude': lat,
                'longitude': lon,
                'grid_cell': f"grid_{grid_row}_{grid_col}"
            })
            lon += GRID_SPACING
            grid_col += 1
        
        lat -= GRID_SPACING
        grid_row += 1
    
    return grid_points

def collect_pois_for_grid_point(api_client, grid_point, poi_collection):
    """Collect all POIs around a grid point"""
    lat = grid_point['latitude']
    lon = grid_point['longitude']
    grid_cell = grid_point['grid_cell']
    
    print(f"Collecting POIs for {grid_cell} ({lat:.4f}, {lon:.4f})")
    
    pois_collected = 0
    
    for category_name, place_types in POI_CATEGORIES.items():
        try:
            places = api_client.search_nearby(
                lat, lon, place_types, SEARCH_RADIUS, max_results=20
            )
            
            for place in places:
                # Check if POI already exists (by place_id)
                existing = poi_collection.find_one({'place_id': place['place_id']})
                
                if not existing:
                    # Add new POI
                    poi_doc = {
                        'poi_type': category_name,
                        'name': place['name'],
                        'place_id': place['place_id'],
                        'coordinates': {
                            'type': 'Point',
                            'coordinates': [
                                place['coordinates']['longitude'],
                                place['coordinates']['latitude']
                            ]
                        },
                        'latitude': place['coordinates']['latitude'],
                        'longitude': place['coordinates']['longitude'],
                        'rating': place.get('rating'),
                        'user_ratings_total': place.get('user_ratings_total', 0),
                        'last_updated': datetime.now(),
                        'discovered_in_grid': grid_cell
                    }
                    
                    poi_collection.insert_one(poi_doc)
                    pois_collected += 1
            
            # Small delay between categories
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error collecting {category_name} for {grid_cell}: {e}")
    
    print(f"  → Collected {pois_collected} new POIs")
    return pois_collected

def main():
    """Main execution"""
    print("="*80)
    print("BUILDING GOLD COAST POI DATABASE")
    print("="*80)
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client['Gold_Coast']
    poi_collection = db['gold_coast_pois']
    
    # Create indexes
    print("\nCreating indexes...")
    poi_collection.create_index([('coordinates', '2dsphere')])
    poi_collection.create_index('poi_type')
    poi_collection.create_index([('poi_type', 1), ('coordinates', '2dsphere')])
    poi_collection.create_index('place_id', unique=True)
    
    # Initialize API client
    api_client = GooglePlacesClient(GOOGLE_API_KEY)
    
    # Generate grid
    grid_points = generate_grid_points()
    print(f"\nGenerated {len(grid_points)} grid points")
    print(f"Expected API calls: ~{len(grid_points) * 3} (with category grouping)")
    
    # Collect POIs
    total_pois = 0
    api_calls = 0
    
    for i, grid_point in enumerate(grid_points, 1):
        print(f"\n[{i}/{len(grid_points)}] Processing grid point...")
        
        pois = collect_pois_for_grid_point(api_client, grid_point, poi_collection)
        total_pois += pois
        api_calls += len(POI_CATEGORIES)
        
        if i % 10 == 0:
            print(f"\nProgress: {i}/{len(grid_points)} grid points")
            print(f"Total POIs collected: {total_pois}")
            print(f"API calls made: {api_calls}")
            print(f"Estimated cost so far: ${api_calls * 0.032:.2f}")
    
    # Final summary
    print("\n" + "="*80)
    print("POI DATABASE BUILD COMPLETE")
    print("="*80)
    
    # Count POIs by category
    for category in POI_CATEGORIES.keys():
        count = poi_collection.count_documents({'poi_type': category})
        print(f"{category:20s}: {count:5,} POIs")
    
    total_db_pois = poi_collection.count_documents({})
    print(f"\n{'Total POIs in database':20s}: {total_db_pois:5,}")
    print(f"API calls made: {api_calls}")
    print(f"Total cost: ${api_calls * 0.032:.2f}")
    print("="*80)

if __name__ == '__main__':
    main()
```

#### Script 2: Process Properties Using POI Database (`process_properties_local.py`)

```python
#!/usr/bin/env python3
"""
Process all properties using local POI database
Calculate distances without making API calls
"""

import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from distance_calculator import DistanceCalculator
import logging

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_closest_pois(poi_collection, property_lat, property_lon, poi_type, max_count=5):
    """Find closest POIs from local database"""
    
    # Query MongoDB using geospatial index
    nearby_pois = poi_collection.find({
        'poi_type': poi_type,
        'coordinates': {
            '$near': {
                '$geometry': {
                    'type': 'Point',
                    'coordinates': [property_lon, property_lat]
                },
                '$maxDistance': 10000  # 10km
            }
        }
    }).limit(20)
    
    # Calculate exact distances
    poi_distances = []
    for poi in nearby_pois:
        distance_km = DistanceCalculator.haversine_distance(
            property_lat, property_lon,
            poi['latitude'], poi['longitude']
        )
        
        poi_distances.append({
            'name': poi['name'],
            'place_id': poi['place_id'],
            'distance_meters': int(distance_km * 1000),
            'distance_km': distance_km,
            'coordinates': {
                'latitude': poi['latitude'],
                'longitude': poi['longitude']
            },
            'rating': poi.get('rating'),
            'user_ratings_total': poi.get('user_ratings_total', 0)
        })
    
    # Sort and return closest N
    poi_distances.sort(key=lambda x: x['distance_km'])
    return poi_distances[:max_count]

def process_property(property_data, poi_collection, property_collection):
    """Process single property using local POI database"""
    lat = property_data['latitude']
    lon = property_data['longitude']
    
    logger.info(f"Processing: {property_data['address']}")
    
    # Find closest POIs for each category
    distances = {}
    
    poi_categories = {
        'primary_schools': 'primary_school',
        'secondary_schools': 'secondary_school',
        'childcare_centers': 'childcare',
        'supermarkets': 'supermarket',
        'shopping_malls': 'shopping_mall',
        'hospitals': 'hospital',
        'medical_centers': 'medical_center',
        'parks': 'park',
        'pharmacies': 'pharmacy',
        'public_transport': 'public_transport'
    }
    
    for field_name, poi_type in poi_categories.items():
        max_results = 5 if 'school' in field_name or field_name == 'childcare_centers' else 3
        distances[field_name] = find_closest_pois(
            poi_collection, lat, lon, poi_type, max_results
        )
    
    # Add hardcoded locations
    distances['airport'] = DistanceCalculator.distance_to_airport(lat, lon)
    distances['beaches'] = DistanceCalculator.distances_to_beaches(lat, lon)
    
    # Calculate summary stats
    summary_stats = calculate_summary_stats(distances)
    
    # Build georeference data
    georeference_data = {
        'last_updated': datetime.now(),
        'coordinates': {'latitude': lat, 'longitude': lon},
        'distances': distances,
        'summary_stats': summary_stats,
        'calculation_method': 'local_poi_database'
    }
    
    # Update property
    property_collection.update_one(
        {'_id': property_data['_id']},
        {'$set': {'georeference_data': georeference_data}}
    )
    
    logger.info(f"✓ Completed: {property_data['address']}")

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("PROCESSING PROPERTIES WITH LOCAL POI DATABASE")
    logger.info("="*80)
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client['Gold_Coast']
    poi_collection = db['gold_coast_pois']
    
    # Verify POI database exists
    poi_count = poi_collection.count_documents({})
    if poi_count == 0:
        logger.error("POI database is empty! Run build_poi_database.py first.")
        return
    
    logger.info(f"POI database loaded: {poi_count:,} POIs")
    
    # Get qualifying properties (same logic as before)
    # ... [same as previous script]
    
    logger.info(f"\nProcessing {len(properties)} properties...")
    logger.info("Cost: $0 (using local database)")
    
    # Process all properties
    for i, prop in enumerate(properties, 1):
        process_property(prop, poi_collection, collection)
        
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{len(properties)} ({i/len(properties)*100:.1f}%)")
    
    logger.info("="*80)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*80)

if __name__ == '__main__':
    main()
```

### 5A.7 Advantages of Approach B

1. **Massive Cost Savings**: ~$500-700 savings
2. **Reusable Data**: POI database can be used for future properties
3. **Faster Processing**: Local queries are instant
4. **No API Rate Limits**: Can process as fast as you want
5. **Offline Capable**: Once POI database built, can work without internet
6. **Flexible**: Can add drive distances later if needed
7. **Updatable**: Refresh POI database quarterly/annually

### 5A.8 When to Refresh POI Database

- **Initial build**: Now (one-time)
- **Regular updates**: Quarterly or semi-annually
- **Triggered updates**: When major developments occur (new school, shopping center)
- **Cost per update**: ~$5-10 (same as initial build but fewer new POIs)

---

## 6. Distance Calculation Methods

### 6.1 Haversine Formula (Straight-Line Distance)

For calculating direct distance between two coordinate points:

```python
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
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
    
    return c * r
```

**Use Cases**:
- Quick distance estimation
- Airport distance (fixed location)
- Major beach distances (fixed locations)
- Validation/sanity checking

### 6.2 Google Distance Matrix API (Road Distance)

For calculating actual driving/walking distances:

```python
# Request to Distance Matrix API
# GET https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix

{
  "origins": [
    {
      "waypoint": {
        "location": {
          "latLng": {"latitude": -28.110, "longitude": 153.407}
        }
      }
    }
  ],
  "destinations": [
    # Multiple destinations for schools, supermarkets, etc.
  ],
  "travelMode": "DRIVE",
  "routingPreference": "TRAFFIC_AWARE"
}
```

**Use Cases**:
- Schools (families care about drive time)
- Shopping centers
- Hospitals
- More accurate for property valuation

**Trade-off**: More expensive, but more accurate for valuation

---

## 7. Implementation Code Structure

### 7.1 Recommended Project Structure

```
06_Property_Georeference/
├── README.md                          # This plan document
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── config.py                          # Configuration management
├── src/
│   ├── __init__.py
│   ├── api_client.py                 # Google Places API wrapper
│   ├── distance_calculator.py        # Distance calculation utilities
│   ├── data_processor.py             # Main processing logic
│   ├── mongodb_handler.py            # MongoDB operations
│   ├── batch_manager.py              # Batch processing controller
│   └── worker.py                     # Individual worker process
├── scripts/
│   ├── setup_api_credentials.py      # Setup Google API
│   ├── validate_setup.py             # Test API and DB connection
│   ├── process_all_properties.py     # Main execution script
│   ├── generate_report.py            # Processing report
│   └── start_workers.sh              # Launch worker pool
├── tests/
│   ├── test_api_client.py
│   ├── test_distance_calc.py
│   └── test_single_property.py       # Test with one property
└── logs/
    ├── processing.log
    ├── errors.log
    └── api_usage.log
```

### 7.2 Key Components

#### Component 1: API Client (`api_client.py`)
```python
class GooglePlacesClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://places.googleapis.com/v1"
        
    def search_nearby(self, latitude, longitude, included_types, radius=5000):
        """Search for places near coordinates"""
        
    def get_place_details(self, place_id):
        """Get detailed information about a place"""
        
    def calculate_distance_matrix(self, origins, destinations):
        """Calculate distances using Distance Matrix API"""
```

#### Component 2: Distance Calculator (`distance_calculator.py`)
```python
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance"""
    
def calculate_all_distances(property_coords, poi_categories):
    """Calculate distances to all POI categories"""
    
def get_closest_n_pois(pois, n=5):
    """Filter to get N closest POIs"""
```

#### Component 3: Data Processor (`data_processor.py`)
```python
class PropertyGeoreferencer:
    def __init__(self, api_client, db_handler):
        self.api_client = api_client
        self.db_handler = db_handler
        
    def process_property(self, property_doc):
        """Process single property and update with georeference data"""
        
    def process_batch(self, property_ids):
        """Process batch of properties"""
        
    def calculate_summary_stats(self, distances):
        """Calculate summary statistics"""
```

#### Component 4: MongoDB Handler (`mongodb_handler.py`)
```python
class MongoDBHandler:
    def __init__(self, connection_string):
        self.client = MongoClient(connection_string)
        self.db = self.client['Gold_Coast']
        
    def get_qualifying_properties(self):
        """Fetch all properties matching criteria"""
        
    def update_georeference_data(self, property_id, georeference_data):
        """Update property with georeference data"""
        
    def get_processing_progress(self):
        """Track which properties have been processed"""
```

#### Component 5: Batch Manager (`batch_manager.py`)
```python
class BatchManager:
    def __init__(self, batch_size=100, num_workers=10):
        self.batch_size = batch_size
        self.num_workers = num_workers
        
    def distribute_work(self, total_properties):
        """Divide properties into batches for workers"""
        
    def monitor_progress(self):
        """Monitor and report processing progress"""
        
    def handle_errors(self, error_log):
        """Handle and retry failed properties"""
```

---

## 8. API Quota Management

### 8.1 Rate Limiting Strategy

```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests_per_second=100):
        self.max_rps = max_requests_per_second
        self.requests = []
        
    def wait_if_needed(self):
        """Implement rate limiting"""
        now = datetime.now()
        # Remove requests older than 1 second
        self.requests = [r for r in self.requests if now - r < timedelta(seconds=1)]
        
        if len(self.requests) >= self.max_rps:
            sleep_time = 1.0 - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.requests.append(now)
```

### 8.2 Quota Monitoring

Track API usage in MongoDB:
```javascript
{
  "_id": "api_usage_tracker",
  "date": "2025-11-09",
  "total_requests": 1250,
  "requests_by_type": {
    "nearby_search": 1000,
    "place_details": 250
  },
  "estimated_cost": 42.50,
  "remaining_monthly_budget": 157.50
}
```

### 8.3 Cost Control Measures

1. **Daily Budget Cap**: Stop processing if daily cost exceeds threshold
2. **Alert System**: Email/Slack notification at 50%, 75%, 90% of budget
3. **Optimization Metrics**: Track cost per property processed
4. **Fallback Strategy**: Use Haversine only if API budget exhausted

---

## 9. Error Handling & Resilience

### 9.1 Common Error Scenarios

| Error Type | Cause | Handling Strategy |
|------------|-------|-------------------|
| API Rate Limit | Too many requests | Exponential backoff, retry |
| API Quota Exceeded | Monthly limit reached | Pause processing, alert admin |
| Invalid Coordinates | Bad property data | Log error, skip property |
| No Results Found | Remote location | Use larger search radius |
| Network Timeout | Connection issues | Retry with timeout increase |
| API Authentication | Invalid API key | Fatal error, stop processing |

### 9.2 Retry Logic

```python
import time

def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = initial_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed. Retrying in {delay}s...")
            time.sleep(delay)
```

### 9.3 Error Logging

Store errors in MongoDB for analysis:
```javascript
{
  "_id": ObjectId("..."),
  "property_id": "ChIJ...",
  "complete_address": "123 Smith St, Robina",
  "error_type": "API_RATE_LIMIT",
  "error_message": "Rate limit exceeded",
  "timestamp": ISODate("2025-11-09T07:30:00Z"),
  "retry_count": 2,
  "resolved": false
}
```

---

## 10. Progress Tracking

### 10.1 Processing Status Collection

Create a separate MongoDB collection to track progress:

```javascript
// Collection: georeference_progress
{
  "_id": ObjectId("..."),
  "session_id": "20251109_163000",
  "start_time": ISODate("2025-11-09T06:30:00Z"),
  "total_properties": 6950,
  "processed": 1250,
  "successful": 1200,
  "failed": 50,
  "in_progress": 45,
  "remaining": 5655,
  "percentage_complete": 18.0,
  "estimated_completion": ISODate("2025-11-09T10:15:00Z"),
  "avg_time_per_property_seconds": 3.2,
  "api_calls_made": 15000,
  "estimated_cost": 85.50,
  "errors_by_type": {
    "rate_limit": 30,
    "no_results": 15,
    "timeout": 5
  }
}
```

### 10.2 Real-Time Monitoring Script

```python
# scripts/monitor_progress.py
def display_progress():
    """Display real-time progress dashboard"""
    while True:
        stats = get_progress_stats()
        print(f"\n{'='*60}")
        print(f"Georeference Processing Progress")
        print(f"{'='*60}")
        print(f"Processed: {stats['processed']}/{stats['total']} ({stats['percent']:.1f}%)")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Estimated Completion: {stats['eta']}")
        print(f"Current Cost: ${stats['cost']:.2f}")
        print(f"{'='*60}")
        time.sleep(10)
```

---

## 11. Testing Strategy

### 11.1 Test Phases

**Phase 1: Unit Tests**
- Test distance calculation accuracy (compare with known distances)
- Test API client methods
- Test MongoDB operations

**Phase 2: Integration Tests**
- Test single property end-to-end
- Verify data structure in MongoDB
- Validate API responses

**Phase 3: Small Batch Test**
- Process 10 properties from different suburbs
- Verify results manually
- Check API usage and costs

**Phase 4: Pilot Run**
- Process 100 properties
- Monitor performance and errors
- Refine based on results

**Phase 5: Full Production Run**
- Process all 6,950 properties
- Continuous monitoring
- Error handling validation

### 11.2 Test Properties Selection

Select diverse test properties:
1. Urban property (Surfers Paradise) - high POI density
2. Suburban property (Robina) - medium POI density
3. Coastal property (Burleigh Heads) - near beach
4. Remote property (Hinterland) - low POI density
5. Property near major landmarks

---

## 12. Performance Optimization

### 12.1 Expected Performance Metrics

Based on similar projects:

| Metric | Target | Notes |
|--------|--------|-------|
| Properties/second | 5-10 | With 10 workers |
| API calls/property | 8-12 | Optimized grouping |
| Processing time/property | 2-5 seconds | Including API calls |
| Total processing time | 2-3 hours | For 6,950 properties |
| Success rate | >95% | With retry logic |
| Cost per property | $0.03-0.05 | Optimized approach |

### 12.2 Parallelization Strategy

```python
from multiprocessing import Pool
import concurrent.futures

def process_property_parallel(property_ids):
    """Process properties in parallel"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_single_property, pid): pid 
                   for pid in property_ids}
        
        for future in concurrent.futures.as_completed(futures):
            property_id = futures[future]
            try:
                result = future.result()
                print(f"Processed {property_id}: Success")
            except Exception as e:
                print(f"Processed {property_id}: Failed - {e}")
```

### 12.3 Caching Strategy

Implement Redis cache for POI data:
```python
import redis

class POICache:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379)
        
    def get_nearby_pois(self, lat, lon, poi_type, radius):
        """Check cache before API call"""
        cache_key = f"{lat:.5f}_{lon:.5f}_{poi_type}_{radius}"
        cached = self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
        
    def set_nearby_pois(self, lat, lon, poi_type, radius, data):
        """Cache POI results for 7 days"""
        cache_key = f"{lat:.5f}_{lon:.5f}_{poi_type}_{radius}"
        self.redis_client.setex(cache_key, 604800, json.dumps(data))
```

---

## 13. Data Quality & Validation

### 13.1 Validation Checks

After processing, run validation queries:

```python
# Check for missing data
missing_georeference = db.collection.count_documents({
    "complete_address": {"$exists": True},
    "georeference_data": {"$exists": False}
})

# Check for incomplete data
incomplete_data = db.collection.count_documents({
    "georeference_data.distances.primary_schools": {"$size": 0}
})

# Check for outliers
outliers = db.collection.find({
    "georeference_data.summary_stats.closest_beach_km": {"$gt": 50}
})
```

### 13.2 Data Quality Metrics

Generate quality report:
- % properties with complete georeference data
- Average number of POIs found per category
- Properties with unusually high/low POI counts
- Geographic distribution of processed properties

---

## 14. Post-Processing Analysis

### 14.1 Analytical Queries

Once data is populated, enable powerful queries:

```javascript
// Find houses within 1km of primary school and 5km of beach
db.collection.find({
  "georeference_data.summary_stats.closest_primary_school_km": {"$lte": 1},
  "georeference_data.summary_stats.closest_beach_km": {"$lte": 5}
})

// Average distance to amenities by suburb
db.collection.aggregate([
  {$group: {
    _id: "$suburb",
    avg_beach_distance: {$avg: "$georeference_data.summary_stats.closest_beach_km"},
    avg_school_distance: {$avg: "$georeference_data.summary_stats.closest_primary_school_km"}
  }}
])
```

### 14.2 Visualization Opportunities

Create maps and charts showing:
- Heat map of POI accessibility
- Property clusters by amenity proximity
- Correlation between distance and property value
- Suburb comparison dashboards

---

## 15. Maintenance & Updates

### 15.1 Update Strategy

POI data should be refreshed periodically:
- **Quarterly**: Update all georeference data
- **Monthly**: Update high-turnover categories (restaurants, shops)
- **On-Demand**: After major developments (new school, shopping center)

### 15.2 Change Detection

Track changes in POI landscape:
```javascript
{
  "property_id": "ChIJ...",
  "georeference_history": [
    {
      "date": ISODate("2025-11-09"),
      "closest_primary_school_km": 0.85,
      "total_amenities_within_2km": 28
    },
    {
      "date": ISODate("2026-02-09"),
      "closest_primary_school_km": 0.85,
      "total_amenities_within_2km": 32  // New amenities added
    }
  ]
}
```

---

## 16. Implementation Timeline

### 16.1 Recommended Phased Rollout

**Week 1: Setup & Testing**
- Day 1-2: Set up Google Cloud project, enable APIs, configure credentials
- Day 3-4: Develop and test core components (API client, distance calculator)
- Day 5: Test with 10 sample properties
- Day 6-7: Refine based on test results

**Week 2: Pilot & Optimization**
- Day 1-2: Process 100 properties (pilot batch)
- Day 3: Analyze results, optimize queries
- Day 4: Implement caching and rate limiting
- Day 5: Process 500 properties
- Day 6-7: Optimization round based on 500-property insights

**Week 3: Full Deployment**
- Day 1: Final pre-production checks
- Day 2-3: Process all 6,950 properties
- Day 4: Validation and quality checks
- Day 5: Generate comprehensive reports
- Day 6-7: Documentation and knowledge transfer

### 16.2 Critical Path Items

1. **Google Cloud Setup** (Blocker for everything else)
2. **API Authentication** (Blocker for API calls)
3. **MongoDB Connection** (Blocker for data operations)
4. **Core Distance Calculator** (Blocker for processing)
5. **Batch Manager** (Blocker for scalability)

---

## 17. API Authentication & Setup

### 17.1 Google Cloud Project Setup

**Step-by-step guide**:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project: `fields-estate` (already created)
3. Navigate to "APIs & Services" → "Enabled APIs & services"
4. Verify "Places API (New)" is enabled ✓
5. Navigate to "Credentials"
6. Create API Key:
   - Click "Create Credentials" → "API Key"
   - Restrict key by API: Select "Places API (New)"
   - Restrict key by IP (optional, for security)
   - Save API key securely

### 17.2 Environment Configuration

Create `.env` file:
```bash
# Google Places API
GOOGLE_PLACES_API_KEY=AIzaSy...your_api_key_here

# MongoDB
MONGODB_URI=mongodb://127.0.0.1:27017/
MONGODB_DATABASE=Gold_Coast

# Processing Configuration
BATCH_SIZE=100
NUM_WORKERS=10
MAX_API_REQUESTS_PER_SECOND=100

# Cost Control
DAILY_BUDGET_USD=50
ALERT_THRESHOLD_PERCENT=75

# Search Parameters
DEFAULT_SEARCH_RADIUS_METERS=5000
MAX_SEARCH_RADIUS_METERS=10000
```

### 17.3 Security Best Practices

- **Never commit** API keys to version control
- Use `.env` file (add to `.gitignore`)
- Implement API key rotation every 90 days
- Monitor API usage daily
- Set up billing alerts in Google Cloud Console

---

## 18. Sample Implementation Code

### 18.1 Distance Calculator (Complete Implementation)

```python
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
```

### 18.2 API Client (Core Implementation)

```python
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
```

### 18.3 Main Processing Script

```python
# scripts/process_all_properties.py

#!/usr/bin/env python3
"""
Process all qualifying properties and add georeference data
"""

import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_client import GooglePlacesClient
from distance_calculator import DistanceCalculator
from mongodb_handler import MongoDBHandler

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 100))

# POI Category Configuration
POI_CATEGORIES = {
    'primary_schools': ['primary_school'],
    'secondary_schools': ['secondary_school'],
    'childcare_centers': ['child_care'],
    'supermarkets': ['supermarket'],
    'shopping_malls': ['shopping_mall'],
    'hospitals': ['hospital'],
    'medical_centers': ['medical_center'],
    'parks': ['park'],
    'pharmacies': ['pharmacy'],
    'public_transport': ['bus_station', 'train_station', 'light_rail_station']
}

def get_qualifying_properties(db):
    """Get all properties that match criteria"""
    twelve_months_ago = datetime.now() - timedelta(days=365)
    
    all_properties = []
    collections = [col for col in db.list_collection_names() 
                   if not col.startswith('system')]
    
    for col_name in collections:
        collection = db[col_name]
        
        # Query for qualifying properties
        query = {
            'complete_address': {'$exists': True},
            'LATITUDE': {'$exists': True},
            'LONGITUDE': {'$exists': True},
            'scraped_data.property_timeline.0': {'$exists': True},
            'georeference_data': {'$exists': False}  # Not yet processed
        }
        
        docs = list(collection.find(query))
        
        for doc in docs:
            address = doc.get('complete_address', '')
            
            # Check if house (no slash)
            if '/' in address:
                continue
            
            # Check for recent sale
            timeline = doc.get('scraped_data', {}).get('property_timeline', [])
            has_recent_sale = False
            
            for entry in timeline:
                if entry.get('category') == 'Sale' and entry.get('is_sold'):
                    date_str = entry.get('date')
                    if date_str:
                        try:
                            sale_date = datetime.strptime(date_str, '%Y-%m-%d')
                            if sale_date >= twelve_months_ago:
                                has_recent_sale = True
                                break
                        except:
                            pass
            
            if has_recent_sale:
                all_properties.append({
                    'collection': col_name,
                    'property_id': doc['_id'],
                    'address': address,
                    'latitude': doc['LATITUDE'],
                    'longitude': doc['LONGITUDE']
                })
    
    logger.info(f"Found {len(all_properties)} qualifying properties")
    return all_properties

def process_single_property(property_data, api_client, db):
    """Process a single property"""
    try:
        lat = property_data['latitude']
        lon = property_data['longitude']
        
        logger.info(f"Processing: {property_data['address']}")
        
        # Get POI data from API
        poi_results = api_client.search_by_category_group(
            lat, lon, POI_CATEGORIES, radius_meters=5000
        )
        
        # Calculate distances and add metadata
        distances = {}
        for category, places in poi_results.items():
            category_distances = []
            for place in places:
                place_lat = place['coordinates']['latitude']
                place_lon = place['coordinates']['longitude']
                
                distance_km = DistanceCalculator.haversine_distance(
                    lat, lon, place_lat, place_lon
                )
                
                category_distances.append({
                    'name': place['name'],
                    'place_id': place['place_id'],
                    'distance_meters': int(distance_km * 1000),
                    'distance_km': distance_km,
                    'coordinates': place['coordinates'],
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total', 0)
                })
            
            # Sort by distance
            category_distances.sort(key=lambda x: x['distance_km'])
            distances[category] = category_distances[:5]  # Top 5
        
        # Add airport and beaches
        distances['airport'] = DistanceCalculator.distance_to_airport(lat, lon)
        distances['beaches'] = DistanceCalculator.distances_to_beaches(lat, lon)
        
        # Calculate summary stats
        summary_stats = calculate_summary_stats(distances)
        
        # Build georeference data structure
        georeference_data = {
            'last_updated': datetime.now(),
            'coordinates': {
                'latitude': lat,
                'longitude': lon
            },
            'distances': distances,
            'summary_stats': summary_stats
        }
        
        # Update MongoDB
        collection = db[property_data['collection']]
        collection.update_one(
            {'_id': property_data['property_id']},
            {'$set': {'georeference_data': georeference_data}}
        )
        
        logger.info(f"✓ Successfully processed: {property_data['address']}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to process {property_data['address']}: {e}")
        return False

def calculate_summary_stats(distances):
    """Calculate summary statistics from distance data"""
    def get_closest(category_list):
        if isinstance(category_list, list) and len(category_list) > 0:
            return category_list[0]['distance_km']
        elif isinstance(category_list, dict):
            return category_list['distance_km']
        return None
    
    summary = {
        'closest_primary_school_km': get_closest(distances.get('primary_schools', [])),
        'closest_secondary_school_km': get_closest(distances.get('secondary_schools', [])),
        'closest_childcare_km': get_closest(distances.get('childcare_centers', [])),
        'closest_supermarket_km': get_closest(distances.get('supermarkets', [])),
        'closest_beach_km': get_closest(distances.get('beaches', [])),
        'closest_hospital_km': get_closest(distances.get('hospitals', [])),
        'airport_distance_km': distances['airport']['distance_km']
    }
    
    # Count amenities within distance thresholds
    all_pois = []
    for category, pois in distances.items():
        if isinstance(pois, list):
            all_pois.extend(pois)
    
    summary['total_amenities_within_1km'] = len([p for p in all_pois if p['distance_km'] <= 1])
    summary['total_amenities_within_2km'] = len([p for p in all_pois if p['distance_km'] <= 2])
    summary['total_amenities_within_5km'] = len([p for p in all_pois if p['distance_km'] <= 5])
    
    return summary

def main():
    """Main execution function"""
    logger.info("="*80)
    logger.info("PROPERTY GEOREFERENCE PROCESSING")
    logger.info("="*80)
    
    # Initialize clients
    api_client = GooglePlacesClient(GOOGLE_API_KEY)
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client['Gold_Coast']
    
    # Get properties to process
    properties = get_qualifying_properties(db)
    total = len(properties)
    
    logger.info(f"Total properties to process: {total}")
    
    if total == 0:
        logger.info("No properties to process!")
        return
    
    # Process properties
    success_count = 0
    fail_count = 0
    
    for i, property_data in enumerate(properties, 1):
        logger.info(f"\n[{i}/{total}] Processing property...")
        
        success = process_single_property(property_data, api_client, db)
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        # Progress update every 100 properties
        if i % 100 == 0:
            logger.info(f"\nProgress: {i}/{total} ({i/total*100:.1f}%)")
            logger.info(f"Success: {success_count}, Failed: {fail_count}")
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*80)
    logger.info(f"Total processed: {total}")
    logger.info(f"Successful: {success_count} ({success_count/total*100:.1f}%)")
    logger.info(f"Failed: {fail_count} ({fail_count/total*100:.1f}%)")
    logger.info("="*80)

if __name__ == '__main__':
    main()
```

---

## 19. Next Steps & Recommendations

### 19.1 Immediate Action Items

1. **Review and Approve Plan**: Stakeholder review of this implementation plan
2. **Budget Approval**: Secure $300-500 for Google Places API costs
3. **API Setup**: Configure Google Cloud project and generate API key
4. **Development Environment**: Set up development environment with required dependencies
5. **Test Run**: Execute pilot with 10 test properties to validate approach

### 19.2 Success Criteria

- ✓ At least 95% of properties successfully processed
- ✓ Average processing time < 5 seconds per property
- ✓ API costs within $500 budget
- ✓ Data quality validated with spot checks
- ✓ MongoDB indexes created for efficient querying
- ✓ Processing can be resumed after interruptions

### 19.3 Post-Implementation Activities

1. **Data Analysis**: Analyze POI accessibility patterns across suburbs
2. **Valuation Integration**: Integrate distance data into property valuation models
3. **Visualization**: Create maps and dashboards for data exploration
4. **Documentation**: Document API usage patterns and optimization strategies
5. **Monitoring**: Set up ongoing monitoring for data freshness

---

## 20. Conclusion

This implementation plan provides a comprehensive roadmap for calculating and storing distances to significant geographic locations for ~6,950 Gold Coast properties. The approach leverages the Google Places API (New) with optimization strategies to minimize costs while ensuring high-quality data collection.

### Key Highlights:

- **Targeted Approach**: Focuses on family-relevant amenities for 1-3M dollar houses
- **Cost-Effective**: Estimated $300-500 total cost with optimization
- **Scalable**: Parallel processing architecture for efficient execution
- **Resilient**: Built-in error handling and retry logic
- **Maintainable**: Structured codebase with clear separation of concerns
- **Valuable**: Enriches property data for valuation and sales analysis

The system is designed to be run once for initial data population, with quarterly updates to maintain freshness. The georeference data will enable powerful analytical queries and enhance property valuation models significantly.

---

**Document Version**: 1.0  
**Last Updated**: November 9, 2025  
**Status**: Ready for Review and Implementation
