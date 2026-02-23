**Yes! I found the script you're looking for.**

## Location
`01_House_Plan_Data/src/gpt_client.py`

## Key Details

**AI Model Used:** `gpt-5-nano-2025-08-07` (configured in `config.py`)

**What It Does:**
1. **Analyzes property images** using OpenAI's GPT Vision API
2. **Creates detailed descriptions** of property features including:
   - Structural features (roof type, building type, stories)
   - Exterior condition (cladding, paint, windows, doors)
   - Interior features (flooring, kitchen, bathrooms, appliances)
   - Outdoor features (landscaping, pool, fencing)
   - Renovation level and quality scores

3. **Identifies and ranks images** by:
   - Detecting which images are floor plans vs regular photos
   - Assigning confidence scores (0-1) to each floor plan
   - Ranking images on usefulness with quality scores (1-10 scale)
   - Extracting floor area from floor plans

4. **Scores image quality** including:
   - Image quality assessment (professional/good/average/poor)
   - Professional photography detection
   - Property presentation score (1-10)
   - Market appeal score (1-10)

## How to Use It

The system works with the `properties_for_sale` collection. To run it:

```bash
cd 01_House_Plan_Data
python src/main.py
```

Or for parallel processing:
```bash
python src/main_parallel.py
```

## Configuration
Edit `01_House_Plan_Data/.env` to:
- Point to your `properties_for_sale` collection
- Set number of workers
- Configure batch sizes

The system will analyze images, create descriptions, rank them by usefulness, and update your MongoDB documents with the AI-generated insights.