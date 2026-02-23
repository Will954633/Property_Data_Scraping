# Busy Road and Corner Block Detection Strategy
# Last Edit: 13/02/2026, 2:38 PM (Thursday) — Brisbane Time
#
# Description: Detailed strategy for detecting busy roads and corner blocks using GPT + external data
# These are challenging fields that require multi-source validation
#
# Edit History:
# - 13/02/2026 2:38 PM: Initial creation - addressing specific detection challenges

---

## 🎯 Overview

**Challenge:** Busy road and corner block are difficult to determine from photos/descriptions alone

**Solution:** Multi-layered approach combining:
1. GPT Vision analysis of photos
2. Natural language processing of descriptions
3. Address parsing and analysis
4. External data sources (Google Maps API, OpenStreetMap)

---

## 🚗 Busy Road Detection

### Confidence Levels

| Method | Confidence | Accuracy |
|--------|-----------|----------|
| GPT Vision + Description | 60% | Medium |
| + Address Analysis | 70% | Medium-High |
| + Google Maps API | 85% | High |
| + Traffic Data | 90% | Very High |

### Method 1: GPT Vision Analysis (Base Layer)

**What GPT Can See in Photos:**

✅ **Positive Indicators (Busy Road):**
- Wide multi-lane roads visible
- Road markings (center lines, lane dividers)
- Traffic signs (speed limit 60+, warning signs)
- Noise barriers or high fences facing road
- Commercial properties nearby
- Bus stops visible
- Traffic lights in view
- Heavy vehicle access signs

❌ **Negative Indicators (Quiet Street):**
- Narrow single-lane street
- Cul-de-sac visible
- "No Through Road" signs
- Residential character
- Street trees and landscaping
- Children playing signs
- Low fences
- Quiet street appearance

**GPT Prompt:**
```python
"""
Analyze these property photos to assess if the property is on a busy road.

Look for visual indicators:

BUSY ROAD INDICATORS:
- Road width: Multi-lane (2+ lanes each direction)
- Road markings: Center lines, lane dividers, turning lanes
- Traffic infrastructure: Traffic lights, pedestrian crossings
- Signage: Speed limit signs (60+ km/h), warning signs
- Noise mitigation: High fences, noise barriers, double glazing mentions
- Road type: Divided road, highway-style
- Commercial presence: Shops, businesses nearby

QUIET STREET INDICATORS:
- Road width: Single lane, narrow
- Cul-de-sac: Dead-end street visible
- Residential character: Low fences, gardens, street trees
- Signage: "Quiet street", "No through road", children playing
- Street parking: Cars parked on street (residential)

Provide:
1. Busy road assessment: yes/no/unknown
2. Confidence: high/medium/low
3. Road type estimate: residential/collector/arterial/highway
4. Visual evidence: List what you observed
5. Uncertainty factors: What makes this hard to determine

Return as JSON.
"""
```

### Method 2: Description Analysis

**Keywords to Search:**

**Busy Road Indicators:**
- "main road"
- "busy street"
- "arterial road"
- "highway"
- "boulevard"
- "double glazing" (noise mitigation)
- "sound insulation"
- "traffic noise"

**Quiet Street Indicators:**
- "quiet street"
- "peaceful location"
- "cul-de-sac"
- "no through road"
- "leafy street"
- "family-friendly street"
- "safe for children"

### Method 3: Address Analysis

**Road Name Patterns:**

**High Probability Busy Roads:**
```python
BUSY_ROAD_KEYWORDS = [
    'highway', 'hwy',
    'boulevard', 'blvd',
    'parkway', 'pkwy',
    'expressway',
    'main road', 'main st',
    'gold coast highway',
    'pacific motorway',
    'connection road',
    'arterial'
]
```

**Example Implementation:**
```python
def analyze_address_for_busy_road(address):
    """
    Analyze address string for busy road indicators
    """
    address_lower = address.lower()
    
    # Check for busy road keywords
    for keyword in BUSY_ROAD_KEYWORDS:
        if keyword in address_lower:
            return {
                'is_busy': True,
                'confidence': 'high',
                'evidence': f'Address contains "{keyword}"'
            }
    
    # Check for cul-de-sac indicators
    if any(word in address_lower for word in ['court', 'close', 'cul-de-sac', 'place']):
        return {
            'is_busy': False,
            'confidence': 'high',
            'evidence': 'Cul-de-sac street type'
        }
    
    return {
        'is_busy': 'unknown',
        'confidence': 'low',
        'evidence': 'No clear indicators in address'
    }
```

