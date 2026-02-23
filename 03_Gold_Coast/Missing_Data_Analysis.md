# Missing Data Analysis: Gold Coast MongoDB vs QLD Spatial GIS API

## Current MongoDB Database Structure

**Database:** `Gold_Coast`  
**Collections:** 81 (one per suburb)  
**Total Records:** Properties across Gold Coast suburbs

### Existing Fields (24 fields):
1. ADDRESS_PID - Address point ID
2. ADDRESS_STANDARD - Address standard code
3. ADDRESS_STATUS - Address status
4. DATUM - Coordinate datum (GDA94)
5. GEOCODE_TYPE - Geocode type
6. LATITUDE - Latitude coordinate
7. LGA_CODE - Local government area code
8. LOCALITY - Suburb/locality name
9. LOCAL_AUTHORITY - Local government authority name
10. LONGITUDE - Longitude coordinate
11. LOT - Lot number
12. LOTPLAN_STATUS - Lot/plan status
13. PLAN - Plan number
14. PROPERTY_NAME - Property name (if applicable)
15. STREET_NAME - Street name
16. STREET_NO_1 - Street number (from)
17. STREET_NO_1_SUFFIX - Street number suffix
18. STREET_NO_2 - Street number (to, for ranges)
19. STREET_NO_2_SUFFIX - Street number to suffix
20. STREET_SUFFIX - Street suffix
21. STREET_TYPE - Street type (e.g., STREET, ROAD)
22. UNIT_NUMBER - Unit number
23. UNIT_SUFFIX - Unit suffix
24. UNIT_TYPE - Unit type

---

## Available Data from QLD Spatial GIS API (NOT in MongoDB)

### 🔴 CRITICAL MISSING DATA - From Layer 4 (Cadastral Parcels)

These are the most valuable fields for property analysis:

#### Property Area & Size:
1. **lot_area** (Double) - ⭐ **LOT AREA IN SQUARE METERS (m²)** - PRIMARY MISSING DATA
2. **excl_area** (Double) - Excluded area in m² (roads, easements within lot)
3. **lot_volume** (Double) - Lot volume for volumetric parcels (3D properties)
4. **st_area(shape)** (Double) - Calculated shape area
5. **st_perimeter(shape)** (Double) - Calculated shape perimeter

#### Parcel Classification & Type:
6. **cover_typ** (String) - Coverage type:
   - Base (standard lots)
   - Strata (multi-level developments)
   - Volumetric (3D parcels)
   - Easement (service easements)

7. **parcel_typ** (String) - Parcel type:
   - Lot Type Parcel
   - Road Type Parcel
   - Easement
   - (and other types)

#### Legal & Survey Information:
8. **tenure** (String) - Tenure type (Freehold, Leasehold, etc.)
9. **acc_code** (String) - Positional accuracy code
10. **surv_ind** (String) - Surveyed indicator (Y/N)

#### Property Identification:
11. **lotplan** (String) - Combined lot/plan identifier (e.g., "521SP131523")
12. **feat_name** (String) - Feature name
13. **alias_name** (String) - Alias names (up to 400 chars)

#### Administrative Links:
14. **shire_name** (String) - Local authority name (similar to LOCAL_AUTHORITY but may differ)
15. **smis_map** (String) - SmartMap link URL for viewing property

#### Geometry:
16. **shape** (Geometry) - Full polygon geometry of the property boundary
17. **objectid** (OID) - Unique object identifier for the parcel

---

### 🟡 ADDITIONAL MISSING DATA - From Layer 0 (Addresses)

18. **address** (String) - Formatted full address string (e.g., "3 LUMLEY STREET, MUDGEERABA QLD 4213")
19. **street_full** (String) - Full street name formatted
20. **floor_number** (String) - Floor number (for multi-level buildings)
21. **floor_type** (String) - Floor type
22. **floor_suffix** (String) - Floor suffix
23. **state** (String) - State code (QLD)

---

### 🟢 OPTIONAL DATA - From Layer 50 (Rural Properties)

Only applicable for named rural/agricultural properties:

24. **dimension_m2** (Double) - Property dimension in m² (for rural properties)
25. **feature_type** (String) - Feature type
26. **attribute_source** (String) - Source of attribute data
27. **attribute_date** (Date) - Date of attribute data
28. **additional_names** (String) - Additional property names
29. **add_names_source** (String) - Source of additional names
30. **feature_source** (String) - Source of feature data
31. **feature_date** (Date) - Date of feature data
32. **property_code** (Double) - Property code
33. **pfi** (String) - Property Feature ID
34. **ufi** (String) - Unique Feature ID
35. **upper_scale** (Integer) - Upper scale value
36. **text_note** (String) - Text notes
37. **add_information** (String) - Additional information
38. **globalid** (GlobalID) - Global unique identifier

