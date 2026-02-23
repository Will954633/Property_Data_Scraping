# Last Edit: 01/02/2026, Saturday, 7:15 am (Brisbane Time)
# UPDATED: Fixed suburb names in config.py (underscores for multi-word, correct spellings)

# Ollama Property Analysis System

## Overview

This system uses **Ollama's llama3.2-vision:11b** model to analyze property images and extract detailed valuation data. It replaces OpenAI GPT models with a locally-hosted Ollama instance for cost-effective, private property analysis.

### Key Features

- **Local AI Processing**: Uses Ollama instead of cloud-based OpenAI API
- **Suburb Filtering**: Only processes properties in target Gold Coast suburbs
- **Vision Analysis**: Analyzes property images to extract structural, exterior, interior, and outdoor features
- **Image Ranking**: Ranks images by marketing usefulness
- **Water View Detection**: Identifies and scores natural water views
- **Batch Processing**: Efficiently processes multiple properties
- **MongoDB Integration**: Stores results in Gold_Coast_Currently_For_Sale database

### Target Suburbs

- Robina
- Mudgeeraba
- Varsity Lakes (varsity_lakes)
- Reedy Creek (reedy_creek)
- Burleigh Waters (burleigh_waters)
- Merrimac (merrimac)
- Worongary (worongary)

**Note:** Collection names use underscores for multi-word suburbs. See `SUBURB_NAME_FIX_SUMMARY.md` for details.

---

## Prerequisites

### 1. Ollama Installation

Install Ollama on your system:

```bash
# macOS
brew install ollama

# Or download from https://ollama.ai
```

### 2. Pull the Vision Model

```bash
ollama pull llama3.2-vision:11b
```

### 3. Start Ollama Server

```bash
ollama serve
```

The server will run on `http://localhost:11434` by default.

### 4. MongoDB

Ensure MongoDB is running and accessible at `mongodb://localhost:27017/`

### 5. Python Dependencies

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && pip install -r requirements.txt
```

---

## Setup

### 1. Create Environment File

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && cp .env.example .env
```

### 2. Configure Settings (Optional)

Edit `.env` to customize:
- MongoDB connection
- Ollama server URL
- Processing parameters
- Test mode settings

---

## Usage

### Test Run (Recommended First)

Process a small batch to verify everything works:

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 run_production.py
```

By default, `TEST_RUN=True` in config.py, which limits processing to 2 batches (100 properties).

### Production Run

To process all unprocessed properties:

1. Edit `config.py` and set:
   ```python
   TEST_RUN = False
   MAX_BATCHES = 0  # Unlimited
   ```

2. Run:
   ```bash
   cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 run_production.py
   ```

---

## How It Works

### 1. Document Selection

The system queries MongoDB for properties that:
- Are in one of the target suburbs
- Have images available
- Have NOT been processed by Ollama (`ollama_analysis.processed != True`)

### 2. Image Analysis

For each property:
1. Downloads and encodes images (up to 30 per property)
2. Sends to Ollama llama3.2-vision:11b model
3. Receives structured JSON analysis

### 3. Data Extraction

Extracts comprehensive property data:

**Structural Features:**
- Building type, stories, roof type/condition
- Architectural style

**Exterior Features:**
- Cladding material/condition
- Paint quality
- Windows, doors, garage

**Interior Features:**
- Flooring type/quality
- Kitchen and bathroom condition
- Appliances, fixtures
- Natural light, ceiling height

**Outdoor Features:**
- Landscaping quality
- Pool presence/type/condition
- Fencing, driveway

**Water Views:**
- Natural water view detection
- View type (ocean/lake/river/canal/bay)
- Quality scoring (1-10)
- Room-specific view analysis

**Image Analysis:**
- Image type classification
- Usefulness scoring (1-10)
- Quality assessment
- Marketing value rating

### 4. MongoDB Storage

Results are stored in three new fields:
- `ollama_analysis`: Processing metadata
- `ollama_image_analysis`: Image rankings and descriptions
- `ollama_property_data`: Extracted property features

---

## Output Structure

### ollama_analysis
```json
{
  "processed": true,
  "images_analyzed": 25,
  "processed_at": "2026-01-31T09:44:00Z",
  "model": "llama3.2-vision:11b",
  "engine": "ollama",
  "worker_id": "main_worker",
  "processing_duration_seconds": 145.3
}
```

### ollama_image_analysis
```json
[
  {
    "image_index": 0,
    "image_type": "exterior",
    "usefulness_score": 9,
    "description": "Front facade showing modern architecture",
    "quality_score": 8,
    "marketing_value": "high",
    "url": "https://..."
  }
]
```

### ollama_property_data
```json
{
  "structural": {
    "number_of_stories": 2,
    "building_type": "house",
    "roof_type": "tile",
    "roof_condition_score": 8
  },
  "exterior": { ... },
  "interior": { ... },
  "renovation": { ... },
  "outdoor": {
    "natural_water_view": true,
    "water_view_type": "canal",
    "water_view_quality_score": 7,
    "water_view_description": "Direct canal views from rear",
    "water_view_rooms": [
      {
        "room_type": "living_room",
        "water_view_type": "canal",
        "view_quality_score": 8,
        "description": "Panoramic canal views"
      }
    ]
  },
  "layout": { ... },
  "overall": { ... },
  "metadata": {
    "model_used": "llama3.2-vision:11b",
    "extracted_at": 1738324440.5,
    "analysis_engine": "ollama"
  }
}
```

---

## Performance

### Expected Processing Times

- **Per Property**: 60-180 seconds (depending on image count)
- **Per Batch (50 properties)**: 50-150 minutes
- **Full Run (all suburbs)**: Varies by property count

### Resource Requirements

- **RAM**: 8GB+ recommended for llama3.2-vision:11b
- **GPU**: Optional but significantly faster
- **Disk**: ~7GB for model storage

---

## Monitoring

### View Progress

Check logs in real-time:
```bash
tail -f logs/ollama_processing.log
```

### Check Statistics

The system displays:
- Initial property counts by suburb
- Processing progress
- Success/failure rates
- Final statistics

---

## Troubleshooting

### Ollama Not Running

**Error**: `Failed to connect to Ollama at http://localhost:11434`

