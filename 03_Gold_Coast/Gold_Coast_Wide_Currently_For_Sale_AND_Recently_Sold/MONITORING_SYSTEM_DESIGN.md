# Property Monitoring System Design
**Last Updated:** 31/01/2026, 7:14 pm (Brisbane Time)

## 🎯 OBJECTIVE

Create three headless monitoring scripts that integrate with the fast parallel processing system (`run_dynamic_10_suburbs.py --all --max-concurrent 3 --parallel-properties 2`) to:

1. **Monitor price changes** in listed properties
2. **Monitor description changes** in listed properties  
3. **Detect sold properties** and move them to `Gold_Coast_Recently_Sold` collection

---

## 📊 CURRENT SYSTEM ARCHITECTURE

### **Existing For-Sale Discovery System**
- **Location:** `03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/`
- **Main Script:** `run_dynamic_10_suburbs.py`
- **Performance:** 5 hours for 52 suburbs (2,200 properties)
- **Configuration:** `--max-concurrent 3 --parallel-properties 2`
- **Database:** `Gold_Coast_Currently_For_Sale` (52 collections, one per suburb)
- **Mode:** Headless Chrome with parallel processing

### **Legacy Sold Monitor System**
- **Location:** `02_Domain_Scaping/For_Sale_To_Sold_Transition/`
- **Main Script:** `sold_property_monitor_selenium.py`
- **Issues:** 
  - Full-head browser mode (slow)
  - Sequential processing (~9 seconds per property)
  - Single collection (`properties_for_sale`)
  - ~40 minutes for monitoring
  - Not compatible with new parallel architecture

---

## 🏗️ NEW MONITORING SYSTEM DESIGN

### **Architecture Principles**

1. **Headless Operation:** All monitoring in headless Chrome
2. **Parallel Processing:** Support `--max-concurrent` and `--parallel-properties` flags
3. **Multi-Collection Support:** Work with 52 suburb collections
4. **Change Detection:** Track historical changes with timestamps
5. **MongoDB Safety:** Connection pooling, unique indexes, idempotent operations
6. **Modular Design:** Three separate scripts that can run independently or together

---

## 📋 THREE MONITORING SCRIPTS

### **1. Price Change Monitor** (`monitor_price_changes.py`)

**Purpose:** Detect and record price changes for all listed properties

**Features:**
- Scrapes current price from each property listing
- Compares with last recorded price in MongoDB
- Records price history with timestamps
- Detects: price increases, decreases, new prices
- Flags properties with frequent price changes

**Data Structure:**
```python
{
  "listing_url": "https://domain.com.au/...",
  "address": "123 Main St, Robina, QLD 4226",
  "current_price": "$850,000",
  "previous_price": "$900,000",
  "price_change_detected": True,
  "price_change_date": "2026-01-31T19:14:00",
  "price_change_amount": -50000,
  "price_change_percentage": -5.56,
  "price_history": [
    {"price": "$900,000", "recorded_at": "2026-01-15T10:00:00"},
    {"price": "$850,000", "recorded_at": "2026-01-31T19:14:00"}
  ],
  "price_change_count": 1
}
```

**Execution:**
```bash
# Monitor all suburbs
python3 monitor_price_changes.py --all --max-concurrent 3 --parallel-properties 2

# Monitor specific suburbs
python3 monitor_price_changes.py --suburbs "Robina:4226" "Varsity Lakes:4227"

# Test mode (first 10 properties per suburb)
python3 monitor_price_changes.py --test --max-concurrent 2
```

---

### **2. Description Change Monitor** (`monitor_description_changes.py`)

**Purpose:** Detect and record changes in agent descriptions

**Features:**
- Scrapes current agent description
- Compares with last recorded description
- Records description history with timestamps
- Detects: text additions, removals, complete rewrites
- Calculates similarity score between versions

**Data Structure:**
```python
{
  "listing_url": "https://domain.com.au/...",
  "address": "123 Main St, Robina, QLD 4226",
  "current_description": "Beautiful family home...",
  "previous_description": "Lovely property...",
  "description_change_detected": True,
  "description_change_date": "2026-01-31T19:14:00",
  "description_similarity_score": 0.65,  # 0-1 scale
  "description_history": [
    {"description": "Lovely property...", "recorded_at": "2026-01-15T10:00:00"},
    {"description": "Beautiful family home...", "recorded_at": "2026-01-31T19:14:00"}
  ],
  "description_change_count": 1
}
```

**Execution:**
```bash
# Monitor all suburbs
python3 monitor_description_changes.py --all --max-concurrent 3 --parallel-properties 2

# Monitor specific suburbs
python3 monitor_description_changes.py --suburbs "Robina:4226" "Varsity Lakes:4227"

# Test mode
python3 monitor_description_changes.py --test --max-concurrent 2
```

---

### **3. Sold Property Detector** (`monitor_sold_properties.py`)

**Purpose:** Detect sold properties and move them to `Gold_Coast_Recently_Sold` collection

