# Sold Properties Scraper (Last 6 Months)

**Created:** 15 December 2025  
**Status:** ✅ Ready to Use  
**Database:** `property_data`  
**Collection:** `sold_last_6_months`

---

## 📋 Overview

This scraper collects all properties sold in the last 6 months from Domain.com.au for 5 Gold Coast suburbs. It features intelligent stop conditions to ensure efficient data collection and avoid scraping old or duplicate data.

### Suburbs Covered
- **Robina** (7 pages)
- **Mudgeeraba** (5 pages)
- **Varsity Lakes** (4 pages)
- **Reedy Creek** (2 pages)
- **Burleigh Waters** (4 pages)

### Key Features
✅ **Sale Date Extraction** - Extracts and validates sale dates from each property  
✅ **Intelligent Stop Conditions** - Stops per suburb when:
  - 3 consecutive properties have sale dates >6 months old, OR
  - 3 consecutive properties already exist in database  
✅ **Suburb-by-Suburb Processing** - Sequential processing for clean stop triggers  
✅ **Complete Property Data** - Beds, baths, price, images, floor plans, features, etc.  
✅ **MongoDB Integration** - Stores in `sold_last_6_months` collection  
✅ **Incremental Updates** - Subsequent runs only add new sales  

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold_In_Last_6_Months
pip3 install -r requirements.txt
```

### 2. Make Scripts Executable

```bash
chmod +x process_sold_properties.sh
chmod +x *.py
```

### 3. Run the Scraper

```bash
./process_sold_properties.sh
```

This will:
1. Extract property URLs from all suburbs
2. Scrape property details (including sale dates)
3. Upload to MongoDB with stop conditions
4. Display summary statistics

---

## 📂 File Structure

```
02_Domain_Scaping/Sold_In_Last_6_Months/
├── DEVELOPMENT_PLAN.md              # Detailed development plan
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
│
├── html_parser_sold.py              # HTML parser with sale date extraction
├── list_page_scraper_sold.py        # Stage 1: Extract property URLs
├── property_detail_scraper_sold.py  # Stage 2: Scrape property details
├── mongodb_uploader_sold.py         # Stage 3: Upload with stop conditions
├── check_mongodb_status_sold.py     # View collection statistics
├── process_sold_properties.sh       # Main orchestration script
│
├── listing_results/                 # Output: Property URLs by suburb
├── property_data/                   # Output: Scraped property data
│   └── html/                        # Raw HTML files
└── upload_log_*.json                # Upload logs with stop reasons
```

---

## 🔧 Usage

### Run Complete Pipeline

```bash
./process_sold_properties.sh
```

### Run Individual Stages

**Stage 1: Extract URLs**
```bash
python3 list_page_scraper_sold.py
```

**Stage 2: Scrape Properties (by suburb)**
```bash
python3 property_detail_scraper_sold.py --suburb robina
python3 property_detail_scraper_sold.py --suburb mudgeeraba
python3 property_detail_scraper_sold.py --suburb varsity_lakes
python3 property_detail_scraper_sold.py --suburb reedy_creek
python3 property_detail_scraper_sold.py --suburb burleigh_waters
```

**Stage 3: Upload to MongoDB**
```bash
python3 mongodb_uploader_sold.py
```

**Check Status**
```bash
python3 check_mongodb_status_sold.py
```

---

## 🛑 Stop Conditions Explained

The scraper implements **two independent stop conditions** per suburb:

### Stop Condition A: Sale Date Check
- Tracks consecutive properties with sale dates >6 months from today
- **Stops** when 3 consecutive properties exceed 6 months
- **Resets** counter when a property within 6 months is found

### Stop Condition B: Duplicate Check
- Checks if property already exists in database (by address)
- **Stops** when 3 consecutive duplicates are found
- **Resets** counter when a new property is found

### Example Flow

```
Robina Suburb:
  Property 1: Sold 2024-12-01 ✓ New → Insert (consecutive_old=0, consecutive_dup=0)
  Property 2: Sold 2024-11-15 ✓ New → Insert (consecutive_old=0, consecutive_dup=0)
  Property 3: Sold 2024-10-20 ✓ Duplicate → Update (consecutive_old=0, consecutive_dup=1)
  Property 4: Sold 2024-09-30 ✓ Duplicate → Update (consecutive_old=0, consecutive_dup=2)
  Property 5: Sold 2024-08-15 ✓ Duplicate → Update (consecutive_old=0, consecutive_dup=3)
  🛑 STOP: 3 consecutive duplicates
  
