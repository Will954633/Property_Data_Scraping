# Data Enrichment Pipeline for 12-Month Sold Properties
# Last Edit: 13/02/2026, 2:36 PM (Thursday) — Brisbane Time
#
# Description: Complete pipeline for enriching 2,400 sold properties with GPT-5-nano analysis
# This pipeline will extract missing data fields using AI vision analysis of photos and descriptions
#
# Edit History:
# - 13/02/2026 2:36 PM: Initial creation based on gap analysis and existing GPT systems

---

## 📋 Executive Summary

**Goal:** Enrich 2,400 scraped sold properties with missing data fields using GPT-5-nano-2025-08-07

**Current Status:**
- ✅ Property detail scraper running (expected completion: ~2:00 AM tomorrow)
- ✅ GPT-5-nano credentials available
- ✅ Existing GPT enrichment system in `01.1_Floor_Plan_Data/`
- ✅ 2,400 properties with photos, descriptions, and floor plans

**What We'll Extract:**
1. **Building condition** (from photos) - excellent/good/fair/poor
2. **Building age/year built** (from description + photos)
3. **Corner block** (from photos + description)
4. **Busy road** (from photos + description + address analysis)
5. **North facing** (from description + floor plans)
6. **Garage vs carport details** (from photos + description)
7. **Outdoor entertainment quality** (from photos) - score 1-10
8. **Renovation status** (from photos + description)

---

## 🎯 Data Fields We Can Extract with GPT

### High Confidence (90%+ accuracy expected)

| Field | Source | Method | Confidence |
|-------|--------|--------|------------|
| **Building Condition** | Photos | GPT Vision analysis of exterior/interior | 90% |
| **Building Age** | Description + Photos | NLP + visual cues (style, materials) | 85% |
| **Garage vs Carport** | Photos + Description | Visual identification + text parsing | 95% |
| **Outdoor Entertainment** | Photos | Visual analysis + scoring | 90% |
| **Renovation Status** | Photos + Description | Visual cues + keywords | 85% |

### Medium Confidence (70-85% accuracy expected)

| Field | Source | Method | Confidence |
|-------|--------|--------|------------|
| **Corner Block** | Photos + Description + Address | Street view analysis + text mentions | 75% |
| **North Facing** | Description + Floor Plans | Keyword extraction + compass analysis | 70% |

### Requires Additional Research (50-70% accuracy)

| Field | Source | Method | Confidence |
|-------|--------|--------|------------|
| **Busy Road** | Photos + Description + Address | Traffic visual cues + road name analysis | 60% |

---

## 🔧 Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   ENRICHMENT PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. MongoDB Uploader                                         │
│     └─> Upload scraped JSON → Gold_Coast_Recently_Sold      │
│                                                              │
│  2. Photo Downloader                                         │
│     └─> Download property_images → local cache              │
│                                                              │
│  3. GPT Enrichment Engine                                    │
│     ├─> Building Condition Analyzer                          │
│     ├─> Building Age Extractor                               │
│     ├─> Corner Block Detector                                │
│     ├─> Busy Road Detector                                   │
│     ├─> North Facing Extractor                               │
│     ├─> Garage/Carport Identifier                            │
│     ├─> Outdoor Entertainment Scorer                         │
│     └─> Renovation Status Analyzer                           │
│                                                              │
│  4. Data Validator                                           │
│     └─> Quality checks + confidence scoring                  │
│                                                              │
│  5. MongoDB Updater                                          │
│     └─> Save enriched data back to database                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **AI Model:** GPT-5-nano-2025-08-07 (OpenAI)
- **Database:** Azure Cosmos DB (MongoDB API)
- **Language:** Python 3.x
- **Key Libraries:**
  - `openai` - GPT API client
  - `pymongo` - MongoDB operations
  - `requests` - Photo downloading
  - `Pillow` - Image processing
  - `python-dotenv` - Environment management

---

## 📊 GPT Prompts Design

### 1. Building Condition Analysis

**Input:** 5-10 property photos (exterior + interior)

**Prompt:**
```
Analyze these property photos and assess the building condition.

Consider:
- Exterior: Paint condition, roof state, landscaping, general maintenance
- Interior: Finishes, fixtures, flooring, walls, overall presentation
- Age indicators: Wear and tear, outdated features, modernization

Provide:
1. Overall condition: excellent/good/fair/poor
2. Confidence level: high/medium/low
3. Key observations (2-3 bullet points)
4. Estimated maintenance level: well-maintained/average/needs-work

Return as JSON.
```

### 2. Building Age Estimation

**Input:** Description text + 3-5 photos