**Features:**
- Checks each property for sold indicators (5 detection methods)
- Extracts sold date and sale price
- Moves property from suburb collection to `Gold_Coast_Recently_Sold`
- Preserves all historical data
- Handles auction properties correctly (prevents false positives)

**Detection Methods (Priority Order):**
1. **Listing Tag:** `<span data-testid="listing-details__listing-tag">Sold</span>`
2. **Breadcrumb Navigation:** Links containing "/sold/" or "Sold in"
3. **URL Pattern:** URL redirects to "/sold/" path
4. **Meta Tags:** og:type or other meta tags indicating sold status
5. **Auction Protection:** Prevents false positives from "SOLD BY [AGENT]" text

**Data Structure:**
```python
{
  # All original property data preserved
  "listing_url": "https://domain.com.au/...",
  "address": "123 Main St, Robina, QLD 4226",
  "original_price": "$850,000",
  
  # Sold detection metadata
  "sold_status": "sold",
  "sold_detection_date": "2026-01-31T19:14:00",
  "sold_date": "2026-01-28",
  "sold_date_text": "Sold by private treaty 28 Jan 2026",
  "sale_price": "$875,000",
  "detection_method": "listing_tag",
  "url_redirected": True,
  "final_url": "https://domain.com.au/.../sold/...",
  
  # Migration metadata
  "moved_to_sold_date": "2026-01-31T19:14:00",
  "original_collection": "robina",
  "original_suburb": "Robina"
}
```

**Collections:**
- **Source:** 52 suburb collections in `Gold_Coast_Currently_For_Sale`
- **Destination:** Single collection `Gold_Coast_Recently_Sold` in same database

**Execution:**
```bash
# Monitor all suburbs for sold properties
python3 monitor_sold_properties.py --all --max-concurrent 3 --parallel-properties 2

# Monitor specific suburbs
python3 monitor_sold_properties.py --suburbs "Robina:4226" "Varsity Lakes:4227"

# Test mode (first 10 properties per suburb)
python3 monitor_sold_properties.py --test --max-concurrent 2

# Generate sold properties report
python3 monitor_sold_properties.py --report
```

---

## 🔄 INTEGRATION WITH PARALLEL SYSTEM

### **IMPORTANT: Independent Execution**

These three monitors run **SEPARATELY** from `run_dynamic_10_suburbs.py`:
- They are **NOT** integrated into the discovery process
- They run **AFTER** properties have been discovered and scraped
- They monitor **EXISTING** properties in the database
- Time must pass between runs for changes to occur

**Execution Order:**
1. **First:** Run sold property detector (removes sold properties)
2. **Second:** Run price change monitor (on remaining properties)
3. **Third:** Run description change monitor (on remaining properties)

### **Shared Architecture Components**

All three monitors use the same parallel processing framework:

```python
# From run_dynamic_10_suburbs.py
- Dynamic suburb spawning (max concurrent suburbs)
- Parallel property processing (multiple properties at once)
- MongoDB connection pooling (maxPoolSize=50)
- Progress monitoring with Queue
- Graceful error handling
- Auto-recovery from transient issues

# From run_parallel_suburb_scrape.py
- Headless Chrome WebDriver setup
- ThreadPoolExecutor for parallel properties
- Thread-safe progress updates
- Dedicated WebDriver per property thread
- HTML parsing with BeautifulSoup
```

### **Performance Estimates**

Based on current system performance (5 hours for 2,200 properties):

**Price Change Monitor:**
- **Time per property:** ~3 seconds (only need price, not full scrape)
- **Total time (2,200 properties):** ~1.8 hours with parallel processing
- **Frequency:** Daily or every 2-3 days

**Description Change Monitor:**
- **Time per property:** ~3 seconds (only need description)
- **Total time (2,200 properties):** ~1.8 hours with parallel processing
- **Frequency:** Weekly or bi-weekly

**Sold Property Detector:**
- **Time per property:** ~5 seconds (need full page analysis)
- **Total time (2,200 properties):** ~3 hours with parallel processing
- **Frequency:** Daily

**Combined Daily Run:**
- Price monitoring: ~1.8 hours
- Sold detection: ~3 hours
- **Total:** ~4.8 hours (can run overnight)

---

## 🛡️ SAFETY FEATURES

### **MongoDB Safety**

1. **Unique Indexes:** Prevent duplicate entries
   ```python
   collection.create_index([("listing_url", ASCENDING)], unique=True)
   ```

2. **Connection Pooling:** Support concurrent operations
   ```python
   MongoClient(MONGODB_URI, maxPoolSize=50, minPoolSize=10)
   ```

3. **Idempotent Operations:** Safe to re-run
   ```python
   # Update if exists, insert if new
   collection.update_one(
       {"listing_url": url},
       {"$set": data},
       upsert=True
   )
   ```

