# Quick Start Guide

Get up and running in 3 simple steps!

## Step 1: Install Dependencies

You're using conda (base environment), so install with conda:

```bash
conda install -c conda-forge selenium
```

Or if you prefer pip with your conda environment:

```bash
pip install selenium
```

Alternatively, use pip with --user flag:

```bash
pip3 install --user selenium
```

## Step 2: Start Chrome with Remote Debugging

Open a **new terminal window** and run:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**IMPORTANT:** 
- Log into your Google account in this Chrome window
- Keep this terminal window open while running the script

## Step 3: Run the Scraper

In your original terminal, run:

```bash
./run.sh
```

Or directly:

```bash
python3 simple_screenshot_scraper.py
```

## What Happens Next?

The script will:
1. Connect to your open Chrome browser ✓
2. Navigate to the realestate.com.au search page ✓
3. Scroll down from top to bottom ✓
4. Take screenshots of each section ✓
5. Save them to `screenshots/` folder ✓

## View Your Screenshots

```bash
open screenshots/
```

Screenshots will be named like:
- `section_01_20251211_194230.png`
- `section_02_20251211_194231.png`
- etc.

---

## Troubleshooting

### "Failed to connect to Chrome"
Make sure you ran Step 2 first and the Chrome window is still open.

### "No screenshots created"
The page may need more loading time. Edit `simple_screenshot_scraper.py` and increase the `time.sleep(3)` value to `time.sleep(5)` or higher.

### Change the URL
Edit the `TARGET_URL` variable at the top of `simple_screenshot_scraper.py`.

---

## Full Documentation

See [README.md](README.md) for complete documentation.
