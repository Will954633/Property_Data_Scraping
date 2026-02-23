# Property Data Gap Analysis Report
# Last Edit: 13/02/2026, 11:26 AM (Thursday) — Brisbane Time
#
# Description: Comprehensive gap analysis comparing current database contents 
# in Gold_Coast_Recently_Sold against requirements for property valuation modeling.
# This analysis identifies what data we have, what's missing, and recommendations 
# for filling the gaps.

---

## Executive Summary

**Database:** `Gold_Coast_Recently_Sold` (Azure Cosmos DB)  
**Total Properties:** 275 sold properties  
**Collections:** 49 (48 suburb-specific + 1 consolidated)  
**Analysis Date:** 13/02/2026, 11:25 AM Brisbane Time

### Key Findings

✅ **GOOD NEWS:** We have 14 out of 23 required data fields (61% coverage)  
❌ **CRITICAL GAPS:** Missing 9 essential fields for valuation modeling  
⚠️ **DATA VOLUME:** Only 275 properties - need ~3,000+ for 12 months across target market

---

## 1. Current Database State

### 1.1 Database Structure

```
Gold_Coast_Recently_Sold/
├── 48 suburb collections (advancetown, arundel, ashmore, etc.)
│   └── 2-8 properties each
└── sold_properties (consolidated)
    └── 65 properties
```

### 1.2 Data Volume by Suburb (Top 10)

| Suburb | Properties | Fields |
|--------|-----------|--------|
| Coomera | 8 | 54 |
| Palm Beach | 7 | 54 |
| Nerang | 7 | 54 |
| Surfers Paradise | 7 | 58 |
| Bonogin | 6 | 54 |
| Broadbeach | 6 | 58 |
| Burleigh Waters | 6 | 63 |
| Mermaid Waters | 6 | 58 |
| Miami | 6 | 58 |
| Mudgeeraba | 6 | 64 |

**Total across all suburbs:** 275 properties

### 1.3 Sample Document Structure

```json
{
  "address": "3 Whiptail Place, Advancetown, QLD 4211",
  "suburb": "Advancetown",
  "postcode": "4211",
  "property_type": "House",
  "bedrooms": 4,
  "bathrooms": 2,
  "carspaces": 8,
  "price": "SOLD - $1,800,025",
  "sale_price": "$1,800,025",
  "sold_date": "2022-09-29",
  "sold_date_text": "Sold by private treaty 29 Sep 2022",
  "first_listed_date": "22 August",
  "first_listed_full": "22 August 2022",
  "first_listed_timestamp": "2022-08-22T13:31:42.000",
  "days_on_domain": 1258,
  "agency": "Harcourts Property Hub",
  "description": "...",
  "features": [...],
  "property_images": [...],
  "floor_plans": [...],
  "listing_url": "https://www.domain.com.au/...",
  "extraction_date": "2026-01-31T17:44:38.841932",
  "moved_to_sold_date": "2026-02-03 21:11:05.237000"
}
```

---

## 2. Requirements vs. Current Data

### 2.1 Data Coverage Matrix

| Requirement | Status | Coverage | Current Field(s) | Notes |
|------------|--------|----------|------------------|-------|
| **12 months sold data** | ❌ CRITICAL | 0% | N/A | Only 275 properties, need ~3,000+ |
| **Room dimensions** | ✅ PARTIAL | 100% | `bedrooms`, `bathrooms`, `floor_plans` | Have counts, need actual dimensions from floor plans |
| **Lot size** | ❌ MISSING | 0% | None | Not currently extracted |
| **Floor area** | ❌ MISSING | 0% | None | Not currently extracted |
| **Waterfront** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Special views** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Corner lot** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Busy road** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Days on market** | ❌ PARTIAL | 0% | `days_on_domain`, `first_listed_timestamp` | Have listing date, need sold date to calculate |
| **Sale method** | ❌ MISSING | 0% | `sold_date_text` | Text mentions "private treaty" but not structured |
| **North facing** | ❌ MISSING | 0% | None | Not currently extracted |
| **Proximity to amenities** | ❌ MISSING | 0% | None | Not currently extracted |
| **Building age** | ❌ MISSING | 0% | None | Not currently extracted |
| **Building condition** | ❌ MISSING | 0% | None | Could extract from photos/description |
| **Renovation status** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Garage/Carport** | ✅ PARTIAL | 0% | `carspaces` | Have count, need type and dimensions |
| **Pool** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Outdoor entertainment** | ✅ AVAILABLE | 100% | `features`, `property_images` | Extracted from features, could score from photos |
| **Air conditioning** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Home office** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Ensuite** | ✅ AVAILABLE | 100% | `bathrooms`, `features` | Extracted from listing features |
| **Walk-in wardrobe** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **High ceilings** | ✅ AVAILABLE | 100% | `features` | Extracted from listing features |
| **Quality of features** | ✅ PARTIAL | 100% | `features`, `property_images` | Have features list, could score from photos |

