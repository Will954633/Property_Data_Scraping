# Mouse + OCR System - Quick Start Guide

## ✅ Recording Successfully Captured!

Your recording contains:
- **1,051 total actions**
- **7 clicks** (opening Chrome, clicking properties)
- **1,036 scrolls** (viewing pages)
- **6 keystrokes** (typing URL)
- **39.6 seconds** duration

This is perfect! The system can now replay these exact actions.

---

## 🚀 Quick Start - Complete Workflow

### Step 1: Install Tesseract OCR (One-time)

```bash
# Install Tesseract for OCR text extraction
brew install tesseract

# Verify installation
tesseract --version
# Should show: tesseract 5.x.x
```

---

### Step 2: Test the Replay System

```bash
cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method

# Replay your recorded actions
python 3_replay/mouse_action_replayer.py --suburb robina --session 1

# What happens:
# 1. System loads your 1,051 actions
# 2. Replays them with timing variations
# 3. Takes screenshots after each click
# 4. OCR extracts text from screenshots
# 5. Parses property data
# 6. Saves to MongoDB
```

**Expected:**
- Mouse will move and click automatically
- Screenshots saved to `4_data/screenshots/`
- Data extracted via OCR
- Properties saved to MongoDB

---

### Step 3: Verify Results

```bash
# Check screenshots were captured
ls -lh 4_data/screenshots/

# Check MongoDB for extracted data
mongosh mongodb://127.0.0.1:27017/property_data
> db.properties_for_sale.find().pretty()
> db.properties_for_sale.count()
> exit
```

---

## 📋 Complete Daily Workflow (After Testing)

Once you've verified it works, daily scraping is:

```bash
# 1. Clear database
python 3_replay/clear_collection.py

# 2. Replay your recorded session
python 3_replay/mouse_action_replayer.py --suburb robina --session 1

# 3. Data is now in MongoDB!
```

**Time:** ~40 seconds (plus screenshot processing)

---

## 🎯 System Architecture

```
YOUR RECORDING (one-time):
┌─────────────────────────────────────────┐
│ 1. Open Chrome                          │
│ 2. Navigate to realestate.com.au        │
│ 3. Scroll through property listings     │
│ 4. Click property #1 → view → back      │
│ 5. Click property #2 → view → back      │
│ 6. Click property #3 → view → back      │
│ 7. etc...                                │
└─────────────────────────────────────────┘
         ↓
    SAVED AS JSON (1,051 actions)
         ↓
┌─────────────────────────────────────────┐
│ DAILY REPLAY (automated):               │
│ - Loads JSON                             │
│ - Replays actions with ±15% timing      │
│ - Takes screenshots after each click    │
│ - OCR extracts text                     │
│ - Parses property data                  │
│ - Saves to MongoDB                      │
└─────────────────────────────────────────┘
```

---

## 🔍 OCR Data Extraction

### What Gets Extracted:

From each screenshot, OCR extracts:
- **Address** - Pattern: "XXX Street, Robina QLD 4226"
- **Price** - Pattern: "$XXX,XXX" or "$X.XM"
- **Bedrooms** - Pattern: "X bed"
- **Bathrooms** - Pattern: "X bath"
- **Parking** - Pattern: "X car"
- **Property Type** - Keywords: "house", "unit", "townhouse"

### Example OCR Output:

```
Raw OCR Text:
"123 Main Street, Robina QLD 4226
$750,000
4 bed 2 bath 2 car
Beautiful family home..."

Parsed Data:
{
  "address": "123 Main Street, Robina QLD 4226",
  "price": "$750,000",
  "bedrooms": 4,
  "bathrooms": 2,
  "parking": 2,
  "property_type": "House"
}
```

---

## ⚙️ Configuration Options

### Replay Speed