### Method 4: Google Maps API (Recommended)

**API:** Google Maps Roads API + Places API

**What We Can Get:**
- Road classification (residential/arterial/highway)
- Speed limit
- Number of lanes
- Traffic data (if available)
- Nearby amenities (commercial vs residential)

**Implementation:**
```python
import googlemaps

def check_busy_road_google_maps(address, api_key):
    """
    Use Google Maps to determine road type
    """
    gmaps = googlemaps.Client(key=api_key)
    
    # Geocode address
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        return {'is_busy': 'unknown', 'confidence': 'low'}
    
    location = geocode_result[0]['geometry']['location']
    
    # Get nearest road
    roads = gmaps.nearest_roads(
        points=[(location['lat'], location['lng'])]
    )
    
    if roads and 'snappedPoints' in roads:
        road_info = roads['snappedPoints'][0]
        place_id = road_info.get('placeId')
        
        # Get place details
        place_details = gmaps.place(place_id)
        
        # Analyze road type
        types = place_details.get('result', {}).get('types', [])
        
        if 'route' in types:
            # Check if it's a major road
            name = place_details.get('result', {}).get('name', '').lower()
            
            if any(word in name for word in ['highway', 'motorway', 'boulevard']):
                return {
                    'is_busy': True,
                    'confidence': 'high',
                    'road_type': 'arterial/highway',
                    'evidence': f'Google Maps classifies as major road: {name}'
                }
    
    return {
        'is_busy': False,
        'confidence': 'medium',
        'road_type': 'residential',
        'evidence': 'No major road classification found'
    }
```

**Cost:** ~$0.005 per property (very affordable)

### Method 5: OpenStreetMap (Free Alternative)

**API:** Overpass API (free, no API key needed)

**What We Can Get:**
- Road classification (highway tag)
- Max speed
- Lanes
- Surface type

**Implementation:**
```python
import requests

def check_busy_road_osm(lat, lon):
    """
    Use OpenStreetMap to determine road type (FREE)
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query for roads near this location
    query = f"""
    [out:json];
    way(around:50,{lat},{lon})["highway"];
    out tags;
    """
    
    response = requests.post(overpass_url, data={'data': query})
    data = response.json()
    
    if data.get('elements'):
        road = data['elements'][0]
        tags = road.get('tags', {})
        
        highway_type = tags.get('highway', '')
        max_speed = tags.get('maxspeed', '')
        lanes = tags.get('lanes', '')
        
        # Classify based on highway type
        busy_types = ['primary', 'secondary', 'trunk', 'motorway']
        quiet_types = ['residential', 'service', 'unclassified']
        
        if highway_type in busy_types:
            return {
                'is_busy': True,
                'confidence': 'high',
                'road_type': highway_type,
                'evidence': f'OSM highway type: {highway_type}, speed: {max_speed}'
            }
        elif highway_type in quiet_types:
            return {
                'is_busy': False,
                'confidence': 'high',
                'road_type': highway_type,
                'evidence': f'OSM highway type: {highway_type}'
            }
    
    return {'is_busy': 'unknown', 'confidence': 'low'}
```

### Recommended Combined Approach

```python
def detect_busy_road_comprehensive(property_data, photos, api_key=None):
    """
    Multi-layered busy road detection
    """
    results = []
    
    # Layer 1: GPT Vision
    gpt_result = analyze_photos_for_busy_road(photos)
    results.append(gpt_result)
    
    # Layer 2: Description NLP
    desc_result = analyze_description_for_busy_road(property_data['description'])
    results.append(desc_result)
    
    # Layer 3: Address parsing
    addr_result = analyze_address_for_busy_road(property_data['address'])
    results.append(addr_result)
    
    # Layer 4: OpenStreetMap (free)
    if 'latitude' in property_data and 'longitude' in property_data:
        osm_result = check_busy_road_osm(
            property_data['latitude'],
            property_data['longitude']
        )
        results.append(osm_result)
    
    # Layer 5: Google Maps (if API key available)
    if api_key:
        gmaps_result = check_busy_road_google_maps(
            property_data['address'],
            api_key
        )
        results.append(gmaps_result)
    
    # Combine results with weighted voting
    return combine_busy_road_results(results)
```

---

## 🏘️ Corner Block Detection

### Confidence Levels