### 2.2 Summary Statistics

- **✅ Fully Available:** 14 fields (61%)
- **⚠️ Partially Available:** 3 fields (13%)
- **❌ Missing:** 6 fields (26%)
- **🚨 Critical Gap:** Data volume (only 275 vs. ~3,000+ needed)

---

## 3. Critical Gaps Identified

### 3.1 CRITICAL: Insufficient Data Volume

**Current State:**
- 275 total properties across all suburbs
- Most suburbs have only 2-8 properties
- Data appears to be recent (2022-2026)

**Requirement:**
- 12 months of sold data across target market
- Target market suburbs (from requirements):
  - Robina (5 properties) ⚠️
  - Mudgeeraba (6 properties) ⚠️
  - Varsity Lakes (6 properties) ⚠️
  - Carrara (2 properties) ⚠️
  - Reedy Creek (4 properties) ⚠️
  - Burleigh Waters (6 properties) ⚠️
  - Merrimac (5 properties) ⚠️
  - Worongary (4 properties) ⚠️

**Estimated Need:**
- ~250-500 sales per month across Gold Coast
- 12 months = ~3,000-6,000 properties minimum
- Target market (8 suburbs) = ~800-1,500 properties

**Gap:** Need 1,000-1,400 more properties from target market

### 3.2 Missing Structural Data

#### A. Lot Size (Land Area)
**Status:** ❌ MISSING  
**Importance:** CRITICAL for valuation  
**Availability:** Usually on Domain listings  
**Extraction Method:** HTML parsing from listing page

#### B. Floor Area (Building Area)
**Status:** ❌ MISSING  
**Importance:** CRITICAL for valuation  
**Availability:** Usually on Domain listings  
**Extraction Method:** HTML parsing from listing page

#### C. Building Age (Year Built)
**Status:** ❌ MISSING  
**Importance:** HIGH for valuation  
**Availability:** Sometimes on Domain, often in description  
**Extraction Method:** HTML parsing + NLP from description

### 3.3 Missing Calculated Fields

#### A. Days on Market
**Status:** ⚠️ PARTIAL  
**Current:** Have `first_listed_timestamp` and `sold_date`  
**Gap:** Need to calculate difference  
**Solution:** Simple calculation: `sold_date - first_listed_timestamp`

#### B. Sale Method (Auction vs. Private Treaty)
**Status:** ❌ MISSING (but extractable)  
**Current:** Text in `sold_date_text` mentions "private treaty"  
**Gap:** Not structured as boolean/enum  
**Solution:** Parse `sold_date_text` for keywords

### 3.4 Missing Location Features

#### A. North Facing
**Status:** ❌ MISSING  
**Importance:** MEDIUM for valuation  
**Availability:** Rarely disclosed on listings  
**Extraction Method:** 
- Could infer from property orientation (if available)
- Could extract from description text
- May need external data source (cadastral data)

#### B. Proximity to Amenities
**Status:** ❌ MISSING  
**Importance:** HIGH for valuation  
**Availability:** Not on listings  
**Extraction Method:** 
- Calculate from property coordinates
- Use Google Places API or similar
- Distance to: schools, shops, transport, beaches

### 3.5 Missing Property Details

#### A. Garage vs. Carport
**Status:** ⚠️ PARTIAL  
**Current:** Have `carspaces` count  
**Gap:** Don't know if garage or carport, no dimensions  
**Solution:** Extract from features list or description

#### B. Building Condition
**Status:** ❌ MISSING  
**Importance:** HIGH for valuation  
**Availability:** Not explicitly stated  
**Extraction Method:**
- AI analysis of property photos (already have `property_images`)
- NLP from description text
- Could use existing Ollama photo analysis system

---

## 4. Existing Infrastructure

