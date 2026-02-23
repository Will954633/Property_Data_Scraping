# Implementation Steps - Dynamic + Parallel Scraping
**Last Updated: 31/01/2026, 12:17 pm (Brisbane Time)**

## IMPLEMENTATION APPROACH

Given the complexity of implementing BOTH optimizations simultaneously, I'll break this into manageable phases:

### PHASE 1: Dynamic Suburb Spawning (IMPLEMENT FIRST)
**Time:** 20 minutes  
**Risk:** VERY LOW  
**Benefit:** 3-4× faster for all suburbs

**What it does:**
- Maintains max 5 concurrent suburb processes
- Spawns new suburb when one completes
- Processes all 52 suburbs efficiently

**Implementation:**
1. Modify existing `run_parallel_suburb_scrape.py`
2. Add suburb queue management
3. Add dynamic process spawning logic
4. Reduce startup stagger from 10s to 5s

### PHASE 2: Parallel Property Scraping (IMPLEMENT SECOND)
**Time:** 30 minutes  
**Risk:** LOW  
**Benefit:** 3× faster per suburb

**What it does:**
- Each suburb spawns 3 WebDriver instances
- Properties scraped in parallel (3 at a time)
- All write to same collection (safe due to unique index)

**Implementation:**
1. Create thread pool within each suburb process
2. Each thread gets its own WebDriver
3. Distribute property URLs across threads
4. Maintain MongoDB safety with unique indexes

## RECOMMENDED EXECUTION SEQUENCE

### Step 1: Test Dynamic Spawning Only (30 mins)
```bash
# Test with 3 small suburbs
python3 run_dynamic_suburb_scrape.py --test
```

**Test Suburbs:**
- Bilinga (small - ~10 properties)
- Tugun (small - ~15 properties)  
- Elanora (medium - ~30 properties)

**Success Criteria:**
- All 3 suburbs complete
- Dynamic spawning works (starts 3, spawns as they finish)
- MongoDB writes successful
- No errors

### Step 2: Add Parallel Property Scraping (if Step 1 succeeds)
```bash
# Test with same 3 suburbs but with parallel properties
python3 run_dynamic_parallel_scrape.py --test --parallel-properties 3
```

**Success Criteria:**
- 3× faster than Step 1
- No duplicate entries in MongoDB
- All properties scraped correctly

### Step 3: Full Production Run
```bash
# All 52 suburbs with both optimizations
python3 run_dynamic_parallel_scrape.py --all-suburbs --parallel-properties 3
```

**Expected Time:** 1-2 hours (vs 8+ hours sequential)

## SAFETY CONSIDERATIONS

### Why Parallel Properties is Safe:

1. **Unique Index on listing_url**
   - MongoDB prevents duplicates automatically
   - If two threads try to insert same property, one succeeds, one gets DuplicateKeyError
   - We catch and ignore DuplicateKeyError

2. **Separate WebDriver Instances**
   - Each thread has its own browser
   - No shared state between threads
   - Thread-safe by design

3. **MongoDB Connection Pooling**
   - Pool size = 50 connections
   - 5 suburbs × 3 threads = 15 concurrent connections
   - Well within safe limits

4. **Atomic Operations**
   - Each property insert/update is atomic
   - No partial writes
   - No data corruption risk

## FILES TO CREATE

1. `run_dynamic_suburb_scrape.py` - Dynamic spawning only
2. `run_dynamic_parallel_scrape.py` - Both optimizations
3. `test_dynamic_scrape.sh` - Test script for 3 suburbs
4. `run_all_suburbs.sh` - Production script for all 52

## CURRENT STATUS

- [x] Analysis complete
- [x] Collections cleared
- [ ] Create dynamic spawning script
- [ ] Test with 3 suburbs
- [ ] Add parallel property scraping
- [ ] Test with 3 suburbs again
- [ ] Run full 52-suburb scrape

## NEXT IMMEDIATE ACTION

Create `run_dynamic_suburb_scrape.py` with:
- Dynamic suburb queue management
- Max 5 concurrent processes
- Auto-spawn on completion
- Reduced startup stagger (5s)
- Test mode for 3 suburbs