```bash
# Slower replay (better for debugging)
python 3_replay/mouse_action_replayer.py --suburb robina --session 1 --speed 0.5

# Faster replay
python 3_replay/mouse_action_replayer.py --suburb robina --session 1 --speed 2.0

# Normal speed (default)
python 3_replay/mouse_action_replayer.py --suburb robina --session 1
```

### Disable Screenshots (Testing Only)

```bash
# Just replay actions without screenshots/OCR
python 3_replay/mouse_action_replayer.py --suburb robina --session 1 --no-screenshots
```

---

## 📊 Monitoring & Debugging

### View Screenshots

```bash
# Open screenshots folder
open 4_data/screenshots/

# List all screenshots
ls -lht 4_data/screenshots/ | head -20
```

### Check OCR Quality

```bash
# View OCR text from a screenshot manually
python3 << 'EOF'
from PIL import Image
import pytesseract

img = Image.open('4_data/screenshots/robina_session_01_click_1_xxx.png')
text = pytesseract.image_to_string(img)
print(text)
EOF
```

### View MongoDB Data

```bash
mongosh mongodb://127.0.0.1:27017/property_data

# View all properties
> db.properties_for_sale.find().pretty()

# Search by suburb
> db.properties_for_sale.find({suburb: "robina"})

# Check extraction quality
> db.properties_for_sale.find({
    "address.full": {$exists: true, $ne: null},
    "price.display": {$exists: true, $ne: null}
  }).count()
```

---

## 🎬 Recording vs Replay

### Recording (You just did):
- **Duration:** 39.6 seconds
- **Actions:** 1,051 mouse/keyboard events
- **Clicks:** 7 (opening apps, clicking properties)
- **Result:** JSON file with all actions

### Replay (Automated):
- **Duration:** ~40 seconds (same as recording)
- **Variations:** ±15% timing on each action
- **Screenshots:** Taken after each click
- **OCR:** Extracts data from screenshots
- **Result:** Properties in MongoDB

---

## ⚠️ Important Notes

### Screen Resolution

**Your recording:** 1728 x 1117 pixels

**For replay to work properly:**
- Screen resolution MUST match
- If different, click coordinates will be wrong
- System will warn you if mismatch detected

### Multiple Recordings

Create 3 variations for natural behavior:

```bash
# Session 1 (fast clicking)
python 1_recorder/mouse_action_recorder.py --suburb robina --session 1

# Session 2 (slower, more scrolling)
python 1_recorder/mouse_action_recorder.py --suburb robina --session 2

# Session 3 (mixed)
python 1_recorder/mouse_action_recorder.py --suburb robina --session 3
```

Then use random selection:
```python
# Randomly picks session 1, 2, or 3
import random
session = random.randint(1, 3)
# Use this session number in replay
```

---

## 🔧 Troubleshooting

### "Tesseract not found"
```bash
brew install tesseract
```

### "Screen resolution mismatch"
- Match your screen to recording resolution (1728x1117)
- Or re-record at current resolution
- Actions will click wrong places if mismatch

### "Poor OCR quality"
- Screenshots may be blurry
- Try slower replay: `--speed 0.5`
- Or improve screenshots (take at higher DPI)

### "No data extracted"
- Check screenshots manually: `open 4_data/screenshots/`
- Verify they show property pages
- Check OCR text quality
- May need to refine regex patterns

---

## 📝 Next Steps

1. **Install Tesseract:**
   ```bash
   brew install tesseract
   ```

2. **Test Replay:**
   ```bash
   python 3_replay/mouse_action_replayer.py --suburb robina --session 1
   ```

3. **Check Results:**
   - Screenshots in `4_data/screenshots/`
   - Data in MongoDB

4. **Refine if needed:**
   - Adjust OCR parsing patterns
   - Add more data fields
   - Improve screenshot timing

---

## 🎉 Success Metrics

**Recording:** ✅ 1,051 actions captured  
**Replay:** ⏳ Test now  
**OCR:** ⏳ Test now  
**MongoDB:** ✅ Working  

**You're almost there!** Just need to test the replay + OCR extraction.
