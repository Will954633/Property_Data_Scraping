# Harcourts Scraper - Usage Guide

## Quick Start

### 1. Test the Scraper (2 properties)

```bash
cd 10_Harcourts
python3 quick_test.py
```

This will:
- Scrape 2 properties from Robina listings
- Save results to `test_output.csv` and `test_output.json`
- Display a summary in the terminal

### 2. Run Full Scraper (10 properties)

```bash
python3 harcourts_scraper.py
```

This will:
- Scrape 10 properties from Robina listings
- Save to `harcourts_properties.csv` and `harcourts_properties.json`

## Custom Scraping

### Scrape Different Locations

Edit the search URL in `harcourts_scraper.py` or create your own script:

```python
from harcourts_scraper import HarcourtsPropertyScraper

scraper = HarcourtsPropertyScraper(headless=True)

# Example: Burleigh Heads
search_url = "https://propertyhub.harcourts.com.au/property-hub/listings/buy/?property-type=House&location=Burleigh-Heads-4220&include-suburb=1&category=buy&listing-category=residential"

properties = scraper.scrape_listings(search_url, max_properties=20)
scraper.save_to_json(properties, 'burleigh_properties.json')
```

### Scrape All Available Properties

```python
# Remove max_properties limit
properties = scraper.scrape_listings(search_url)
```

### Different Property Types

Modify the URL parameter `property-type`:
- `House` - Houses
- `Apartment` - Apartments/Units
- `Townhouse` - Townhouses
- `Land` - Land/Vacant blocks

Example:
```
https://propertyhub.harcourts.com.au/property-hub/listings/buy/?property-type=Apartment&location=Surfers-Paradise-4217
```

## Output Files

### JSON Format
Best for:
- Data analysis with Python/JavaScript
- API integration
- Maintaining data structure

### CSV Format
Best for:
- Excel spreadsheets
- Database imports
- Quick data review

## Extracted Data Fields

✓ **url** - Direct link to property listing
✓ **title** - Property headline/title
✓ **address** - Full street address with suburb and postcode
✓ **bed** - Number of bedrooms
✓ **bathrooms** - Number of bathrooms
✓ **car_spaces** - Number of car spaces/garage spots
✓ **price** - Asking price or "Contact Agent"
✓ **description** - Full property description with features
✓ **listing_agent** - Agent name(s) handling the property
✓ **image_urls** - Array of all property image URLs
✓ **Inspection_01, 02, ...** - Open inspection times (if scheduled)
✓ **scraped_at** - ISO timestamp of when data was scraped

## Tips for Best Results

1. **Rate Limiting**: The scraper includes built-in delays. Don't modify these to be faster, as it may trigger anti-bot measures.

2. **Headless vs Visible**: Use headless mode (default) for production. Use visible mode (`headless=False`) for debugging.

3. **Batch Processing**: For large datasets, scrape in batches:
   ```python
   # Scrape 50 properties at a time
   for i in range(0, 200, 50):
       properties = scraper.scrape_listings(search_url, max_properties=50)
       scraper.save_to_json(properties, f'batch_{i}.json')
       time.sleep(60)  # Wait between batches
   ```

4. **Error Handling**: The scraper handles missing fields gracefully. Check the output for any properties that may have incomplete data.

## Example Workflow

```python
from harcourts_scraper import HarcourtsPropertyScraper
import pandas as pd

# 1. Scrape properties
scraper = HarcourtsPropertyScraper(headless=True)
search_url = "https://propertyhub.harcourts.com.au/property-hub/listings/buy/?property-type=House&location=Robina-4023&include-suburb=1&category=buy&listing-category=residential"

properties = scraper.scrape_listings(search_url, max_properties=20)

# 2. Save raw data
scraper.save_to_json(properties, 'robina_houses.json')
scraper.save_to_csv(properties, 'robina_houses.csv')

# 3. Analyze with pandas
df = pd.read_json('robina_houses.json')
print(df.describe())
print(df['price'].value_counts())

# 4. Filter results
luxury_homes = df[df['bed'].astype(int) >= 5]
luxury_homes.to_csv('luxury_homes.csv', index=False)
```

## Support

For issues or questions about the scraper, check:
- README.md for general information
- Debug scripts in the directory for troubleshooting specific issues
- Test output files for example data structure
