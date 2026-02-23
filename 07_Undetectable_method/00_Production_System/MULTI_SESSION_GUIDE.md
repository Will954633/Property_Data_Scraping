# Multi-Session Property Scraper Guide

## Overview

This guide covers the **multi-session property scraping system** that allows you to scrape multiple URLs from realestate.com.au simultaneously using separate browser sessions with variable time delays.

## What's New

The system has been updated to support:

✅ **Multiple URLs** - Process up to 3 different property listing pages  
✅ **Separate Browser Sessions** - Each URL opens in its own session  
✅ **Variable Time Delays** - Configurable delays between sessions (5s, 8s, 6s)  
✅ **Parallel Processing** - All sessions run autonomously  
✅ **Organized Output** - Separate directories for each session  
✅ **100% Undetectable** - Uses native macOS tools like the original system

## System Architecture

```
[Multi-Session Runner]
    ↓ Session 1 (list-1) → screenshots_session_1/ → ocr_output_session_1/
    ↓ 5 second delay
    ↓ Session 2 (list-2) → screenshots_session_2/ → ocr_output_session_2/
    ↓ 8 second delay
    ↓ Session 3 (list-3) → screenshots_session_3/ → ocr_output_session_3/
    ↓ 6 second delay
    ↓ Complete
```

## Current Configuration

### URLs Being Scraped

The system is currently configured to scrape these 3 URLs:

1. **List Page 1**: `https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-1?includeSurrounding=false&activeSort=relevance`

2. **List Page 2**: `https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-2?includeSurrounding=false&activeSort=relevance`

3. **List Page 3**: `https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-3?includeSurrounding=false&activeSort=relevance`

### Time Delays Between Sessions

- **After Session 1**: 5 seconds wait before Session 2
- **After Session 2**: 8 seconds wait before Session 3
- **After Session 3**: 6 seconds wait (final delay)

These delays help make the scraping appear more natural and human-like.

## Quick Start

### Option 1: Run Complete Pipeline (Recommended)

Run everything with one command:

```bash
cd 07_Undetectable_method/Simple_Method
./process_all_sessions.sh
```

This will:
1. Capture screenshots for all 3 URLs
2. Extract text using OCR for each session
3. Provide instructions for parsing property data

**Total time**: ~7-8 minutes for all 3 sessions

### Option 2: Manual Step-by-Step

If you prefer more control:

```bash
cd 07_Undetectable_method/Simple_Method

# Step 1: Capture screenshots for all sessions
python multi_session_runner.py

# Step 2: Extract text for each session
python ocr_extractor_multi.py --session 1
python ocr_extractor_multi.py --session 2
python ocr_extractor_multi.py --session 3

# Step 3: Parse property data (you would need to adapt data_parser_best.py)
# See "Data Parsing" section below
```

## File Structure

After running the multi-session scraper, you'll have:

```
07_Undetectable_method/Simple_Method/
├── multi_session_runner.py           # Main multi-session script
├── ocr_extractor_multi.py            # OCR extractor with session support
├── process_all_sessions.sh           # Complete pipeline script
├── screenshots_session_1/            # Session 1 screenshots
│   ├── section_01_*.png
│   ├── section_02_*.png
│   └── ... (25 screenshots)
├── screenshots_session_2/            # Session 2 screenshots
│   └── ... (25 screenshots)
├── screenshots_session_3/            # Session 3 screenshots
│   └── ... (25 screenshots)
├── ocr_output_session_1/             # Session 1 OCR results
│   ├── raw_text_all.txt
│   ├── ocr_data.json
│   └── section_*.txt
├── ocr_output_session_2/             # Session 2 OCR results
│   └── ...
└── ocr_output_session_3/             # Session 3 OCR results
    └── ...
```

## Detailed Usage

### 1. Multi-Session Screenshot Capture

**Script**: `multi_session_runner.py`

**What it does**:
- Opens each URL in a separate Chrome browser session
- Takes 25 screenshots per session while scrolling
- Automatically closes each tab after completion
- Adds variable time delays between sessions
- Saves screenshots to separate directories

**Run**:
```bash
python multi_session_runner.py
```

**Expected output**:
```
======================================================================
MULTI-SESSION PROPERTY SCRAPER
FULLY AUTONOMOUS & UNDETECTABLE
======================================================================

Configuration:
  • Total sessions: 3
  • Screenshots per session: 25
  • Delays between sessions: [5, 8, 6] seconds

======================================================================
SESSION 1: STARTING
URL: https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-1...
======================================================================

→ Opening URL in Chrome...
→ Activating Chrome window...
→ Scrolling to top of page...
→ Taking 25 screenshots while scrolling down...
  📸 Screenshot 1/25: section_01_*.png
  ...

✅ SESSION 1 COMPLETED!
Screenshots saved: 25

⏳ Waiting 5 seconds before next session...

[Repeats for Session 2 and 3]

🎉 ALL SESSIONS COMPLETED SUCCESSFULLY!
```

