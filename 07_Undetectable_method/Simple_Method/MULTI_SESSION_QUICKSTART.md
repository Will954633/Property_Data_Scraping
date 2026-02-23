# Multi-Session Scraper - Quick Reference

## 🚀 Quick Start (3 URLs)

### Run Everything at Once
```bash
cd 07_Undetectable_method/Simple_Method
./process_all_sessions.sh
```

### Or Run Step by Step
```bash
# Step 1: Capture screenshots for all 3 URLs
python multi_session_runner.py

# Step 2: Extract OCR text for each session
python ocr_extractor_multi.py --session 1
python ocr_extractor_multi.py --session 2
python ocr_extractor_multi.py --session 3
```

## 📋 Current Configuration

**3 URLs being scraped:**
1. list-1: https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-1?includeSurrounding=false&activeSort=relevance
2. list-2: https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-2?includeSurrounding=false&activeSort=relevance
3. list-3: https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-3?includeSurrounding=false&activeSort=relevance

**Time delays:**
- After Session 1: 5 seconds
- After Session 2: 8 seconds
- After Session 3: 6 seconds

## 📁 Output Structure

```
screenshots_session_1/     → ocr_output_session_1/
screenshots_session_2/     → ocr_output_session_2/
screenshots_session_3/     → ocr_output_session_3/
```

## ⏱️ Expected Duration
- Total runtime: ~7-8 minutes for all 3 sessions
- Screenshot capture: ~6-7 minutes
- OCR extraction: ~90 seconds

## 🔧 Customization

### Change URLs
Edit `multi_session_runner.py` line 13-17:
```python
URLS = [
    "your-url-1",
    "your-url-2",
    "your-url-3"
]
```

### Modify Delays
Edit `multi_session_runner.py` line 20:
```python
SESSION_DELAYS = [5, 8, 6]  # seconds
```

### Add More Sessions
```python
URLS = ["url1", "url2", "url3", "url4"]
SESSION_DELAYS = [5, 8, 6, 7]
```

## 📖 Full Documentation

See [MULTI_SESSION_GUIDE.md](../00_Production_System/MULTI_SESSION_GUIDE.md) for complete documentation.

## ✅ What's Different from Single Session?

| Feature | Single Session | Multi-Session |
|---------|---------------|---------------|
| URLs processed | 1 | 3 (or more) |
| Browser sessions | 1 | 3 separate |
| Time delays | None | Variable (5s, 8s, 6s) |
| Output directories | screenshots/, ocr_output/ | screenshots_session_N/, ocr_output_session_N/ |
| Total time | ~2 minutes | ~7-8 minutes |
| Properties captured | ~20-30 | ~60-90 |

## 🎯 Key Benefits

✅ Process multiple pages automatically  
✅ Natural time delays between sessions  
✅ Organized output in separate directories  
✅ Same undetectable technology  
✅ Easy to scale to more URLs