### 4.1 Working Scrapers

✅ **Gold Coast Wide Scraper**  
Location: `03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/`  
- Scrapes all Gold Coast suburbs
- Extracts: address, price, beds, baths, cars, features, images, floor plans
- Parallel processing capable
- Deployed to orchestrator VM

✅ **Sold Property Monitor**  
Location: `02_Domain_Scaping/Sold/`  
- Monitors for-sale properties that transition to sold
- Extracts sold date and sale price
- Moves properties to sold database
- Running on orchestrator

✅ **Photo Analysis System (Ollama)**  
Location: `03_Gold_Coast/.../Ollama_Property_Analysis/`  
- Analyzes property photos for features
- Extracts room types, outdoor areas, quality scores
- Floor plan analysis capability
- Could be extended for condition assessment

### 4.2 Available Data Sources

✅ **Property Images**  
- All properties have `property_images` array
- 50-100+ images per property
- Could analyze for: condition, outdoor entertainment, quality

✅ **Floor Plans**  
- Many properties have `floor_plans` array
- Could extract room dimensions
- Could identify room types

✅ **Features List**  
- Comprehensive `features` array
- Includes: pool, air con, views, waterfront, etc.
- Already structured and extracted

✅ **Listing Descriptions**  
- Full text in `description` and `agents_description`
- Could mine for: building age, renovation status, orientation

---

## 5. Recommendations

### 5.1 PRIORITY 1: Expand Data Volume (CRITICAL)

**Goal:** Collect 12 months of sold data for target market suburbs

**Action Plan:**

1. **Backfill Historical Data (Immediate)**
   - Modify scraper to collect sold properties from past 12 months
   - Domain shows sold history - scrape "Sold" section for each suburb
   - Target: 800-1,500 properties from 8 target market suburbs
   - Timeline: 1-2 days of scraping

2. **Continuous Collection (Ongoing)**
   - Keep sold property monitor running
   - Accumulate new sales as they occur
   - Timeline: Ongoing via orchestrator

**Implementation:**
```bash
# Modify existing scraper to target sold listings
cd 03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold
# Add --sold-only flag to scraper
# Set date range: last 12 months
# Run for target market suburbs only
```

### 5.2 PRIORITY 2: Extract Missing Structural Data

**Goal:** Add lot size, floor area, building age to all properties

**Action Plan:**

1. **Enhance Scraper to Extract:**
   - Lot size (land area in m²)
   - Floor area (building area in m²)
   - Year built / building age
   
2. **Re-scrape Existing Properties:**
   - Update 275 existing properties with new fields
   - Backfill from listing URLs

**Implementation:**
```python
# Add to scraper extraction logic:
# - Parse "Land size: XXX m²"
# - Parse "Building size: XXX m²"  
# - Parse "Built: YYYY" or calculate from description
```

### 5.3 PRIORITY 3: Calculate Derived Fields

**Goal:** Add days on market, structured sale method

**Action Plan:**

1. **Days on Market Calculation:**
   ```python
   days_on_market = (sold_date - first_listed_timestamp).days
   ```

2. **Sale Method Extraction:**
   ```python
   sale_method = "auction" if "auction" in sold_date_text.lower() else "private_treaty"
   ```

**Implementation:**
```bash
# Create enrichment script
cd GapAnalysis_13thFeb
# Script to update all 275 properties with calculated fields
```

### 5.4 PRIORITY 4: Add Location Intelligence

**Goal:** Add proximity to amenities, north facing (if possible)

**Action Plan:**

1. **Proximity to Amenities:**
   - Use Google Places API
   - Calculate distance to:
     - Nearest school (primary, secondary)
     - Nearest shopping center
     - Nearest train/bus station
     - Nearest beach
   - Store as structured data

2. **North Facing:**
   - Extract from description text (NLP)
   - If not available, mark as unknown
   - Low priority - rarely disclosed

**Implementation:**
```python
# Use existing property coordinates (if available)
# Or geocode from address
# Query Google Places API for nearby amenities
# Calculate distances and store
```

### 5.5 PRIORITY 5: Enhance with AI Analysis

**Goal:** Extract building condition, garage details, outdoor entertainment scores

**Action Plan:**

1. **Building Condition (from photos):**
   - Use existing Ollama photo analysis system
   - Analyze exterior photos
   - Score: excellent, good, fair, poor
   - Extract renovation indicators