---

## PRIORITY RANKING for Data Enhancement

### 🎯 HIGHEST PRIORITY (Essential for Property Analysis):
1. **lot_area** - Property size in m² (THE MOST IMPORTANT)
2. **excl_area** - Excluded areas from lot
3. **cover_typ** - Property coverage type
4. **parcel_typ** - Parcel type classification
5. **tenure** - Tenure type (Freehold/Leasehold)
6. **lotplan** - Combined identifier (makes queries easier)

### 🎯 HIGH PRIORITY (Very Useful):
7. **shape** (geometry) - Property boundaries (for mapping/GIS)
8. **lot_volume** - For volumetric/3D properties
9. **address** - Formatted full address
10. **acc_code** - Accuracy of location data
11. **surv_ind** - Survey status
12. **smis_map** - Link to view property on map

### 🎯 MEDIUM PRIORITY (Nice to Have):
13. **feat_name** - Feature names
14. **alias_name** - Alternate names
15. **floor_number**, **floor_type**, **floor_suffix** - For apartments
16. **st_area(shape)**, **st_perimeter(shape)** - Calculated measurements

### 🎯 LOW PRIORITY (Specialized Use):
17. Rural property fields (Layer 50) - Only for agricultural properties
18. **objectid**, **globalid** - System identifiers

---

## Data Enrichment Strategy

### Option 1: Query on Demand (Recommended for Starting)
- Keep current MongoDB as-is
- When lot area is needed, query QLD Spatial GIS API using LOT + PLAN
- Cache results to avoid repeated API calls
- **Pros:** No upfront work, always current data
- **Cons:** Requires API calls, slower for bulk operations

### Option 2: Bulk Enrichment
- Query API for all Gold Coast properties (by locality)
- Add new fields to existing MongoDB documents
- Update nightly/weekly to stay current
- **Pros:** Fast queries, all data local
- **Cons:** Initial time investment, need update mechanism

### Option 3: Hybrid Approach
- Enrich most-accessed properties on demand
- Store enriched data in MongoDB
- Set TTL (time-to-live) for cache expiration
- **Pros:** Balance of speed and freshness
- **Cons:** More complex logic

---

## Sample API Query to Get Missing Data

For a Gold Coast property with LOT="521" and PLAN="SP131523":

```bash
# Query cadastral parcels for lot area and other data
curl 'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer/4/query?where=lot=%27521%27%20AND%20plan=%27SP131523%27&outFields=lot,plan,lotplan,lot_area,excl_area,lot_volume,tenure,cover_typ,parcel_typ,acc_code,surv_ind,locality,shire_name,smis_map&f=json'
```

This single query would return:
- lot_area: Property size in m²
- excl_area: Excluded area
- tenure: Freehold/Leasehold
- cover_typ: Base/Strata/Volumetric
- parcel_typ: Lot Type/Road/Easement
- All other cadastral details

---

## Estimated Impact

### Current Database:
- **24 fields** per property
- Basic addressing and location data
- No property size or tenure information

### With Cadastral Data (Layer 4) Added:
- **~41 fields** per property (17 new fields)
- Complete property analysis capability
- Property area, boundaries, tenure, classification
- **Use cases enabled:**
  - Property size analysis
  - Land value estimation (area-based)
  - Development potential assessment
  - Strata vs freehold identification
  - Accurate property comparisons

### With Full Enrichment:
- **~62 fields** per property (38 new fields)
- Comprehensive property intelligence
- Rural property support
- Complete addressing with floor levels
- Full geometry for mapping

---

## Recommendation

**START WITH:** Cadastral Parcels data (Layer 4) - specifically **lot_area** field

**WHY:**
1. It's the most requested data point (property size in m²)
2. Single API endpoint, straightforward integration
3. Available for ALL properties (not just rural)
4. Unlocks significant analytical capabilities
5. Can be queried using existing LOT + PLAN fields

**NEXT STEPS:**
1. Add geometry data if mapping/GIS features are needed
2. Add rural property data only if working with agricultural properties
3. Add floor-level data only if focusing on apartments/multi-level buildings
