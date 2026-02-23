# Session Recording Instructions

## 🎯 Overview

You'll create 6 recordings total:
- 3 for Robina
- 3 for Mudgeeraba

Each recording captures you manually browsing and clicking 3 properties.

---

## 📋 Step-by-Step Guide

### Before You Start

1. **Close ALL Chrome windows** (important for clean recording)

2. **Verify MongoDB is running**:
   ```bash
   mongosh mongodb://127.0.0.1:27017/
   # Should connect successfully
   ```

3. **Install dependencies** (if not done yet):
   ```bash
   cd 07_Undetectable_method
   pip install -r requirements.txt
   playwright install chromium
   ```

---

## 🎬 Recording Process

### Session 1 - Robina (Fast Browsing)

```bash
python 1_recorder/session_recorder.py --suburb robina --session 1
```

**What to do:**
1. Browser opens at realestate.com.au/buy/in-robina
2. Scroll down the listings page (5-10 seconds)
3. Click on **Property #1** → view the page → click back button
4. Click on **Property #2** → view the page → click back button
5. Click on **Property #3** → view the page
6. **Close the browser** (this saves the recording)

**Timing:** 2-3 minutes total (fast pace)

---

### Session 2 - Robina (Slow/Careful Browsing)

```bash
python 1_recorder/session_recorder.py --suburb robina --session 2
```

**What to do:**
1. Browser opens at realestate.com.au/buy/in-robina
2. Scroll slowly through listings (15-20 seconds)
3. Scroll back up to look at earlier properties
4. Click on **Property #1** → scroll through images → read description → back
5. Click on **Property #2** → view details carefully → back
6. Scroll more listings
7. Click on **Property #3** → view details
8. **Close the browser**

**Timing:** 4-5 minutes total (slow, careful pace)

---

### Session 3 - Robina (Mixed Pace)

```bash
python 1_recorder/session_recorder.py --suburb robina --session 3
```

**What to do:**
1. Browser opens at realestate.com.au/buy/in-robina
2. Quick scroll through listings
3. Click on **Property #1** → quick view → back
4. Scroll more (pause to "read")
5. Click on **Property #2** → thorough view → back
6. Click on **Property #3** → medium viewing time
7. **Close the browser**

**Timing:** 3-4 minutes total (varied pace)

---

### Session 4 - Mudgeeraba (Fast Browsing)

```bash
python 1_recorder/session_recorder.py --suburb mudgeeraba --session 1
```

**What to do:** Same as Robina Session 1, but for Mudgeeraba
- Fast browsing
- Click 3 properties
- 2-3 minutes total

---

### Session 5 - Mudgeeraba (Slow Browsing)

```bash
python 1_recorder/session_recorder.py --suburb mudgeeraba --session 2
```

**What to do:** Same as Robina Session 2, but for Mudgeeraba
- Slow, careful browsing
- Click 3 properties
- 4-5 minutes total

---

### Session 6 - Mudgeeraba (Mixed Pace)

```bash
python 1_recorder/session_recorder.py --suburb mudgeeraba --session 3
```

**What to do:** Same as Robina Session 3, but for Mudgeeraba
- Mixed pace
- Click 3 properties
- 3-4 minutes total

---

## ✅ Best Practices

### DO:
- ✅ Browse naturally (like you normally would)
- ✅ Scroll up and down occasionally
- ✅ Hover over property cards
- ✅ Click images to view property galleries
- ✅ Read descriptions (or appear to)
- ✅ Use the browser back button to return to listings
- ✅ Take your time (no rush)
- ✅ Vary your behavior across sessions

### DON'T:
- ❌ Rush through mechanically
- ❌ Click properties too quickly
- ❌ Use keyboard shortcuts excessively
- ❌ Navigate away from realestate.com.au
- ❌ Open multiple tabs
- ❌ Close browser with Cmd+Q (use the X button)

---

## 📝 What Gets Recorded

The Playwright trace captures:
- Every mouse movement
- Every scroll position and speed
- Every click and where you clicked
- Exact timing between actions
- Page snapshots at each step
- Network requests
- Screenshots

**This creates a perfect replay of your browsing!**

---

## 🎯 Property Selection Strategy

### Which Properties to Click?

**Random is best!** Don't always click properties 1, 2, 3.

**Examples:**
- Session 1: Click properties 2, 5, 7
- Session 2: Click properties 1, 3, 8
- Session 3: Click properties 4, 6, 9

**Why?** This makes your sessions look more natural and varied.

---

## 🔍 What to Look for on Property Pages

When viewing a property, make sure the page shows:
- ✅ Property address
- ✅ Price
- ✅ Bedrooms, bathrooms, parking
- ✅ Property description
- ✅ Images/gallery
- ✅ Agent information

(The replay engine will extract this data automatically)

---

## 💾 Verifying Your Recordings

After each recording:

```bash
# Check the file was created
ls -lh 2_recordings/robina/
# Should show: session_01.zip, session_02.zip, etc.

# Check metadata
cat 2_recordings/metadata.json
```

