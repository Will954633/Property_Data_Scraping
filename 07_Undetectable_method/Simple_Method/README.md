# Simple Screenshot Scraper

A simple Python script that connects to your existing Chrome browser (logged into Google) and automatically scrolls through a webpage while taking screenshots of each section.

## What It Does

1. Connects to your open Chrome browser (must be logged into Google)
2. Opens the realestate.com.au search page
3. Scrolls down from top to bottom
4. Takes a screenshot of each visible section
5. Saves all screenshots to a `screenshots/` folder

## How to Use

### Step 1: Start Chrome with Remote Debugging

In a terminal, run:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**IMPORTANT:** Make sure you're logged into Google in this Chrome browser before continuing.

### Step 2: Run the Script

```bash
python3 simple_screenshot_scraper.py
```

Or use the convenience script:

```bash
./run.sh
```

### Step 3: View Screenshots

Screenshots will be saved in the `screenshots/` directory with names like:
- `section_01_20251211_194230.png`
- `section_02_20251211_194231.png`
- etc.

## Features

✓ Uses your existing Chrome session (stays logged into Google)  
✓ Automatically scrolls through the entire page  
✓ Takes high-quality full-viewport screenshots  
✓ Timestamped filenames  
✓ Simple and straightforward  
✓ Leaves browser open after completion  

## Requirements

- Python 3.6+
- Selenium
- Chrome browser
- ChromeDriver (automatically managed by selenium)

Install requirements (you're using conda):
```bash
conda install -c conda-forge selenium
```

Or with pip in your conda environment:
```bash
pip install selenium
```

Or with pip --user flag:
```bash
pip3 install --user selenium
```

## Target URL

Currently configured for:
```
https://www.realestate.com.au/buy/property-house-in-robina,+qld+4226/list-1?includeSurrounding=false&activeSort=relevance&sourcePage=rea:homepage&sourceElement=suburb-select:recent%20searches%20tiles
```

You can modify the `TARGET_URL` variable in the script to change this.

## Troubleshooting

**"Failed to connect to Chrome"**
- Make sure Chrome is running with remote debugging enabled (see Step 1)
- Check that port 9222 is not already in use

**"No screenshots created"**
- Check that the URL is accessible
- Ensure you're logged into Google in the Chrome browser
- Check the console output for errors

**"Screenshots are blank"**
- The page may need more time to load
- Increase the `time.sleep(3)` value in the script