**Prompt:**
```
Estimate the building age of this property.

Analyze:
- Description mentions of "built in YYYY" or "circa YYYY"
- Architectural style visible in photos
- Materials and construction methods
- Fixtures and fittings style
- Kitchen/bathroom modernization level

Provide:
1. Estimated year built (YYYY or range YYYY-YYYY)
2. Confidence level: high/medium/low
3. Evidence used (description keywords, visual cues)
4. Era classification: modern (2010+), contemporary (2000-2009), established (1990-1999), older (pre-1990)

Return as JSON.
```

### 3. Corner Block Detection

**Input:** Address + Description + 3-5 exterior photos

**Prompt:**
```
Determine if this property is on a corner block.

Analyze:
- Address: Does it mention two street names or "corner of X and Y"?
- Description: Keywords like "corner", "corner block", "dual street frontage"
- Photos: Visual evidence of property facing two streets
- Photos: Driveway access from side street
- Photos: Fencing configuration suggesting corner position

Provide:
1. Is corner block: yes/no/unknown
2. Confidence level: high/medium/low
3. Evidence: List specific indicators found
4. Street names if identifiable

Return as JSON.
```

### 4. Busy Road Detection

**Input:** Address + Description + 3-5 exterior photos

**Prompt:**
```
Assess if this property is located on a busy road.

Analyze:
- Address: Road name suggests major thoroughfare (Highway, Boulevard, Main Road, etc.)
- Description: Mentions of "quiet street", "cul-de-sac", "no through road" (negative indicators)
- Description: Mentions of "main road", "busy street" (positive indicators)
- Photos: Visual traffic indicators (road width, lane markings, traffic signs)
- Photos: Noise barriers, high fences (suggesting traffic mitigation)

Provide:
1. Busy road assessment: yes/no/unknown
2. Confidence level: high/medium/low
3. Road type: residential/collector/arterial/highway/unknown
4. Evidence: Specific indicators found

Return as JSON.
```

### 5. North Facing Detection

**Input:** Description + Floor plan images

**Prompt:**
```
Determine if this property has north-facing living areas.

Analyze:
- Description: Keywords "north-facing", "northern aspect", "north orientation"
- Floor plans: Compass rose or north arrow indicators
- Floor plans: Sun symbols showing orientation
- Description: Mentions of "morning sun", "afternoon sun" (orientation clues)

Provide:
1. North facing: yes/no/unknown
2. Which rooms face north (if determinable)
3. Confidence level: high/medium/low
4. Evidence: Specific indicators found
5. Methodology: description/floor_plan/both/none

Return as JSON.
```

### 6. Garage vs Carport Identification

**Input:** Description + Features list + 3-5 photos

**Prompt:**
```
Identify the parking type for this property.

Analyze:
- Features list: Look for "garage", "carport", "covered parking"
- Description: Mentions of parking type
- Photos: Visual identification of enclosed garage vs open carport
- Photos: Number of spaces visible

Provide:
1. Parking type: garage/carport/mixed/unknown
2. Number of garage spaces: N
3. Number of carport spaces: N
4. Garage type: single/double/triple/tandem
5. Confidence level: high/medium/low
6. Evidence: What you observed

Return as JSON.
```

### 7. Outdoor Entertainment Scoring

**Input:** 5-10 photos (outdoor areas)

**Prompt:**
```
Score the outdoor entertainment area quality.

Analyze:
- Size: Small/medium/large outdoor space
- Features: Deck, patio, alfresco, BBQ area, pool, spa
- Quality: Materials, finishes, design
- Functionality: Covered areas, lighting, seating capacity
- Landscaping: Gardens, privacy, aesthetics

Provide:
1. Overall score: 1-10 (1=minimal, 10=exceptional)
2. Size category: small/medium/large
3. Key features: List identified features
4. Quality assessment: basic/good/premium/luxury
5. Confidence level: high/medium/low

Return as JSON.
```

### 8. Renovation Status Analysis

**Input:** Description + 5-10 photos

**Prompt:**
```
Assess the renovation status of this property.

Analyze:
- Description: Keywords "renovated", "updated", "modernized", "original condition"
- Photos: Kitchen - modern appliances, benchtops, cabinetry
- Photos: Bathrooms - fixtures, tiles, vanities
- Photos: Flooring - new/old, type
- Photos: Paint - fresh/dated
- Photos: Fixtures - modern/dated light fittings, door handles

Provide:
1. Renovation status: fully-renovated/partially-renovated/original/mixed
2. Renovated areas: List (kitchen, bathrooms, flooring, etc.)
3. Renovation quality: budget/mid-range/high-end
4. Estimated renovation age: recent (0-3 years)/moderate (4-7 years)/older (8+ years)
5. Confidence level: high/medium/low

Return as JSON.
```

---

## 🔄 Workflow Steps

### Phase 1: Data Upload (30 minutes)

**Goal:** Upload all scraped JSON files to MongoDB

