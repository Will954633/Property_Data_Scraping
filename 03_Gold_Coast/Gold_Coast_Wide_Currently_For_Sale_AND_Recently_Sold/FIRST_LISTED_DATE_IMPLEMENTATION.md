# First Listed Date Extraction - Implementation Summary
**Last Updated: 31/01/2026, 10:47 am (Brisbane Time)**

## Overview
Successfully implemented extraction of "First listed on DD Month" date and days on market data from Domain.com.au property pages.

## Changes Made

### 1. Updated `run_complete_suburb_scrape.py`

#### New Method: `extract_first_listed_date()`
Added a new method to extract listing date information from property HTML:

```python
def extract_first_listed_date(self, html: str) -> Dict:
    """
    Extract 'First listed' date and days on market from HTML
    
    Returns dict with:
    - first_listed_date: str (e.g., "20 January")
    - first_listed_year: int (inferred from current year)
    - first_listed_full: str (e.g., "20 January 2026")
    - days_on_domain: int (extracted from text)
    - last_updated_date: str (if available)
    """
```

**Pattern Matching:**
- Searches for: `"First listed on DD Month, this house has been on Domain for NN days"`
- Uses regex pattern: `r'First listed on (\d{1,2})\s+([A-Za-z]+)(?:,?\s+this\s+\w+\s+has\s+been\s+on\s+Domain\s+for\s+(\d+)\s+days?)?'`
- Also extracts "last updated on DD Month" if available

**Year Inference Logic:**
- Assumes current year for most listings
- If we're in January and the listing month is December, assumes previous year
- This handles year-end edge cases correctly

#### Integration in `scrape_property()`
The extraction is now called for every property scraped:

```python
# Extract "First listed" date and days on market
listing_date_info = self.extract_first_listed_date(html)
property_data['first_listed_date'] = listing_date_info['first_listed_date']
property_data['first_listed_year'] = listing_date_info['first_listed_year']
property_data['first_listed_full'] = listing_date_info['first_listed_full']
property_data['days_on_domain'] = listing_date_info['days_on_domain']
property_data['last_updated_date'] = listing_date_info['last_updated_date']
```

#### Enhanced Output Display
When a property is successfully scraped, the console now shows:
```
✓ Saved: 5bed, 3bath
✓ Agents: John Smith, Jane Doe
✓ First listed: 20 January (11 days on Domain)
```

### 2. New MongoDB Fields

The following fields are now stored in MongoDB for each property:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `first_listed_date` | String | Day and month property was first listed | "20 January" |
| `first_listed_year` | Integer | Year property was first listed (inferred) | 2026 |
| `first_listed_full` | String | Complete date string | "20 January 2026" |
| `days_on_domain` | Integer | Number of days property has been on Domain | 11 |
| `last_updated_date` | String | Date the listing was last updated | "20 January" |

**Note:** These fields will be `None` if the "First listed" text is not found on the property page.

### 3. Test Script Created

Created `test_first_listed_extraction.py` to test the extraction logic:
- Tests extraction on live property URLs
- Saves HTML for inspection
- Validates the regex pattern matching
- Can be used to verify extraction on different property types

## Usage

### Running the Main Script
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 run_complete_suburb_scrape.py --suburb "Varsity Lakes" --postcode 4227
```

### Running the Test Script
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 test_first_listed_extraction.py
```

## Data Availability Notes

### When Data is Available
The "First listed" text appears on Domain.com.au property pages in this format:
> "First listed on 20 January, this house has been on Domain for 11 days (last updated on 20 January)."

### When Data May Not Be Available
- Very new listings (may not have the text yet)
- Sold properties or removed listings
- Properties under offer
- Domain may not show this for all property types

### Handling Missing Data
The script gracefully handles missing data:
- Fields are set to `None` if not found
- No errors are raised
- Scraping continues normally
- Data is captured when available

## Days on Market Calculation

The script captures the days on market directly from Domain's text rather than calculating it ourselves. This ensures:
- ✅ Accuracy matches Domain's calculation
- ✅ No timezone or date calculation issues
- ✅ Consistent with what users see on Domain
- ✅ Can be used for subsequent analysis and reporting

## Future Enhancements

Potential improvements for future iterations:

1. **Calculate Days on Market from First Listed Date**
   - If `days_on_domain` is not provided, calculate from `first_listed_full`
   - Compare current date with first listed date
   - Store as calculated field

2. **Track Listing History**
   - Monitor changes to `days_on_domain` over time
   - Detect if property is relisted (days reset to low number)
   - Track price changes relative to days on market

3. **Analytics**
   - Average days on market by suburb
   - Price reduction patterns vs days on market
   - Seasonal trends in listing dates

4. **Alerts**
   - Properties on market > X days
   - Recently listed properties (< 7 days)
   - Properties with price changes after extended time on market

## Testing Recommendations

1. **Test with Various Property Types:**
   - Houses
   - Apartments
   - Townhouses
   - Land

2. **Test Edge Cases:**
   - Brand new listings (< 1 day)
   - Long-term listings (> 90 days)
   - Relisted properties
   - Properties near year-end (December/January)

3. **Verify Data Quality:**
   - Check MongoDB documents have the new fields
   - Verify dates are parsed correctly
   - Confirm days on market matches Domain's display

## Example MongoDB Document

```json
{
  "listing_url": "https://www.domain.com.au/21-carnoustie-drive-varsity-lakes-qld-4227-2020062598",
  "address": "21 Carnoustie Drive, Varsity Lakes, QLD 4227",
  "bedrooms": 5,
  "bathrooms": 3,
  "first_listed_date": "20 January",
  "first_listed_year": 2026,
  "first_listed_full": "20 January 2026",
  "days_on_domain": 11,
  "last_updated_date": "20 January",
  "extraction_date": "2026-01-31T10:47:00",
  "source": "complete_suburb_scraper"
}
```

## Conclusion

The implementation is complete and ready for production use. The extraction function will:
- ✅ Capture "First listed" dates when available
- ✅ Extract days on market directly from Domain
- ✅ Store data in MongoDB for analysis
- ✅ Handle missing data gracefully
- ✅ Display captured data in console output

The data can now be used for:
- Days on market analysis
- Listing age tracking
- Price change correlation studies
- Market velocity metrics
- Automated alerts and monitoring
