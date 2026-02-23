# Sold Property Monitoring System

**Last Updated: 27/01/2026, 8:40 AM (Monday) - Brisbane**
- Enhanced with multiple fallback detection methods
- Added breadcrumb navigation detection
- Added "SOLD BY" text pattern detection
- Added URL redirect detection
- Improved robustness to catch properties missed by simple tag detection

Automated monitoring system that tracks properties from the `properties_for_sale` MongoDB collection and detects when they've been sold, then moves them to the `properties_sold` collection with sale information.

## Overview

This system monitors Domain.com.au property listings to detect when properties transition from "for sale" to "sold" status. When a sold property is detected, it captures:
- Sold date (when the property was sold)
- Sale price (if disclosed)
- Detection date (when our system discovered it was sold)
- Detection method used (for debugging and improvement)

The property is then automatically moved from the `properties_for_sale` collection to the new `properties_sold` collection in MongoDB.

## How It Works

### Enhanced Detection Methods

The system uses **5 different detection methods** with fallback logic to ensure maximum detection accuracy. Each method is tried in order until a sold property is detected:

#### Method 1: Listing Tag (Primary)
Searches for HTML elements indicating sold status:
- Example: `<span data-testid="listing-details__listing-tag">Sold by private treaty 25 Nov 2025</span>`
- **Detection Method ID**: `listing_tag`

#### Method 2: Breadcrumb Navigation
Checks navigation breadcrumbs for sold indicators:
- Looks for "Sold in [Suburb]" text in breadcrumb navigation
- Checks for links containing `/sold/` in navigation paths
- Example: `< Sold in Robina > Home > Sold > QLD > Robina`
- **Detection Method ID**: `breadcrumb_navigation` or `breadcrumb_link`

#### Method 3: Description Text Patterns
Searches for "SOLD BY" patterns in property descriptions:
- Patterns: "SOLD BY [AGENT NAME]", "Sold by [Agent Name]"
- Checks meta descriptions and content areas
- Example: "SOLD BY TINA NENADIC AND JULIANNE PETERSEN"
- **Detection Method ID**: `description_sold_by`

#### Method 4: URL Pattern Detection
Checks if the URL contains `/sold/` path:
- Detects when URLs redirect from `/buy/` to `/sold/`
- Example: `https://www.domain.com.au/sold/12-carnoustie-court-robina-qld-4226`
- **Detection Method ID**: `url_pattern`

#### Method 5: Meta Tags
Checks Open Graph and other meta tags:
- Looks for `og:type` containing "sold"
- Example: `<meta property="og:type" content="property:sold">`
- **Detection Method ID**: `meta_og_type`

### Sale Price Extraction

Extracts sale price from multiple possible locations:
- Price display elements (e.g., "SOLD - $1,240,000")
- Meta tags (og:price:amount)
- Page title
- Property description

### Sold Date Parsing

Parses date information from the sold tag text:
- Example: "Sold by private treaty 25 Nov 2025" → "2025-11-25"
- Supports multiple date formats

### Data Flow

```
properties_for_sale → Monitor Script → Fetch HTML → Check if Sold
                                            ↓
                                       [If Sold]
                                            ↓
                            Add sold metadata + Move to properties_sold
                                            ↓
                                  Remove from properties_for_sale
```

## Installation

### Prerequisites

- Python 3.7+
- MongoDB running locally on port 27017
- Internet connection to fetch listing pages

### Install Dependencies

```bash
cd 02_Domain_Scaping/Sold
pip3 install -r requirements.txt
```

Required packages:
- `requests` - HTTP requests to fetch property pages
- `beautifulsoup4` - HTML parsing to extract sold information
- `pymongo` - MongoDB database operations

## Usage

### Quick Start

Make the shell script executable (first time only):
```bash
chmod +x monitor_sold_properties.sh
```

Run the monitor:
```bash
./monitor_sold_properties.sh
```

This will check all properties in the `properties_for_sale` collection and move any sold properties to `properties_sold`.

### Command Line Options

#### Shell Script Options

```bash
# Monitor all properties (production)
./monitor_sold_properties.sh

# Test with limited properties (recommended for first run)
./monitor_sold_properties.sh --limit 10

# Adjust delay between requests (default: 2 seconds)
./monitor_sold_properties.sh --delay 3

# Generate sold properties report
./monitor_sold_properties.sh --report

# Show help
./monitor_sold_properties.sh --help
```

#### Python Script Direct Usage

```bash
# Monitor all properties
python3 sold_property_monitor.py

# Test mode - check only 5 properties
python3 sold_property_monitor.py --limit 5

# Adjust request delay
python3 sold_property_monitor.py --delay 3.0

# Generate report of sold properties
python3 sold_property_monitor.py --report

# Verbose logging for debugging
python3 sold_property_monitor.py --verbose

# Custom MongoDB URI
python3 sold_property_monitor.py --mongodb-uri mongodb://localhost:27017/
```

## MongoDB Collections

### Source Collection: `properties_for_sale`

