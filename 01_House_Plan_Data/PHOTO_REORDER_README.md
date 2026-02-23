# Photo Reordering System for Virtual Property Tours

## Overview

This system processes properties from the `properties_for_sale` collection that already have `image_analysis` data and creates an optimal photo ordering for virtual property tours.

## What It Does

1. **Analyzes existing image data** - Uses the `image_analysis` field that was created by `main_parallel.py`
2. **Creates optimal photo tours** - Uses GPT-5-nano to select and order up to 15 photos following a logical property tour flow
3. **Adds tour metadata** - Inserts `photo_tour_order` and `photo_reorder_status` fields into documents

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

- Properties must already have `image_analysis` field populated (run `main_parallel.py` first)
- MongoDB connection to `property_data.properties_for_sale`
- OpenAI API key configured in `.env`

## Configuration

Edit `01_House_Plan_Data/.env` to configure:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
# Note: Database and collection are hardcoded to:
# - Database: property_data
# - Collection: properties_for_sale

# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here

# Processing Configuration
NUM_WORKERS=3                    # Number of parallel workers
PARALLEL_BATCH_SIZE=100          # Documents per batch
TEST_RUN=True                    # Set to False for full run
MAX_BATCHES=5                    # Limit batches in test mode (0 = unlimited)
WORKER_STARTUP_DELAY=0           # Seconds between worker startups
```

## Usage

### Run Photo Reordering

```bash
cd 01_House_Plan_Data
python src/photo_reorder_parallel.py
```

### Test Mode (Recommended First)

The system defaults to test mode (`TEST_RUN=True`) which processes only 5 batches. This is perfect for:
- Verifying the system works correctly
- Testing on a subset of properties
- Checking the quality of photo ordering

### Production Mode

To process all properties:

1. Edit `.env` and set:
   ```bash
   TEST_RUN=False
   MAX_BATCHES=0
   ```

2. Run the script:
   ```bash
   python src/photo_reorder_parallel.py
   ```

## Output Data Structure

The system adds these fields to each document:

### `photo_tour_order` (Array)

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
    "tour_completeness_score": 9,
    "model_used": "gpt-5-nano-2025-08-07",
    "created_at": 1702612345.67
  }
}
```

### `photo_reorder_status` (Object)

```json
{
  "photo_tour_created": true,
  "photos_in_tour": 15,
  "reordered_at": "2025-12-15T08:30:00Z",
  "worker_id": 2,
  "processing_duration_seconds": 3.5
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

## Monitoring Progress

Logs are saved to timestamped directories in `01_House_Plan_Data/logs/`:

- `coordinator.log` - Overall system progress
- `worker_01.log`, `worker_02.log`, etc. - Individual worker logs
- `progress.log` - Real-time progress updates

## Key Features

1. **Intelligent Selection** - Chooses photos with highest usefulness scores
2. **Maximum 15 Photos** - Keeps tours concise and engaging
3. **Logical Flow** - Follows natural property walkthrough sequence
4. **Parallel Processing** - Uses multiple workers for speed
5. **Idempotent** - Only processes properties without `photo_tour_order`

## Files Created

- `photo_reorder_parallel.py` - Main coordinator
- `batch_manager_reorder.py` - Batch management
- `worker_reorder.py` - Worker process
- `mongodb_reorder_client.py` - Database operations
- `gpt_reorder_client.py` - GPT API client
- `prompts_reorder.py` - GPT prompts

## Troubleshooting

### No documents found for reordering

- Ensure `main_parallel.py` has been run first to create `image_analysis` data
- Check that properties have images available

### Connection errors

- Verify MongoDB is running: `mongosh`
- Check `MONGODB_URI` in `.env`

### API errors

- Verify `OPENAI_API_KEY` is set correctly
- Check API quota/limits

## Performance

- **Processing Speed**: ~3-5 seconds per property
- **Parallel Workers**: 3 workers by default (configurable)
- **Batch Size**: 100 properties per batch

## Next Steps

After running the photo reordering system, you can:

1. Query properties with photo tours:
   ```javascript
   db.properties_for_sale.find({ "photo_tour_order": { $exists: true } })
   ```

2. Use the `photo_tour_order` array to display properties in optimal order
3. Filter by `tour_section` to show specific areas
4. Sort by `reorder_position` for the correct sequence

## Notes

- The system uses `gpt-5-nano-2025-08-07` (same as main_parallel.py)
- Only processes properties that don't already have `photo_tour_order`
- Skips properties without `image_analysis` data
- Creates up to 15 photos per tour (configurable in prompt)
