# End-to-End Gold Coast Property Monitoring Process
**Last Updated:** 03/02/2026, 7:14 pm (Brisbane Time)

## 📋 Executive Summary

This document describes the complete automated process for monitoring all Gold Coast properties, detecting sales, tracking changes, and enriching data with visual analysis. The system differentiates between **Target Market suburbs** (monitored nightly) and **Other suburbs** (monitored weekly).

---

## 🎯 Target Market Definition

Based on `/Users/projects/Documents/Feilds_Website/02_Target_Market/BUSINESS_SUMMARY.md`:

### **8 Core Target Market Suburbs** (Nightly Monitoring)
1. **Robina** (4226) - Anchor market, 228 sales/year
2. **Mudgeeraba** (4213) - Adjacent, 144 sales/year
3. **Varsity Lakes** (4227) - Adjacent, 117 sales/year
4. **Reedy Creek** (4227) - Adjacent premium, 87 sales/year
5. **Burleigh Waters** (4220) - High volume premium, 225 sales/year
6. **Merrimac** (4226) - Adjacent affordable, 59 sales/year
7. **Worongary** (4213) - Adjacent acreage, 41 sales/year
8. **Carrara** (4211) - Adjacent (implied from business context)

### **Other Gold Coast Suburbs** (Weekly Monitoring)
All remaining 44 suburbs in `gold_coast_suburbs.json`

---

## 🔄 Complete Monitoring Workflow

### **Phase 1: Initial Property Discovery & Scraping**

#### 1.1 Scrape Currently Listed Properties
**Script:** `headless_forsale_mongodb_scraper.py`  
**Location:** `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/`

**Purpose:** Discover and scrape all currently listed for-sale properties

**Process:**
```bash
# Run for all 52 suburbs
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 run_dynamic_10_suburbs.py
```

**What It Does:**
- Scrapes Domain.com.au for all for-sale listings
- Extracts property details (beds, baths, price, images, floor plans, etc.)
- Stores in MongoDB: `Gold_Coast_Currently_For_Sale` database
- One collection per suburb (e.g., `robina`, `varsity_lakes`)
- Tracks changes in `history.{field}` arrays
- Captures agent information via carousel rotation

**Output Collections:**
- Database: `Gold_Coast_Currently_For_Sale`
- Collections: 52 suburb collections (one per suburb)

**Frequency:**
- **Target Market:** Run nightly (8 suburbs)
- **Other Suburbs:** Run weekly on Sunday (44 suburbs)

---

### **Phase 2: Monitor for Sold Properties**

#### 2.1 Detect Sold Properties
**Script:** `monitor_sold_properties.py` (**OPTIMIZED VERSION**)  
**Location:** `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/`

**Purpose:** Check all currently-listed properties to detect which have sold

**Performance:** 
- ✅ **10x faster** after ChromeDriver optimization
- Creates ONE driver per suburb (not per property)
- ~10 properties per minute (vs ~1 property/minute before)

**Process:**

**For Target Market (Nightly):**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --suburbs "Robina:4226" "Mudgeeraba:4213" "Varsity Lakes:4227" "Reedy Creek:4227" "Burleigh Waters:4220" "Merrimac:4226" "Worongary:4213" "Carrara:4211" --max-concurrent 5
```

**For Other Suburbs (Weekly - Sunday):**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --all --max-concurrent 5
```

**What It Does:**
1. **Checks each property** using 5 detection methods:
   - Listing tag detection
   - Breadcrumb navigation
   - URL pattern analysis
   - Meta tag inspection
   - Auction protection (prevents false positives)

2. **Extracts sold data:**
   - Sold date
   - Sale price
   - Detection method used

3. **Moves sold properties:**
   - From: `Gold_Coast_Currently_For_Sale.{suburb}`
   - To: `Gold_Coast_Currently_For_Sale.Gold_Coast_Recently_Sold`