Properties actively listed for sale. Must contain:
- `listing_url`: The Domain.com.au URL for the property
- `address`: Property address for identification

### Destination Collection: `properties_sold`

Properties confirmed as sold. Additional fields added:
- `sold_status`: "sold"
- `sold_detection_date`: When our system detected the sale
- `sold_date`: Actual sale date (if available)
- `sold_date_text`: Raw text from the sold tag
- `sale_price`: Sale amount (if disclosed)
- `detection_method`: Which detection method found the sold status (e.g., "breadcrumb_navigation", "listing_tag")
- `url_redirected`: Boolean indicating if URL was redirected
- `final_url`: The final URL after any redirects
- `moved_to_sold_date`: When moved to this collection
- `original_collection`: "properties_for_sale"

All original property data is preserved when moving to the sold collection.

SOLD PROPERTY MONITORING
Total properties to monitor: 37

✓ MongoDB indexes ensured
Checking: 927 Medinah Avenue, Robina, QLD 4226
Checking: 3 Carpentaria Court, Robina, QLD 4226
...
🏠 SOLD PROPERTY DETECTED: 14a Pinehurst Place, Robina, QLD 4226
  Sold Date: 2025-08-29
  Sale Price: SOLD - $1,525,000
✓ Moved property to sold collection: 14a Pinehurst Place, Robina, QLD 4226
...

MONITORING SUMMARY
Properties checked: 37
Properties sold: 3
Errors: 0
Properties still for sale: 34

DATABASE STATUS:
  properties_for_sale: 34
  properties_sold: 3
```
## Testing

### Test Enhanced Detection

A test script is provided to validate the enhanced detection methods:

```bash
# Test the known problematic property (12 Carnoustie Court, Robina)
python3 test_enhanced_detection.py

# Test a specific property by address
python3 test_enhanced_detection.py --address "12 Carnoustie Court, Robina, QLD 4226"

# Test all detection methods with sample HTML
python3 test_enhanced_detection.py --test-methods

# Verbose output for debugging
python3 test_enhanced_detection.py --verbose
```

## Example Output

### Monitoring Process (Enhanced)

```
SOLD PROPERTY MONITORING
Total properties to monitor: 186

✓ MongoDB indexes ensured
Checking: 927 Medinah Avenue, Robina, QLD 4226
  ✗ No sold indicators found
Checking: 3 Carpentaria Court, Robina, QLD 4226
  ✗ No sold indicators found
Checking: 12 Carnoustie Court, Robina, QLD 4226
  ✓ Detection Method 2 (Breadcrumb): Found 'Sold' in navigation
🏠 SOLD PROPERTY DETECTED: 12 Carnoustie Court, Robina, QLD 4226
  Detection Method: breadcrumb_navigation
  Sold Date: Not available
  Sale Price: Not disclosed
✓ Moved property to sold collection: 12 Carnoustie Court, Robina, QLD 4226
...
🏠 SOLD PROPERTY DETECTED: 14a Pinehurst Place, Robina, QLD 4226
  Detection Method: listing_tag
  Sold Date: 2025-08-29
  Sale Price: SOLD - $1,525,000
✓ Moved property to sold collection: 14a Pinehurst Place, Robina, QLD 4226
...

MONITORING SUMMARY
Properties checked: 186
Properties sold: 5
Errors: 0
Properties still for sale: 181

DATABASE STATUS:
  properties_for_sale: 181
  properties_sold: 15
```
================================================================================
SOLD PROPERTY MONITORING
================================================================================
Total properties to monitor: 37

✓ MongoDB indexes ensured
Checking: 927 Medinah Avenue, Robina, QLD 4226
Checking: 3 Carpentaria Court, Robina, QLD 4226
...
🏠 SOLD PROPERTY DETECTED: 14a Pinehurst Place, Robina, QLD 4226
  Sold Date: 2025-08-29
  Sale Price: SOLD - $1,525,000
✓ Moved property to sold collection: 14a Pinehurst Place, Robina, QLD 4226
...

================================================================================
MONITORING SUMMARY
================================================================================
Properties checked: 37
Properties sold: 3
Errors: 0
Properties still for sale: 34

DATABASE STATUS:
  properties_for_sale: 34
  properties_sold: 3
================================================================================
```

### Report Output

```bash
./monitor_sold_properties.sh --report
```

```json
{
  "total_sold": 3,
  "properties": [
    {
      "address": "14a Pinehurst Place, Robina, QLD 4226",
      "listing_url": "https://www.domain.com.au/14a-pinehurst-place-robina-qld-4226-2020303720",
      "sold_date": "2025-08-29",
      "sold_date_text": "Sold by private treaty 29 Aug 2025",
      "sale_price": "SOLD - $1,525,000",
      "sold_detection_date": "2025-12-04T14:30:15.123456",
      "original_price": "Contact Agent"
    },
    ...
  ]
}
```

## Scheduling Automated Monitoring

### Using Cron (Recommended)

