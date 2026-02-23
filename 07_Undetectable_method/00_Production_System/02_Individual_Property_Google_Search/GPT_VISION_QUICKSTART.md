# GPT Vision Link Clicker - Quick Start

## What This Does

This script solves the challenge of clicking on realestate.com.au links in Google search results by using OpenAI's GPT Vision API to analyze screenshots and identify the exact coordinates to click.

## Quick Start (3 Steps)

### 1. Install Dependencies (First Time Only)
```bash
# Install OpenAI Python package
pip3 install --break-system-packages openai

# cliclick should already be installed
# If not: brew install cliclick
```

### 2. Run the Test Script
```bash
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/
./test_gpt_vision.sh
```

### 3. Watch It Work!
The script will:
- Open Chrome in a maximized window
- Search for "279 Ron Penhaligon Way, Robina" on Google
- Take a screenshot
- Send it to GPT Vision API
- Get click coordinates
- Move mouse naturally and click the realestate.com.au link

## For Different Addresses

Edit `gpt_vision_clicker.py` and change:
```python
SEARCH_ADDRESS = "YOUR ADDRESS HERE"
```

Then run:
```bash
python3 gpt_vision_clicker.py
```

## What You'll See

The script provides detailed output showing each step:
- ✓ Checkmarks for successful steps
- → Arrows for actions in progress
- Coordinate information from GPT
- Confidence levels and reasoning
- Screenshots saved in `screenshots/` directory

## Key Features

✅ **AI-Powered**: Uses GPT vision to intelligently find the right link  
✅ **Human-Like**: Natural curved mouse movement  
✅ **Flexible**: Works with any property address  
✅ **Debuggable**: Saves screenshots before and after clicking  
✅ **Production-Ready**: Full error handling and logging

## Files Created

1. **gpt_vision_clicker.py** - Main script
2. **GPT_VISION_GUIDE.md** - Detailed documentation
3. **test_gpt_vision.sh** - Quick test script
4. **screenshots/** - Auto-created directory for screenshots

## Requirements

- Python 3 with OpenAI package
- cliclick (for mouse control)
- OpenAI API key (configured in script)
- Google Chrome
- macOS

## Next Steps

After testing with the default address, you can:
1. Modify `SEARCH_ADDRESS` for different properties
2. Adjust timing parameters if needed
3. Integrate into batch processing workflows
4. Review screenshots to verify accuracy

## Need Help?

See **GPT_VISION_GUIDE.md** for:
- Detailed workflow explanation
- Configuration options
- Troubleshooting guide
- Integration examples
- Cost considerations

## API Key Security

The API key is currently hardcoded in the script. For production:
- Use environment variables: `export OPENAI_API_KEY="your-key"`
- Or use a `.env` file (add to `.gitignore`)
- Never commit API keys to version control
