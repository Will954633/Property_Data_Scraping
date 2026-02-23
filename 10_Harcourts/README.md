# Harcourts Property Scraper

A Python-based web scraper for extracting property listing data from Harcourts Property Hub (https://propertyhub.harcourts.com.au).

## Features

- Scrapes property listings from search results pages
- Extracts comprehensive property details including:
  - Title
  - Address
  - Bedrooms, Bathrooms, Car Spaces
  - Price
  - Open inspection times
  - Full property description
  - Listing agents
  - Property images
- Exports data to both CSV and JSON formats
- Anti-detection measures to bypass CloudFront protection
- Configurable for headless or visible browser operation

## Requirements

- Python 3.7+
- Chrome browser installed
- ChromeDriver (matching your Chrome version)

## Installation

1. Install required Python packages:
```bash
pip install -r requirements.txt
```

2. Ensure ChromeDriver is installed and in your PATH

## Usage

### Quick Test (2 properties)

```bash
python3 quick_test.py
```

### Full Scraper (10 properties)

```bash
python3 harcourts_scraper.py
```

### Custom Usage

```python
from harcourts_scraper import HarcourtsPropertyScraper

# Initialize scraper
scraper = HarcourtsPropertyScraper(headless=True)

# Custom search URL
search_url = "https://propertyhub.harcourts.com.au/property-hub/listings/buy/?property-type=House&location=Robina-4023"

# Scrape properties
properties = scraper.scrape_listings(search_url, max_properties=20)

# Save results
scraper.save_to_csv(properties, 'my_properties.csv')
scraper.save_to_json(properties, 'my_properties.json')
```

## Output Format

### JSON Example
```json
{
  "url": "https://propertyhub.harcourts.com.au/listing/...",
  "title": "Luxury Main River Living in Prestigious Sorrento",
  "address": "925 Medinah Avenue, Robina, QLD 4226",
  "bed": "5",
  "bathrooms": "3",
  "car_spaces": "4",
  "price": "Contact Agent",
  "description": "Sophisticated Luxury Residence...",
  "listing_agent": "Isaac Genc, Frank Kasikci",
  "image_urls": ["https://...", "https://..."],
  "scraped_at": "2025-11-25T12:27:18.823974",
  "Inspection_01": "29 November, 2025 — 12:00 PM to 12:45 PM"
}
```

### CSV Output

The scraper generates a CSV file with all property data in a tabular format, suitable for importing into Excel or data analysis tools.

## Configuration Options

### Headless Mode
```python
# Run with visible browser (for debugging)
scraper = HarcourtsPropertyScraper(headless=False)

# Run headless (default, faster)
scraper = HarcourtsPropertyScraper(headless=True)
```

### Limiting Properties
```python
# Scrape first 5 properties
properties = scraper.scrape_listings(search_url, max_properties=5)

# Scrape all properties (no limit)
properties = scraper.scrape_listings(search_url)
```

## Anti-Detection Features

The scraper includes several anti-detection measures to bypass CloudFront protection:

- Custom user agent
- Headless mode optimizations
- CDP commands to hide automation
- Randomized delays between requests
- WebDriver property masking

## Data Fields Extracted

| Field | Description | Example |
|-------|-------------|---------|
| url | Property listing URL | https://propertyhub.harcourts.com.au/listing/... |
| title | Property title | "Luxury Main River Living in Prestigious Sorrento" |
| address | Full property address | "925 Medinah Avenue, Robina, QLD 4226" |
| bed | Number of bedrooms | "5" |
| bathrooms | Number of bathrooms | "3" |
| car_spaces | Number of car spaces/garage | "4" |
| price | Asking price or contact method | "Contact Agent" |
| description | Full property description | "Sophisticated Luxury Residence..." |
| listing_agent | Agent name(s) | "Isaac Genc, Frank Kasikci" |
| image_urls | Array of property image URLs | ["https://...", ...] |
| Inspection_01, 02, etc. | Open inspection times | "29 November, 2025 — 12:00 PM to 12:45 PM" |
| scraped_at | Timestamp of scraping | "2025-11-25T12:27:18.823974" |

## Notes

- The scraper is configured for the Robina, QLD area by default
- Adjust the search URL for different locations or property types
- Respect the website's terms of service and implement appropriate delays
- The scraper includes 2-4 second delays between requests to be polite
- Some properties may not have all fields (e.g., inspection times, certain attributes)

## Troubleshooting

### 403 CloudFront Errors
If you encounter 403 errors, the anti-detection measures should handle this. If issues persist:
- Increase the sleep delays in the code
- Try running in non-headless mode
- Check if your IP has been rate-limited

### Missing Data Fields
Some properties may not have all data fields available. The scraper handles this gracefully by setting empty strings for missing data.

### ChromeDriver Issues
Ensure ChromeDriver version matches your installed Chrome browser version:
```bash
google-chrome --version
chromedriver --version
```

## License

For educational and research purposes only. Ensure compliance with Harcourts' terms of service.
