# Last Edit: 01/02/2026, Saturday, 8:22 am (Brisbane Time)
# Ollama Photo Reordering System - README

## Overview

This system creates optimal photo tour sequences for Gold Coast properties using the Ollama llama3.2:3b text model. It processes properties that already have `ollama_image_analysis` data and creates a logical virtual property tour.

## What It Does

1. **Analyzes existing image data** - Uses the `ollama_image_analysis` field created by the main Ollama analysis system
2. **Creates optimal photo tours** - Uses Ollama llama3.2:3b to select and order up to 15 photos following a logical property tour flow
3. **Adds tour metadata** - Inserts `ollama_photo_tour_order` and `ollama_photo_reorder_status` fields into documents

## Tour Flow

The system creates a virtual tour following this logical sequence:

1. **Front of property** (exterior/street view)
2. **Through the front door** (entrance/foyer)
3. **Into the kitchen**
4. **Main living area** (living room/lounge)
5. **Main bedroom** (master bedroom)
6. **Other bedrooms**
7. **Laundry**
8. **Back yard**
9. **Pool** (if present)

## Requirements

- Properties must already have `ollama_image_analysis` field populated (run `run_production.py` first)
- MongoDB connection to `Gold_Coast_Currently_For_Sale` database
- Ollama running locally with llama3.2:3b model installed

## Installation

### 1. Install Ollama Model

```bash
ollama pull llama3.2:3b
```

### 2. Verify Ollama is Running

```bash
ollama list
```

You should see `llama3.2:3b` in the list.

## Usage

### Test with Single Property

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 test_photo_reorder_single.py
```

### Process All Properties

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 ollama_photo_reorder.py
```

### Process Limited Number of Properties

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 ollama_photo_reorder.py 10
```

This will process only 10 properties (useful for testing).

## Output Data Structure

The system adds these fields to each document:

### `ollama_photo_tour_order` (Array)

Each photo in the tour contains:

```json
{
  "reorder_position": 1,
  "image_index": 5,
  "url": "https://...",
  "tour_section": "front_exterior",
  "description": "Front view of the property",
  "usefulness_score": 9,
  "selection_reason": "High-quality exterior shot showing curb appeal",
  "tour_metadata": {
    "total_photos_selected": 15,
    "sections_included": ["front_exterior", "kitchen", "living_area", ...],
    "sections_missing": ["laundry"],
    "average_usefulness_score": 8.2,
    "tour_completeness_score": 9
  }
}
```

### `ollama_photo_reorder_status` (Object)

```json
{
  "photo_tour_created": true,
  "photos_in_tour": 15,
  "reordered_at": "2026-01-02T08:22:00Z",
  "processing_duration_seconds": 3.5,
  "model": "llama3.2:3b",
  "engine": "ollama"
}
```

## Valid Tour Sections

- `front_exterior` - Front of property
- `entrance` - Entry/foyer
- `kitchen` - Kitchen
- `living_area` - Main living room
- `main_bedroom` - Master bedroom
- `other_bedroom` - Additional bedrooms
- `laundry` - Laundry room
- `back_yard` - Outdoor/backyard
- `pool` - Pool area

## Files

- `ollama_photo_reorder.py` - Main script for processing all properties
- `test_photo_reorder_single.py` - Test script for single property
- `ollama_reorder_client.py` - Ollama API client for photo reordering
- `mongodb_reorder_client.py` - MongoDB operations for reordering
- `prompts_reorder.py` - Prompts for Ollama model

## Configuration

The system uses the same configuration as the main Ollama analysis system:

- **Database**: `Gold_Coast_Currently_For_Sale`
- **Target Suburbs**: robina, mudgeeraba, varsity_lakes, reedy_creek, burleigh_waters, merrimac, worongary
- **Model**: llama3.2:3b (fast text model)
- **Max Photos**: 15 per tour

## Performance

- **Processing Speed**: ~3-5 seconds per property
- **Model**: llama3.2:3b (2GB, text-only)
- **Cost**: FREE (runs locally)

## Troubleshooting

### No properties found for reordering

- Ensure `run_production.py` has been run first to create `ollama_image_analysis` data
- Check that properties have images available
- Verify MongoDB connection

### Ollama connection errors

- Verify Ollama is running: `ollama list`
- Check Ollama is accessible at `http://localhost:11434`
- Ensure llama3.2:3b model is installed: `ollama pull llama3.2:3b`

### Model not found

```bash
ollama pull llama3.2:3b
```

## Next Steps

After running the photo reordering system, you can:

1. Query properties with photo tours:
   ```javascript
   db.robina.find({ "ollama_photo_tour_order": { $exists: true } })
   ```

2. Use the `ollama_photo_tour_order` array to display properties in optimal order
3. Filter by `tour_section` to show specific areas
4. Sort by `reorder_position` for the correct sequence

## Advantages

- ✅ **FREE** - No API costs (runs locally with Ollama)
- ✅ **Fast** - Text-only model is very quick
- ✅ **Private** - All data stays on your machine
- ✅ **No Rate Limits** - Process as many properties as needed
- ✅ **Consistent** - Uses existing analysis data for reliable results

## Integration with Main System

This photo reorder system is designed to run **after** the main Ollama property analysis:

1. Run `run_production.py` to analyze property images (creates `ollama_image_analysis`)
2. Run `ollama_photo_reorder.py` to create photo tours (creates `ollama_photo_tour_order`)

Both systems work together to provide comprehensive property image analysis and optimal photo sequencing for virtual tours.
