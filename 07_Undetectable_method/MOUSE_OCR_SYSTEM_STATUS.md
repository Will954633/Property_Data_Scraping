# Mouse + OCR System - Current Status & Plan

## 🎯 System Overview

Building a **100% undetectable** scraping system using:
- **Mouse recording** - Records YOUR actual actions
- **Action replay** - Replays with timing variations
- **OCR extraction** - Extracts data from screenshots (no browser automation)
- **MongoDB storage** - Structured property data

---

## ✅ COMPLETED (Phase 1)

### 1. Mouse Action Recorder (`1_recorder/mouse_action_recorder.py`)
- Records all mouse movements, clicks, scrolls
- Records keyboard inputs
- Saves as timestamped JSON file
- Press ESC to stop recording

**Usage:**
```bash
python 1_recorder/mouse_action_recorder.py --suburb robina --session 1
```

### 2. Dependencies Installed
- ✅ pyautogui - Mouse automation
- ✅ pynput - Input recording
- ✅ pytesseract - OCR
- ✅ OpenCV - Image processing
- ✅ mss - Screenshot capture
- ✅ pymongo - MongoDB

### 3. MongoDB Integration (from previous build)
- ✅ mongodb_saver.py ready
- ✅ clear_collection.py ready
- ✅ Connects to local MongoDB

---

## 🚧 IN PROGRESS (Phase 2)

### Components Needed:

**1. Mouse Action Replayer** (`3_replay/mouse_action_replayer.py`)
- Load recorded actions from JSON
- Replay mouse movements/clicks with timing variations
- Take screenshots at key moments (when property pages open)
- Coordinate with OCR extractor

**2. Screenshot Manager** (`3_replay/screenshot_manager.py`)
- Capture full screen at specific moments
- Detect when on property detail page
- Save screenshots for OCR processing
- Manage screenshot file organization

**3. OCR Extractor** (`3_replay/ocr_extractor.py`)
- Use Tesseract to extract text from screenshots
- Parse property data fields:
  - Address recognition
  - Price extraction
  - Bedroom/bathroom numbers
  - Property features
- Structure data for MongoDB

**4. Property Data Assembler** (`3_replay/data_assembler.py`)
- Combine OCR results from multiple screenshots
- Validate and clean extracted data
- Format for MongoDB insertion
- Handle missing/unclear fields

---

## 📋 Complete Workflow (When Finished)

### Recording Phase (You do once per suburb):

```bash
# Install Tesseract OCR
brew install tesseract

# Record your actions
python 1_recorder/mouse_action_recorder.py --suburb robina --session 1

# YOUR ACTIONS:
# 1. Cmd+Space → type "chrome" → Enter (opens Chrome)
# 2. Click address bar
# 3. Type/paste URL
# 4. Scroll down listings page
# 5. Click property #1 → view page → scroll → press Back
# 6. Click property #2 → view page → scroll → press Back
# 7. Click property #3 → view page → scroll → press Back
# 8. Press ESC to stop
```

**Result:** `session_01_actions.json` with all your actions recorded

---

### Replay Phase (Daily automated):

```bash
# Clear MongoDB
python 3_replay/clear_collection.py

# Replay and extract
python 3_replay/mouse_action_replayer.py --suburb robina --session random

# SYSTEM DOES:
# 1. Loads recorded actions
# 2. Replays with ±15% timing variation
# 3. Takes screenshot when property page opens
# 4. OCR extracts text from screenshot
# 5. Parses data (address, price, features)
# 6. Saves to MongoDB
# 7. Repeats for all properties
```

**Result:** All properties in MongoDB

---

## 🔧 Technical Challenges & Solutions

### Challenge 1: Detecting When Property Page Opens
**Solution:** 
- Monitor screen for specific pixels/patterns unique to property pages
- Or: Take screenshot every 2 seconds, OCR for "Back to results" text
- Or: Use window title monitoring

### Challenge 2: OCR Accuracy
**Solution:**
- Preprocess images (enhance contrast, resize)
- Use multiple OCR passes with different settings
- Regex patterns to validate extracted text
- Fallback: Save screenshot for manual review if confidence low

