# Keyboard Maestro Integration - Quick Start Guide

## 🚀 Complete Setup in 15 Minutes

This guide will get you up and running with Keyboard Maestro for undetectable property scraping.

---

## Step 1: Install Keyboard Maestro (2 mins)

```bash
# Move app to Applications folder
cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method
mv "Keyboard Maestro.app" /Applications/

# Launch Keyboard Maestro
open /Applications/Keyboard\ Maestro.app
```

**On First Launch:**
1. Click "Start Trial" (30 days free, or enter license if you have one)
2. System will ask for **Accessibility permissions** → Click "Open System Settings"
3. Toggle ON the switch for "Keyboard Maestro Engine"
4. Return to Keyboard Maestro

✅ **Keyboard Maestro is now installed and ready!**

---

## Step 2: Install Python Dependencies (3 mins)

```bash
cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method

# Install OCR and image processing libraries
pip install pytesseract pillow opencv-python pymongo

# Install Tesseract OCR engine
brew install tesseract

# Verify installation
tesseract --version
```

---

## Step 3: Verify MongoDB is Running (1 min)

```bash
# Check if MongoDB is running
mongosh mongodb://127.0.0.1:27017/

# Should see: "Connected to MongoDB"
# Type: exit
```

If MongoDB is not running:
```bash
brew services start mongodb-community
```

---

## Step 4: Create Your First Macro (5 mins)

### In Keyboard Maestro Editor:

1. **Create Macro Group:**
   - Click "+ New Macro Group"
   - Name: "Property Scraping"
   - Click "Create"

2. **Create Macro:**
   - Click "+ New Macro"
   - Name: "Scrape Robina Properties - Session 1"
   - Click "Create"

3. **Add Recording Trigger:**
   - In the macro, click "+ New Action"
   - Search for: "Record Quick Macro"
   - Click to add

4. **Start Recording:**
   - Click "Start Recording" button
   - **Now perform these actions:**
     a. Open Safari or Chrome
     b. Go to: `https://www.realestate.com.au/sold/in-robina,+qld+4226/list-1`
     c. Scroll down slowly to see listings
     d. Click on the FIRST property
     e. **IMPORTANT:** Take a screenshot (Shift+⌘+4) of the property details
        - Save as: `robina_property_001.png` on Desktop
     f. Click browser back button
     g. Click on the SECOND property
     h. Take screenshot → Save as: `robina_property_002.png`
     i. Click browser back button
     j. Click on the THIRD property
     k. Take screenshot → Save as: `robina_property_003.png`
     l. Close the browser tab

5. **Stop Recording:**
   - **Method 1:** Press the **Stop button** in the floating recording control window
   - **Method 2:** Use keyboard shortcut: **⌘⌥R** (Command-Option-R)
   - **Method 3:** Click the Keyboard Maestro icon in the menu bar → "Stop Recording"
   - The recording will be automatically added to your macro

6. **Save Your Macro** (⌘S)

---

## Step 5: Organize Screenshots (1 min)

```bash
# Move screenshots to correct folder
cd ~/Desktop
mv robina_property_*.png /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/5_keyboard_maestro/screenshots/robina/
```

---

## Step 6: Test OCR Extraction (3 mins)

```bash
cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method

# Process the screenshots
python 5_keyboard_maestro/scripts/km_screenshot_processor.py robina
```

**Expected Output:**
```
✓ Connected to MongoDB: property_data.properties_for_sale
Found 3 screenshots to process
Processing: robina_property_001.png
✓ Successfully processed and saved: robina_property_001.png
Processing: robina_property_002.png
✓ Successfully processed and saved: robina_property_002.png
Processing: robina_property_003.png
✓ Successfully processed and saved: robina_property_003.png

=== Processing Complete ===
Successfully processed: 3
Errors: 0
Total: 3
```

---

## Step 7: Verify Data in MongoDB

```bash
# Check the data
mongosh mongodb://127.0.0.1:27017/property_data

# In MongoDB shell:
db.properties_for_sale.find().pretty()
```

You should see your 3 properties with extracted data!

---

## 🎉 You're Done! Now Automate It

### Daily Automated Scraping:

**Option 1: Keyboard Maestro Scheduled Trigger**

1. In KM Editor, select your macro
2. Click "+ New Trigger"
3. Select "Time of Day"
4. Set: "9:00 AM" daily
5. Add another action at the END of macro:
   - "Execute Shell Script"
   - Script:
   ```bash
   cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method
   python 5_keyboard_maestro/scripts/km_screenshot_processor.py robina
   ```