4. **Updates master database:**
   - Database: `Gold_Coast`
   - Collection: `{suburb_name}` (e.g., `Robina`)
   - Appends to `sales_history` array
   - Updates `last_sold_date` and `last_sale_price`

**Output:**
- Sold properties in: `Gold_Coast_Currently_For_Sale.Gold_Coast_Recently_Sold`
- Master records updated in: `Gold_Coast.{suburb_name}`

---

### **Phase 3: Data Enrichment (Target Market Only)**

#### 3.1 Photo Reordering with Visual Analysis
**Script:** `ollama_photo_reorder.py`  
**Location:** `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis/`

**Purpose:** Analyze and reorder property photos for optimal presentation

**Process:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 run_production.py --collection robina --workers 4
```

**What It Does:**
- Uses Ollama LLaVA vision model
- Analyzes each photo for:
  - Room type identification
  - Quality assessment
  - Feature detection
  - Presentation value
- Reorders photos for maximum impact
- Stores analysis in `image_analysis` array

**Run For Each Target Market Suburb:**
```bash
# Robina
python3 run_production.py --collection robina --workers 4

# Mudgeeraba
python3 run_production.py --collection mudgeeraba --workers 4

# Varsity Lakes
python3 run_production.py --collection varsity_lakes --workers 4

# Reedy Creek
python3 run_production.py --collection reedy_creek --workers 4

# Burleigh Waters
python3 run_production.py --collection burleigh_waters --workers 4

# Merrimac
python3 run_production.py --collection merrimac --workers 4

# Worongary
python3 run_production.py --collection worongary --workers 4

# Carrara
python3 run_production.py --collection carrara --workers 4
```

**Documentation:** `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis/PHOTO_REORDER_README.md`

---

#### 3.2 Floor Plan Analysis
**Script:** `ollama_floor_plan_analysis.py`  
**Location:** `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis/`

**Purpose:** Extract structured data from floor plan images

**Process:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 ollama_floor_plan_analysis.py --collection robina --workers 4
```

**What It Does:**
- Analyzes floor plan images using Ollama LLaVA
- Extracts:
  - Room dimensions
  - Room types and counts
  - Total living area
  - Layout features
  - Special features (pool, deck, etc.)
- Stores in `floor_plan_analysis` field

**Run For Each Target Market Suburb:**
```bash
# Robina
python3 ollama_floor_plan_analysis.py --collection robina --workers 4

# Mudgeeraba
python3 ollama_floor_plan_analysis.py --collection mudgeeraba --workers 4

# (Repeat for all 8 target market suburbs)
```

**Documentation:** `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis/FLOOR_PLAN_ANALYSIS_README.md`

---

## 📅 Monitoring Schedule

### **Nightly Schedule (Target Market - 8 Suburbs)**

**Time:** 2:00 AM Brisbane Time (off-peak)

**Sequence:**
1. **2:00 AM** - Scrape new/updated listings (Target Market only)
2. **3:00 AM** - Monitor for sold properties (Target Market only)
3. **4:00 AM** - Photo reordering analysis (Target Market only)
4. **5:00 AM** - Floor plan analysis (Target Market only)

**Estimated Duration:** ~3-4 hours total

**Cron Schedule:**
```bash
# Nightly scraping (Target Market)
0 2 * * * cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 run_target_market_scrape.py

# Nightly sold monitoring (Target Market)
0 3 * * * cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --suburbs "Robina:4226" "Mudgeeraba:4213" "Varsity Lakes:4227" "Reedy Creek:4227" "Burleigh Waters:4220" "Merrimac:4226" "Worongary:4213" "Carrara:4211" --max-concurrent 5

# Nightly photo analysis (Target Market)
0 4 * * * cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && ./run_target_market_photo_analysis.sh

# Nightly floor plan analysis (Target Market)
0 5 * * * cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && ./run_target_market_floorplan_analysis.sh
```

---