| Method | Confidence | Accuracy |
|--------|-----------|----------|
| GPT Vision + Description | 75% | Medium-High |
| + Address Analysis | 85% | High |
| + Google Maps API | 95% | Very High |

### Method 1: GPT Vision Analysis

**What GPT Can See:**

✅ **Corner Block Indicators:**
- Property visible from two streets
- Two street-facing facades
- Driveway access from side street
- Fencing on two street sides
- Corner position visible in aerial/street view
- Triangular or L-shaped lot
- Two street addresses visible

**GPT Prompt:**
```python
"""
Determine if this property is on a corner block.

Analyze the photos for:

CORNER BLOCK INDICATORS:
- Two street frontages visible
- Property faces two different streets
- Driveway or gate access from side street
- Fencing configuration: Two sides facing streets
- Corner position: Property at intersection
- Lot shape: Triangular, L-shaped, or irregular
- Multiple street views: Photos from different street angles

SINGLE FRONTAGE INDICATORS:
- Only one street visible
- Neighbors on both sides
- Standard rectangular lot
- Single street access
- Fencing only on front

Provide:
1. Is corner block: yes/no/unknown
2. Confidence: high/medium/low
3. Evidence: What you observed
4. Street names if visible in photos

Return as JSON.
"""
```

### Method 2: Description Analysis

**Keywords to Search:**

**Corner Block Indicators:**
- "corner block"
- "corner position"
- "corner lot"
- "dual street frontage"
- "two street frontage"
- "corner of [Street A] and [Street B]"
- "prominent corner"
- "corner location"

**Example:**
```python
def analyze_description_for_corner(description):
    """
    Search description for corner block mentions
    """
    desc_lower = description.lower()
    
    corner_keywords = [
        'corner block', 'corner position', 'corner lot',
        'dual street frontage', 'two street frontage',
        'corner of', 'prominent corner'
    ]
    
    for keyword in corner_keywords:
        if keyword in desc_lower:
            return {
                'is_corner': True,
                'confidence': 'high',
                'evidence': f'Description mentions "{keyword}"'
            }
    
    return {
        'is_corner': 'unknown',
        'confidence': 'low',
        'evidence': 'No corner mentions in description'
    }
```

### Method 3: Address Analysis

**Pattern Matching:**

```python
import re

def analyze_address_for_corner(address):
    """
    Parse address for corner block indicators
    """
    # Pattern: "Corner of X Street and Y Street"
    corner_pattern = r'corner of ([\w\s]+) and ([\w\s]+)'
    match = re.search(corner_pattern, address.lower())
    
    if match:
        return {
            'is_corner': True,
            'confidence': 'high',
            'evidence': f'Address explicitly states corner of {match.group(1)} and {match.group(2)}',
            'streets': [match.group(1).strip(), match.group(2).strip()]
        }
    
    # Pattern: "123 Main Street & Smith Road"
    ampersand_pattern = r'(\d+\s+[\w\s]+)\s*&\s*([\w\s]+)'
    match = re.search(ampersand_pattern, address)
    
    if match:
        return {
            'is_corner': True,
            'confidence': 'medium',
            'evidence': 'Address contains & suggesting two streets',
            'streets': [match.group(1).strip(), match.group(2).strip()]
        }
    
    return {
        'is_corner': 'unknown',
        'confidence': 'low',
        'evidence': 'No corner indicators in address'
    }
```

### Method 4: Google Maps API (Highest Accuracy)

**Approach:** Check if property is at intersection

```python
def check_corner_block_google_maps(address, api_key):
    """
    Use Google Maps to verify corner block position
    """
    gmaps = googlemaps.Client(key=api_key)
    
    # Geocode address
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        return {'is_corner': 'unknown', 'confidence': 'low'}
    
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
    
    # Count unique roads within 20m
    unique_roads = set()
    if 'snappedPoints' in nearby_roads:
        for point in nearby_roads['snappedPoints']:
            place_id = point.get('placeId')
            if place_id:
                place = gmaps.place(place_id)
                road_name = place.get('result', {}).get('name')
                if road_name:
                    unique_roads.add(road_name)
    
    # If 2+ roads nearby, likely corner block
    if len(unique_roads) >= 2:
        return {
            'is_corner': True,
            'confidence': 'high',
            'evidence': f'Property at intersection of {len(unique_roads)} roads',
            'streets': list(unique_roads)
        }
    
    return {
        'is_corner': False,
        'confidence': 'medium',
        'evidence': 'Only one road detected nearby'
    }
```

