# Ray White Robina Property Scraper

A comprehensive web scraping system for extracting all property data from Ray White Robina properties for sale.

## Features

- ✅ Scrapes all properties from Ray White Robina's for-sale listings
- ✅ Extracts complete property details including:
  - Title and address
  - Price information
  - Property type
  - Features (bedrooms, bathrooms, parking, land size, etc.)
  - Full property description
  - Agent contact information
  - **All image URLs** for each property
  - Listing ID and date
  - Inspection times
  - Additional property details
- ✅ Handles pagination automatically
- ✅ Saves all data to structured JSON format
- ✅ Comprehensive logging for monitoring and debugging
- ✅ Polite scraping with delays between requests
- ✅ Anti-detection measures (user agent, headless mode, etc.)

## Installation

### Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- pip (Python package manager)

### Setup Steps

1. **Navigate to the project directory:**
   ```bash
   cd 09_Ray_White
   ```

2. **Install required Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - selenium (web automation)
   - webdriver-manager (automatic ChromeDriver management)
   - beautifulsoup4 (HTML parsing)
   - requests (HTTP requests)
   - lxml (XML/HTML parser)
   - python-dotenv (environment variables)

## Usage

### Basic Usage

Run the scraper with default settings (headless mode):

```bash
python ray_white_scraper.py
```

### What It Does

1. **Loads the property listing page** from Ray White Robina
2. **Discovers all property URLs** by:
   - Scrolling through all pagination pages
   - Extracting links to individual property pages
3. **Visits each property page** and extracts:
   - All property details
   - All image URLs
   - Agent information
   - Inspection times
   - Any additional metadata
4. **Saves everything to JSON** with timestamp in filename

### Output

The scraper generates two files:

1. **JSON Data File**: `ray_white_properties_YYYYMMDD_HHMMSS.json`
   - Contains all scraped property data in structured format
   - Includes metadata (scrape timestamp, total count, source URL)
   - All image URLs are preserved

2. **Log File**: `ray_white_scraper_YYYYMMDD_HHMMSS.log`
   - Detailed execution log
   - Error tracking
   - Progress monitoring

### Output JSON Structure

```json
{
  "scraped_at": "2025-11-25T09:30:00.000000",
  "total_properties": 25,
  "source_url": "https://raywhiterobina.com.au/properties/...",
  "properties": [
    {
      "url": "https://raywhiterobina.com.au/property/...",
      "scraped_at": "2025-11-25T09:30:15.000000",
      "title": "Stunning Family Home in Prime Location",
      "address": "123 Main Street, Robina QLD 4226",
      "price": "$850,000",
      "property_type": "House",
      "features": {
        "bedrooms": "4 Bed",
        "bathrooms": "2 Bath",
        "parking": "2 Car",
        "land_size": "600 m²"
      },
      "description": "Full property description here...",
      "agent": {
        "name": "John Smith",
        "phone": "07 5555 5555",
        "email": "john.smith@raywhite.com"
      },
      "image_urls": [
        "https://raywhiterobina.com.au/images/property1.jpg",
        "https://raywhiterobina.com.au/images/property2.jpg",
        ...
      ],
      "listing_id": "12345",
      "date_listed": "01/11/2025",
      "inspection_times": [
        "Saturday 25 Nov 2025, 10:00am - 10:30am"
      ],
      "additional_details": {
        "Council Rates": "$2,500 per year",
        "Water Rates": "$1,200 per year"
      }
    },
    ...
  ]
}
```

## Customization

### Running in Non-Headless Mode

To see the browser in action (useful for debugging):

Edit `ray_white_scraper.py` and change:
```python
scraper = RayWhiteRobinaScraper(headless=False)
```

### Adjusting Delays

To change the delay between requests, modify the `time.sleep()` values in the code:
- Line after loading listing page: `time.sleep(3)`
- Line after processing each property: `time.sleep(2)`

### Custom Output Filename

Modify the `save_to_json()` method call:
```python
scraper.save_to_json('custom_filename.json')
```

## Troubleshooting

### ChromeDriver Issues

If you encounter ChromeDriver errors:
- Ensure Chrome browser is installed
- The script automatically downloads the correct ChromeDriver version
- Check Chrome version: `google-chrome --version` or `Chrome > About Chrome`

### No Properties Found

If the scraper returns no properties:
1. Check the listing URL is still valid
2. Run in non-headless mode to see what's happening
3. Check the log file for specific errors
4. The website structure may have changed - inspect page HTML

### Timeout Errors

If you get timeout errors:
- Increase wait times in the `WebDriverWait` calls
- Check your internet connection
- The website may be slow or temporarily unavailable

### Missing Data Fields

If certain fields are always empty:
- The website HTML structure may differ from expected selectors
- Check the page source and update the CSS selectors in the code
- Some fields may not be present on all properties

## Technical Details

### Scraping Strategy

1. **Selenium WebDriver**: Used for JavaScript-rendered content
2. **BeautifulSoup**: Used for efficient HTML parsing
3. **Multiple Selector Fallbacks**: Tries various CSS selectors for each field
4. **Pagination Handling**: Automatically clicks through all pages
5. **Image Extraction**: Captures `src`, `data-src`, and `data-lazy` attributes
6. **URL Normalization**: Converts relative URLs to absolute

### Anti-Detection Features

- Custom user agent (mimics real browser)
- Disables automation flags
- Random delays between requests
- Headless mode support
- No webdriver property exposed to JavaScript

## Maintenance

### Updating Selectors

If the Ray White website changes its HTML structure:

1. Inspect the new page structure
2. Update CSS selectors in the `extract_property_data()` method
3. Test with a small subset of properties first

### Testing Changes

Run with verbose logging to see what's being extracted:
```python
# In the script, set logging to DEBUG
logging.basicConfig(level=logging.DEBUG, ...)
```

## Data Usage

The scraped data can be used for:
- Market analysis
- Property comparison
- Price tracking
- Image collection for ML/AI training
- Real estate research
- Investment analysis

## Legal & Ethical Considerations

- Respect robots.txt and website terms of service
- Use reasonable delays between requests (implemented)
- Don't overwhelm the server with requests
- Use data responsibly and within legal bounds
- Consider reaching out to Ray White for official API access for commercial use

## Support

For issues or questions:
1. Check the log file for detailed error messages
2. Review the troubleshooting section
3. Inspect the website structure for changes
4. Ensure all dependencies are correctly installed

## Version History

- **v1.0** (2025-11-25)
  - Initial release
  - Full property data extraction
  - Image URL collection
  - JSON export
  - Comprehensive logging
  - Pagination support
