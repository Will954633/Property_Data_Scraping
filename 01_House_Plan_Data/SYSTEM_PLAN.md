# GPT-Powered Property Valuation Data Extraction System
## System Design Plan

**Model:** `gpt-5-nano-2025-08-07`  
**Database:** MongoDB Collection `robina`  
**Purpose:** Extract property valuation data for CatBoost model and organize house plan URLs

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Data Extraction Schema](#data-extraction-schema)
3. [System Architecture](#system-architecture)
4. [Implementation Phases](#implementation-phases)
5. [MongoDB Schema Changes](#mongodb-schema-changes)
6. [Testing Strategy](#testing-strategy)
7. [Error Handling](#error-handling)
8. [Performance Considerations](#performance-considerations)

---

## System Overview

### Objectives
1. **Extract Property Valuation Data**: Use GPT vision capabilities to analyze property images and extract structured data for CatBoost valuation model
2. **Identify House Plans**: Detect house plan images/URLs within the images field
3. **Reorganize Data**: Move house plan URLs from `images` field to new `house_plan` field
4. **Extract Floor Size**: Read floor area measurements from house plans
5. **Pre-processing**: Check if documents have `images` field before calling GPT API

### Key Features
- Batch processing of MongoDB documents
- Conditional GPT API calls (only when images exist)
- Structured data extraction for ML model
- Automatic document schema updates
- Progress tracking and logging
- Test mode with first house plan detection

---

## Data Extraction Schema

### Property Valuation Features for CatBoost Model

The GPT model will extract the following features from property images:

#### 1. **Structural Features**
```json
{
  "number_of_stories": "integer (1-3+)",
  "building_type": "enum (house, duplex, townhouse, apartment, unit)",
  "roof_type": "enum (tile, metal, colorbond, slate, flat)",
  "roof_condition_score": "integer (1-10)",
  "architectural_style": "string (modern, traditional, contemporary, colonial, etc.)"
}
```

#### 2. **Exterior Condition & Materials**
```json
{
  "overall_exterior_condition_score": "integer (1-10)",
  "cladding_material": "enum (brick, weatherboard, render, vinyl, fibro, composite, stone)",
  "cladding_condition_score": "integer (1-10)",
  "paint_quality_score": "integer (1-10)",
  "paint_condition": "enum (new, good, fair, poor, peeling)",
  "window_type": "enum (aluminium, timber, upvc, double_glazed)",
  "window_condition_score": "integer (1-10)",
  "door_quality_score": "integer (1-10)",
  "garage_type": "enum (none, carport, single, double, triple)",
  "garage_condition_score": "integer (1-10)"
}
```

#### 3. **Interior Features** (if visible)
```json
{
  "overall_interior_condition_score": "integer (1-10)",
  "flooring_type": "enum (carpet, timber, tiles, vinyl, concrete, laminate, hybrid)",
  "flooring_quality_score": "integer (1-10)",
  "flooring_condition_score": "integer (1-10)",
  "kitchen_quality_score": "integer (1-10)",
  "kitchen_condition": "enum (new, renovated, original, dated)",
  "bathroom_quality_score": "integer (1-10)",
  "bathroom_condition": "enum (new, renovated, original, dated)",
  "appliances_quality_score": "integer (1-10)",
  "fixtures_quality_score": "integer (1-10)",
  "ceiling_height": "enum (standard, high, very_high)",
  "natural_light_score": "integer (1-10)"
}
```

#### 4. **Renovation & Updates**
```json
{
  "renovation_level": "enum (fully_renovated, partial_renovation, original, tired)",
  "renovation_recency": "enum (0-5_years, 5-10_years, 10-20_years, 20+_years, unknown)",
  "modern_features_score": "integer (1-10)"
}
```

#### 5. **Outdoor Features** (if visible)
```json
{
  "landscaping_quality_score": "integer (1-10)",
  "pool_present": "boolean",
  "pool_type": "enum (none, inground, aboveground, lap)",
  "pool_condition_score": "integer (1-10)",
  "outdoor_entertainment_score": "integer (1-10)",
  "fence_type": "enum (none, timber, colorbond, brick, pool_fence)",
  "fence_condition_score": "integer (1-10)",
  "driveway_type": "enum (concrete, paver, gravel, asphalt, exposed_aggregate)",
  "driveway_condition_score": "integer (1-10)"
}
```

#### 6. **Layout & Space** (from floor plans)
```json
{
  "floor_area_sqm": "float (extracted from floor plan)",
  "number_of_bedrooms": "integer",
  "number_of_bathrooms": "float (e.g., 2.5 for 2 full + 1 half)",
  "number_of_living_areas": "integer",
  "open_plan_layout": "boolean",
  "study_present": "boolean",
  "layout_efficiency_score": "integer (1-10)"
}
```

#### 7. **Overall Quality Metrics**
```json
{
  "property_presentation_score": "integer (1-10)",
  "maintenance_level": "enum (well_maintained, average, needs_work, poor)",
  "market_appeal_score": "integer (1-10)",
  "unique_features": "array of strings",
  "negative_features": "array of strings"
}
```

#### 8. **Image Metadata**
```json
{
  "total_images_analyzed": "integer",
  "image_quality": "enum (professional, good, average, poor)",
  "has_professional_photography": "boolean"
}
```

#### 9. **House Plan Specific Data**
```json
{
  "house_plan": {
    "urls": "array of strings",
    "floor_area_sqm": "float",
    "floor_area_source": "enum (main_plan, ground_floor, upper_floor, total)",
    "block_size_sqm": "float (if visible)",
    "dimensions": "string (e.g., '12m x 8m')",
    "number_of_levels": "integer",
    "confidence_score": "float (0-1)"
  }
}
```

### Scoring Guidelines for GPT

**Scoring Scale (1-10):**
- **10**: Exceptional, luxury quality
- **8-9**: High quality, excellent condition
- **6-7**: Good quality, well maintained
- **4-5**: Average quality, acceptable condition
- **2-3**: Below average, needs attention
- **1**: Poor quality, significant issues

**Confidence Levels:**
- Always include confidence score for extracted values
- Flag uncertain extractions for manual review

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Processing System                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. MongoDB Query Module                                     │
│     - Fetch documents from 'robina' collection              │
│     - Filter: documents with 'images' field populated       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Image Pre-processor                                      │
│     - Check if 'images' field exists                        │
│     - Check if 'images' field is not empty                  │
│     - Validate image URLs                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. GPT Vision Analysis Module                               │
│     - API: OpenAI GPT-5-Nano-2025-08-07                     │
│     - Process all images in document                        │
│     - Extract structured property data                      │
│     - Identify house plan images                            │
│     - Extract floor size from plans                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Data Transformation Module                               │
│     - Structure extracted data                              │
│     - Separate house plan URLs from regular images          │
│     - Calculate confidence scores                           │
│     - Validate data types                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. MongoDB Update Module                                    │
│     - Create 'house_plan' field if plans found              │
│     - Move house plan URLs from 'images' to 'house_plan'    │
│     - Add extracted property valuation data                 │
│     - Update processing metadata                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Logging & Tracking Module                                │
│     - Log all processed documents                           │
│     - Track first house plan detection                      │
│     - Error logging                                         │
│     - Performance metrics                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Setup & Configuration
**Duration:** 1 day

**Tasks:**
- [ ] Set up Python environment
- [ ] Install dependencies (openai, pymongo, requests, pillow)
- [ ] Configure OpenAI API key
- [ ] Set up MongoDB connection
- [ ] Create configuration file

**Deliverables:**
- `config.py` - Configuration management
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (API key, DB connection)

### Phase 2: MongoDB Integration
**Duration:** 1-2 days

**Tasks:**
- [ ] Create MongoDB connection module
- [ ] Implement document query logic
- [ ] Create update operations for schema changes
- [ ] Test connection and queries

**Deliverables:**
- `mongodb_client.py` - Database operations
- `queries.py` - Query definitions
- Test connection script

### Phase 3: Image Processing & GPT Integration
**Duration:** 2-3 days

**Tasks:**
- [ ] Create image validation module
- [ ] Implement GPT API client
- [ ] Design prompt engineering for data extraction
- [ ] Create prompt for house plan detection
- [ ] Create prompt for floor size extraction
- [ ] Implement retry logic for API failures

**Deliverables:**
- `image_processor.py` - Image validation and preprocessing
- `gpt_client.py` - GPT API integration
- `prompts.py` - Structured prompts for GPT
- API response parser

### Phase 4: Data Extraction & Transformation
**Duration:** 2-3 days

**Tasks:**
- [ ] Implement property feature extraction
- [ ] Create house plan detection logic
- [ ] Implement floor size extraction from plans
- [ ] Build data validation module
- [ ] Create confidence scoring system

**Deliverables:**
- `data_extractor.py` - Main extraction logic
- `validators.py` - Data validation
- `schema.py` - Data schemas

### Phase 5: Document Update Logic
**Duration:** 1-2 days

**Tasks:**
- [ ] Implement house_plan field creation
- [ ] Create URL migration logic (images → house_plan)
- [ ] Build batch update functionality
- [ ] Add rollback capability

**Deliverables:**
- `document_updater.py` - Update operations
- `migration.py` - Data migration logic

### Phase 6: Testing Mode Implementation
**Duration:** 1-2 days

**Tasks:**
- [ ] Create test mode flag
- [ ] Implement "stop at first house plan" logic
- [ ] Build address tracking system
- [ ] Create data export for review
- [ ] Implement logging for manual review

**Deliverables:**
- `test_mode.py` - Test mode logic
- Test results output (JSON/CSV)
- Manual review report template

### Phase 7: Logging & Monitoring
**Duration:** 1 day

**Tasks:**
- [ ] Set up comprehensive logging
- [ ] Create progress tracking
- [ ] Implement error handling
- [ ] Build performance monitoring

**Deliverables:**
- `logger.py` - Logging configuration
- `monitor.py` - Performance tracking
- Log files structure

### Phase 8: Main Processing Pipeline
**Duration:** 2-3 days

**Tasks:**
- [ ] Build main orchestrator
- [ ] Implement batch processing
- [ ] Add pause/resume capability
- [ ] Create CLI interface
- [ ] Integration testing

**Deliverables:**
- `main.py` - Main execution script
- `pipeline.py` - Processing pipeline
- CLI documentation

### Phase 9: Testing & Validation
**Duration:** 2-3 days

**Tasks:**
- [ ] Unit testing all modules
- [ ] Integration testing
- [ ] Test with sample data
- [ ] Run in test mode until first house plan
- [ ] Manual review of results
- [ ] Performance testing

**Deliverables:**
- Test suite
- Test reports
- Performance benchmarks

### Phase 10: Documentation & Deployment
**Duration:** 1-2 days

**Tasks:**
- [ ] Complete system documentation
- [ ] Create user guide
- [ ] Write deployment instructions
- [ ] Production configuration
- [ ] Backup procedures

**Deliverables:**
- Complete documentation
- Deployment guide
- Operational procedures

**Total Estimated Duration:** 15-23 days

---

## MongoDB Schema Changes

### Before Processing
```json
{
  "_id": ObjectId("..."),
  "address": "123 Main Street, Robina, QLD",
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/floorplan.jpg"
  ],
  "existing_field": "value"
}
```

### After Processing
```json
{
  "_id": ObjectId("..."),
  "address": "123 Main Street, Robina, QLD",
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "house_plan": {
    "urls": [
      "https://example.com/floorplan.jpg"
    ],
    "floor_area_sqm": 250.5,
    "floor_area_source": "main_plan",
    "dimensions": "15m x 12m",
    "number_of_levels": 2,
    "confidence_score": 0.95,
    "extracted_at": ISODate("2025-11-07T09:00:00Z")
  },
  "property_valuation_data": {
    "structural": {
      "number_of_stories": 2,
      "building_type": "house",
      "roof_type": "tile",
      "roof_condition_score": 8,
      "architectural_style": "modern"
    },
    "exterior": {
      "overall_exterior_condition_score": 8,
      "cladding_material": "brick",
      "cladding_condition_score": 9,
      "paint_quality_score": 8,
      "paint_condition": "good",
      "window_type": "aluminium",
      "window_condition_score": 7,
      "door_quality_score": 8,
      "garage_type": "double",
      "garage_condition_score": 8
    },
    "interior": {
      "overall_interior_condition_score": 8,
      "flooring_type": "timber",
      "flooring_quality_score": 8,
      "flooring_condition_score": 8,
      "kitchen_quality_score": 9,
      "kitchen_condition": "renovated",
      "bathroom_quality_score": 8,
      "bathroom_condition": "renovated",
      "appliances_quality_score": 8,
      "fixtures_quality_score": 8,
      "ceiling_height": "high",
      "natural_light_score": 9
    },
    "renovation": {
      "renovation_level": "partial_renovation",
      "renovation_recency": "0-5_years",
      "modern_features_score": 8
    },
    "outdoor": {
      "landscaping_quality_score": 7,
      "pool_present": true,
      "pool_type": "inground",
      "pool_condition_score": 8,
      "outdoor_entertainment_score": 7,
      "fence_type": "colorbond",
      "fence_condition_score": 8,
      "driveway_type": "concrete",
      "driveway_condition_score": 7
    },
    "layout": {
      "floor_area_sqm": 250.5,
      "number_of_bedrooms": 4,
      "number_of_bathrooms": 2.5,
      "number_of_living_areas": 2,
      "open_plan_layout": true,
      "study_present": true,
      "layout_efficiency_score": 8
    },
    "overall": {
      "property_presentation_score": 8,
      "maintenance_level": "well_maintained",
      "market_appeal_score": 8,
      "unique_features": ["pool", "modern_kitchen", "high_ceilings"],
      "negative_features": []
    },
    "metadata": {
      "total_images_analyzed": 15,
      "image_quality": "professional",
      "has_professional_photography": true,
      "extraction_confidence": 0.89,
      "extracted_at": ISODate("2025-11-07T09:00:00Z"),
      "model_used": "gpt-5-nano-2025-08-07"
    }
  },
  "processing_status": {
    "images_processed": true,
    "house_plans_found": true,
    "floor_size_extracted": true,
    "processed_at": ISODate("2025-11-07T09:00:00Z")
  },
  "existing_field": "value"
}
```

### Update Operations

**1. When House Plans Detected:**
```javascript
db.robina.updateOne(
  { _id: ObjectId("...") },
  {
    $set: {
      "house_plan": {
        urls: ["url1", "url2"],
        floor_area_sqm: 250.5,
        // ... other house plan data
      },
      "property_valuation_data": { /* extracted data */ },
      "processing_status": { /* status info */ }
    },
    $pull: {
      "images": { $in: ["url1", "url2"] }
    }
  }
)
```

**2. When No House Plans Found:**
```javascript
db.robina.updateOne(
  { _id: ObjectId("...") },
  {
    $set: {
      "property_valuation_data": { /* extracted data */ },
      "processing_status": {
        images_processed: true,
        house_plans_found: false,
        processed_at: new Date()
      }
    }
  }
)
```

---

## Testing Strategy

### Test Mode Features

1. **Incremental Processing**
   - Process documents one at a time
   - Check for house plans after each document
   - Stop when first house plan is found

2. **Data Collection**
   - Save all processed documents (with and without house plans)
   - Track the address of first property with house plans
   - Export data for manual review

3. **Logging Requirements**
   ```
   [TIMESTAMP] Processing document: 123 Main St, Robina
   [TIMESTAMP] Images found: 12
   [TIMESTAMP] GPT analysis started
   [TIMESTAMP] House plans detected: 0
   [TIMESTAMP] Property data extracted
   [TIMESTAMP] Document updated successfully
   
   [TIMESTAMP] Processing document: 456 Oak Ave, Robina
   [TIMESTAMP] Images found: 18
   [TIMESTAMP] GPT analysis started
   [TIMESTAMP] House plans detected: 2
   [TIMESTAMP] Floor size extracted: 285.5 sqm
   [TIMESTAMP] *** FIRST HOUSE PLAN FOUND ***
   [TIMESTAMP] Address: 456 Oak Ave, Robina
   [TIMESTAMP] Document updated successfully
   [TIMESTAMP] Test mode complete - stopping execution
   ```

4. **Output Files**
   - `test_run_summary.json` - All processed documents
   - `first_house_plan.json` - Details of property with plans
   - `processing_log.txt` - Detailed execution log

### Test Scenarios

1. **Documents without images field** - Should skip
2. **Documents with empty images array** - Should skip
3. **Documents with only property photos** - Extract data, no house plans
4. **Documents with house plans** - Extract all data + relocate plans
5. **Invalid image URLs** - Handle gracefully
6. **GPT API errors** - Retry logic
7. **Multiple floor plans in one property** - Handle all plans

### Manual Review Checklist

After test run completes, manually verify:
- [ ] All documents processed correctly
- [ ] House plan detection accuracy
- [ ] Floor size extraction accuracy
- [ ] URLs moved correctly from images to house_plan
- [ ] Property data quality and consistency
- [ ] No data loss or corruption
- [ ] Appropriate handling of edge cases

---

## GPT Prompt Design

### Prompt 1: Property Analysis & House Plan Detection

```python
PROPERTY_ANALYSIS_PROMPT = """
You are a property valuation expert analyzing images for a machine learning model.

Your task is to:
1. Analyze all provided property images
2. Extract structured property features for valuation
3. Identify any house floor plans among the images
4. If floor plans exist, extract the floor size area in square meters

For each image, determine:
- Is this a house floor plan? (yes/no)
- If yes, what is the floor area in sqm?

For the property overall, extract:

STRUCTURAL FEATURES:
- number_of_stories: (integer)
- building_type: (house/duplex/townhouse/apartment/unit)
- roof_type: (tile/metal/colorbond/slate/flat)
- roof_condition_score: (1-10)
- architectural_style: (description)

EXTERIOR FEATURES:
- overall_exterior_condition_score: (1-10)
- cladding_material: (brick/weatherboard/render/vinyl/fibro/composite/stone)
- cladding_condition_score: (1-10)
- paint_quality_score: (1-10)
- paint_condition: (new/good/fair/poor/peeling)
- window_type: (aluminium/timber/upvc/double_glazed)
- window_condition_score: (1-10)
- door_quality_score: (1-10)
- garage_type: (none/carport/single/double/triple)
- garage_condition_score: (1-10)

INTERIOR FEATURES (if visible):
- overall_interior_condition_score: (1-10)
- flooring_type: (carpet/timber/tiles/vinyl/concrete/laminate/hybrid)
- flooring_quality_score: (1-10)
- flooring_condition_score: (1-10)
- kitchen_quality_score: (1-10)
- kitchen_condition: (new/renovated/original/dated)
- bathroom_quality_score: (1-10)
- bathroom_condition: (new/renovated/original/dated)
- appliances_quality_score: (1-10)
- fixtures_quality_score: (1-10)
- ceiling_height: (standard/high/very_high)
- natural_light_score: (1-10)

RENOVATION:
- renovation_level: (fully_renovated/partial_renovation/original/tired)
- renovation_recency: (0-5_years/5-10_years/10-20_years/20+_years/unknown)
- modern_features_score: (1-10)

OUTDOOR FEATURES (if visible):
- landscaping_quality_score: (1-10)
- pool_present: (true/false)
- pool_type: (none/inground/aboveground/lap)
- pool_condition_score: (1-10, or null if no pool)
- outdoor_entertainment_score: (1-10)
- fence_type: (none/timber/colorbond/brick/pool_fence)
- fence_condition_score: (1-10)
- driveway_type: (concrete/paver/gravel/asphalt/exposed_aggregate)
- driveway_condition_score: (1-10)

LAYOUT (from floor plans if available):
- floor_area_sqm: (extract from floor plan)
- number_of_bedrooms: (integer)
- number_of_bathrooms: (float, e.g., 2.5)
- number_of_living_areas: (integer)
- open_plan_layout: (true/false)
- study_present: (true/false)
- layout_efficiency_score: (1-10)

OVERALL QUALITY:
- property_presentation_score: (1-10)
- maintenance_level: (well_maintained/average/needs_work/poor)
- market_appeal_score: (1-10)
- unique_features: (list any special features)
- negative_features: (list any issues)

IMAGE METADATA:
- total_images_analyzed: (count)
- image_quality: (professional/good/average/poor)
- has_professional_photography: (true/false)

HOUSE PLANS:
For each floor plan image:
- image_url: (the URL of the floor plan image)
- is_floor_plan: true
- floor_area_sqm: (extracted number)
- floor_area_source: (main_plan/ground_floor/upper_floor/total)
- dimensions: (e.g., "12m x 8m")
- confidence_score: (0-1)

Return your analysis as valid JSON with all the above fields.
Use null for fields where data is not visible or cannot be determined.
Include confidence scores for uncertain values.

IMPORTANT: Be consistent with your scoring. Use the 1-10 scale appropriately:
- 10: Exceptional
- 8-9: High quality
- 6-7: Good/Average
- 4-5: Below average
- 1-3: Poor

Images to analyze:
{image_urls}
"""
```

---

## Error Handling

### Error Categories

1. **MongoDB Errors**
   - Connection failures → Retry with exponential backoff
   - Query timeouts → Log and skip document
   - Update failures → Rollback and retry

2. **API Errors**
   - Rate limiting → Implement backoff strategy
   - Invalid API key → Stop execution immediately
   - Timeout errors → Retry with longer timeout
   - Model errors → Log and mark for manual review

3. **Image Processing Errors**
   - Invalid URLs → Skip image, log error
   - Download failures → Retry 3 times
   - Unsupported formats → Skip image, log error

4. **Data Validation Errors**
   - Invalid data types → Use default values
   - Missing required fields → Mark for review
   - Out of range values → Flag for verification

### Error Recovery

```python
ERROR_HANDLING_STRATEGY = {
    "mongodb_connection_error": {
        "action": "retry",
        "max_retries": 5,
        "backoff": "exponential",
        "fallback": "stop_execution"
    },
    "gpt_api_rate_limit": {
        "action": "wait_and_retry",
        "wait_time": 60,
        "max_retries": 3
    },
    "gpt_api_error": {
        "action": "retry",
        "max_retries": 3,
        "fallback": "skip_document_and_log"
    },
    "image_download_error": {
        "action": "retry",
        "max_retries": 3,
        "fallback": "skip_image"
    },
    "data_validation_error": {
        "action": "use_defaults",
        "log_level": "warning",
        "mark_for_review": true
    }
}
```

---

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**
   - Process multiple documents in parallel (configurable)
   - Use connection pooling for MongoDB
   - Implement queue system for API calls

2. **Caching**
   - Cache GPT responses for identical image sets
   - Store processed document IDs to avoid reprocessing
   - Cache image downloads temporarily

3. **Rate Limiting**
   - Respect OpenAI API rate limits
   - Implement token bucket algorithm
   - Configure requests per minute

4. **Resource Management**
   - Clean up temporary image files
   - Limit concurrent API calls
   - Monitor memory usage

### Performance Targets

- **Processing Speed**: 50-100 documents per hour (depends on images per property)
- **API Success Rate**: >95%
- **Data Accuracy**: >90% (measured against manual review)
- **Error Rate**: <5%

### Monitoring Metrics

```python
METRICS_TO_TRACK = {
    "documents_processed": "counter",
    "documents_with_images": "counter",
    "house_plans_found": "counter",
    "api_calls_made": "counter",
    "api_errors": "counter",
    "processing_time_avg": "gauge",
    "confidence_score_avg": "gauge",
    "images_per_property_avg": "gauge"
}
```

---

## Configuration File Structure

### config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "your_database_name"
COLLECTION_NAME = "robina"

# OpenAI Configuration
OPENAI_API_KEY = "REDACTED_OPENAI_KEY"
GPT_MODEL = "gpt-5-nano-2025-08-07"
MAX_TOKENS = 4000
TEMPERATURE = 0.1  # Low temperature for consistent, factual responses

# Processing Configuration
BATCH_SIZE = 10  # Number of documents to process in parallel
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 120  # seconds

# Test Mode Configuration
TEST_MODE = True  # Set to False for production run
STOP_AT_FIRST_HOUSE_PLAN = True  # Stop when first house plan is found

# Image Processing
MAX_IMAGES_PER_PROPERTY = 50
IMAGE_DOWNLOAD_TIMEOUT = 30
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".webp"]

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "logs/processing.log"
SAVE_PROCESSED_DATA = True
DATA_EXPORT_DIR = "output/"

# Paths
TEMP_DIR = "temp/"
OUTPUT_DIR = "output/"
LOG_DIR = "logs/"
```

### requirements.txt

```
openai>=1.0.0
pymongo>=4.0.0
python-dotenv>=1.0.0
requests>=2.31.0
Pillow>=10.0.0
retry>=0.9.2
```

---

## API Implementation Details

### GPT Vision API Call Structure

```python
import openai
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_property_images(image_urls, address):
    """
    Analyze property images using GPT vision model
    """
    try:
        # Prepare image messages
        messages = [
            {
                "role": "system",
                "content": "You are a property valuation expert..."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROPERTY_ANALYSIS_PROMPT
                    }
                ] + [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": url,
                            "detail": "high"  # For detailed analysis
                        }
                    }
                    for url in image_urls[:MAX_IMAGES_PER_PROPERTY]
                ]
            }
        ]
        
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"}  # Ensure JSON response
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"GPT API error for {address}: {str(e)}")
        raise
```

---

## Workflow Diagram

```
START
  |
  v
[Query MongoDB for documents with 'images' field]
  |
  v
[For each document:]
  |
  +---> [Check if 'images' field exists and not empty]
  |       |
  |       v
  |     [YES] --> Continue
  |     [NO]  --> Skip to next document
  |
  +---> [Validate image URLs]
  |
  +---> [Call GPT Vision API with all images]
  |
  +---> [Parse GPT response (JSON)]
  |
  +---> [Extract property valuation data]
  |
  +---> [Check if house plans detected]
  |       |
  |       v
  |     [House plans found?]
  |       |
  |       +--[YES]--> [Extract floor size]
  |       |           |
  |       |           v
  |       |         [Create 'house_plan' field]
  |       |           |
  |       |           v
  |       |         [Move URLs from 'images' to 'house_plan']
  |       |           |
  |       |           v
  |       |         [Log: HOUSE PLAN FOUND]
  |       |           |
  |       |           v
  |       |         [If TEST_MODE: Check stop condition]
  |       |           |
  |       |           +--[First house plan?]--> STOP & Export
  |       |           |
  |       |           +--[Not first]--> Continue
  |       |
  |       +--[NO]--> Continue
  |
  +---> [Update MongoDB document with extracted data]
  |
  +---> [Log processing result]
  |
  +---> [Save to output file for review]
  |
  v
[Next document]
  |
  v
[All documents processed or stop condition met]
  |
  v
[Generate final report]
  |
  v
END
```

---

## Output File Structures

### 1. test_run_summary.json

```json
{
  "run_metadata": {
    "start_time": "2025-11-07T09:00:00Z",
    "end_time": "2025-11-07T09:45:00Z",
    "total_documents_queried": 150,
    "documents_with_images": 120,
    "documents_processed": 45,
    "house_plans_found": 1,
    "first_house_plan_address": "456 Oak Ave, Robina",
    "test_mode": true,
    "stopped_at_first_house_plan": true
  },
  "processed_documents": [
    {
      "address": "123 Main St, Robina",
      "document_id": "507f1f77bcf86cd799439011",
      "images_count": 12,
      "house_plans_detected": false,
      "processing_time_seconds": 45.3,
      "extracted_features": {
        "building_type": "house",
        "number_of_stories": 1,
        "overall_condition_score": 7,
        "...": "..."
      },
      "confidence_score": 0.87,
      "processed_at": "2025-11-07T09:05:30Z"
    },
    {
      "address": "456 Oak Ave, Robina",
      "document_id": "507f1f77bcf86cd799439012",
      "images_count": 18,
      "house_plans_detected": true,
      "floor_plans_count": 2,
      "floor_area_sqm": 285.5,
      "processing_time_seconds": 52.1,
      "extracted_features": {
        "building_type": "house",
        "number_of_stories": 2,
        "overall_condition_score": 8,
        "...": "..."
      },
      "confidence_score": 0.93,
      "processed_at": "2025-11-07T09:12:15Z",
      "is_first_house_plan": true
    }
  ],
  "statistics": {
    "avg_processing_time": 48.7,
    "avg_images_per_property": 15.2,
    "avg_confidence_score": 0.88,
    "house_plan_detection_rate": 0.022
  }
}
```

### 2. first_house_plan.json

```json
{
  "address": "456 Oak Ave, Robina",
  "document_id": "507f1f77bcf86cd799439012",
  "mongodb_collection": "robina",
  "found_at": "2025-11-07T09:12:15Z",
  "original_images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/floorplan1.jpg",
    "https://example.com/image3.jpg",
    "https://example.com/floorplan2.jpg"
  ],
  "house_plan_urls": [
    "https://example.com/floorplan1.jpg",
    "https://example.com/floorplan2.jpg"
  ],
  "floor_size_data": {
    "floor_area_sqm": 285.5,
    "floor_area_source": "main_plan",
    "dimensions": "18m x 15.5m",
    "number_of_levels": 2,
    "confidence_score": 0.95
  },
  "property_valuation_data": {
    "structural": {
      "number_of_stories": 2,
      "building_type": "house",
      "roof_type": "tile",
      "roof_condition_score": 8,
      "architectural_style": "modern"
    },
    "exterior": {
      "overall_exterior_condition_score": 8,
      "cladding_material": "brick",
      "cladding_condition_score": 8,
      "paint_quality_score": 8,
      "paint_condition": "good"
    },
    "full_data": "..."
  },
  "manual_review_notes": {
    "verify_floor_size": true,
    "verify_house_plan_detection": true,
    "verify_url_migration": true
  }
}
```

### 3. processing_log.txt

```
2025-11-07 09:00:00 [INFO] Starting property valuation data extraction
2025-11-07 09:00:00 [INFO] Configuration: TEST_MODE=True, STOP_AT_FIRST_HOUSE_PLAN=True
2025-11-07 09:00:01 [INFO] Connected to MongoDB: localhost:27017
2025-11-07 09:00:01 [INFO] Collection: robina
2025-11-07 09:00:02 [INFO] Found 150 total documents
2025-11-07 09:00:02 [INFO] Documents with images: 120
2025-11-07 09:00:02 [INFO] Starting processing...