**Expected output:**
```json
{
  "robina": {
    "session_01": {
      "recorded_at": "2025-12-11T11:50:00",
      "file": "session_01.zip",
      "file_size_mb": 15.3,
      "suburb_url": "https://www.realestate.com.au/buy/in-robina..."
    }
  }
}
```

---

## ⚠️ Troubleshooting

### "Browser doesn't open"
```bash
# Reinstall Playwright browsers
playwright install chromium
```

### "Chrome is already running"
- Close ALL Chrome windows first
- Or: quit Chrome completely (Cmd+Q on Mac)
- Try recording again

### "Recording file not saved"
- Make sure you closed the browser properly
- Check `logs/execution.log` for errors
- Recording only saves when browser closes

### "Can't find suburb in config"
- Check spelling: `robina` not `Robina`
- Verify suburb is in `config.yaml`
- Available: robina, mudgeeraba

---

## 📊 Progress Tracking

Keep track of your recordings:

```
✅ Robina Session 1 (Fast)
✅ Robina Session 2 (Slow)
✅ Robina Session 3 (Mixed)
✅ Mudgeeraba Session 1 (Fast)
✅ Mudgeeraba Session 2 (Slow)
✅ Mudgeeraba Session 3 (Mixed)
```

**Total time:** ~20-30 minutes

---

## 🚀 After Recording

Once all 6 sessions are recorded:

1. **Test one replay:**
   ```bash
   python 3_replay/test_replay.py --suburb robina --session 1
   ```

2. **Verify data extraction:**
   ```bash
   mongosh mongodb://127.0.0.1:27017/property_data
   > db.properties_for_sale.find().pretty()
   ```

3. **If test succeeds, run all replays:**
   ```bash
   python 3_replay/replay_engine.py --suburb robina --session random
   python 3_replay/replay_engine.py --suburb mudgeeraba --session random
   ```

---

## 💡 Tips for Natural Recordings

### Vary Your Behavior

**Session 1 (Fast):**
- Quick scrolls
- Brief property views
- Minimal reading time

**Session 2 (Slow):**
- Slow scrolls with pauses
- Thorough property viewing
- Read descriptions fully
- View all images

**Session 3 (Mixed):**
- Alternate fast/slow
- Random pauses
- Sometimes scroll back up
- Hover over elements

### Natural Mouse Movements

- Don't move in straight lines
- Overshoot and correct occasionally
- Hover over elements while "thinking"
- Move mouse while scrolling

### Realistic Timing

- Pause to "read" text (3-5 seconds)
- Wait before clicking (1-2 seconds)
- Scroll at varying speeds
- Take breaks between properties

---

## 🎬 Example Recording Session

**Session: Robina #1 (Fast)**

```
0:00 - Browser opens
0:03 - Quick scroll down
0:08 - Click property #2
0:10 - View headline + price
0:12 - Click back
0:14 - Scroll more
0:16 - Click property #5
0:18 - Quick view
0:20 - Click back
0:22 - Click property #7
0:25 - View property
0:27 - Close browser
✅ Recording saved!
```

**Total:** ~30 seconds of actual data collection

**With natural browsing:** 2-3 minutes total

---

## 📁 File Organization

After all recordings:

```
2_recordings/
├── robina/
│   ├── session_01.zip (15.3 MB)
│   ├── session_02.zip (22.1 MB)
│   └── session_03.zip (18.7 MB)
├── mudgeeraba/
│   ├── session_01.zip (14.8 MB)
│   ├── session_02.zip (21.5 MB)
│   └── session_03.zip (19.2 MB)
└── metadata.json
```

---

## ⏱️ Time Estimate

- **Per recording:** 3-5 minutes
- **Total recordings:** 6
- **Total time:** 20-30 minutes

**Plus:**
- Setup: 5 minutes
- Testing: 5 minutes
- **Grand total:** ~40 minutes one-time work

---

## ✅ Checklist

Before starting:
- [ ] MongoDB is running
- [ ] Dependencies installed
- [ ] All Chrome windows closed
- [ ] In correct directory: `07_Undetectable_method/`

For each session:
- [ ] Run recorder command
- [ ] Browser opens successfully
- [ ] Browse naturally for 2-5 minutes
- [ ] Click exactly 3 properties
- [ ] View each property page fully
- [ ] Close browser properly
- [ ] Recording file created (check ls)

After all recordings:
- [ ] All 6 .zip files exist
- [ ] metadata.json is complete
- [ ] Test replay one session
- [ ] Verify data in MongoDB

---

## 🆘 Need Help?

**Check logs:**
```bash
cat logs/execution.log
```

**Verify recordings:**
```bash
ls -lh 2_recordings/robina/
ls -lh 2_recordings/mudgeeraba/
```

**Check metadata:**
```bash
cat 2_recordings/metadata.json
```

---

## 🎉 You're Done!

Once all 6 recordings are complete:
- ✅ You have a library of browsing sessions
- ✅ Each session is unique
- ✅ Ready for automated replay
- ✅ Data extraction can begin!

**Next:** Test replay and data extraction!