### **Weekly Schedule (All Suburbs - Sunday)**

**Time:** 1:00 AM Sunday Brisbane Time

**Sequence:**
1. **1:00 AM** - Scrape all 52 suburbs
2. **6:00 AM** - Monitor all suburbs for sold properties

**Estimated Duration:** ~8-10 hours total

**Cron Schedule:**
```bash
# Weekly full scrape (All suburbs - Sunday)
0 1 * * 0 cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 run_dynamic_10_suburbs.py

# Weekly sold monitoring (All suburbs - Sunday)
0 6 * * 0 cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --all --max-concurrent 5
```

---

## 🗄️ Database Structure

### **Database 1: Gold_Coast_Currently_For_Sale**
**Purpose:** Active listings and recently sold properties

**Collections:**
- `robina` - Currently listed in Robina
- `varsity_lakes` - Currently listed in Varsity Lakes
- ... (52 suburb collections total)
- `Gold_Coast_Recently_Sold` - All sold properties (moved from suburb collections)

**Document Structure (For-Sale Property):**
```javascript
{
  _id: ObjectId,
  listing_url: "https://www.domain.com.au/...",
  address: "6 480 Christine Avenue, Robina, QLD 4226",
  price: "$1,400,000",
  bedrooms: 4,
  bathrooms: 2,
  car_spaces: 2,
  land_size: "650 sqm",
  property_type: "House",
  agents_description: "...",
  images: ["url1", "url2", ...],
  floor_plans: ["url1", "url2", ...],
  
  // Timestamps
  first_seen: ISODate("2026-01-15T10:30:00Z"),
  last_updated: ISODate("2026-02-03T02:15:00Z"),
  first_listed_date: "2026-01-15",
  
  // Change tracking
  change_count: 3,
  history: {
    price: [
      { value: "$1,450,000", recorded_at: ISODate("2026-01-15") },
      { value: "$1,400,000", recorded_at: ISODate("2026-02-01") }
    ],
    inspection_times: [...],
    agents_description: [...]
  },
  
  // Enrichment data (Target Market only)
  image_analysis: [
    {
      url: "...",
      room_type: "Living Room",
      quality_score: 8.5,
      features: ["fireplace", "high ceilings"],
      recommended_order: 1
    },
    ...
  ],
  floor_plan_analysis: {
    total_area: "245 sqm",
    rooms: [
      { type: "Master Bedroom", dimensions: "4.5m x 3.8m" },
      ...
    ],
    features: ["pool", "outdoor entertaining"]
  },
  
  // Enrichment status
  enriched: true,
  last_enriched: ISODate("2026-02-03T04:30:00Z")
}
```

**Document Structure (Sold Property):**
```javascript
{
  // All fields from for-sale property, plus:
  
  sold_status: "sold",
  sold_detection_date: ISODate("2026-02-03T03:15:00Z"),
  sold_date: "2026-02-01",
  sold_date_text: "Sold 1 Feb 2026",
  sale_price: "$1,420,000",
  detection_method: "listing_tag",
  url_redirected: false,
  
  // Migration metadata
  moved_to_sold_date: ISODate("2026-02-03T03:15:00Z"),
  original_collection: "robina",
  original_suburb: "Robina"
}
```

---

### **Database 2: Gold_Coast**
**Purpose:** Master property database (permanent records)

**Collections:**
- `Robina` - All properties in Robina (permanent)
- `Varsity Lakes` - All properties in Varsity Lakes (permanent)
- ... (52 suburb collections total)