**Duration**: ~6-7 minutes total
- Session 1: ~120 seconds
- 5 second delay
- Session 2: ~120 seconds
- 8 second delay
- Session 3: ~120 seconds
- 6 second delay

### 2. OCR Text Extraction

**Script**: `ocr_extractor_multi.py`

**What it does**:
- Processes screenshots from a specific session directory
- Extracts text using Tesseract OCR
- Saves results to session-specific output directory

**Run for each session**:
```bash
python ocr_extractor_multi.py --session 1
python ocr_extractor_multi.py --session 2
python ocr_extractor_multi.py --session 3
```

**Or process custom directories**:
```bash
python ocr_extractor_multi.py --screenshot-dir screenshots_session_1 --output-dir ocr_output_session_1
```

**Expected output per session**:
```
======================================================================
OCR TEXT EXTRACTOR
======================================================================
Screenshot directory: screenshots_session_1
Output directory: ocr_output_session_1

→ Found 25 screenshots
→ Extracting text using Tesseract OCR...

  [1/25] Processing section_01_*.png...
  ...

✅ OCR EXTRACTION COMPLETE
Screenshots processed: 25
Total characters extracted: 45,000+

Output files:
  • Combined text: ocr_output_session_1/raw_text_all.txt
  • JSON data: ocr_output_session_1/ocr_data.json
  • Individual text files: ocr_output_session_1/section_*.txt
```

**Duration**: ~30 seconds per session

### 3. Data Parsing

Currently, `data_parser_best.py` expects specific file paths. You have two options:

#### Option A: Parse Each Session Manually

Copy the parser and modify for each session:

```bash
# Create session-specific parsers
cp data_parser_best.py data_parser_session_1.py
cp data_parser_best.py data_parser_session_2.py
cp data_parser_best.py data_parser_session_3.py
```

Then edit each to use the correct input/output paths:

```python
# In data_parser_session_1.py
INPUT_FILE = "ocr_output_session_1/raw_text_all.txt"
OUTPUT_FILE = "property_data_session_1.json"
```

#### Option B: Use sed to Process in Place

```bash
# Quick way to process each session
sed 's|ocr_output|ocr_output_session_1|g' data_parser_best.py > temp_parser.py
sed -i '' 's|property_data_best.json|property_data_session_1.json|g' temp_parser.py
python temp_parser.py

# Repeat for session 2 and 3
```

## Customization

### Change URLs

Edit `multi_session_runner.py`:

```python
# Line 13-17
URLS = [
    "https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-1?includeSurrounding=false&activeSort=relevance",
    "https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-2?includeSurrounding=false&activeSort=relevance",
    "https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-3?includeSurrounding=false&activeSort=relevance"
]
```

**Examples of different configurations**:

```python
# Different suburbs
URLS = [
    "https://www.realestate.com.au/buy/in-robina,+qld+4226/list-1",
    "https://www.realestate.com.au/buy/in-burleigh-heads,+qld+4220/list-1",
    "https://www.realestate.com.au/buy/in-mudgeeraba,+qld+4213/list-1"
]

# Same suburb, more pages
URLS = [
    "https://www.realestate.com.au/buy/in-robina,+qld+4226/list-1",
    "https://www.realestate.com.au/buy/in-robina,+qld+4226/list-2",
    "https://www.realestate.com.au/buy/in-robina,+qld+4226/list-3",
    "https://www.realestate.com.au/buy/in-robina,+qld+4226/list-4"
]

# Sold properties
URLS = [
    "https://www.realestate.com.au/sold/in-robina,+qld+4226/list-1",
    "https://www.realestate.com.au/sold/in-robina,+qld+4226/list-2",
    "https://www.realestate.com.au/sold/in-robina,+qld+4226/list-3"
]
```

### Modify Time Delays

Edit `multi_session_runner.py`:

```python
# Line 20
SESSION_DELAYS = [5, 8, 6]  # After session 1, 2, 3 (in seconds)
```

**Recommendations**:
- Minimum: 3 seconds (too fast may seem robotic)
- Recommended: 5-10 seconds (natural browsing)
- Conservative: 15-30 seconds (very cautious)

**Examples**:

