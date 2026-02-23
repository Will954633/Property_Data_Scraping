# GPT Vision-Based Link Clicker Guide

## Overview

This approach uses OpenAI's GPT Vision API to analyze Google search results screenshots and intelligently identify the correct realestate.com.au link to click. This method solves the challenge of reliably clicking on the right search result by leveraging AI vision capabilities.

## How It Works

The workflow consists of 7 steps:

1. **Open Chrome in Maximized Window** - Opens a new Chrome window and maximizes it to ensure consistent screenshot dimensions
2. **Search for Address on Google** - Types the property address into the Chrome address bar and presses Enter
3. **Take Screenshot** - Captures a screenshot of the Google search results page
4. **Send to GPT Vision API** - Uploads the screenshot to OpenAI's GPT model for analysis
5. **Get Click Coordinates** - GPT analyzes the image and returns the pixel coordinates of the realestate.com.au link
6. **Human-Like Mouse Movement** - Moves the mouse cursor naturally to the target coordinates with curved motion
7. **Click the Link** - Clicks at the coordinates to open the realestate.com.au property page

## Key Features

### AI-Powered Link Detection
- Uses `gpt-5-nano-2025-08-07` model to analyze screenshots
- Intelligently identifies the correct realestate.com.au link based on the search address
- Provides confidence levels and reasoning for transparency

### Natural Mouse Movement
- Implements curved, human-like mouse trajectories
- Variable speed and acceleration to mimic human behavior
- Random micro-movements to avoid detection

### Flexible Address Handling
- Works with any property address (configurable via `SEARCH_ADDRESS` variable)
- Can be easily integrated into batch processing workflows
- Handles various Google search result layouts

### Production-Ready
- Comprehensive error handling
- Detailed logging and progress tracking
- Screenshots saved for debugging and verification

## Prerequisites

### 1. Python Packages
```bash
# Install OpenAI package
pip3 install --break-system-packages openai
```

### 2. cliclick for Mouse Control
```bash
# Install via Homebrew
brew install cliclick
```

### 3. OpenAI API Key
- You need a valid OpenAI API key
- The key is configured in the script: `OPENAI_API_KEY`

## Configuration

Edit the following variables in `gpt_vision_clicker.py`:

```python
# Your OpenAI API key
OPENAI_API_KEY = "REDACTED_OPENAI_KEY..."

# GPT model to use (do not change unless you have a different model)
GPT_MODEL = "gpt-5-nano-2025-08-07"

# Property address to search for
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"

# Screenshot directory
SCREENSHOT_DIR = "screenshots"

# Timing configuration
INITIAL_LOAD_DELAY = 5  # Wait time for Google page to load
CLICK_DELAY = 2  # Wait before clicking after getting coordinates
```

## Usage

### Basic Usage
```bash
# Navigate to the script directory
cd 07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/

# Run the script
python3 gpt_vision_clicker.py
```

### Expected Output
```
================================================================================
GPT VISION-BASED LINK CLICKER
REALESTATE.COM.AU LINK DETECTION AND CLICKING
================================================================================

Search Address: 279 Ron Penhaligon Way, Robina
GPT Model: gpt-5-nano-2025-08-07

Workflow:
  1. Open Chrome in maximized window
  2. Search for address on Google
  3. Take screenshot of results
  4. Send screenshot to GPT Vision API
  5. Get click coordinates from GPT
  6. Move mouse naturally to coordinates
  7. Click on the realestate.com.au link

================================================================================
✓ cliclick is installed

→ Step 1-2: Opening Chrome and searching...
✓ Opened Chrome
✓ Maximized Chrome window
✓ Typed address: 279 Ron Penhaligon Way, Robina
✓ Pressed Enter - Google search initiated
→ Waiting 5 seconds for page to load...

→ Step 3: Taking screenshot...
✓ Screenshot captured (bounds: [0, 0, 1920, 1080])

→ Step 4-5: Analyzing with GPT Vision...

✓ GPT Response received:
{
    "found": true,
    "x": 450,
    "y": 320,
    "confidence": "high",
    "reasoning": "Found realestate.com.au link for 279 Ron Penhaligon Way"
}

✓ Link found!
  Coordinates: (450, 320)
  Confidence: high
  Reasoning: Found realestate.com.au link for 279 Ron Penhaligon Way

→ Waiting 2 seconds before clicking...

→ Moving mouse to coordinates (450, 320) with human-like movement...
  Current position: (960, 540)
✓ Mouse moved to target position

→ Clicking at coordinates (450, 320)...
✓ Clicked!

→ Waiting for realestate.com.au page to load...
✓ Screenshot captured (bounds: [0, 0, 1920, 1080])

================================================================================
✅ WORKFLOW COMPLETED SUCCESSFULLY!
================================================================================

Search Address: 279 Ron Penhaligon Way, Robina
Screenshot: /Users/projects/Documents/Property_Data_Scraping/.../google_search_20251113_143210.png
After Click: /Users/projects/Documents/Property_Data_Scraping/.../after_click_20251113_143210.png
Total Time: 0:00:15.234567

The realestate.com.au page should now be loaded in Chrome.

================================================================================
```

