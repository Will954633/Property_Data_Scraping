# Run Single Address Test - Terminal Commands

## ⚠️ PYTHON PATH ISSUE DETECTED!

Your `python3` command uses Homebrew Python (/opt/homebrew/bin/python3.14), but your packages are installed in conda (/Users/projects/miniconda3/). You need to use conda's Python.

## Prerequisites Setup (Run Once)

### Step 1: Change to project root
```bash
cd /Users/projects/Documents/Property_Data_Scraping
```

### Step 2: Install Python dependencies in Homebrew Python (since that's what python3 uses)
```bash
/opt/homebrew/bin/python3 -m pip install pillow pytesseract openai
```

**Alternative: Use conda's Python instead**
```bash
# Packages are already installed in conda
# Just use conda's python directly (see run command below)
```

### Step 3: Install system tools (Homebrew required)
```bash
brew install tesseract
brew install cliclick
```

### Step 4: Verify installations worked
```bash
python3 -c "from PIL import Image; print('✓ PIL/Pillow installed')"
python3 -c "import pytesseract; print('✓ pytesseract installed')"
python3 -c "import openai; print('✓ openai installed')"
tesseract --version
cliclick -V
```

**If any verification fails, re-run the installation commands for that package.**

## Run the Test (Every Time)

### Option A: Use Homebrew Python (after installing packages there)
```bash
cd /Users/projects/Documents/Property_Data_Scraping
/opt/homebrew/bin/python3 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/batch_processor.py --address "5 Picabeen Close, Robina, Qld 4226"
```

### Option B: Use conda's Python (packages already installed) ⭐ RECOMMENDED
```bash
cd /Users/projects/Documents/Property_Data_Scraping
/Users/projects/miniconda3/bin/python3 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/batch_processor.py --address "5 Picabeen Close, Robina, Qld 4226"
```

### Option C: Activate conda base environment first
```bash
cd /Users/projects/Documents/Property_Data_Scraping
conda activate base
python3 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/batch_processor.py --address "5 Picabeen Close, Robina, Qld 4226"
```

## Output Locations

After successful run, check these directories:
- `batch_results/property_screenshots/*.png` - Screenshot of property page
- `batch_results/ocr/*.txt` - Raw OCR text
- `batch_results/property_data_*.json` - Parsed property data
- `batch_results/batch_report_*.json` - Batch processing report

## Troubleshooting

### ModuleNotFoundError: No module named 'PIL'
```bash
pip3 install --upgrade pillow
```

### tesseract: command not found
```bash
brew install tesseract
```

### cliclick: command not found
```bash
brew install cliclick
```

### Permission issues with AppleScript
1. Open System Settings → Privacy & Security → Accessibility
2. Add Terminal (or your shell app)
3. Open System Settings → Privacy & Security → Automation
4. Grant Terminal permission to control Google Chrome