```python
# Quick processing
SESSION_DELAYS = [3, 3, 3]

# Natural browsing
SESSION_DELAYS = [7, 5, 9]

# Very conservative
SESSION_DELAYS = [20, 25, 18]
```

### Add More Sessions

To scrape more than 3 URLs:

```python
# In multi_session_runner.py
URLS = [
    "url1",
    "url2",
    "url3",
    "url4",  # Add more URLs
    "url5"
]

# Update delays (one per session)
SESSION_DELAYS = [5, 8, 6, 7, 5]
```

### Adjust Screenshots Per Session

Edit `multi_session_runner.py`:

```python
# Line 23
NUM_SCROLLS = 25  # Increase for longer pages
```

**Guidelines**:
- 15-20 scrolls: Short pages (~15-20 properties)
- 25-30 scrolls: Medium pages (~25-35 properties)
- 35-40 scrolls: Long pages (40+ properties)

## Advantages Over Single Session

### Benefits

1. **More Coverage**: Capture multiple pages in one run
2. **Time Efficient**: All sessions run back-to-back automatically
3. **Natural Delays**: Variable waits between sessions appear human-like
4. **Organized Output**: Separate directories prevent data mixing
5. **Parallel Analysis**: Process each session's data independently
6. **Scalable**: Easy to add more URLs or suburbs

### Use Cases

**Scenario 1: Multiple List Pages**
```python
# Scrape pages 1-3 of Robina houses
URLS = ["list-1", "list-2", "list-3"]
```

**Scenario 2: Multiple Suburbs**
```python
# Compare properties across suburbs
URLS = [
    "robina,+qld+4226",
    "burleigh-heads,+qld+4220",
    "mudgeeraba,+qld+4213"
]
```

**Scenario 3: Buy vs Sold**
```python
# Analyze current vs sold properties
URLS = [
    "/buy/in-robina",
    "/sold/in-robina"
]
```

## Troubleshooting

### Issue: Sessions Not Completing

**Symptoms**: Script stops after Session 1 or 2

**Solutions**:
1. Check if Chrome window is being blocked
2. Ensure no other programs are interfering
3. Increase `INITIAL_LOAD_DELAY` if pages load slowly
4. Check internet connection

### Issue: Wrong Number of Screenshots

**Symptoms**: Less than 25 screenshots per session

**Solutions**:
1. Verify Chrome window is maximized
2. Check if page has enough content for 25 scrolls
3. Adjust `NUM_SCROLLS` based on page length
4. Ensure `SCROLL_DELAY` allows page to render

### Issue: OCR Extraction Fails

**Symptoms**: "No screenshots found" error

**Solutions**:
```bash
# Check if screenshots exist
ls -la screenshots_session_1/
ls -la screenshots_session_2/
ls -la screenshots_session_3/

# Verify screenshot directory structure
python ocr_extractor_multi.py --screenshot-dir screenshots_session_1 --output-dir ocr_output_session_1
```

### Issue: Mixed Up Session Data

**Symptoms**: Wrong data in wrong session

**Prevention**:
- Always use session-specific directories
- Don't run multiple sessions manually - use `multi_session_runner.py`
- Clean up old session directories between runs

```bash
# Clean all session directories
rm -rf screenshots_session_*
rm -rf ocr_output_session_*
```

## Performance Metrics

### Single Session (Original System)
- Duration: ~2 minutes
- URLs processed: 1
- Total screenshots: 25
- Properties captured: ~20-30

### Multi-Session System (3 URLs)
- Duration: ~7-8 minutes
- URLs processed: 3
- Total screenshots: 75 (25 × 3)
- Properties captured: ~60-90
- Overhead: Variable delays (19 seconds total)

### Time Breakdown
```
Session 1 screenshots:  ~120 seconds
Delay 1:                   5 seconds
Session 2 screenshots:  ~120 seconds
Delay 2:                   8 seconds
Session 3 screenshots:  ~120 seconds
Delay 3:                   6 seconds
Total:                  ~379 seconds (6m 19s)

OCR Session 1:          ~30 seconds
OCR Session 2:          ~30 seconds
OCR Session 3:          ~30 seconds
Total OCR:              ~90 seconds

Grand Total:            ~469 seconds (7m 49s)
```

## Best Practices

### Before Running

1. ✅ Close unnecessary Chrome tabs
2. ✅ Maximize Chrome window
3. ✅ Ensure stable internet connection
4. ✅ Check available disk space (need ~50MB per session)
5. ✅ Verify Tesseract is installed: `tesseract --version`

### During Execution

1. ✅ Don't use computer (let it run autonomously)
2. ✅ Don't manually interact with Chrome
3. ✅ Don't close terminal window
4. ✅ Let each session complete fully

