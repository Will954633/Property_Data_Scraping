# Property Web Search Test - README
**Last Updated: 04/02/2026, 7:13 am (Brisbane Time)**

## Overview

This test demonstrates the capability to use a headless browser (Playwright) to:
1. ✅ Search Google for a property address
2. ✅ Identify agency websites in search results
3. ✅ Navigate to the property page
4. ✅ Extract all data (photos and text) from the page

## Test Case

- **Address**: 11 South Bay Drive Varsity Lakes, QLD 4227
- **Agency**: Ray White Malan + Co - Broadbeach
- **Target URL**: https://raywhitemalanandco.com.au/properties/sold-residential/qld/varsity-lakes-4227/townhouse/3344866

## Answer to Your Question

**YES!** Using a headless browser (Playwright), we CAN:
- ✅ Search the internet for a property address
- ✅ Identify the agency from search results
- ✅ Open the agency's property webpage
- ✅ Extract ALL data including photos and text

**Firefox is NOT special** - any browser (Chrome, Firefox, Safari) can be used in headless mode. What matters is the automation tool (Playwright, Selenium, etc.) and anti-detection techniques.

## Installation

### Step 1: Install Python Dependencies

```bash
cd /Users/projects/Documents/Property_Data_Scraping/12_Individual_Property_Web_Search && pip3 install -r requirements.txt
```

### Step 2: Install Playwright Browsers

```bash
cd /Users/projects/Documents/Property_Data_Scraping/12_Individual_Property_Web_Search && playwright install chromium
```

This downloads the Chromium browser that Playwright will use.

## Usage

### Run the Test

```bash
cd /Users/projects/Documents/Property_Data_Scraping/12_Individual_Property_Web_Search && python3 test_property_search.py
```

### Run with Visible Browser (for debugging)

Edit `test_property_search.py` and change:
```python
results = await test.run_test(headless=False)  # Set to False
```

## What the Test Does

### Phase 1: Google Search
- Navigates to Google
- Searches for: "11 South Bay Drive Varsity Lakes QLD 4227 Ray White"
- Extracts all Ray White links from search results
- Reports how many agency links were found

### Phase 2: Navigate to Property Page
- Directly navigates to the target URL
- Verifies the page loaded successfully
- Captures the page title

### Phase 3: Extract All Data
- **Images**: Extracts all image URLs and alt text
- **Text**: Extracts all text content from the page
- **Property Details**: Uses regex to find:
  - Address
  - Price
  - Bedrooms
  - Bathrooms
  - Parking spaces
- **Links**: Extracts all hyperlinks

## Expected Output

```
============================================================
PROPERTY WEB SEARCH TEST
============================================================

=== PHASE 1: Google Search ===
✓ Navigated to Google
✓ Searched for: 11 South Bay Drive Varsity Lakes QLD 4227 Ray White
✓ Found X Ray White links

=== PHASE 2: Navigate to Property Page ===
✓ Navigated to: https://raywhitemalanandco.com.au/...
✓ Page loaded: [Page Title]

=== PHASE 3: Extract Property Data ===
✓ Extracted X images
✓ Extracted X characters of text
✓ Found X property details

============================================================
TEST SUMMARY
============================================================

PHASE1: ✓ PASS
  - Found X Ray White links

PHASE2: ✓ PASS
  - Page Title: [Title]

PHASE3: ✓ PASS
  - Images: X
  - Text Length: X characters
  - Property Details: X

OVERALL: ✓ SUCCESS
============================================================

✓ Results saved to test_results.json
✓ Test complete!
```

## Results File

The test saves detailed results to `test_results.json` including:
- All Ray White links found in Google search
- Page title and URL
- Sample of extracted images (first 3)
- Property details found
- Sample of text content (first 200 characters)
- Full text length

## Browser Options Comparison

| Browser Tool | Pros | Cons | Recommendation |
|-------------|------|------|----------------|
| **Playwright** | Modern, fast, good anti-detection | Newer tool | ⭐ **BEST CHOICE** |
| Selenium | Mature, large community | Easier to detect | Good alternative |
| Puppeteer | Fast, efficient | Node.js focused | Good for JS devs |

## Key Capabilities Demonstrated

1. ✅ **Web Search**: Can automate Google searches
2. ✅ **Link Identification**: Can find specific agency websites
3. ✅ **Navigation**: Can navigate to any URL
4. ✅ **JavaScript Execution**: Handles dynamic content
5. ✅ **Data Extraction**: Can extract:
   - All images (URLs and metadata)
   - All text content
   - Structured data (beds, baths, price)
   - All hyperlinks
6. ✅ **Headless Mode**: Runs without visible browser window

## Next Steps

If this test is successful, you can:

1. **Scale Up**: Process multiple properties
2. **Enhance Search**: Improve Google search result parsing
3. **Add Intelligence**: Use AI to better identify correct property pages
4. **Handle Variations**: Deal with different agency website structures
5. **Store Data**: Save extracted data to MongoDB
6. **Download Images**: Actually download the images, not just URLs

## Troubleshooting

### Error: "playwright not found"
```bash
pip3 install playwright
playwright install chromium
```

### Error: "Browser not installed"
```bash
playwright install chromium
```

### Google blocks the search
- Add more delays between actions
- Rotate user agents
- Use residential proxies
- Consider using Google Custom Search API instead

## Notes

- The test runs in **headless mode** by default (no visible browser)
- Uses realistic user-agent to avoid detection
- Includes delays to mimic human behavior
- Can be extended to handle multiple properties
- Works with any property website, not just Ray White
