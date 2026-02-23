# Queensland Spatial GIS API - Data Summary

## Overview
Queensland's Department of Resources provides access to land parcel and property data through ArcGIS REST Services. This service contains cadastral (land parcel) data, addresses, and property information for all of Queensland.

**Base URL:** `https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer`

**Update Frequency:** Updated nightly from the Queensland Digital Cadastral Database (DCDB)

---

## Key Layers for Retrieving Property Area (m²)

### 1. Cadastral Parcels (Layer 4) - PRIMARY DATA SOURCE
**Endpoint:** `/MapServer/4`

**Description:** Individual land parcels/lots with detailed cadastral information

**Key Area Fields:**
- `lot_area` (Double) - **Lot area in square meters (m²)**
- `excl_area` (Double) - Excluded area in m²
- `lot_volume` (Double) - For volumetric parcels

**Other Important Fields:**
- `lot` (String) - Lot number
- `plan` (String) - Plan number
- `lotplan` (String) - Combined lot/plan identifier (e.g., "1SP123456")
- `tenure` (String) - Tenure type
- `locality` (String) - Suburb/locality name
- `shire_name` (String) - Local government area
- `parcel_typ` (String) - Parcel type (Lot Type Parcel, Easement, etc.)
- `cover_typ` (String) - Coverage type (Base, Strata, Volumetric, Easement)

**Query Capabilities:**
- Max 4000 records per query
- Supports advanced queries, statistics, pagination
- Supports spatial queries (geometry intersection)
- Has relationships with Addresses layer (0)

**Query Examples:**

1. **Query by Lot/Plan:**
```
/MapServer/4/query?where=lotplan='1SP123456'&outFields=lot,plan,lot_area,locality,shire_name&f=json
```

2. **Query by Address (requires relationship):**
   - First query Addresses layer to get lot/plan
   - Then query this layer with the lot/plan

3. **Query by Location (spatial query):**
```
/MapServer/4/query?geometry={"x":longitude,"y":latitude,"spatialReference":{"wkid":4326}}&geometryType=esriGeometryPoint&spatialRel=esriSpatialRelIntersects&outFields=*&f=json
```

---

### 2. Addresses (Layer 0) - ADDRESS LOOKUP
**Endpoint:** `/MapServer/0`

**Description:** Foundation dataset of address location points in Queensland

**Key Fields:**
- `address` (String) - Full address
- `lot` (String) - Lot number
- `plan` (String) - Plan number  
- `lotplan` (String) - Combined lot/plan identifier
- `street_full` (String) - Full street name
- `locality` (String) - Suburb/locality
- `local_authority` (String) - Local government area
- `latitude` (Double) - Latitude coordinate
- `longitude` (Double) - Longitude coordinate
- `address_pid` (Integer) - Address point ID

**Important:** This layer does NOT contain area data. It must be linked to Cadastral Parcels (Layer 4) to get area information.

**Relationships:**
- Has relationships to Cadastral parcels (Layer 4) via lot/plan
- Can use `queryRelatedRecords` operation to get parcel data including area

**Query Examples:**

1. **Search by Address:**
```
/MapServer/0/query?where=address LIKE '%10 Main Street, Brisbane%'&outFields=address,lotplan,lot,plan,locality&f=json
```

2. **Search by Street and Locality:**
```
/MapServer/0/query?where=street_name='Main' AND street_type='Street' AND locality='Brisbane'&outFields=*&f=json
```

3. **Query Related Parcel Data (to get area):**
```
/MapServer/0/queryRelatedRecords?objectIds=<address_objectid>&relationshipId=2&outFields=lot_area,lot,plan&f=json
```
(relationshipId 2 links to Cadastral parcels layer 4)

---

### 3. Properties (Layer 50) - RURAL PROPERTIES
**Endpoint:** `/MapServer/50`

**Description:** Named rural properties (agricultural/horticultural properties)

**Key Area Field:**
- `dimension_m2` (Double) - **Property dimension in square meters (m²)**

**Other Fields:**
- `name` (String) - Property name
- `feature_type` (String) - Feature type
- `local_government` (String) - Local government area
- `property_code` (Double) - Property code
- `pfi` (String) - Property Feature ID
- `text_note` (String) - Text notes

**Note:** This layer is specifically for rural properties and may not cover all residential properties. Use Layer 4 (Cadastral Parcels) for comprehensive coverage.

**Query Example:**
```
/MapServer/50/query?where=name='Property Name'&outFields=name,dimension_m2,local_government&f=json
```

---

## Complete Workflow: Get m² from Property Address

### Method 1: Two-Step Query (Recommended)

**Step 1:** Query Addresses layer to get lot/plan
```
GET /MapServer/0/query?
  where=address LIKE '%10 Example Street, Brisbane%'
  &outFields=address,lotplan,lot,plan,locality,address_pid
  &f=json
```

**Step 2:** Query Cadastral Parcels with the lot/plan from Step 1
```
GET /MapServer/4/query?
  where=lotplan='1SP123456'
  &outFields=lot,plan,lot_area,excl_area,locality,shire_name,tenure
  &f=json
```

### Method 2: Relationship Query (Single Request)

**Step 1:** Get the objectid from Addresses
```
GET /MapServer/0/query?
  where=address LIKE '%10 Example Street, Brisbane%'
  &outFields=address,objectid
  &f=json
```