### Challenge 3: Timing Variations
**Solution:**
- Add ±15% variation to ALL recorded timings
- Random pauses between actions (0.5-2s)
- Makes each replay unique while following same pattern

### Challenge 4: Data Structure from OCR
**Solution:**
- Use regex patterns for data fields:
  - `$XXX,XXX` or `$X.XM` for price
  - `X bed` for bedrooms
  - `X bath` for bathrooms
  - Address usually at top of page
- Zone-based extraction (top = address, left = features, etc.)

---

## 📊 Data Extraction Strategy

### Screenshot Zones:

```
Property Detail Page Layout:
┌─────────────────────────────────────┐
│ [Address Zone]          │           │ <- Top: OCR for address
│ 123 Main St, Robina QLD │  Gallery  │
├─────────────────────────┴───────────┤
│ [Price Zone]                        │ <- Left: OCR for price
│ $750,000                            │
├─────────────────────────────────────┤
│ [Features Zone]                     │ <- Left: OCR for features
│ 🛏️ 4 bed  🛁 2 bath  🚗 2 car      │
├─────────────────────────────────────┤
│ [Description Zone]                  │ <- Center: OCR for description
│ Beautiful family home...            │
└─────────────────────────────────────┘
```

### OCR Processing Pipeline:

```
Screenshot → Preprocess → OCR → Parse → Validate → MongoDB
    ↓           ↓          ↓      ↓        ↓         ↓
  PNG      Enhance    Extract  Regex  Check    Save
  file     contrast    text   patterns fields  data
```

---

## 🎬 Example Recording Session

```
TIME    ACTION              DETAILS
0.0s    [START]             Recording begins
1.2s    [KEY]               Cmd+Space (Spotlight)
1.5s    [KEY]               Type "chrome"
2.0s    [KEY]               Enter
3.5s    [CLICK]             (450, 100) - Address bar
4.0s    [KEY]               Type URL
5.5s    [KEY]               Enter
8.0s    [SCROLL]            Down 500px
10.0s   [CLICK]             (300, 400) - Property #1
12.0s   [SCREENSHOT]        Property page loaded
13.0s   [SCROLL]            View property details
15.0s   [CLICK]             Back button
17.0s   [CLICK]             (300, 600) - Property #2
19.0s   [SCREENSHOT]        Property page loaded
...
```

---

## 🚀 Next Implementation Steps

### Step 1: Build Action Replayer (~2 hours)
- Load action JSON
- Replay using PyAutoGUI
- Add timing variations
- Detect property pages
- Trigger screenshots

### Step 2: Build OCR Extraction (~1.5 hours)
- Screenshot preprocessing
- Tesseract OCR
- Text parsing with regex
- Data structuring

### Step 3: Integration & Testing (~1 hour)
- Connect replayer + OCR + MongoDB
- Test with real recording
- Verify data quality
- Handle edge cases

---

## 💡 Alternative Simpler Approach

If OCR proves challenging, we can use a **hybrid approach**:

**Recording + Manual Assist:**
1. Record mouse movements (automates navigation)
2. System takes screenshots automatically
3. YOU quickly review/edit OCR results
4. System saves to MongoDB

This gives you:
- Automated browsing (undetectable)
- Quick data verification (1-2 mins)
- High data accuracy
- Still saves significant time

---

## 🎯 Current Status Summary

**Completed:**
- ✅ Mouse action recorder
- ✅ Dependencies installed
- ✅ MongoDB integration
- ✅ Configuration files

**Next:**
- ⏳ Action replayer
- ⏳ Screenshot capture
- ⏳ OCR extraction
- ⏳ Data assembly

**Estimated completion:** 4-5 hours of development

---

## 📝 Ready to Proceed?

**You can:**

1. **Test the recorder now:**
   ```bash
   python 1_recorder/mouse_action_recorder.py --suburb robina --session 1
   # Perform your actions, press ESC when done
   ```

2. **Wait for complete system** - I'll build remaining components

**Which would you prefer?**