### Method 5: Satellite Imagery Analysis (Advanced)

**Using Google Static Maps API:**

```python
def analyze_satellite_for_corner(lat, lng, api_key):
    """
    Download satellite image and analyze for corner position
    """
    # Get satellite image
    url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=19&size=400x400&maptype=satellite&key={api_key}"
    
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    
    # Use GPT Vision to analyze satellite image
    gpt_result = analyze_satellite_image_for_corner(image)
    
    return gpt_result
```

### Recommended Combined Approach

```python
def detect_corner_block_comprehensive(property_data, photos, api_key=None):
    """
    Multi-layered corner block detection
    """
    results = []
    
    # Layer 1: GPT Vision of property photos
    gpt_result = analyze_photos_for_corner(photos)
    results.append(gpt_result)
    
    # Layer 2: Description NLP
    desc_result = analyze_description_for_corner(property_data['description'])
    results.append(desc_result)
    
    # Layer 3: Address parsing
    addr_result = analyze_address_for_corner(property_data['address'])
    results.append(addr_result)
    
    # Layer 4: Google Maps (if API key available)
    if api_key:
        gmaps_result = check_corner_block_google_maps(
            property_data['address'],
            api_key
        )
        results.append(gmaps_result)
        
        # Layer 5: Satellite imagery
        if 'latitude' in property_data:
            satellite_result = analyze_satellite_for_corner(
                property_data['latitude'],
                property_data['longitude'],
                api_key
            )
            results.append(satellite_result)
    
    # Combine results with weighted voting
    return combine_corner_block_results(results)
```

---

## 💰 Cost Analysis

### Google Maps API Costs

| API | Cost per Request | Requests per Property | Cost per Property |
|-----|------------------|----------------------|-------------------|
| Geocoding | $0.005 | 1 | $0.005 |
| Roads API | $0.010 | 1 | $0.010 |
| Places API | $0.017 | 1 | $0.017 |
| Static Maps | $0.002 | 1 | $0.002 |
| **TOTAL** | | | **$0.034** |

**For 2,400 properties:** 2,400 × $0.034 = **$81.60**

### OpenStreetMap (Free Alternative)

- **Cost:** $0
- **Accuracy:** 80-85% (vs 90-95% for Google Maps)
- **Rate Limits:** Reasonable for 2,400 properties

---

## 🎯 Recommended Implementation Strategy

### Phase 1: GPT + Free Methods (No Additional Cost)

1. GPT Vision analysis of photos
2. Description NLP
3. Address parsing
4. OpenStreetMap API (free)

**Expected Accuracy:**
- Busy Road: 70-75%
- Corner Block: 80-85%

### Phase 2: Add Google Maps (If Budget Allows)

Add Google Maps API for properties where Phase 1 confidence is "low" or "medium"

**Expected Accuracy:**
- Busy Road: 85-90%
- Corner Block: 90-95%

**Additional Cost:** ~$80 for 2,400 properties

---

## 📊 Confidence Scoring System

```python
def calculate_final_confidence(results):
    """
    Combine multiple detection results into final answer
    """
    # Weight each method
    weights = {
        'gpt_vision': 0.25,
        'description': 0.20,
        'address': 0.15,
        'osm': 0.20,
        'google_maps': 0.20
    }
    
    # Count votes
    yes_votes = sum(weights[method] for method, result in results.items() if result['answer'] == 'yes')
    no_votes = sum(weights[method] for method, result in results.items() if result['answer'] == 'no')
    
    # Determine final answer
    if yes_votes > 0.6:
        return {'answer': 'yes', 'confidence': 'high'}
    elif yes_votes > 0.4:
        return {'answer': 'yes', 'confidence': 'medium'}
    elif no_votes > 0.6:
        return {'answer': 'no', 'confidence': 'high'}
    elif no_votes > 0.4:
        return {'answer': 'no', 'confidence': 'medium'}
    else:
        return {'answer': 'unknown', 'confidence': 'low'}
```

---

## 🚀 Next Steps

1. **Implement Phase 1** (GPT + Free methods)
2. **Test on 50 sample properties**
3. **Manually validate results**
4. **Decide if Phase 2** (Google Maps) is needed
5. **Run full enrichment pipeline**

---

*Strategy created: 13/02/2026, 2:38 PM Brisbane Time*
*Ready to implement when property scraping completes*
