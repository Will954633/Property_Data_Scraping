# GPT-Powered Property Valuation Data Extraction System

This system uses GPT Vision API to extract property valuation data from property images and identify house floor plans in the MongoDB `robina` collection.

## Features

- Analyzes property images using GPT-4 Vision
- Extracts 80+ property features for CatBoost valuation model
- Identifies and extracts floor plans from property images
- Extracts floor area from floor plans
- Updates MongoDB with structured data
- Test mode to validate system before full run

## Installation

1. Install Python dependencies:
```bash
cd 01_House_Plan_Data
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

Required configuration:
- `OPENAI_API_KEY`: Your OpenAI API key
- `MONGODB_URI`: MongoDB connection string (default: mongodb://localhost:27017/)
- `DATABASE_NAME`: Database name (default: Fetcha_Addresses)
- `COLLECTION_NAME`: Collection name (default: robina)

## Usage

### Test Mode (Recommended First Run)

Run in test mode to process documents until the first house plan is found:

```bash
cd src
python main.py
```

This will:
- Process documents one at a time
- Stop when the first house plan is found
- Save results to `output/` directory
- Generate detailed logs in `logs/` directory

### Production Mode

To run on all documents, edit `.env`:
```
TEST_MODE=False
STOP_AT_FIRST_HOUSE_PLAN=False
```

Then run:
```bash
cd src
python main.py
```

## Output Files

The system generates the following output files in the `output/` directory:

1. **test_run_summary_[timestamp].json** - Complete processing summary including:
   - All processed documents
   - Statistics
   - House plans found
   
2. **first_house_plan_[timestamp].json** - Details of the first property with house plans found (in test mode)

## Logs

Detailed logs are saved to `logs/processing.log` with:
- Document processing progress
- GPT API calls and responses
- House plan detections
- Errors and warnings

## MongoDB Schema

### Before Processing
```json
{
  "_id": ObjectId("..."),
  "address": "123 Main Street, Robina, QLD",
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/floorplan.jpg"
  ]
}
```

### After Processing (with house plans)
```json
{
  "_id": ObjectId("..."),
  "address": "123 Main Street, Robina, QLD",
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "house_plan": {
    "urls": ["https://example.com/floorplan.jpg"],
    "floor_area_sqm": 250.5,
    "floor_area_source": "main_plan",
    "number_of_levels": 2,
    "confidence_score": 0.95
  },
  "property_valuation_data": {
    "structural": {...},
    "exterior": {...},
    "interior": {...},
    "renovation": {...},
    "outdoor": {...},
    "layout": {...},
    "overall": {...},
    "metadata": {...}
  },
  "processing_status": {
    "images_processed": true,
    "house_plans_found": true,
    "floor_size_extracted": true,
    "processed_at": ISODate("2025-11-07T09:00:00Z")
  }
}
```

## Configuration Options

Edit `.env` to customize:

```bash
# Processing Configuration
TEST_MODE=True                    # Run in test mode
STOP_AT_FIRST_HOUSE_PLAN=True    # Stop when first house plan found
BATCH_SIZE=1                      # Process 1 document at a time
MAX_RETRIES=3                     # Retry failed API calls 3 times
RETRY_DELAY=5                     # Wait 5 seconds between retries

# Image Processing
MAX_IMAGES_PER_PROPERTY=50        # Maximum images to analyze per property

# Logging
LOG_LEVEL=INFO                    # Logging level (DEBUG, INFO, WARNING, ERROR)
```

## Project Structure

```
01_House_Plan_Data/
├── src/
│   ├── main.py              # Main execution script
│   ├── config.py            # Configuration management
│   ├── logger.py            # Logging setup
│   ├── mongodb_client.py    # MongoDB operations
│   ├── gpt_client.py        # GPT API client
│   └── prompts.py           # GPT prompts
├── logs/                    # Log files
├── output/                  # Output JSON files
├── temp/                    # Temporary files
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in git)
├── .env.example            # Example environment variables
└── README.md               # This file
```

## Extracted Features

The system extracts 80+ features across 8 categories:

1. **Structural** (5 features): stories, building type, roof type, etc.
2. **Exterior** (9 features): cladding, paint, windows, garage, etc.
3. **Interior** (11 features): flooring, kitchen, bathrooms, appliances, etc.
4. **Renovation** (3 features): renovation level, recency, modern features
5. **Outdoor** (8 features): landscaping, pool, fence, driveway, etc.
6. **Layout** (7 features): floor area, bedrooms, bathrooms, living areas, etc.
7. **Overall** (4 features): presentation, maintenance, appeal, features
8. **Metadata** (3 features): image count, quality, photography type

## Error Handling

The system includes:
- Automatic retries for API failures
- Graceful error handling for invalid images
- Detailed error logging
- Transaction safety for MongoDB updates

## Troubleshooting

### MongoDB Connection Error
```
Failed to connect to MongoDB
```
**Solution**: Ensure MongoDB is running:
```bash
# Check if MongoDB is running
mongosh --eval "db.version()"

# Start MongoDB if needed
brew services start mongodb-community
```

### OpenAI API Error
```
Invalid API key
```
**Solution**: Check your `.env` file has the correct `OPENAI_API_KEY`

### No Documents Found
```
Found 0 documents with images to process
```
**Solution**: 
- Verify collection name is correct in `.env`
- Check documents have an `images` field with URLs
- Ensure documents haven't already been processed

## Performance

- Processing time: ~30-60 seconds per property (depending on image count)
- API costs: ~$0.01-0.05 per property (depending on image count and quality)
- Recommended batch size for production: 10-100 documents at a time

## Support

For issues or questions, check:
1. Log files in `logs/processing.log`
2. Output files in `output/` directory
3. System plan in `SYSTEM_PLAN.md`

## License

Internal use only.

## Version

v1.0.0 - Initial implementation
