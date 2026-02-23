# OCR System Setup Guide

Complete guide for setting up and using the OCR property data extraction system.

## Overview

This system extracts property data from screenshots using OCR (Optical Character Recognition) and structures it into JSON format.

**Three-step process:**
1. Capture screenshots (native_scroll_screenshot.py)
2. Extract text with OCR (ocr_extractor.py)
3. Parse and structure data (data_parser.py)

## Installation

### Step 1: Install Tesseract OCR

Tesseract is the OCR engine that reads text from images.

**macOS:**
```bash
brew install tesseract
```

**Verify installation:**
```bash
tesseract --version
```

### Step 2: Install Python Dependencies

**Option A: Using conda (recommended for your system):**
```bash
cd 07_Undetectable_method/Simple_Method
conda install -c conda-forge pytesseract pillow
```

**Option B: Using pip:**
```bash
pip install -r ocr_requirements.txt
```

Or install individually:
```bash
pip install pytesseract Pillow
```

## Usage

### Complete Workflow

**Step 1: Capture Screenshots**
```bash
python3 native_scroll_screenshot.py
```
- Opens realestate.com.au in Chrome
- Takes 25 screenshots while scrolling
- Saves to `screenshots/` folder
- Closes tab automatically

**Step 2: Extract Text with OCR**
```bash
python3 ocr_extractor.py
```
- Reads all screenshots from `screenshots/`
- Extracts text using Tesseract OCR
- Saves raw text to `ocr_output/`
- Creates combined text file and JSON

**Step 3: Parse Property Data**
```bash
python3 data_parser.py
```
- Reads OCR text from `ocr_output/`
- Parses property information using regex
- Structures data into JSON
- Saves to `property_data.json`

### Quick Run (All Steps)

```bash
# Run all three steps sequentially
python3 native_scroll_screenshot.py && \
python3 ocr_extractor.py && \
python3 data_parser.py
```

## Output Files

### After Screenshot Capture:
```
screenshots/
  section_01_20251112_201230.png
  section_02_20251112_201232.png
  ...
  section_25_20251112_201305.png
```

### After OCR Extraction:
```
ocr_output/
  raw_text_all.txt          # Combined text from all screenshots
  ocr_data.json             # Structured OCR data
  section_01_*.txt          # Individual text files
  section_02_*.txt
  ...
```

### After Data Parsing:
```
property_data.json          # Final structured property data
```

## Property Data Structure

Example `property_data.json`:
```json
{
  "extraction_date": "2025-12-11T20:15:30",
  "total_properties": 45,
  "properties": [
    {
      "address": "123 Main St, Robina QLD 4226",
      "price": "$850,000",
      "bedrooms": 4,
      "bathrooms": 2,
      "parking": 2,
      "property_type": "House",
      "raw_text": "..."
    }
  ],
  "statistics": {
    "with_price": 42,
    "with_bedrooms": 45,
    "with_bathrooms": 43,
    "with_parking": 40,
    "with_type": 38
  }
}
```

## Extracted Data Fields

- **address** - Full property address
- **price** - Sale price (if available)
- **bedrooms** - Number of bedrooms
- **bathrooms** - Number of bathrooms
- **parking** - Number of car spaces
- **property_type** - House, Townhouse, Unit, etc.
- **raw_text** - Original text line containing the property

## Troubleshooting

### Issue: "Tesseract not found"

**Solution:**
```bash
# Install Tesseract
brew install tesseract

# Verify installation
tesseract --version
```

### Issue: "No screenshots found"

**Solution:**
Run the screenshot capture first:
```bash
python3 native_scroll_screenshot.py
```

### Issue: "OCR file not found"

**Solution:**
Run OCR extraction before parsing:
```bash
python3 ocr_extractor.py
```

### Issue: Low OCR accuracy

**Possible causes:**
- Screenshot quality is poor
- Text is too small
- Image has low contrast

**Solutions:**
- Increase Chrome window size before capturing
- Ensure page is fully loaded
- Check screenshot quality manually

### Issue: Few properties extracted

**Possible causes:**
- OCR text quality is poor
- Regex patterns need tuning
- Property format differs from expected

**Solutions:**
1. Check `ocr_output/raw_text_all.txt` to see what was extracted
2. Manually verify a few screenshots
3. Adjust regex patterns in `data_parser.py` if needed

## Configuration

### Adjust Number of Screenshots

Edit `native_scroll_screenshot.py`:
```python
NUM_SCROLLS = 25  # Change this number
```

### Adjust OCR Settings

Edit `ocr_extractor.py` to add Tesseract config:
```python
text = pytesseract.image_to_string(img, config='--psm 6')
```

PSM modes:
- `3` = Fully automatic (default)
- `6` = Assume uniform block of text
- `11` = Sparse text

### Customize Regex Patterns

Edit `data_parser.py` to modify extraction patterns:
```python
# Example: Add support for different address formats
address_pattern = r'your_pattern_here'
```

## Tips for Best Results

1. **Maximize Chrome window** before running screenshot script
2. **Ensure good page loading** - increase `INITIAL_LOAD_DELAY` if needed
3. **Check screenshots** in `screenshots/` folder to verify quality
4. **Review raw OCR text** in `ocr_output/raw_text_all.txt`
5. **Iterative refinement** - run multiple times and refine patterns

## Advanced Usage

### Process Different URLs

Edit `native_scroll_screenshot.py`:
```python
TARGET_URL = "your_url_here"
```

### Batch Processing

Create a script to process multiple suburbs:
```bash
#!/bin/bash
SUBURBS=("robina" "burleigh" "mudgeeraba")

for suburb in "${SUBURBS[@]}"; do
    # Update URL in script
    # Run all three steps
    python3 native_scroll_screenshot.py
    python3 ocr_extractor.py
    python3 data_parser.py
    # Move output files
    mv property_data.json "property_data_${suburb}.json"
done
```

## Performance

**Typical processing times:**
- Screenshot capture: ~1 minute (25 screenshots)
- OCR extraction: ~30 seconds (25 images)
- Data parsing: <1 second

**Total: ~2 minutes** from start to finish

## Support

For issues or questions:
1. Check this setup guide
2. Review error messages carefully
3. Test each step individually
4. Check intermediate output files

## Next Steps

After getting property data:
1. Import into database (MongoDB, PostgreSQL, etc.)
2. Add geocoding for mapping
3. Analyze pricing trends
4. Compare with other data sources
5. Build visualization dashboard