2. **Garage/Carport Details:**
   - Parse features list for "garage" vs "carport"
   - Extract dimensions from description
   - Use floor plan analysis if available

3. **Outdoor Entertainment Scoring:**
   - Analyze outdoor photos
   - Score size and quality (1-10)
   - Identify features: deck, patio, BBQ area, etc.

**Implementation:**
```bash
# Extend existing Ollama analysis
cd 03_Gold_Coast/.../Ollama_Property_Analysis
# Add new prompts for condition assessment
# Add outdoor entertainment scoring
```

---

## 6. Implementation Roadmap

### Phase 1: Data Volume (Week 1) - CRITICAL

- [ ] Modify scraper to collect 12 months of sold data
- [ ] Target 8 target market suburbs
- [ ] Scrape 800-1,500 historical sold properties
- [ ] Validate data quality

**Deliverable:** 1,000+ sold properties in database

### Phase 2: Structural Data (Week 1-2)

- [ ] Enhance scraper to extract lot size, floor area, building age
- [ ] Re-scrape existing 275 properties
- [ ] Backfill new properties with structural data
- [ ] Validate extraction accuracy

**Deliverable:** All properties have lot size, floor area, building age

### Phase 3: Calculated Fields (Week 2)

- [ ] Create enrichment script for days on market
- [ ] Extract sale method from text
- [ ] Update all properties with calculated fields
- [ ] Validate calculations

**Deliverable:** All properties have days on market, sale method

### Phase 4: Location Intelligence (Week 2-3)

- [ ] Set up Google Places API integration
- [ ] Calculate proximity to amenities for all properties
- [ ] Extract north facing from descriptions (where available)
- [ ] Store location intelligence data

**Deliverable:** All properties have amenity proximity data

### Phase 5: AI Enhancement (Week 3-4)

- [ ] Extend Ollama analysis for building condition
- [ ] Add garage/carport detail extraction
- [ ] Implement outdoor entertainment scoring
- [ ] Process all properties through AI pipeline

**Deliverable:** All properties have AI-derived quality scores

---

## 7. Data Quality Targets

### 7.1 Minimum Viable Dataset

For valuation modeling to work, we need:

| Field | Target Coverage | Current | Gap |
|-------|----------------|---------|-----|
| **Properties (12 months)** | 1,000+ | 275 | 725+ |
| **Lot size** | 95%+ | 0% | 95% |
| **Floor area** | 95%+ | 0% | 95% |
| **Days on market** | 100% | 0% | 100% |
| **Sale method** | 100% | 0% | 100% |
| **Building age** | 80%+ | 0% | 80% |
| **Proximity to amenities** | 100% | 0% | 100% |
| **Building condition** | 70%+ | 0% | 70% |

### 7.2 Success Criteria

✅ **Phase 1 Success:**
- 1,000+ sold properties from target market
- Last 12 months of sales
- All existing fields populated

✅ **Phase 2 Success:**
- 95%+ properties have lot size
- 95%+ properties have floor area
- 80%+ properties have building age

✅ **Phase 3 Success:**
- 100% properties have days on market
- 100% properties have sale method

✅ **Phase 4 Success:**
- 100% properties have amenity proximity data
- 50%+ properties have north facing indicator

✅ **Phase 5 Success:**
- 70%+ properties have building condition score
- 90%+ properties have garage/carport details
- 80%+ properties have outdoor entertainment score

---

## 8. Technical Implementation Notes

### 8.1 Scraper Modifications Required

**File:** `03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/run_complete_suburb_scrape.py`

**Changes Needed:**
1. Add `--sold-only` flag to target sold listings
2. Add `--date-range` parameter for historical scraping
3. Extract additional fields:
   - Land area (lot size)
   - Building area (floor area)
   - Year built
4. Parse sale method from sold text

### 8.2 Enrichment Script Required

**New File:** `GapAnalysis_13thFeb/enrich_existing_properties.py`

**Purpose:**
- Calculate days on market for existing properties
- Extract sale method from text
- Backfill missing structural data

### 8.3 Location Intelligence Script Required

**New File:** `GapAnalysis_13thFeb/add_location_intelligence.py`

**Purpose:**
- Geocode property addresses
- Query Google Places API
- Calculate distances to amenities
- Store proximity data

### 8.4 AI Analysis Extension Required