2025-11-07 09:05:15 [INFO] Processing document 1/120
2025-11-07 09:05:15 [INFO] Address: 123 Main St, Robina
2025-11-07 09:05:15 [INFO] Images found: 12
2025-11-07 09:05:16 [INFO] Calling GPT Vision API...
2025-11-07 09:06:01 [INFO] GPT analysis complete (45.3s)
2025-11-07 09:06:01 [INFO] House plans detected: 0
2025-11-07 09:06:01 [INFO] Extracting property valuation data...
2025-11-07 09:06:02 [INFO] Data validation passed (confidence: 0.87)
2025-11-07 09:06:02 [INFO] Updating MongoDB document...
2025-11-07 09:06:02 [INFO] Document updated successfully
2025-11-07 09:06:02 [INFO] Saved to test_run_summary.json

2025-11-07 09:12:00 [INFO] Processing document 2/120
2025-11-07 09:12:00 [INFO] Address: 456 Oak Ave, Robina
2025-11-07 09:12:00 [INFO] Images found: 18
2025-11-07 09:12:01 [INFO] Calling GPT Vision API...
2025-11-07 09:12:53 [INFO] GPT analysis complete (52.1s)
2025-11-07 09:12:53 [INFO] *** HOUSE PLANS DETECTED: 2 ***
2025-11-07 09:12:53 [INFO] Floor plan URLs: ['https://example.com/floorplan1.jpg', 'https://example.com/floorplan2.jpg']
2025-11-07 09:12:53 [INFO] Floor size extracted: 285.5 sqm (confidence: 0.95)
2025-11-07 09:12:53 [INFO] Creating 'house_plan' field...
2025-11-07 09:12:54 [INFO] Migrating URLs from 'images' to 'house_plan'...
2025-11-07 09:12:54 [INFO] Updating MongoDB document...
2025-11-07 09:12:54 [INFO] Document updated successfully
2025-11-07 09:12:54 [INFO] *** FIRST HOUSE PLAN FOUND ***
2025-11-07 09:12:54 [INFO] Address for manual review: 456 Oak Ave, Robina
2025-11-07 09:12:54 [INFO] Saved to first_house_plan.json
2025-11-07 09:12:54 [INFO] TEST MODE: Stopping at first house plan
2025-11-07 09:12:55 [INFO] Generating final summary...
2025-11-07 09:12:55 [INFO] Processing complete!
2025-11-07 09:12:55 [INFO] Summary saved to test_run_summary.json
2025-11-07 09:12:55 [INFO] Total documents processed: 2
2025-11-07 09:12:55 [INFO] House plans found: 1
2025-11-07 09:12:55 [INFO] Total processing time: 12m 55s
```

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] Test with sample data in test environment
- [ ] Verify MongoDB connection and permissions
- [ ] Validate OpenAI API key and quotas
- [ ] Review and adjust rate limiting settings
- [ ] Set up logging infrastructure
- [ ] Create backup of database before processing
- [ ] Document rollback procedures

### Configuration
- [ ] Set `TEST_MODE = False` for production run
- [ ] Set `STOP_AT_FIRST_HOUSE_PLAN = False`
- [ ] Configure appropriate `BATCH_SIZE`
- [ ] Set up monitoring alerts
- [ ] Configure data retention policies

### Monitoring
- [ ] Set up real-time processing dashboard
- [ ] Configure error alerting
- [ ] Monitor API usage and costs
- [ ] Track processing performance
- [ ] Monitor database performance

### Post-Processing
- [ ] Validate data quality with sampling
- [ ] Generate processing reports
- [ ] Archive logs and outputs
- [ ] Document any issues encountered
- [ ] Update documentation with lessons learned

---

## Security Considerations

1. **API Key Management**
   - Store API key in environment variables
   - Never commit to version control
   - Rotate keys periodically
   - Use restricted API keys if possible

2. **Database Security**
   - Use read-only credentials where possible
   - Implement connection encryption
   - Audit data access
   - Regular security updates

3. **Data Privacy**
   - Handle property data responsibly
   - Comply with data protection regulations
   - Implement data retention policies
   - Secure log files containing sensitive data

4. **Error Handling**
   - Don't expose sensitive info in logs
   - Sanitize error messages
   - Implement proper exception handling

---

## Maintenance and Updates

### Regular Maintenance
- Monitor GPT model updates and deprecations
- Review and update prompts based on results
- Optimize database queries
- Clean up temporary files and logs
- Update dependencies regularly

### Performance Tuning
- Adjust batch sizes based on performance
- Optimize MongoDB queries
- Fine-tune GPT parameters (temperature, max_tokens)
- Implement caching strategies
- Monitor and reduce API costs

### Quality Assurance
- Regular spot-checks of extracted data
- Validation against manual valuations
- Feedback loop for improving prompts
- A/B testing of different approaches
- Continuous model performance tracking

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Set up development environment** according to Phase 1
3. **Create project repository** and initialize version control
4. **Begin implementation** following the phased approach
5. **Run test mode** to validate first house plan detection
6. **Manual review** of first house plan results
7. **Iterate and improve** based on findings
8. **Scale to production** after successful testing

---

## Contact and Support

For questions or issues during implementation:
- Document all technical decisions
- Maintain detailed logs
- Create issue tickets for bugs
- Regular progress reviews
- Stakeholder updates at key milestones

---

## Appendix

### A. Sample MongoDB Query

```javascript
// Query to find documents with images
db.robina.find({
  "images": { 
    $exists: true, 
    $type: "array", 
    $ne: [] 
  }
})
```

### B. Sample Document Update

```javascript
// Update document with house plan data
db.robina.updateOne(
  { _id: ObjectId("507f1f77bcf86cd799439012") },
  {
    $set: {
      "house_plan": {
        "urls": ["url1", "url2"],
        "floor_area_sqm": 285.5,
        "floor_area_source": "main_plan",
        "dimensions": "18m x 15.5m",
        "number_of_levels": 2,
        "confidence_score": 0.95,
        "extracted_at": new Date()
      },
      "property_valuation_data": { /* ... */ }
    },
    $pull: {
      "images": { $in: ["url1", "url2"] }
    }
  }
)
```

### C. Environment Variables Template

```bash
# .env file
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=your_database_name
OPENAI_API_KEY=REDACTED_OPENAI_KEY

# Optional
LOG_LEVEL=INFO
TEST_MODE=True
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-07  
**Status:** Ready for Implementation
