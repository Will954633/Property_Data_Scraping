# Floor Plan Data Extraction System

This system uses GPT-5-nano-2025-08-07 to analyze floor plans from property listings and extract comprehensive data that home buyers would want to know.

## Overview

The system analyzes floor plan images stored in the `properties_for_sale` collection and extracts:
- Total floor area and land area
- Room-by-room dimensions and details
- Bedroom and bathroom counts
- Parking information
- Window orientations (when determinable)
- Layout features and flow
- Buyer insights and suitability

## Files

- **config.py** - Configuration settings (database, API keys, model)
- **prompts.py** - GPT prompt for floor plan analysis
- **logger.py** - Logging configuration
- **gpt_client.py** - OpenAI GPT Vision API client
- **mongodb_client.py** - MongoDB operations
- **analyze_single_property.py** - Main script to test on one property
- **.env** - Environment variables (API keys, database config)
- **requirements.txt** - Python dependencies

## Setup

1. **Install dependencies:**
   ```bash
   cd 01.1_Floor_Plan_Data
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   - The `.env` file is already configured with:
     - MongoDB connection to `property_data.properties_for_sale`
     - OpenAI API key
     - GPT model: `gpt-5-nano-2025-08-07`

3. **Ensure MongoDB is running:**
   ```bash
   # MongoDB should be running on localhost:27017
   ```

## Usage

### Test on One Property

To analyze a single property and manually review the results:

```bash
cd 01.1_Floor_Plan_Data
python analyze_single_property.py
```

This will:
1. Fetch the first property with floor plans from the database
2. Analyze the floor plan(s) using GPT-5-nano
3. Display the complete analysis results
4. Save results to `output/floor_plan_analysis_[address].json`
5. Ask if you want to save to MongoDB

### Analyze a Specific Property

```bash
python analyze_single_property.py "5 Picabeen Close, Robina, QLD 4226"
```

### Production Run (20 Parallel Workers)

To process all properties with floor plans using 20 parallel workers:

```bash
cd 01.1_Floor_Plan_Data
python run_production.py
```

**How it works:**
1. Counts all properties with floor plans that need analysis
2. Divides the work equally among 20 workers
3. Starts workers with 30-second delay between each
4. Each worker processes its assigned properties independently
5. All results are saved directly to MongoDB
6. Provides progress logging and final summary

**Performance:**
- With 20 workers, processing time is reduced by ~20x
- Each property takes ~80-90 seconds to analyze
- 100 properties: ~7-8 minutes (vs ~2.5 hours single-threaded)
- Workers start with 30-second stagger to avoid API rate limits

## Data Structure

The analysis is stored in the `floor_plan_analysis` field of each property document with this structure:

```json
{
  "total_floor_area": {
    "value": 250,
    "unit": "sqm",
    "confidence": "high",
    "notes": "..."
  },
  "bedrooms": {
    "total_count": 4,
    "details": "..."
  },
  "bathrooms": {
    "total_count": 2,
    "full_bathrooms": 1,
    "powder_rooms": 0,
    "ensuites": 1,
    "details": "..."
  },
  "rooms": [
    {
      "room_type": "bedroom",
      "room_name": "Master Bedroom",
      "level": "Ground Floor",
      "dimensions": {
        "length": 4.5,
        "width": 3.8,
        "unit": "m",
        "area": 17.1,
        "area_unit": "sqm"
      },
      "features": ["ensuite", "walk-in robe"],
      "window_orientation": {
        "directions": ["north"],
        "confidence": "high",
        "notes": "Determined from compass rose on floor plan"
      }
    }
  ],
  "parking": {
    "garage_spaces": 2,
    "carport_spaces": 0,
    "total_spaces": 2,
    "garage_type": "double"
  },
  "orientation_analysis": {
    "north_facing_rooms": ["Living Room", "Master Bedroom"],
    "methodology": "Determined from compass rose on floor plan",
    "confidence": "high"
  },
  "buyer_insights": {
    "ideal_for": ["families", "professionals"],
    "key_benefits": ["..."],
    "lifestyle_suitability": "..."
  },
  "data_quality": {
    "floor_plan_clarity": "excellent",
    "measurements_available": true,
    "orientation_indicators": true,
    "confidence_overall": "high"
  },
  "analysis_metadata": {
    "model_used": "gpt-5-nano-2025-08-07",
    "analyzed_at": 1702345678.123,
    "floor_plan_count": 1
  }
}
```

## Key Features

### Comprehensive Room Analysis
- Extracts ALL bedrooms (no upper limit - handles 1, 2, 3, 4, 5, 6+ bedrooms)
- Captures dimensions for every room when available
- Identifies room features (ensuite, walk-in robe, etc.)

### Window Orientation Detection
- Looks for compass rose or north arrow on floor plans
- Checks for sun symbols or orientation markers
- Provides confidence level and methodology explanation
- Honestly reports when orientation cannot be determined

### Standardized Layout
The system provides a consistent data structure across all properties:
- Total floor area
- Living room, kitchen, dining room
- Laundry, bathrooms
- Bedroom 1, Bedroom 2, ... Bedroom N (dynamic based on actual count)
- Outdoor spaces (balcony, patio, deck, alfresco)
- Parking details

### Buyer-Focused Insights
- Ideal buyer profiles
- Key benefits and selling points
- Lifestyle suitability assessment
- Natural light analysis

## Output

### Console Output
The script displays:
- Property address and floor plan URLs
- Complete JSON analysis
- Summary of key metrics (bedrooms, bathrooms, area, etc.)
- Data quality indicators

### File Output
- JSON file saved to `output/floor_plan_analysis_[address].json`
- Log file saved to `logs/floor_plan_processing.log`

### Database Storage
- Analysis stored in `floor_plan_analysis` field
- Can be queried and used for property comparisons
- Preserves original floor plan URLs in metadata

## Testing Workflow

1. **Run on one property:**
   ```bash
   python analyze_single_property.py
   ```

2. **Review the output:**
   - Check the JSON structure
   - Verify room counts are accurate
   - Confirm measurements match the floor plan
   - Validate orientation detection (if applicable)

3. **Assess data quality:**
   - Review the `data_quality` section
   - Check confidence levels
   - Note any missing information

4. **Decide whether to save:**
   - If results look good, save to MongoDB
   - If not, adjust prompts or try another property

## Next Steps

After testing and validating on one property:

1. **Review accuracy** - Manually compare extracted data with actual floor plan
2. **Adjust prompts** - If needed, refine the analysis prompt in `prompts.py`
3. **Scale up** - Create batch processing script to analyze all properties
4. **Monitor quality** - Track confidence scores and data completeness

## Model Information

- **Model:** gpt-5-nano-2025-08-07
- **Detail Level:** High (for accurate measurement extraction)
- **Response Format:** JSON object
- **Temperature:** Default (1.0 for gpt-5-nano)
- **Max Tokens:** 16,000

## Notes

- The system uses high-detail image analysis to capture measurements accurately
- Orientation detection depends on floor plan quality and indicators
- Some floor plans may not have all information available
- Confidence scores help identify reliable vs. uncertain data