**Option 2: crontab (for more control)**

```bash
# Edit crontab
crontab -e

# Add this line (runs at 9 AM daily):
0 9 * * * osascript -e 'tell application "Keyboard Maestro Engine" to do script "Scrape Robina Properties - Session 1"' && cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method && python 5_keyboard_maestro/scripts/km_screenshot_processor.py robina
```

---

## 📈 Scale Up: Add More Suburbs

### For Each New Suburb:

1. **Create new macro** in KM:
   - "Scrape Mudgeeraba Properties - Session 1"
   - Record browsing mudgeeraba listings
   - Take 3 screenshots

2. **Save screenshots:**
   ```bash
   mv ~/Desktop/mudgeeraba_property_*.png /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/5_keyboard_maestro/screenshots/mudgeeraba/
   ```

3. **Process screenshots:**
   ```bash
   python 5_keyboard_maestro/scripts/km_screenshot_processor.py mudgeeraba
   ```

### Create 3 Sessions per Suburb

**Why 3 sessions?**
- Session 1: Fast browsing (morning energy)
- Session 2: Slow browsing (careful reading)
- Session 3: Mixed pace (natural variation)

Record each session at different times of day for maximum variation.

---

## 🔍 Troubleshooting

### "Permission Denied" Error

Keyboard Maestro needs accessibility permissions:
1. System Settings → Privacy & Security → Accessibility
2. Find "Keyboard Maestro Engine"
3. Toggle ON

### OCR Extraction Failing

Check screenshot quality:
```bash
# View a screenshot
open /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/5_keyboard_maestro/screenshots/robina/robina_property_001.png
```

Make sure:
- Screenshot captures property details clearly
- Text is readable
- No overlays blocking information

### MongoDB Connection Error

```bash
# Start MongoDB
brew services start mongodb-community

# Check status
brew services list | grep mongodb
```

---

## 📊 Monitoring Your Data

### Check property count:

```bash
mongosh mongodb://127.0.0.1:27017/property_data --eval "db.properties_for_sale.countDocuments({})"
```

### View recent properties:

```bash
mongosh mongodb://127.0.0.1:27017/property_data --eval "db.properties_for_sale.find().sort({scraped_at: -1}).limit(5).pretty()"
```

### Check extraction logs:

```bash
ls -lth /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/5_keyboard_maestro/logs/

# View latest log
tail -50 /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/5_keyboard_maestro/logs/processing_robina_*.log
```

---

## 🎯 Best Practices

### Recording Macros:

1. ✅ **Browse naturally** - Don't rush
2. ✅ **Vary mouse movements** - Don't be too precise
3. ✅ **Pause to "read"** - Appear human
4. ✅ **Different times of day** - Morning, afternoon, evening sessions
5. ✅ **Clear, full-screen screenshots** - Maximize OCR accuracy

### Running Macros:

1. ✅ **Once per day maximum** - Don't over-scrape
2. ✅ **Rotate sessions** - Use different recordings
3. ✅ **Monitor data quality** - Check extraction accuracy
4. ✅ **Keep KM Engine running** - Required for automation

---

## 🚀 Next Steps

1. **Create more sessions** - Record 2 more sessions for Robina
2. **Add more suburbs** - Mudgeeraba, Varsity Lakes, etc.
3. **Set up automation** - Daily scheduled runs
4. **Monitor quality** - Check extraction logs weekly
5. **Refine OCR patterns** - Improve extraction accuracy as needed

---

## 💡 Pro Tips

### For Better OCR Results:

- Take **full-screen screenshots** (cmd+shift+3) instead of selected area
- Ensure browser zoom is at **100%**
- Use **clean browser window** (no bookmarks bar clutter)
- **Wait 2-3 seconds** after page load before screenshot

### For Better Macro Reliability:

- **Always test replay** after recording
- **Add 1-2 second pauses** between actions
- **Include "Wait for" conditions** if possible
- **Use the same browser** for all sessions

---

## 📧 Support

For issues:
1. Check logs in `5_keyboard_maestro/logs/`
2. Review OCR debug files in `logs/ocr_debug/`
3. Test extraction with: `python km_ocr_extractor.py` (standalone)

**You now have a fully functional, undetectable scraping system!** 🎉