**Step 2:** Query related parcel records
```
GET /MapServer/0/queryRelatedRecords?
  objectIds=<objectid_from_step1>
  &relationshipId=2
  &outFields=lot_area,lot,plan,lotplan
  &f=json
```

### Method 3: Spatial Query (by Coordinates)

If you have latitude/longitude coordinates:
```
GET /MapServer/4/query?
  geometry={"x":153.0251,"y":-27.4698,"spatialReference":{"wkid":4326}}
  &geometryType=esriGeometryPoint
  &spatialRel=esriSpatialRelIntersects
  &outFields=lot,plan,lot_area,locality
  &f=json
```

---

## Important Query Parameters

### Common Parameters:
- `where` - SQL-like WHERE clause for attribute queries
- `outFields` - Comma-separated list of fields to return (use `*` for all)
- `f` - Output format (json, geojson, pjson)
- `returnGeometry` - true/false (set to false if you don't need spatial data)
- `orderByFields` - Field(s) to sort results
- `resultRecordCount` - Max records to return (max 4000)

### Spatial Query Parameters:
- `geometry` - Geometry object for spatial queries
- `geometryType` - Type of geometry (esriGeometryPoint, esriGeometryPolygon, etc.)
- `spatialRel` - Spatial relationship (esriSpatialRelIntersects, esriSpatialRelContains, etc.)
- `inSR` - Input spatial reference
- `outSR` - Output spatial reference

### Example WHERE Clauses:
- `lotplan='1SP123456'` - Exact match
- `locality='Brisbane'` - Match locality
- `lot_area > 1000` - Area greater than 1000 m²
- `address LIKE '%Main Street%'` - Partial address match
- `locality='Brisbane' AND lot_area > 500` - Combined conditions

---

## Data Limitations & Notes

1. **Max Records:** 4000 records per query
   - For large queries, use pagination with `resultOffset` parameter

2. **Scale Limitations:**
   - Addresses layer: Visible at scales 1:15000 or larger
   - Cadastral parcels: Visible at scales 1:1000000 or larger
   - Properties layer: Visible at scales 1:300000 or larger

3. **Address Lookup:**
   - Addresses layer does NOT contain area data
   - Must link to Cadastral Parcels layer to get lot_area
   - Use lot/plan identifier as the linking key

4. **Parcel Types:**
   - Base parcels (standard lots)
   - Easements (service easements)
   - Strata parcels (multi-level developments)
   - Volumetric parcels (3D parcels with volume)

5. **Area Fields:**
   - `lot_area` - Total cadastral area
   - `excl_area` - Areas excluded from lot (e.g., roads, easements)
   - Actual usable area may be: lot_area - excl_area

6. **Coordinates:**
   - Spatial Reference: EPSG:3857 (Web Mercator) for internal storage
   - Can query/return in EPSG:4326 (WGS84 lat/lon) using `inSR` and `outSR` parameters

---

## Python Example Code

```python
import requests

def get_area_by_address(address):
    """Get lot area (m²) for a Queensland property address."""
    
    base_url = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer"
    
    # Step 1: Query address to get lot/plan
    address_params = {
        'where': f"address LIKE '%{address}%'",
        'outFields': 'address,lotplan,lot,plan,locality',
        'f': 'json',
        'returnGeometry': 'false'
    }
    
    address_response = requests.get(f"{base_url}/0/query", params=address_params)
    address_data = address_response.json()
    
    if not address_data.get('features'):
        return {"error": "Address not found"}
    
    # Get the lot/plan from first result
    lotplan = address_data['features'][0]['attributes']['lotplan']
    
    # Step 2: Query cadastral parcels to get area
    parcel_params = {
        'where': f"lotplan='{lotplan}'",
        'outFields': 'lot,plan,lot_area,excl_area,locality,shire_name',
        'f': 'json',
        'returnGeometry': 'false'
    }
    
    parcel_response = requests.get(f"{base_url}/4/query", params=parcel_params)
    parcel_data = parcel_response.json()
    
    if not parcel_data.get('features'):
        return {"error": "Parcel not found"}
    
    attributes = parcel_data['features'][0]['attributes']
    
    return {
        'address': address_data['features'][0]['attributes']['address'],
        'lot': attributes['lot'],
        'plan': attributes['plan'],
        'lotplan': lotplan,
        'area_m2': attributes['lot_area'],
        'excluded_area_m2': attributes['excl_area'],
        'locality': attributes['locality'],
        'local_authority': attributes['shire_name']
    }

# Example usage
result = get_area_by_address("10 Main Street, Brisbane")
print(f"Area: {result.get('area_m2')} m²")
```

---

## Summary

**To retrieve m² for any Queensland property:**

1. **Best approach:** Use Layer 4 (Cadastral Parcels) which contains the `lot_area` field in square meters
2. **If you have an address:** Query Layer 0 (Addresses) first to get the lot/plan, then query Layer 4 with that lot/plan
3. **If you have coordinates:** Use spatial query directly on Layer 4
4. **If you have lot/plan:** Query Layer 4 directly

**Key Field:** `lot_area` in Layer 4 contains the property area in square meters (m²)

The API supports advanced queries, spatial queries, relationships, and returns data in JSON format suitable for automated data retrieval.