## Integration with Batch Processing

To process multiple addresses, modify the script to accept command-line arguments:

```python
import sys

if len(sys.argv) > 1:
    SEARCH_ADDRESS = sys.argv[1]
```

Then run:
```bash
python3 gpt_vision_clicker.py "123 Example Street, Suburb"
```

## Screenshots

The script saves two screenshots:
1. **Before click**: `screenshots/google_search_YYYYMMDD_HHMMSS.png` - The Google search results
2. **After click**: `screenshots/after_click_YYYYMMDD_HHMMSS.png` - The loaded realestate.com.au page

These can be used for:
- Debugging failed clicks
- Verifying correct link detection
- Quality assurance
- Training data for improving the prompts

## Troubleshooting

### Issue: GPT Cannot Find Link
**Solution**: 
- Check if realestate.com.au results appear in Google search
- Increase `INITIAL_LOAD_DELAY` to allow more time for page loading
- Review the screenshot to see what GPT is analyzing

### Issue: Wrong Link Clicked
**Solution**:
- Improve the GPT prompt to be more specific
- Add additional validation criteria (e.g., check if URL contains the suburb name)
- Increase confidence threshold before clicking

### Issue: Mouse Moves Too Fast/Slow
**Solution**:
- Adjust the `duration` parameter in `human_like_mouse_movement()`
- Modify the `num_steps` calculation for smoother or faster movement

### Issue: API Rate Limits
**Solution**:
- Add retry logic with exponential backoff
- Implement request queuing for batch processing
- Consider caching results for repeated addresses

### Issue: Coordinates Off by Window Offset
**Solution**:
- The script automatically adjusts for window bounds
- If issues persist, verify `get_chrome_window_bounds()` is working correctly
- Consider using full-screen mode for consistency

## Advantages Over Previous Methods

### vs OCR-Based Clicking
- More context-aware (understands page layout and link relationships)
- Handles dynamic/changing layouts better
- More reliable with overlapping/similar text

### vs Color/Pixel-Based Detection
- Not dependent on specific colors or pixel patterns
- Works with different Google search UI variations
- More resilient to theme changes and updates

### vs SikuliX
- Doesn't require template images
- Works with any address without pre-configuration
- More flexible with page variations

### vs Direct Selenium Clicking
- More human-like (uses actual mouse movement)
- Harder to detect as automation
- Better mimics real user behavior

## Cost Considerations

- Each screenshot analysis requires one GPT Vision API call
- Cost depends on your OpenAI pricing tier
- For the `gpt-5-nano-2025-08-07` model, costs are minimal per request
- Consider implementing result caching for repeated searches

## Future Enhancements

1. **Multi-Site Support**: Extend to click other property sites (domain.com.au, realestate.com.au)
2. **Fallback Logic**: If GPT fails, fall back to other clicking methods
3. **A/B Testing**: Compare GPT vision accuracy vs other methods
4. **Batch Processing**: Process multiple addresses in sequence
5. **Result Validation**: Verify the correct page loaded after clicking
6. **Cost Optimization**: Cache GPT responses for similar searches

## Security Notes

- **API Key Security**: Never commit your API key to version control
- Use environment variables: `export OPENAI_API_KEY="your-key"`
- Consider using a `.env` file with proper `.gitignore` settings

## Support

If you encounter issues:
1. Check the screenshots in the `screenshots/` directory
2. Review the GPT response in the console output
3. Verify your OpenAI API key is valid and has sufficient credits
4. Ensure Chrome window is visible and not minimized during execution