Move to Mudgeeraba (counters reset)...
```

---

## 📊 Data Schema

Each property document includes:

### Core Fields
- `address` - Full property address (unique index)
- `street_address`, `suburb`, `postcode`
- `bedrooms`, `bathrooms`, `carspaces`
- `property_type` - House, Townhouse, Apartment, etc.
- `land_size_sqm`
- `description`, `agents_description`
- `property_images` - Array of image URLs
- `floor_plans` - Array of floor plan URLs
- `features` - Array of property features
- `listing_url`

### Sold-Specific Fields
- `sale_date` - **CRITICAL** (ISO format: YYYY-MM-DD)
- `sale_price` - Actual sold price
- `suburb_scraped` - Which suburb scrape found this property

### Metadata
- `extraction_method` - "HTML"
- `extraction_date` - When scraped
- `first_seen` - When first added to database
- `last_updated` - Last update timestamp
- `source` - "selenium_sold_scraper"

---

## 📈 Expected Results

### First Run (Fresh Database)
- **Robina:** ~50-100 properties
- **Mudgeeraba:** ~30-60 properties
- **Varsity Lakes:** ~40-80 properties
- **Reedy Creek:** ~15-30 properties
- **Burleigh Waters:** ~40-80 properties

**Total:** 175-350 properties (depending on stop conditions)

### Subsequent Runs
- Only new sales added (incremental updates)
- Stop conditions trigger earlier (more duplicates)
- Efficient updates without re-scraping old data

---

## 🔍 Monitoring

### View Collection Status

```bash
python3 check_mongodb_status_sold.py
```

**Output:**
- Total properties count
- Breakdown by suburb
- Recent sales (30/60/90 days)
- Date range (oldest/newest)
- Data quality metrics
- Top 5 most recent sales

### MongoDB Queries

```javascript
// Connect to MongoDB
use property_data

// Count total sold properties
db.sold_last_6_months.count()

// Find recent sales (last 30 days)
db.sold_last_6_months.find({
  sale_date: { $gte: "2024-11-15" }
}).sort({ sale_date: -1 })

// Count by suburb
db.sold_last_6_months.aggregate([
  { $group: { _id: "$suburb_scraped", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

// Find properties by price range
db.sold_last_6_months.find({
  sale_price: { $regex: /\$[89]\d{2},\d{3}/ }  // $800k-$999k
})
```

---

## 🚨 Troubleshooting

### Issue: No sale dates extracted

**Symptoms:** Properties scraped but missing `sale_date` field  
**Solution:**
1. Check if Domain.com.au changed their HTML structure
2. Review `html_parser_sold.py` extraction methods
3. Examine saved HTML files in `property_data/html/`
4. Update extraction patterns if needed

### Issue: Stop conditions not triggering

**Symptoms:** Scraper processes all properties without stopping  
**Solution:**
1. Check if properties actually have sale dates >6 months
2. Verify MongoDB connection is working
3. Review upload logs for stop condition checks
4. Ensure counters are resetting correctly

### Issue: Selenium/Chrome errors

**Symptoms:** WebDriver fails to start  
**Solution:**
```bash
# Update Chrome
brew upgrade --cask google-chrome

# Reinstall webdriver-manager
pip3 uninstall webdriver-manager
pip3 install webdriver-manager

# Clear webdriver cache
rm -rf ~/.wdm
```

### Issue: MongoDB connection failed

**Symptoms:** Cannot connect to MongoDB  
**Solution:**
```bash
# Start MongoDB
brew services start mongodb-community

# Check if running
brew services list | grep mongodb

# Test connection
mongosh
```

---

## 📅 Maintenance

### Weekly Updates

Run the scraper weekly to catch new sales:

```bash
cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold_In_Last_6_Months
./process_sold_properties.sh
```

### Monthly Review

1. Check data quality metrics
2. Review stop condition logs
3. Clean up old temporary files
4. Update suburb URLs if needed

### Cleanup Old Files

```bash
# Remove old HTML files (keep last 7 days)
find property_data/html -name "*.html" -mtime +7 -delete

# Remove old listing results (keep last 30 days)
find listing_results -name "*.html" -mtime +30 -delete
```

---

## 🔗 Related Documentation

- **Development Plan:** `DEVELOPMENT_PLAN.md`
- **For-Sale Scraper:** `/00_Run_Commands/01_Scraping_For_Sale_Properties_04122025.md`
- **MongoDB Setup:** `/01_Run_Commands/Run_Mongodb.md`

---

## 💡 Tips

1. **First Run:** Expect 20-30 minutes for complete scraping
2. **Subsequent Runs:** Much faster due to stop conditions (5-10 minutes)
3. **Best Time:** Run weekly on Monday mornings to catch weekend sales
4. **Data Quality:** >95% of properties should have sale dates
5. **Stop Logs:** Review `upload_log_*.json` to understand stop reasons

---

## ✅ Success Checklist

Before running in production, verify:

- [ ] MongoDB is running (`brew services list`)
- [ ] Python dependencies installed (`pip3 list`)
- [ ] Chrome browser is up to date
- [ ] Scripts are executable (`chmod +x`)
- [ ] Test run completed successfully
- [ ] Collection `sold_last_6_months` exists
- [ ] Stop conditions triggered correctly
- [ ] Sale dates extracted for >95% of properties

---

## 📞 Support

**Issues?** Check:
1. This README troubleshooting section
2. Development plan for detailed specifications
3. Upload logs for stop condition details
4. MongoDB status for collection health

**Developer:** Property Data Scraping Team  
**Created:** 15 December 2025  
**Version:** 1.0.0

---

**END OF README**
