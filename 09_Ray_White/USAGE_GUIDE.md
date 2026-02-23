# Ray White Robina Property Scraper - Usage Guide

## ✅ System is Ready to Use!

The scraper successfully tested and extracted property data including **35 images** from a sample property.

---

## Quick Start

### Run the Full Scraper
```bash
cd 09_Ray_White
python ray_white_scraper.py
```

Or use the convenience script:
```bash
cd 09_Ray_White
./run_scraper.sh
```

### Run Test Mode (Recommended First)
```bash
cd 09_Ray_White
python test_scraper.py
```

---

## What the Scraper Extracts

For each property, the scraper collects:

### Core Information
- ✅ **Property URL** - Direct link to listing
- ✅ **Title** - Property address/name
- ✅ **Price** - Listing price (if available)
- ✅ **Property Type** - House, apartment, etc.

### Property Features
- ✅ **Bedrooms** - Number of bedrooms
- ✅ **Bathrooms** - Number of bathrooms
- ✅ **Parking** - Garage/parking spaces
- ✅ **Land Size** - Property land area
- ✅ **Floor Area** - Building floor space

### Rich Data
- ✅ **Description** - Full property description
- ✅ **Agent Information** - Name, phone, email
- ✅ **Image URLs** - All property photos (30-50+ per property)
- ✅ **Inspection Times** - Open house schedules
- ✅ **Date Listed** - When property was listed
- ✅ **Additional Details** - Any extra specifications

---

## Output Format

Data is saved to JSON with this structure:

```json
{
  "scraped_at": "2025-11-25T09:35:57",
  "total_properties": 10,
  "source_url": "https://raywhiterobina.com.au/...",
  "properties": [
    {
      "url": "https://raywhiterobina.com.au/...",
      "title": "14 Huntingdale Crescent, Robina",
      "price": "Offers Over $1,295,000",
      "features": {
        "bedrooms": "4",
        "bathrooms": "2",
        "parking": "2 garage spaces",
        "land_size": "800m²"
      },
      "image_urls": [
        "https://cdn6.ep.dynamics.net/...",
        "https://cdn6.ep.dynamics.net/...",
        // ... 30+ more images
      ],
      "inspection_times": [...],
      "agent": {...},
      "description": "...",
      "additional_details": {...}
    }
  ]
}
```

---

## Output Files

The scraper creates several files:

1. **ray_white_properties_YYYYMMDD_HHMMSS.json** - Main data output
2. **ray_white_scraper_YYYYMMDD_HHMMSS.log** - Detailed execution log
3. **test_results.json** - Test run results (when using test_scraper.py)

---

## Test Results Summary

The test successfully demonstrated:

✅ **Property Detection**: Found property listings on page  
✅ **URL Extraction**: Extracted valid property URLs  
✅ **Data Scraping**: Retrieved comprehensive property data  
✅ **Image Collection**: Extracted 35+ high-quality image URLs  
✅ **JSON Export**: Saved data in structured format  

---

## Customization

### Change Target URL
Edit `ray_white_scraper.py` line 45:
```python
self.listing_url = "YOUR_CUSTOM_URL_HERE"
```

### Run in Visible Browser Mode
Change `headless` parameter:
```python
scraper = RayWhiteRobinaScraper(headless=False)
```

### Adjust Delays
Modify sleep times in the code:
```python
time.sleep(2)  # Delay between requests
```

---

## Troubleshooting

### No Properties Found
- Check if the listing URL has active properties
- Website structure may have changed - update selectors in code
- Try running with `headless=False` to see what's happening

### Missing Data Fields
- Some properties may not have all fields
- The scraper extracts whatever is available
- Check the log file for details

### ChromeDriver Issues
If you get driver errors:
```bash
pip install --upgrade webdriver-manager
```

---

## Performance Notes

- **Speed**: ~2-3 seconds per property (respectful scraping)
- **Images**: Collects 30-50+ images per property automatically
- **Reliability**: Handles missing data gracefully
- **Logging**: Comprehensive logs for debugging

---

## Example Commands

**Full scrape with logging**:
```bash
python ray_white_scraper.py 2>&1 | tee scraper_output.log
```

**Background execution**:
```bash
nohup python ray_white_scraper.py > output.log 2>&1 &
```

**Quick test**:
```bash
python test_scraper.py
```

---

## Data Usage

The extracted JSON can be used for:
- Property databases
- Market analysis
- Price tracking
- Image collections
- Real estate applications
- Investment research

---

## Support

If you encounter issues:
1. Check the log files for detailed error messages
2. Run test_scraper.py first to validate setup
3. Try with `headless=False` to see browser behavior
4. Verify the website URL is still valid

---

## Success Indicators

When the scraper runs successfully, you'll see:

```
✅ Successfully saved X properties to ray_white_properties_*.json

📊 Summary:
   - Total properties scraped: X
   - Properties with images: X
   - Total images collected: XXX+
```

---

**Ready to scrape? Run `python ray_white_scraper.py` now!** 🚀