**Solution**:
```bash
ollama serve
```

### Model Not Found

**Error**: `Model llama3.2-vision:11b not found`

**Solution**:
```bash
ollama pull llama3.2-vision:11b
```

### MongoDB Connection Failed

**Error**: `Failed to connect to MongoDB`

**Solution**:
- Ensure MongoDB is running
- Check MONGODB_URI in .env or config.py

### Out of Memory

**Error**: Ollama crashes or system freezes

**Solution**:
- Reduce `MAX_IMAGES_PER_PROPERTY` in config.py
- Close other applications
- Consider using a smaller model

### Slow Processing

**Solutions**:
- Use GPU acceleration if available
- Reduce `MAX_IMAGES_PER_PROPERTY`
- Increase `OLLAMA_TIMEOUT` if requests are timing out

---

## Configuration Options

### config.py

```python
# Target suburbs - Collection names (must match database exactly)
TARGET_SUBURBS = [
    "robina", "mudgeeraba", "varsity_lakes",
    "reedy_creek", "burleigh_waters", "merrimac", "worongary"
]

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2-vision:11b"
OLLAMA_TIMEOUT = 300  # 5 minutes

# Processing
MAX_IMAGES_PER_PROPERTY = 30
MAX_RETRIES = 3
RETRY_DELAY = 5

# Batch processing
PARALLEL_BATCH_SIZE = 50

# Testing
TEST_RUN = True  # Set to False for production
MAX_BATCHES = 2  # Limit for testing
```

---

## Differences from GPT Version

### Advantages

1. **Cost**: Free to run locally (no API costs)
2. **Privacy**: Data never leaves your machine
3. **Control**: Full control over model and processing
4. **No Rate Limits**: Process as fast as hardware allows

### Considerations

1. **Speed**: Slower than GPT-4 Vision (60-180s vs 10-30s per property)
2. **Hardware**: Requires local compute resources
3. **Quality**: May vary from GPT-4 Vision results
4. **Setup**: Requires Ollama installation and model download

---

## File Structure

```
Ollama_Property_Analysis/
├── config.py              # Configuration settings
├── ollama_client.py       # Ollama API client
├── mongodb_client.py      # MongoDB operations with suburb filtering
├── worker.py              # Property processing worker
├── prompts.py             # Analysis prompts
├── logger.py              # Logging configuration
├── run_production.py      # Main execution script
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
├── logs/                  # Processing logs
└── output/                # Optional output files
```

---

## Support

For issues or questions:
1. Check logs in `logs/ollama_processing.log`
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Test MongoDB connection: `mongosh`
4. Review configuration in `config.py`

---

## Future Enhancements

Potential improvements:
- Parallel worker support for faster processing
- Progress monitoring dashboard
- Comparison with GPT results
- Fine-tuning prompts for better accuracy
- Support for additional Ollama vision models
- Automated quality validation

---

## License

Part of the Property Data Scraping project.