Run monitoring daily at 2 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust path to your installation)
0 2 * * * cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold && ./monitor_sold_properties.sh >> logs/monitor_$(date +\%Y\%m\%d).log 2>&1
```

Run monitoring weekly on Sundays at 9 PM:
```bash
0 21 * * 0 cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold && ./monitor_sold_properties.sh >> logs/monitor_weekly.log 2>&1
```

### Create Logs Directory

```bash
mkdir -p logs
```

## Best Practices

### Request Rate Limiting

- Default delay: 2 seconds between requests
- Increase delay if you encounter rate limiting: `--delay 3`
- For large collections, consider running during off-peak hours

### Testing

Always test with a small sample first:
```bash
./monitor_sold_properties.sh --limit 10
```

### Error Handling

The script handles:
- Network timeouts (15 second timeout per request)
- Failed requests (logged, continue to next property)
- MongoDB connection issues (graceful exit)
- Missing listing URLs (skipped with warning)

### Data Integrity

- Properties are only removed from `properties_for_sale` after successful insertion into `properties_sold`
- Original property data is never lost
- Unique indexes on `address` prevent duplicates

## Troubleshooting

### MongoDB Not Running

```
⚠️  WARNING: MongoDB doesn't appear to be running!
```

**Solution**: Start MongoDB
```bash
brew services start mongodb-community
```

### No listing_url Field

```
No listing_url for property: [address]
```

**Solution**: Ensure properties in `properties_for_sale` have the `listing_url` field. This should be populated by the scraping process.

### Rate Limiting / 429 Errors

**Solution**: Increase delay between requests
```bash
./monitor_sold_properties.sh --delay 5
```

### Missing Dependencies

```
ModuleNotFoundError: No module named 'requests'
```

**Solution**: Install requirements
```bash
pip3 install -r requirements.txt
```

## Integration with For Sale System

This monitoring system works in conjunction with the For Sale scraping system:

1. **For Sale System** (`02_Domain_Scaping/For_Sale/`)
   - Scrapes new property listings
   - Uploads to `properties_for_sale` collection

2. **Sold Monitoring System** (`02_Domain_Scaping/Sold/`)
   - Monitors properties in `properties_for_sale`
   - Detects sold properties
   - Moves to `properties_sold` collection

### Workflow

```
Domain.com.au
     ↓
[For Sale Scraper] → properties_for_sale (MongoDB)
                             ↓
                    [Sold Monitor] (this system)
                             ↓
                    properties_sold (MongoDB)
```

## Files

- `sold_property_monitor.py` - Main Python script with enhanced detection
- `monitor_sold_properties.sh` - Shell wrapper script
- `test_enhanced_detection.py` - Test script for validation
- `requirements.txt` - Python dependencies
- `README.md` - This documentation
- `TEST_RESULTS.md` - Test results and validation logs

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Run with `--verbose` flag for debugging
3. Test with `--limit 1` to isolate issues
4. Verify MongoDB connection and collection structure

## Example: Detected Sold Property

**Before** (in properties_for_sale):
```json
{
  "address": "81 Cheltenham Drive, Robina, QLD 4226",
  "listing_url": "https://www.domain.com.au/81-cheltenham-drive-robina-qld-4226-2020360375",
  "price": "Auction",
  "bedrooms": 4,
  "bathrooms": 2,
  ...
}
```

**After** (in properties_sold):
```json
{
  "address": "81 Cheltenham Drive, Robina, QLD 4226",
  "listing_url": "https://www.domain.com.au/81-cheltenham-drive-robina-qld-4226-2020360375",
  "price": "Auction",
  "bedrooms": 4,
  "bathrooms": 2,
  "sold_status": "sold",
  "sold_date": "2025-11-25",
  "sold_date_text": "Sold by private treaty 25 Nov 2025",
  "sale_price": "SOLD - $1,240,000",
  "detection_method": "listing_tag",
  "url_redirected": false,
  "final_url": "https://www.domain.com.au/81-cheltenham-drive-robina-qld-4226-2020360375",
  "sold_detection_date": "2025-12-04T14:28:30.456789",
  "moved_to_sold_date": "2025-12-04T14:28:30.456789",
  "original_collection": "properties_for_sale",
  ...
}
```

## Detection Method Statistics

The system tracks which detection method successfully identified each sold property. This helps identify patterns and improve detection accuracy:

- **listing_tag**: Primary method, most reliable when available
- **breadcrumb_navigation**: Catches properties where the listing tag is missing but breadcrumb shows "Sold in [Suburb]"
- **description_sold_by**: Detects properties with "SOLD BY [AGENT]" in descriptions
- **url_pattern**: Identifies properties where URL contains `/sold/`
- **meta_og_type**: Fallback for properties with sold status in meta tags

### Known Success Cases

The enhanced detection successfully identifies properties like:
- **12 Carnoustie Court, Robina, QLD 4226**: Detected via breadcrumb navigation (missed by original simple detection)
- Properties with "SOLD BY [AGENT NAME]" in descriptions
- Properties where URL redirects from `/buy/` to `/sold/`

## License

Part of the Property Data Scraping project.