**Steps:**
1. Run MongoDB uploader on all property_data/*.json files
2. Verify 2,400 properties uploaded successfully
3. Check for duplicates and data quality

**Command:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold_In_Last_12_Months_8_Suburbs && \
python3 mongodb_uploader_12months.py
```

**Expected Output:**
- 2,400 properties in `Gold_Coast_Recently_Sold` database
- Organized by suburb collections

---

### Phase 2: Photo Download (2-3 hours)

**Goal:** Download representative photos for each property

**Strategy:**
- Download first 10 photos per property (mix of exterior/interior)
- Download all floor plans
- Store in organized folder structure
- Total: ~24,000 photos + floor plans

**Folder Structure:**
```
GapAnalysis_13thFeb/
└── property_photos/
    ├── robina/
    │   ├── 38-nardoo-street/
    │   │   ├── photo_001.jpg
    │   │   ├── photo_002.jpg
    │   │   └── floor_plan_001.jpg
    │   └── ...
    ├── mudgeeraba/
    └── ...
```

**Script:** `download_property_photos.py`

---

### Phase 3: GPT Enrichment (8-12 hours)

**Goal:** Analyze all properties with GPT-5-nano

**Processing Strategy:**
- **Parallel workers:** 10 workers (to avoid API rate limits)
- **Processing time:** ~80-90 seconds per property
- **Total time:** 2,400 properties ÷ 10 workers × 90 seconds = ~6 hours
- **Cost estimate:** ~$0.02 per property × 2,400 = ~$48

**Batch Processing:**
- Process 240 properties per worker
- Each worker handles one suburb
- Stagger worker starts by 30 seconds

**Script:** `run_gpt_enrichment.py`

---

### Phase 4: Data Validation (1 hour)

**Goal:** Verify enrichment quality and completeness

**Checks:**
1. All 2,400 properties processed
2. Confidence scores distribution
3. Field completion rates
4. Outlier detection
5. Manual spot-checks (sample 20 properties)

**Script:** `validate_enriched_data.py`

---

### Phase 5: MongoDB Update (30 minutes)

**Goal:** Save enriched data back to database

**Data Structure:**
```json
{
  "address": "38 Nardoo Street, Robina, QLD 4226",
  "gpt_enrichment": {
    "building_condition": {
      "overall": "excellent",
      "confidence": "high",
      "observations": ["Well-maintained exterior", "Modern finishes", "Quality presentation"],
      "maintenance_level": "well-maintained",
      "analyzed_at": "2026-02-13T14:30:00"
    },
    "building_age": {
      "year_built": 2018,
      "year_range": "2017-2019",
      "confidence": "medium",
      "evidence": ["Modern architectural style", "Contemporary fixtures"],
      "era": "modern"
    },
    "corner_block": {
      "is_corner": false,
      "confidence": "high",
      "evidence": ["Single street frontage visible", "No dual access"]
    },
    "busy_road": {
      "is_busy": false,
      "confidence": "medium",
      "road_type": "residential",
      "evidence": ["Quiet residential street name", "No traffic indicators"]
    },
    "north_facing": {
      "has_north_aspect": true,
      "rooms": ["Living Room", "Master Bedroom"],
      "confidence": "high",
      "evidence": ["Description mentions 'north-facing living'"],
      "methodology": "description"
    },
    "parking": {
      "type": "garage",
      "garage_spaces": 2,
      "carport_spaces": 0,
      "garage_type": "double",
      "confidence": "high"
    },
    "outdoor_entertainment": {
      "score": 8,
      "size": "large",
      "features": ["Covered alfresco", "Pool", "Landscaped gardens"],
      "quality": "premium",
      "confidence": "high"
    },
    "renovation_status": {
      "status": "fully-renovated",
      "areas": ["Kitchen", "Bathrooms", "Flooring"],
      "quality": "high-end",
      "age": "recent",
      "confidence": "high"
    },
    "enrichment_metadata": {
      "model": "gpt-5-nano-2025-08-07",
      "enriched_at": "2026-02-13T14:30:00",
      "photos_analyzed": 10,
      "floor_plans_analyzed": 1,
      "processing_time_seconds": 85
    }
  }
}
```

---

## 🚧 Challenges & Solutions

### Challenge 1: Busy Road Detection (Low Confidence)

**Problem:** Hard to determine from photos alone

**Solutions:**
1. **Address analysis:** Check road name against known major roads
2. **Google Maps API:** Query road classification (residential/arterial/highway)
3. **Traffic data:** Use Google Places API for nearby traffic data
4. **Conservative approach:** Mark as "unknown" if uncertain

**Recommendation:** Implement multi-source validation

---

### Challenge 2: Corner Block Detection (Medium Confidence)

**Problem:** Not always visible in photos

**Solutions:**
1. **Address parsing:** Look for two street names
2. **Description keywords:** "corner", "dual frontage"
3. **Photo analysis:** Look for two street-facing sides
4. **Google Maps API:** Verify property position on map
5. **Conservative approach:** Mark as "unknown" if uncertain

**Recommendation:** Combine multiple indicators

---

### Challenge 3: API Rate Limits

**Problem:** OpenAI API has rate limits

**Solutions:**
1. **Parallel workers:** Limit to 10 concurrent workers
2. **Staggered starts:** 30-second delay between workers
3. **Retry logic:** Exponential backoff on rate limit errors
4. **Progress tracking:** Save state to resume if interrupted

---

### Challenge 4: Cost Management

**Problem:** GPT-5-nano costs per API call

**Estimated Costs:**
- **Per property:** ~$0.02 (8-10 API calls)
- **Total:** 2,400 × $0.02 = ~$48
- **With retries:** ~$55

**Cost Optimization:**
1. Batch multiple analyses in single API call where possible
2. Use image compression to reduce token usage
3. Cache results to avoid re-processing

---

## 📁 File Structure

```
GapAnalysis_13thFeb/
├── DATA_ENRICHMENT_PIPELINE_PLAN.md          # This file
├── ENRICHMENT_MONITORING.md                   # Monitoring guide
├── download_property_photos.py                # Photo downloader
├── gpt_enrichment_engine.py                   # Main GPT enrichment
├── gpt_prompts.py                             # All GPT prompts
├── gpt_client.py                              # GPT API client
├── mongodb_enrichment_client.py               # MongoDB operations
├── validate_enriched_data.py                  # Validation script
├── run_enrichment_pipeline.sh                 # One-command runner
├── config.py                                  # Configuration
├── logger.py                                  # Logging setup
├── .env                                       # Environment variables
├── requirements.txt                           # Python dependencies
├── property_photos/                           # Downloaded photos
│   ├── robina/
│   ├── mudgeeraba/
│   └── ...
└── logs/                                      # Processing logs
    ├── enrichment.log
    ├── photo_download.log
    └── validation.log
```

---

## ⏱️ Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| **Phase 1: Upload** | 30 min | When scraper completes | +30 min |
| **Phase 2: Photos** | 2-3 hours | After upload | +3 hours |
| **Phase 3: GPT** | 6-8 hours | After photos | +8 hours |
| **Phase 4: Validate** | 1 hour | After GPT | +1 hour |
| **Phase 5: Update** | 30 min | After validate | +30 min |
| **TOTAL** | **10-13 hours** | | |

**Recommended Schedule:**
- Scraper completes: ~2:00 AM tomorrow
- Start enrichment: 8:00 AM tomorrow
- Complete enrichment: 6:00 PM tomorrow

---

## 🎯 Success Criteria

### Data Completeness

- [ ] 2,400 properties uploaded to MongoDB
- [ ] 95%+ properties have building condition
- [ ] 90%+ properties have building age estimate
- [ ] 85%+ properties have garage/carport identification
- [ ] 80%+ properties have outdoor entertainment score
- [ ] 80%+ properties have renovation status
- [ ] 70%+ properties have corner block determination
- [ ] 60%+ properties have busy road assessment
- [ ] 50%+ properties have north facing data

### Data Quality

- [ ] 80%+ enrichments have "high" confidence
- [ ] 15%+ enrichments have "medium" confidence
- [ ] <5% enrichments have "low" confidence
- [ ] Manual validation of 20 random properties shows 90%+ accuracy

### Performance

- [ ] Processing completes within 13 hours
- [ ] API costs under $60
- [ ] No data loss or corruption
- [ ] All logs captured for debugging

---

## 🚀 Next Steps

### Immediate (Today)

1. ✅ Review this plan
2. ⏭️ Create enrichment scripts
3. ⏭️ Test on 5 sample properties
4. ⏭️ Validate GPT prompts produce good results
5. ⏭️ Set up monitoring and logging

### Tomorrow (When Scraper Completes)

1. Upload all properties to MongoDB
2. Download photos for all properties
3. Run GPT enrichment pipeline
4. Validate results
5. Update MongoDB with enriched data

### Follow-up

1. Analyze enrichment quality
2. Identify fields needing improvement
3. Re-run low-confidence properties
4. Document findings
5. Prepare for Phase 2 (additional data sources)

---

## 📝 Notes

- **GPT-5-nano model:** Already configured in `.env` files
- **Credentials:** Available in `01.1_Floor_Plan_Data/.env`
- **Existing code:** Can reuse from `01.1_Floor_Plan_Data/` system
- **Database:** `Gold_Coast_Recently_Sold` on Azure Cosmos DB
- **Parallel processing:** Proven to work with 20 workers in existing system

---

*Plan created: 13/02/2026, 2:36 PM Brisbane Time*
*Property detail scraper running - expected completion ~2:00 AM*
*Ready to begin enrichment when scraping completes*