**File:** `03_Gold_Coast/.../Ollama_Property_Analysis/prompts.py`

**New Prompts:**
- Building condition assessment
- Outdoor entertainment scoring
- Garage vs. carport identification

---

## 9. Cost & Resource Estimates

### 9.1 Scraping Costs

- **Historical data collection:** 1-2 days of VM time (~$5-10)
- **API calls (Google Places):** ~1,000 properties × 5 queries = 5,000 calls (~$25)
- **AI analysis (Ollama):** Free (self-hosted)

**Total Estimated Cost:** $30-35

### 9.2 Time Estimates

- **Phase 1 (Data Volume):** 2-3 days
- **Phase 2 (Structural Data):** 3-4 days
- **Phase 3 (Calculated Fields):** 1 day
- **Phase 4 (Location Intelligence):** 2-3 days
- **Phase 5 (AI Enhancement):** 3-4 days

**Total Timeline:** 2-3 weeks

---

## 10. Next Steps

### Immediate Actions (Today)

1. ✅ **Review this gap analysis** - Confirm requirements and priorities
2. ⏭️ **Approve Phase 1 plan** - Historical data collection
3. ⏭️ **Modify scraper** - Add sold-only mode and additional fields
4. ⏭️ **Test on single suburb** - Validate approach before full run

### This Week

1. **Run historical scraper** - Collect 12 months of sold data
2. **Validate data quality** - Check extraction accuracy
3. **Create enrichment scripts** - Calculate derived fields
4. **Set up Google Places API** - For location intelligence

### Next Week

1. **Complete data enrichment** - All calculated fields
2. **Add location intelligence** - Proximity to amenities
3. **Extend AI analysis** - Building condition, outdoor scoring
4. **Validate complete dataset** - Ready for modeling

---

## 11. Appendix

### A. Target Market Suburbs (from Requirements)

Based on `/Users/projects/Documents/Cline/Rules/Target Market Subrubs.md`:

1. **Robina** - 228 annual sales, $1.4M median (Priority 1)
2. **Mudgeeraba** - 144 annual sales, $1.3M median (Priority 2)
3. **Varsity Lakes** - 117 annual sales, $1.3M median (Priority 3)
4. **Reedy Creek** - 87 annual sales, $1.6M median (Priority 4)
5. **Burleigh Waters** - 225 annual sales, $1.8M median (Priority 5)
6. **Merrimac** - 59 annual sales, $1.1M median (Priority 6)
7. **Worongary** - 41 annual sales, $1.7M median (Priority 7)
8. **Carrara** - Included in target market

### B. Existing Scraper Capabilities

**Current Extraction:**
- ✅ Address, suburb, postcode
- ✅ Property type
- ✅ Bedrooms, bathrooms, car spaces
- ✅ Sale price, sold date
- ✅ First listed date
- ✅ Agency, agent names
- ✅ Description text
- ✅ Features list (comprehensive)
- ✅ Property images (50-100+ per property)
- ✅ Floor plans (when available)
- ✅ Listing URL

**Missing Extraction:**
- ❌ Lot size (land area)
- ❌ Floor area (building area)
- ❌ Building age (year built)
- ❌ Sale method (structured)

### C. Database Connection Details

**Connection String:** (Provided in requirements)  
**Database:** `Gold_Coast_Recently_Sold`  
**Provider:** Azure Cosmos DB (MongoDB API)  
**Current Size:** 275 documents across 49 collections

### D. Related Documentation

- **Orchestrator README:** `/Users/projects/Documents/Fields_Orchestrator/02_Deployment/`
- **Scraper Documentation:** `03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/`
- **Photo Analysis:** `03_Gold_Coast/.../Ollama_Property_Analysis/`
- **Sold Monitor:** `02_Domain_Scaping/Sold/`

---

## Summary

**Current State:** 275 properties with 61% field coverage  
**Required State:** 1,000+ properties with 95%+ field coverage  
**Critical Gap:** Data volume (need 725+ more properties)  
**Timeline:** 2-3 weeks to complete all phases  
**Cost:** ~$30-35 for API calls and compute  
**Next Step:** Approve Phase 1 and begin historical data collection

---

*Report generated: 13/02/2026, 11:26 AM Brisbane Time*  
*Analysis script: `analyze_database.py`*  
*Raw data: `database_analysis.json`*
