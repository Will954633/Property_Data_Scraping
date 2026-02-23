# Harcourts Scraper Usage Guide

## Quick Start

The scraper is ready to use! However, the default URL in the code currently has no active listings. Follow these steps to use it effectively:

### Option 1: Use the Default URL (when listings are available)

```bash
cd 10_Harcourts
python harcourts_scraper.py
```

### Option 2: Change the Search URL

To scrape properties from a different search:

1. Go to https://propertyhub.harcourts.com.au/
2. Search for properties (e.g., different location, property type)
3. Copy the URL from your browser
4. Edit `harcourts_scraper.py` and update the `listing_url` variable in the `main()` function

```python
# Example: Change from Robina Houses to Gold Coast Apartments
listing_url = "https://propertyhub.harcourts.com.au/property-hub/listings/buy/?property-type=Apartment&location=Gold-Coast-4217&category=buy&listing-category=residential"
```

## Testing the Scraper

To test with a limited number of properties:

```bash
cd 10_Harcourts
python test_scraper.py
```

This will:
- Only scrape the first page of results
- Only scrape the first 2 properties
- Save results to `test_results.json` and `test_results.csv`

## Understanding the Output

### JSON Output
Complete structured data in JSON format, easy to process programmatically.

**File:** `harcourts_properties_YYYYMMDD_HHMMSS.json`

```json
[
  {
    "url": "https://propertyhub.harcourts.com.au/property/...",
    "title": "Property for Sale",
    "address": "925 Medinah Avenue, Robina, QLD 4226",
    "beds": "5",
    "bathrooms": "3",
    "carspaces": "4",
    "price": "Contact Agent",
    "open_inspection_times": ["29 November, 2025 — 12:00 PM to 12:45 PM"],
    "description": "Beautiful family home...",
    "agents": ["Isaac Genc", "Frank Kasikci"],
    "scraped_at": "2025-11-25T11:48:00.000000"
  }
]
```

### CSV Output
Spreadsheet-compatible format for viewing in Excel or Google Sheets.

**File:** `harcourts_properties_YYYYMMDD_HHMMSS.csv`

## Customization Options

Edit `harcourts_scraper.py` to customize:

### Run in Visible Browser Mode (for debugging)
```python
scraper = HarcourtsPropertyScraper(headless=False)
```

### Limit Number of Pages
```python
properties_data = scraper.scrape_all_properties(
    listing_url=listing_url,
    max_pages=5,  # Only scrape first 5 pages
    delay=2
)
```

### Adjust Delay Between Requests
```python
properties_data = scraper.scrape_all_properties(
    listing_url=listing_url,
    max_pages=None,
    delay=3  # 3 seconds between each property
)
```

## Troubleshooting

### "No property URLs found"
- The search may have no results
- Try a different search URL with active listings
- Check that the website is accessible

### Missing Data Fields
- Some properties may not have all fields (e.g., no inspection times scheduled)
- The scraper handles missing data gracefully by leaving fields empty

### ChromeDriver Errors
```bash
pip install --upgrade webdriver-manager selenium
```

## Finding Active Listings

To find URLs with active listings:

1. Visit https://propertyhub.harcourts.com.au/
2. Use the search filters:
   - **Category:** Buy/Rent
   - **Location:** Any city/suburb
   - **Property Type:** House/Apartment/etc.
3. Click "Search"
4. Copy the URL from your browser
5. Update `listing_url` in the script

Example working searches:
- Gold Coast houses for sale
- Brisbane apartments for rent
- Sydney properties for sale

## Data Fields Extracted

| Field | Description |
|-------|-------------|
| url | Property listing URL |
| title | Property title/heading |
| address | Full address |
| beds | Number of bedrooms |
| bathrooms | Number of bathrooms |
| carspaces | Number of car spaces |
| price | Listed price or "Contact Agent" |
| open_inspection_times | List of scheduled inspection times |
| description | Full property description |
| agents | List of agent names |
| scraped_at | Timestamp when data was collected |

## Performance Notes

- **Headless mode** (default): Faster, runs in background
- **Visible mode** (`headless=False`): Slower, but useful for debugging
- **Recommended delay**: 2-3 seconds between properties to avoid rate limiting
- **Average time**: ~5-10 seconds per property depending on page load speed

## Legal & Ethical Use

- Respect the website's terms of service
- Use for personal/research purposes only
- Don't overwhelm the server with rapid requests
- The default delay of 2 seconds is respectful

## Need Help?

Check the README.md for more detailed information about:
- Installation requirements
- Feature overview
- Technical details
- Example outputs