### After Completion

1. ✅ Verify all screenshot directories have 25 files each
2. ✅ Check OCR output for reasonable character counts
3. ✅ Review a few screenshots manually for quality
4. ✅ Archive completed sessions before next run

## Data Management

### Archiving Sessions

```bash
# Create archive directory
mkdir -p archive/$(date +%Y%m%d_%H%M%S)

# Move session data to archive
mv screenshots_session_* archive/$(date +%Y%m%d_%H%M%S)/
mv ocr_output_session_* archive/$(date +%Y%m%d_%H%M%S)/
mv property_data_session_*.json archive/$(date +%Y%m%d_%H%M%S)/
```

### Automated Archiving Script

```bash
#!/bin/bash
# archive_sessions.sh

ARCHIVE_DIR="archive/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

# Archive all session data
for i in 1 2 3; do
    if [ -d "screenshots_session_$i" ]; then
        mv "screenshots_session_$i" "$ARCHIVE_DIR/"
    fi
    if [ -d "ocr_output_session_$i" ]; then
        mv "ocr_output_session_$i" "$ARCHIVE_DIR/"
    fi
    if [ -f "property_data_session_$i.json" ]; then
        mv "property_data_session_$i.json" "$ARCHIVE_DIR/"
    fi
done

echo "✓ Archived to: $ARCHIVE_DIR"
```

### Combining Session Data

To merge property data from all sessions:

```python
# combine_sessions.py
import json
from datetime import datetime

combined_data = {
    "extraction_date": datetime.now().isoformat(),
    "source": "Multi-session scrape",
    "total_sessions": 3,
    "total_properties": 0,
    "properties": [],
    "sessions": []
}

for i in range(1, 4):
    with open(f'property_data_session_{i}.json') as f:
        session_data = json.load(f)
        
    combined_data["sessions"].append({
        "session": i,
        "url": session_data.get("search_url"),
        "count": session_data.get("total_properties", 0)
    })
    
    combined_data["properties"].extend(session_data.get("properties", []))

combined_data["total_properties"] = len(combined_data["properties"])

with open('property_data_combined.json', 'w') as f:
    json.dump(combined_data, f, indent=2, ensure_ascii=False)

print(f"✓ Combined {combined_data['total_properties']} properties from 3 sessions")
```

## Security & Ethics

### Same Guidelines Apply

⚠️ **Terms of Service**: Check website's ToS  
⚠️ **Rate Limiting**: Don't run too frequently  
⚠️ **Personal Use**: For research/analysis only  
⚠️ **Data Privacy**: Don't share/sell scraped data  
⚠️ **Respectful Use**: Minimize server load  

### Multi-Session Considerations

- Variable delays help distribute load over time
- Separate browser sessions appear as different users
- Still maintains undetectable characteristics
- Total scraping time is reasonable (~8 minutes)

## FAQ

**Q: Can I run more than 3 sessions?**  
A: Yes! Just add more URLs to the `URLS` list and corresponding delays to `SESSION_DELAYS`.

**Q: Do I need to wait for OCR before starting another scrape?**  
A: No, but it's recommended to archive previous data first.

**Q: Can sessions run truly in parallel?**  
A: No, they run sequentially with delays. True parallel would require multiple Chrome instances.

**Q: What if one session fails?**  
A: The script will continue with remaining sessions. Check the failed session's directory for issues.

**Q: Can I customize delays based on session?**  
A: Yes! Edit `SESSION_DELAYS` array with different values for each session.

**Q: How do I add a 4th or 5th URL?**  
A: Add to `URLS` list and add corresponding delay to `SESSION_DELAYS` array.

## Summary

The multi-session scraper provides:

✅ **Efficiency**: 3× coverage in 4× time (not 3× time due to delays)  
✅ **Organization**: Clean separation of session data  
✅ **Flexibility**: Easy to customize URLs and delays  
✅ **Reliability**: Same proven undetectable technology  
✅ **Scalability**: Add more sessions as needed  

Perfect for comprehensive property data collection across multiple pages or suburbs!

---

## Next Steps

1. **Run your first multi-session scrape**:
   ```bash
   cd 07_Undetectable_method/Simple_Method
   python multi_session_runner.py
   ```

2. **Process the OCR data**:
   ```bash
   python ocr_extractor_multi.py --session 1
   python ocr_extractor_multi.py --session 2
   python ocr_extractor_multi.py --session 3
   ```

3. **Parse and analyze the property data**

4. **Combine results from all sessions**

5. **Archive completed runs for future reference**

---

For detailed information about the core scraping technology, see the main [README.md](README.md).
