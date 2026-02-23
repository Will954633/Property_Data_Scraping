# Quick Start Guide

## Installation & Setup (One-Time)

```bash
# 1. Navigate to the directory
cd 09_Ray_White

# 2. Install dependencies
pip install -r requirements.txt
```

## Running the Scraper

### Option 1: Use the Quick Start Script (Recommended)
```bash
./run_scraper.sh
```

### Option 2: Run Python Script Directly
```bash
python ray_white_scraper.py
```

### Option 3: Test First (Scrapes only 3 properties)
```bash
python test_scraper.py
```

## What You'll Get

After running the scraper, you'll find:

1. **JSON file** with all property data:
   - `ray_white_properties_YYYYMMDD_HHMMSS.json`
   - Contains all property details including image URLs

2. **Log file** for debugging:
   - `ray_white_scraper_YYYYMMDD_HHMMSS.log`
   - Contains execution details and any errors

## Example Output Structure

```json
{
  "scraped_at": "2025-11-25T09:30:00",
  "total_properties": 25,
  "properties": [
    {
      "url": "https://raywhiterobina.com.au/property/...",
      "title": "Stunning Family Home",
      "address": "123 Main St, Robina QLD 4226",
      "price": "$850,000",
      "features": {
        "bedrooms": "4 Bed",
        "bathrooms": "2 Bath",
        "parking": "2 Car"
      },
      "image_urls": [
        "https://..../image1.jpg",
        "https://..../image2.jpg"
      ],
      "agent": {
        "name": "John Smith",
        "phone": "07 5555 5555"
      }
    }
  ]
}
```

## Troubleshooting

**No properties found?**
- Check internet connection
- Verify the target URL is still valid
- Run in test mode first: `python test_scraper.py`

**Import errors?**
- Run: `pip install -r requirements.txt`

**ChromeDriver issues?**
- Ensure Chrome is installed
- The script auto-downloads the correct driver version

## Need More Help?

See the full [README.md](README.md) for:
- Detailed documentation
- Customization options
- Advanced troubleshooting
- Technical details