**Document Structure (Master Property Record):**
```javascript
{
  _id: ObjectId,
  complete_address: "6 480 Christine Avenue, Robina, QLD 4226",
  
  // Property characteristics
  bedrooms: 4,
  bathrooms: 2,
  car_spaces: 2,
  land_size: "650 sqm",
  property_type: "House",
  
  // Sales history (appended each time property sells)
  sales_history: [
    {
      listing_date: "2024-03-15",
      listing_price: "$1,200,000",
      sold_date: "2024-04-20",
      sale_price: "$1,250,000",
      days_on_market: 36,
      agent_name: "John Smith",
      agency: "Ray White Robina",
      listing_url: "https://...",
      images: [...],
      floor_plans: [...]
    },
    {
      listing_date: "2026-01-15",
      listing_price: "$1,450,000",
      sold_date: "2026-02-01",
      sale_price: "$1,420,000",
      days_on_market: 17,
      agent_name: "Jane Doe",
      agency: "Harcourts Coastal",
      listing_url: "https://...",
      images: [...],
      floor_plans: [...]
    }
  ],
  
  // Latest sale info
  last_sold_date: "2026-02-01",
  last_sale_price: "$1,420,000",
  last_updated: ISODate("2026-02-03T03:15:00Z")
}
```

---

## 🔧 Helper Scripts & Tools

### **Monitoring & Reporting**

**Check Sold Properties Report:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --report
```

**Check Photo Analysis Readiness:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 check_suburb_names.py
```

**Check Floor Plan Analysis Readiness:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 check_floor_plan_readiness.py
```

**View Analysis Results:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 show_floor_plan_result.py --collection robina --limit 5
```

---

## 📊 Performance Metrics

### **ChromeDriver Optimization Results**
- **Before:** ~1 property/minute (60s cleanup per property)
- **After:** ~10 properties/minute (60s cleanup once per suburb)
- **Improvement:** **10x faster**
- **Implementation:** Single shared driver per suburb process

### **Expected Processing Times**

**Target Market (8 Suburbs - Nightly):**
- Scraping: ~30 minutes
- Sold monitoring: ~45 minutes (assuming ~100 properties per suburb)
- Photo analysis: ~2 hours (4 workers)
- Floor plan analysis: ~1 hour (4 workers)
- **Total:** ~4-5 hours

**All Suburbs (52 Suburbs - Weekly):**
- Scraping: ~3-4 hours
- Sold monitoring: ~4-5 hours
- **Total:** ~8-10 hours

---

## 🚨 Error Handling & Monitoring

### **Logging Locations**

**Scraping Logs:**
- Location: `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/logs/`
- Files: `scrape_{suburb}_{date}.log`

**Sold Monitoring Logs:**
- Console output (redirect to file in cron)
- Example: `monitor_sold_properties_{date}.log`

**Analysis Logs:**
- Location: `/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis/logs/`
- Files: `photo_analysis_{date}.log`, `floorplan_analysis_{date}.log`

### **Monitoring Commands**

**Check if processes are running:**
```bash
ps aux | grep python3 | grep monitor_sold
ps aux | grep python3 | grep ollama
```

**Check MongoDB connection:**
```bash
mongosh --eval "db.adminCommand('ping')"
```

**Check recent sold properties:**
```bash
mongosh Gold_Coast_Currently_For_Sale --eval "db.Gold_Coast_Recently_Sold.find().sort({sold_detection_date: -1}).limit(10).pretty()"
```

---

## 📁 Key File Locations

### **Scripts**
```
/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/
├── headless_forsale_mongodb_scraper.py          # Scrape for-sale listings
├── monitor_sold_properties.py                    # Detect sold properties (OPTIMIZED)
├── monitor_sold_properties.py.backup             # Original backup
├── run_dynamic_10_suburbs.py                     # Run all suburbs dynamically
├── gold_coast_suburbs.json                       # Suburb list (52 suburbs)
└── Ollama_Property_Analysis/
    ├── ollama_photo_reorder.py                   # Photo reordering
    ├── ollama_floor_plan_analysis.py             # Floor plan analysis
    ├── run_production.py                         # Photo analysis runner
    └── mongodb_client.py                         # MongoDB interface
```

