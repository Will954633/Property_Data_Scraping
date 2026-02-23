# Dynamic Suburb Scraping - Action Plan
**Last Updated: 31/01/2026, 12:12 pm (Brisbane Time)**

## TASK BREAKDOWN: Manageable Steps

### ✅ COMPLETED ANALYSIS
- [x] Analyzed current parallel scraping implementation
- [x] Reviewed MongoDB safety mechanisms
- [x] Confirmed MongoDB is SAFE (separate collections, connection pooling, unique indexes)
- [x] Identified performance bottlenecks
- [x] Created comprehensive safety analysis document

### 📋 REMAINING STEPS

#### STEP 1: Clear Existing Collections (5 minutes)
**Goal:** Clean slate for fresh scraping  
**Risk:** LOW - We have backup from previous run  
**Action:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 clear_collections.py --suburbs robina varsity_lakes
```

#### STEP 2: Create Dynamic Spawning Script (15 minutes)
**Goal:** Build script that maintains max 5 concurrent suburbs  
**Risk:** VERY LOW - Uses existing safe architecture  
**Features:**
- Queue of pending suburbs (from gold_coast_suburbs.json)
- Start 5 suburbs initially
- Monitor completion
- Spawn new suburb when one finishes
- Continue until all 52 suburbs processed

**Key Changes from Current Script:**
- Add suburb queue management
- Add dynamic process spawning
- Reduce startup stagger: 10s → 5s
- Keep all MongoDB safety features

#### STEP 3: Create Simple Test Script (5 minutes)
**Goal:** Test with 3 small suburbs first  
**Risk:** VERY LOW  
**Test Suburbs:**
- Bilinga (small)
- Tugun (small)
- Elanora (medium)

#### STEP 4: Run Test (10 minutes)
**Goal:** Verify dynamic spawning works correctly  
**Monitor:**
- Process spawning behavior
- MongoDB writes
- Completion detection
- Error handling

#### STEP 5: Run Full 52-Suburb Scrape (3-4 hours)
**Goal:** Complete Gold Coast scraping  
**Monitor:**
- Progress every 30 minutes
- Check for errors
- Verify MongoDB collections

---

## IMPLEMENTATION DETAILS

### Script Architecture

```python
# Pseudo-code for dynamic spawning

suburbs_queue = load_all_52_suburbs()
active_processes = {}
completed_suburbs = []
MAX_CONCURRENT = 5

# Start initial batch
for i in range(MAX_CONCURRENT):
    if suburbs_queue:
        suburb = suburbs_queue.pop(0)
        process = start_suburb_scraper(suburb)
        active_processes[suburb] = process

# Monitor and spawn
while active_processes or suburbs_queue:
    # Check for completed processes
    for suburb, process in list(active_processes.items()):
        if not process.is_alive():
            completed_suburbs.append(suburb)
            del active_processes[suburb]
            
            # Spawn new suburb if queue has more
            if suburbs_queue:
                new_suburb = suburbs_queue.pop(0)
                new_process = start_suburb_scraper(new_suburb)
                active_processes[new_suburb] = new_process
    
    time.sleep(10)  # Check every 10 seconds

# All done!
```

### MongoDB Safety Guarantees

1. ✅ **Separate Collections** - No write conflicts
2. ✅ **Connection Pooling** - Built-in queuing (maxPoolSize=50)
3. ✅ **Unique Indexes** - Prevents duplicates
4. ✅ **Retry Logic** - Handles transient failures
5. ✅ **One Client Per Process** - No sharing issues

### Performance Optimizations

1. ✅ **Dynamic Spawning** - No idle time waiting for slow suburbs
2. ✅ **Reduced Stagger** - 10s → 5s (saves 25s per batch)
3. ⏳ **Future: Reduce page waits** - 5s → 3s (test first)
4. ⏳ **Future: Parallel properties** - 3 at once per suburb

---

## EXECUTION CHECKLIST

### Pre-Flight Checks
- [ ] MongoDB is running (`mongosh` to verify)
- [ ] Python dependencies installed
- [ ] Selenium/ChromeDriver working
- [ ] Backup of existing data (if needed)

### Execution Steps
- [ ] Step 1: Clear collections (robina, varsity_lakes)
- [ ] Step 2: Create dynamic spawning script
- [ ] Step 3: Create test script (3 suburbs)
- [ ] Step 4: Run test and verify
- [ ] Step 5: Run full 52-suburb scrape

### Post-Execution Verification
- [ ] Check all 52 collections exist
- [ ] Verify document counts match expected
- [ ] Spot-check data quality
- [ ] Review error logs

---

## RISK MITIGATION

### What Could Go Wrong?

1. **WebDriver Crashes**
   - ✅ Mitigation: Each suburb in separate process
   - ✅ Impact: Only affects one suburb, others continue

2. **MongoDB Connection Issues**
   - ✅ Mitigation: Retry logic, connection pooling
   - ✅ Impact: Minimal, auto-recovers

3. **Domain.com.au Rate Limiting**
   - ✅ Mitigation: Delays between requests, headless mode
   - ✅ Impact: Might slow down, but won't break

4. **System Resource Exhaustion**
   - ✅ Mitigation: Max 5 concurrent processes
   - ✅ Impact: Controlled resource usage

### Rollback Plan

If something goes wrong:
1. Stop all processes (Ctrl+C)
2. Check MongoDB for partial data
3. Clear affected collections
4. Restart from specific suburb

---

## ESTIMATED TIMELINE

- **Step 1 (Clear):** 5 minutes
- **Step 2 (Create script):** 15 minutes
- **Step 3 (Test script):** 5 minutes
- **Step 4 (Run test):** 10 minutes
- **Step 5 (Full scrape):** 3-4 hours

**Total:** ~4 hours (mostly automated)

---

## SUCCESS CRITERIA

✅ All 52 suburbs scraped  
✅ No MongoDB errors  
✅ Data quality maintained  
✅ Dynamic spawning works correctly  
✅ Faster than sequential approach  

---

## NEXT STEPS AFTER COMPLETION

1. Analyze scraping statistics
2. Identify any failed suburbs
3. Re-run failed suburbs if needed
4. Consider property-level parallelization for future runs
5. Document lessons learned