4. **Transaction Safety:** Atomic move operations for sold properties
   ```python
   # Copy → Verify → Delete (not Delete → Copy)
   sold_collection.insert_one(property_doc)
   for_sale_collection.delete_one({"_id": property_doc["_id"]})
   ```

### **Error Handling**

1. **WebDriver Failures:** Auto-retry with exponential backoff
2. **Network Timeouts:** Configurable timeouts and retries
3. **MongoDB Disconnects:** Auto-reconnect with connection pooling
4. **Partial Failures:** Continue processing other properties
5. **Graceful Shutdown:** Ctrl+C handling with cleanup

---

## 📊 MONITORING & REPORTING

### **Progress Monitoring**

Real-time progress display:
```
[Robina] Discovery: 45 URLs found
[Varsity Lakes] Discovery: 38 URLs found
[Robina] Progress: 10/45 (8 changes detected)
[Varsity Lakes] Progress: 5/38 (2 changes detected)
[Robina] ✅ COMPLETE - 12 price changes detected
```

### **Summary Reports**

Each monitor generates detailed reports:

```python
# Price changes report
{
  "total_properties_checked": 2200,
  "price_changes_detected": 45,
  "average_price_change": -2.3,  # percentage
  "properties_with_increases": 12,
  "properties_with_decreases": 33,
  "suburbs_processed": 52
}

# Sold properties report
{
  "total_properties_checked": 2200,
  "sold_properties_detected": 18,
  "properties_moved": 18,
  "detection_methods": {
    "listing_tag": 12,
    "url_pattern": 4,
    "breadcrumb_link": 2
  }
}
```

---

## 🚀 IMPLEMENTATION PLAN

### **Phase 1: Core Infrastructure** ✅
- [x] Analyze existing systems
- [x] Design monitoring architecture
- [x] Document data structures

### **Phase 2: Price Change Monitor**
- [ ] Create `monitor_price_changes.py`
- [ ] Implement parallel processing
- [ ] Add price comparison logic
- [ ] Test with sample suburbs

### **Phase 3: Description Change Monitor**
- [ ] Create `monitor_description_changes.py`
- [ ] Implement text similarity detection
- [ ] Add description history tracking
- [ ] Test with sample suburbs

### **Phase 4: Sold Property Detector**
- [ ] Create `monitor_sold_properties.py`
- [ ] Port 5 detection methods from legacy system
- [ ] Implement collection migration logic
- [ ] Add auction protection
- [ ] Test with sample suburbs

### **Phase 5: Integration & Testing**
- [ ] Test all three monitors together
- [ ] Verify MongoDB safety
- [ ] Performance benchmarking
- [ ] Create orchestrator script

### **Phase 6: Documentation**
- [ ] User guide for each monitor
- [ ] Scheduling recommendations
- [ ] Troubleshooting guide

---

## 📝 USAGE EXAMPLES

### **Complete Daily Workflow (Recommended Order)**

```bash
# STEP 1: Discover new properties (5 hours)
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 run_dynamic_10_suburbs.py --all --max-concurrent 3 --parallel-properties 2

# STEP 2: Detect sold properties FIRST (3 hours) - removes sold properties
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_sold_properties.py --all --max-concurrent 3 --parallel-properties 2

# STEP 3: Monitor price changes (1.8 hours) - on remaining properties
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_price_changes.py --all --max-concurrent 3 --parallel-properties 2

# STEP 4: Monitor description changes (1.8 hours) - weekly, not daily
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 monitor_description_changes.py --all --max-concurrent 3 --parallel-properties 2
```

### **Why This Order Matters**

1. **Sold detector runs FIRST** to avoid wasting resources on properties that are no longer for sale
2. **Price monitor runs SECOND** on the cleaned dataset
3. **Description monitor runs LAST** (weekly, not daily)

### **Separate Execution (Not Integrated)**

These monitors are **standalone scripts** that:
- Run independently from discovery
- Monitor existing database properties
- Require time to pass between runs for changes to occur
- Are NOT part of `run_dynamic_10_suburbs.py`

---

## 🎓 KEY DESIGN DECISIONS

1. **Separate Scripts:** Each monitor is independent for flexibility
2. **Independent Execution:** NOT integrated into discovery process - run separately
3. **Execution Order:** Sold detector FIRST to avoid wasting resources
4. **Shared Architecture:** All use same parallel processing framework
5. **Headless Mode:** Faster and more reliable than full-head browsers
6. **Multi-Collection:** Works with 52 suburb collections
7. **Historical Tracking:** All changes recorded with timestamps
8. **Idempotent:** Safe to re-run without data corruption
9. **Scalable:** Connection pooling supports high concurrency

---

## 📚 NEXT STEPS

1. Implement `monitor_price_changes.py`
2. Implement `monitor_description_changes.py`
3. Implement `monitor_sold_properties.py`
4. Create orchestrator script `run_all_monitors.py`
5. Test with sample suburbs
6. Full production run
7. Schedule automated daily runs

---

**Ready to proceed with implementation!** 🚀