### **Documentation**
```
/Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/
├── END_TO_END_PROPERTY_MONITORING_PROCESS.md    # This document
├── CHROMEDRIVER_PERFORMANCE_FIX.md              # Performance optimization details
├── 00_PROCESS_TO_RUN_ALL_GC_FOR_SALE.md        # For-sale scraping guide
├── 00_PROCESS_TO_RUN_ALL_GC_SOLD_AND_CHANGED.md # Sold monitoring guide
└── Ollama_Property_Analysis/
    ├── PHOTO_REORDER_README.md                  # Photo analysis guide
    ├── FLOOR_PLAN_ANALYSIS_README.md            # Floor plan analysis guide
    └── 00_Process_To_Run_All_Photo_and_Floorplan_Analysis.md
```

### **Target Market Reference**
```
/Users/projects/Documents/Feilds_Website/02_Target_Market/
└── BUSINESS_SUMMARY.md                          # Target market definition
```

---

## 🎯 Quick Start Commands

### **Test Target Market Monitoring (10 properties each):**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --suburbs "Robina:4226" "Mudgeeraba:4213" "Varsity Lakes:4227" "Reedy Creek:4227" "Burleigh Waters:4220" "Merrimac:4226" "Worongary:4213" "Carrara:4211" --max-concurrent 5 --test
```

### **Production Target Market Monitoring (All properties):**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --suburbs "Robina:4226" "Mudgeeraba:4213" "Varsity Lakes:4227" "Reedy Creek:4227" "Burleigh Waters:4220" "Merrimac:4226" "Worongary:4213" "Carrara:4211" --max-concurrent 5
```

### **Production All Suburbs Monitoring:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --all --max-concurrent 5
```

---

## 📈 Success Metrics

### **Data Quality Indicators**
- ✅ All target market properties have `image_analysis`
- ✅ All target market properties with floor plans have `floor_plan_analysis`
- ✅ Sold properties detected within 24 hours (nightly monitoring)
- ✅ Master database updated with complete sales history
- ✅ Change tracking captures price reductions and updates

### **Performance Indicators**
- ✅ Target market monitoring completes in < 5 hours
- ✅ Weekly full monitoring completes in < 10 hours
- ✅ Zero missed sold properties (100% detection rate)
- ✅ < 1% error rate in visual analysis

---

## 🔄 Maintenance & Updates

### **Monthly Tasks**
- Review sold properties report
- Check for new suburbs in Gold Coast
- Verify all cron jobs are running
- Review error logs

### **Quarterly Tasks**
- Update target market list if business focus changes
- Review and optimize analysis prompts
- Check MongoDB disk usage and optimize indexes
- Update ChromeDriver if needed

### **Annual Tasks**
- Review entire process for improvements
- Update documentation
- Backup all databases
- Review and update suburb list

---

## 📞 Support & Troubleshooting

### **Common Issues**

**Issue:** ChromeDriver fails to start  
**Solution:** Remove and reinstall: `rm -rf /Users/projects/.wdm/drivers/chromedriver`

**Issue:** MongoDB connection timeout  
**Solution:** Check MongoDB is running: `brew services list | grep mongodb`

**Issue:** Ollama analysis fails  
**Solution:** Check Ollama is running: `ollama list`

**Issue:** Properties not being detected as sold  
**Solution:** Check detection methods in logs, may need to update selectors

---

## ✅ Summary

This end-to-end process provides:

1. **Comprehensive Coverage:** All 52 Gold Coast suburbs monitored
2. **Differentiated Monitoring:** Target market (8 suburbs) nightly, others weekly
3. **Complete Data Enrichment:** Visual analysis for target market properties
4. **Automated Sales Tracking:** Sold properties detected and moved automatically
5. **Master Database Updates:** Permanent sales history maintained
6. **10x Performance:** Optimized ChromeDriver usage
7. **Scalable Architecture:** Can handle growth in property count

**Result:** A fully automated, high-performance property monitoring system tailored to business priorities.
