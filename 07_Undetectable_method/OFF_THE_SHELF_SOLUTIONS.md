# Off-the-Shelf Mouse Recording & Automation Tools

## 🎯 Professional Tools for macOS

These tools are specifically designed for mouse recording and replay - likely more reliable than our custom solution.

---

## ⭐ Top Recommendations:

### 1. **Keyboard Maestro** (Best for macOS)

**What it is:**
- Professional macOS automation tool
- Records and replays mouse movements, clicks, typing
- Very popular in automation community

**Features:**
- ✅ Records exact mouse paths (not just coordinates)
- ✅ Replays with timing variations
- ✅ Can trigger on conditions
- ✅ AppleScript integration
- ✅ Very reliable
- ✅ Active community support

**How to use:**
```
1. Buy/download: https://www.keyboardmaestro.com (free trial)
2. Create new macro
3. Click "Record" → perform your actions
4. Save macro
5. Run macro daily (triggers automatically)
```

**Price:** $36 one-time purchase  
**Trial:** 30 days free

**Pros:**
- Professional, reliable
- Perfect mouse path recording
- Can wait for page elements to load
- Conditional logic (if/then)

**Cons:**
- Costs $36
- Learning curve

---

### 2. **BetterTouchTool** (Great, Cheaper)

**What it is:**
- macOS gesture and automation tool
- Can record and replay sequences

**Features:**
- ✅ Records mouse/keyboard sequences
- ✅ Trigger macros with keyboard shortcuts
- ✅ Much cheaper than Keyboard Maestro
- ✅ Screenshot capabilities

**How to use:**
```
1. Download: https://folivora.ai
2. Create "Named & Other Triggers" →"Record Shortcut Sequence"
3. Perform your actions
4. Trigger with shortcut or script
```

**Price:** $22 one-time OR $10/year  
**Trial:** 45 days free

**Pros:**
- Cheaper
- Good community
- Reliable

**Cons:**
- Slightly less features than Keyboard Maestro

---

### 3. **Automator + AppleScript** (Free, Built into macOS)

**What it is:**
- Mac's built-in automation tool

**Features:**
- ✅ Free (built into macOS)
- ✅ Can control Chrome
- ✅ Click, type, etc.

**Limitations:**
- ❌ Doesn't record mouse paths (you script coordinates manually)
- ❌ No easy recording feature

**Example Script:**
```applescript
tell application "Google Chrome"
    activate
    open location "https://realestate.com.au/..."
    delay 5
end tell

tell application "System Events"
    click at {400, 500}  -- Click property
    delay 2
    click at {100, 100}  -- Click back
end tell
```

**Pros:**
- Free
- Built-in

**Cons:**
- Manual coordinate entry
- No recording

---

### 4. **Sikuli / SikuliX** (Free, Visual Recognition)

**What it is:**
- Visual automation tool
- Clicks based on screenshots, not coordinates

**Features:**
- ✅ Free and open source
- ✅ Finds elements by image matching
- ✅ Adapts to page changes!
- ✅ Cross-platform

**How it works:**
```python
# Take screenshot of property card
# Sikuli finds and clicks it (even if position changes!)
click("property_card.png")
wait(2)
click("back_button.png")
```

**Download:** http://sikulix.com

**Pros:**
- Works with changing layouts!
- Visual recognition (not coordinates)
- Free

**Cons:**
- Java-based (slower)
- Requires screenshots of UI elements

---

### 5. **Pulover's Macro Creator** (Windows only, but via VM)

**Worth mentioning if you have Windows:**
- Visual macro recorder
- Free
- Very powerful

---

## 🏆 **My Top Recommendation:**

### **Use Keyboard Maestro**

**Why:**
1. **Professional grade** - Used by thousands for years
2. **Perfect recording** - Captures exact mouse paths
3. **Reliable replay** - Industry standard
4. **Screenshot triggers** - Can wait for page elements
5. **OCR built-in** - Has OCR capabilities
6. **30-day trial** - Test before buying

**Workflow with Keyboard Maestro:**
```
DAY 1 (Recording - 10 mins):
1. Open Keyboard Maestro
2. Create new macro: "Scrape Robina Properties"
3. Click "Record"
4. Open Chrome → Navigate → Click 3 properties
5. Stop recording
6. Save macro

DAILY (Automated - 2 mins):
1. Trigger macro (keyboard shortcut or script)
2. Macro runs your exact movements
3. KM can even extract text with built-in OCR
4. Export data or integrate with your MongoDB
```

---

## 🔧 **Alternative: Hybrid Approach**

Use Keyboard Maestro for recording/replay + Your Python for data extraction:

```bash
# Keyboard Maestro - Replay your browsing
# Takes screenshots automatically

# Your Python - Process screenshots
python extract_from_screenshots.py
# OCR → Parse → MongoDB
```

---

## 📊 **Comparison:**

| Tool | Price | Ease | Reliability | OCR | Dynamic Pages |
|------|-------|------|-------------|-----|---------------|
| **Keyboard Maestro** | $36 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐ |
| **BetterTouchTool** | $10-22 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | ⭐⭐ |
| **Sikuli** | Free | ⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐⭐ |
| **Our Custom** | Free | ⭐⭐ | ⭐⭐ | ✅ | ⭐ |
| **Automator** | Free | ⭐⭐ | ⭐⭐⭐ | ❌ | ⭐ |

---

## 🚀 **Quick Start with Keyboard Maestro:**

1. **Download trial:**
   ```
   https://www.keyboardmaestro.com/download
   ```

2. **Install and open**

3. **Create macro:**
   - New Macro → Name: "Scrape Robina"
   - Add Action → "Record Quick Macro"
   - Click Record → Do your browsing → Stop
   - Save

4. **Test:**
   - Click macro → Click "Try"
   - Should replay perfectly

5. **Automate:**
   - Trigger: "At scheduled time" → 9 AM daily
   - Or: Run from command line
   ```bash
   osascript -e 'tell application "Keyboard Maestro Engine" to do script "Scrape Robina"'
   ```

---

## 💡 **My Strong Recommendation:**

**Try Keyboard Maestro's 30-day free trial.** If it works (it likely will), it's worth the $36 for a professional, reliable solution that just works.

If you want to avoid cost, **Sikuli** is the best free alternative (visual recognition handles changing layouts).

**For your specific use case (daily property scraping), Keyboard Maestro is probably the right tool.**
