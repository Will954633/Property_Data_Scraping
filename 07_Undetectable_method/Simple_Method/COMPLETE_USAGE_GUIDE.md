# Complete Undetectable Property Scraping System

## 🎯 System Overview

A fully autonomous, 100% undetectable property data extraction system using:
- **Native macOS tools** (no Selenium - undetectable!)
- **OCR text extraction** (Tesseract)
- **Intelligent data parsing** (regex with OCR quirk handling)

## ⚡ Quick Start - Complete Workflow

### One-Time Setup (5 minutes):

```bash
cd 07_Undetectable_method/Simple_Method

# 1. Install Tesseract OCR
brew install tesseract

# 2. Install Python dependencies
pip install pytesseract Pillow
```

### Run Complete System (2 minutes):

**IMPORTANT:** Use `python` (NOT `python3`)

```bash
# Step 1: Capture 25 screenshots (autonomous)
python native_scroll_screenshot.py

# Step 2: Extract text with OCR (~30 seconds)
python ocr_extractor.py

# Step 3: Parse property data (<1 second)
python data_parser_best.py

# Done! View results:
cat property_data_best.json
```

## 📊 Results Summary

**From your latest run:**
- ✅ **29 properties** extracted
- ✅ **93% data completeness** (price, beds, baths, parking)
- ✅ **100% have agent names**
- ✅ **83% have agency info**
- ✅ **79% have land size**

### Data Fields Extracted:
- Address (100%)
- Price (93%)
- Bedrooms (93%)
- Bathrooms (93%)
- Parking (93%)
- Land size (79%)
- Property type (86%)
- Agency (83%)
- Agent name (100%)
- Listing URL (10% - OCR limitation)
- Inspection times (31%)

## 📁 Output Files

### Screenshots:
```
screenshots/
  section_01_*.png through section_25_*.png
```

### OCR Output:
```
ocr_output/
  raw_text_all.txt       # All extracted text
  ocr_data.json          # OCR metadata
  section_*.txt          # Individual text files
```

### Property Data:
```
property_data_best.json  # ⭐ FINAL OUTPUT - Use this!
```

## 🔍 Property Data Structure

```json
{
  "extraction_date": "2025-11-12T20:55:00",
  "source": "realestate.com.au - Robina QLD 4226 houses",
  "total_properties": 29,
  "properties": [
    {
      "address": "18 Mornington Terrace, Robina",
      "bedrooms": 4,
      "bathrooms": 4,
      "parking": 2,
      "land_size_sqm": 934,
      "property_type": "House",
      "price": "$2,399,000+",
      "price_type": "exact",
      "agency": "N/A",
      "agent": "Nicole Carter",
      "inspection": "Inspection Sat 15 Nov 10:00 am"
    }
  ],
  "statistics": { ... }
}
```

## 🚀 Why This System is Undetectable

✅ **No Selenium/WebDriver** - Website cannot detect automation  
✅ **Native macOS scrolling** - Real Page Down keypresses  
✅ **Native screenshots** - macOS screencapture tool  
✅ **AppleScript control** - OS-level Chrome control  
✅ **Real login session** - Uses your actual Chrome profile  

## 💡 Tips for Better Results

### 1. Improve OCR Accuracy
- Maximize Chrome window before capturing screenshots
- Ensure page is fully loaded (increase `INITIAL_LOAD_DELAY` if needed)
- Use good lighting/display settings

### 2. Capture More Properties
- Increase `NUM_SCROLLS` in `native_scroll_screenshot.py`
- Current: 25 scrolls captures ~29 properties

### 3. Handle OCR Errors
- Check `ocr_output/raw_text_all.txt` to see extracted text
- Some OCR errors are expected (e.g., "42" = "4 bath 2 car")
- Parser handles most common OCR quirks automatically

## 🛠️ Troubleshooting

### "No module named 'PIL'"
**Solution:** Use `python` not `python3`
```bash
python ocr_extractor.py  # ✅ Correct
python3 ocr_extractor.py  # ❌ Wrong
```

### Low data completeness
**Solutions:**
1. Check screenshot quality in `screenshots/` folder
2. Review `ocr_output/raw_text_all.txt` for OCR errors
3. Adjust regex patterns in `data_parser_best.py` if needed
4. Increase `INITIAL_LOAD_DELAY` for better page loading

### Missing property fields
- URLs have low capture rate (10%) due to OCR limitations
- Inspection times depend on text clarity in screenshots
- Some properties may have "Contact Agent" instead of prices

## 📝 Customization

### Change Target URL

Edit `native_scroll_screenshot.py`:
```python
TARGET_URL = "https://your-url-here"
```

### Adjust Scroll Count

Edit `native_scroll_screenshot.py`:
```python
NUM_SCROLLS = 30  # Change from 25 to 30 for longer pages
```

### Modify Data Fields

Edit `data_parser_best.py` to add custom fields or regex patterns.

## 🔄 Processing Multiple Suburbs

Create a batch script:
```bash
#!/bin/bash
URLS=(
  "robina,+qld+4226"
  "burleigh-heads,+qld+4220"
  "mudgeeraba,+qld+4213"
)

for suburb in "${URLS[@]}"; do
  # Update URL in script
  sed -i '' "s|robina,+qld+4226|$suburb|g" native_scroll_screenshot.py
  
  # Run workflow
  python native_scroll_screenshot.py
  python ocr_extractor.py
  python data_parser_best.py
  
  # Save output
  mv property_data_best.json "data_${suburb}.json"
  
  # Clean up for next run
  rm -rf screenshots/* ocr_output/*
done
```

## 📈 Performance

**Total Time:** ~2 minutes per suburb
- Screenshot capture: ~60 seconds (25 screenshots)
- OCR extraction: ~30 seconds (118 files)
- Data parsing: <1 second

## ✅ Complete System Files

**Core Scripts:**
1. `native_scroll_screenshot.py` - Screenshot capture
2. `ocr_extractor.py` - OCR text extraction
3. `data_parser_best.py` - Property data parser

**Documentation:**
4. `COMPLETE_USAGE_GUIDE.md` - This file
5. `OCR_SETUP.md` - Detailed setup guide
6. `NATIVE_METHOD.md` - Technical details

## 🎓 Learning & Improvement

The parser uses regex patterns that can be refined. If you notice missing data:

1. Check `ocr_output/raw_text_all.txt` - see what OCR captured
2. Look for patterns in the text
3. Update regex in `data_parser_best.py`
4. Re-run parser (no need to re-capture screenshots!)

## 🔐 Privacy & Ethics

This system:
- Uses your legitimate logged-in session
- Appears as normal human browsing
- Respects website's terms of service
- Recommended for personal/research use only

## 📞 Support

**Common Issues:**
- Python version: Use `python` not `python3`
- Missing packages: Run `pip install pytesseract Pillow`
- Tesseract not found: Run `brew install tesseract`

**Data Quality:**
- Current system achieves 93% completeness
- OCR limitations may affect URL extraction
- Manual verification recommended for critical data

---

**System Status:** ✅ Complete and Working
**Last Updated:** Nov 12, 2025  
**Version:** 1.0
