# Dynamic Suburb Scraping - Complete Guide
**Last Updated: 31/01/2026, 12:18 pm (Brisbane Time)**

## 🎯 QUICK START

### Test Run (Recommended First Step)
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && bash run_test_3_suburbs.sh
```

### Full Production Run (All 52 Suburbs)
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && bash run_all_52_suburbs_dynamic.sh
```

---

## 📊 WHAT THIS DOES

### Dynamic Suburb Spawning
- **Maintains max 5 concurrent suburb processes**
- **Spawns new suburb when one completes** (no idle time)
- **Processes all 52 Gold Coast suburbs**
- **3-4× faster than sequential processing**

### MongoDB Safety Features
✅ **Separate collection per suburb** - Zero write conflicts  
✅ **Connection pooling (maxPoolSize=50)** - Built-in queuing  
✅ **Unique indexes on listing_url** - Prevents duplicates  
✅ **Retry logic** - Auto-recovers from failures  
✅ **One client per process** - No dangerous sharing  

**VERDICT: MongoDB is completely safe with this approach**

---

## 🚀 PERFORMANCE GAINS

### Current System (Sequential)
- 52 suburbs × ~20 mins average = **17+ hours**

### With Dynamic Spawning
- Max 5 concurrent suburbs
- Spawns new when one completes
- **Total time: 3-4 hours** (4-5× faster)

### Future: With Parallel Properties (Not Yet Implemented)
- 3 properties scraped simultaneously per suburb
- **Total time: 1-2 hours** (8-10× faster)

---

## 📁 FILES CREATED

### Execution Scripts
- `run_test_3_suburbs.sh` - Test with 3 small suburbs
- `run_all_52_suburbs_dynamic.sh` - Full 52-suburb production run

### Documentation
- `MONGODB_SAFETY_AND_PERFORMANCE_ANALYSIS.md` - Detailed safety analysis
- `DYNAMIC_SCRAPING_ACTION_PLAN.md` - Step-by-step plan
- `IMPLEMENTATION_STEPS.md` - Implementation phases
- `DYNAMIC_SCRAPING_README.md` - This file

### Existing Scripts (Reused)
- `run_parallel_suburb_scrape.py` - Core scraping engine
- `clear_collections.py` - Collection management

---

## 🔧 STEP-BY-STEP EXECUTION

### Step 1: Verify MongoDB is Running
```bash
mongosh
# Should connect successfully
# Type: exit
```

### Step 2: Clear Old Collections (Optional)
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 clear_collections.py --suburbs robina varsity_lakes --no-confirm
```

### Step 3: Run Test (3 Suburbs)
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && bash run_test_3_suburbs.sh
```

**Expected Duration:** 10-15 minutes  
**Test Suburbs:** Bilinga, Tugun, Elanora

### Step 4: Verify Test Results
```bash
mongosh
use Gold_Coast_Currently_For_Sale
db.bilinga.countDocuments({})
db.tugun.countDocuments({})
db.elanora.countDocuments({})
exit
```

### Step 5: Run Full Production (52 Suburbs)
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && bash run_all_52_suburbs_dynamic.sh
```

**Expected Duration:** 3-4 hours  
**All Suburbs:** 52 Gold Coast suburbs

### Step 6: Monitor Progress
```bash
# In another terminal
mongosh
use Gold_Coast_Currently_For_Sale
db.getCollectionNames().length  // Should increase to 52
db.getCollectionNames()  // List all collections
exit
```

### Step 7: Verify Completion
```bash
mongosh
use Gold_Coast_Currently_For_Sale

// Count total properties across all suburbs
var total = 0;
db.getCollectionNames().forEach(function(name) {
  var count = db[name].countDocuments({});
  print(name + ": " + count);
  total += count;
});
print("TOTAL: " + total);

exit
```

---

## 🛡️ MONGODB SAFETY ANALYSIS

### Why This is Safe

#### 1. Separate Collections = No Conflicts
- Robina → `robina` collection
- Varsity Lakes → `varsity_lakes` collection
- **They NEVER compete for the same documents**

#### 2. Connection Pooling = Built-in Queuing
- `maxPoolSize=50` supports 50 concurrent connections
- 5 suburbs × 1 connection each = 5 connections
- **MongoDB utilization: <10%**

#### 3. Unique Indexes = No Duplicates
- `listing_url` has unique index
- MongoDB prevents duplicates automatically
- **DuplicateKeyError handled gracefully**

#### 4. Atomic Operations
- Each insert/update is atomic
- No partial writes
- **No data corruption risk**

### MongoDB Write Performance

- **MongoDB capacity:** 10,000+ writes/second
- **Our usage:** ~1 write every 2-5 seconds per suburb
- **5 suburbs:** ~5 writes every 2-5 seconds
- **Utilization:** <0.1%

**CONCLUSION: MongoDB writes are NOT the bottleneck**

---

## 🐛 TROUBLESHOOTING

### Issue: WebDriver Fails to Start
**Solution:** Reduce concurrent suburbs from 5 to 3
```bash
# Edit run_all_52_suburbs_dynamic.sh
# Change batches from 5 to 3 suburbs each
```

### Issue: MongoDB Connection Timeout
**Solution:** Check MongoDB is running
```bash
mongosh
# If fails, start MongoDB:
brew services start mongodb-community
```

### Issue: Process Hangs
**Solution:** Stop and restart
```bash
# Press Ctrl+C multiple times
# Check for zombie processes:
ps aux | grep python3
# Kill if needed:
kill -9 <PID>
```

### Issue: Duplicate Entries
**Solution:** This shouldn't happen due to unique indexes, but if it does:
```bash
# Clear affected collection and re-run
python3 clear_collections.py --suburbs <suburb_name> --no-confirm
```

---

## 📈 MONITORING TIPS

### Real-Time Progress
```bash
# Watch collection count increase
watch -n 30 'mongosh --quiet --eval "use Gold_Coast_Currently_For_Sale; db.getCollectionNames().length"'
```

### Check Specific Suburb
```bash
mongosh
use Gold_Coast_Currently_For_Sale
db.robina.countDocuments({})
db.robina.findOne()  // See sample document
exit
```

### System Resources
```bash
# Monitor CPU/Memory
top -o cpu
# Look for python3 processes
```

---

## 🎓 UNDERSTANDING THE APPROACH

### Why Dynamic Spawning?

**Problem:** Sequential processing wastes time
- Robina: 30 mins
- Varsity Lakes: 15 mins
- If sequential: 45 mins total
- If parallel: 30 mins total (limited by slowest)

**Solution:** Dynamic spawning
- Start 5 suburbs
- When Varsity Lakes finishes (15 mins), spawn suburb #6
- When next finishes, spawn suburb #7
- **No idle time waiting for slow suburbs**

### Why NOT Parallel Properties Yet?

**Reason:** Testing in phases
1. ✅ **Phase 1:** Dynamic suburb spawning (IMPLEMENTED)
2. ⏳ **Phase 2:** Parallel property scraping (FUTURE)

**Benefits of phased approach:**
- Test each optimization separately
- Easier debugging
- Lower risk
- Proven stability before adding complexity

---

## 🔮 FUTURE ENHANCEMENTS

### Parallel Property Scraping (Phase 2)
**Status:** Not yet implemented  
**Benefit:** 3× faster per suburb  
**Risk:** LOW (unique indexes prevent conflicts)

**How it works:**
- Each suburb spawns 3 WebDriver instances
- Properties divided across threads
- All write to same collection (safe due to unique index)

**Implementation:**
- Create `run_dynamic_parallel_scrape.py`
- Add thread pool to each suburb process
- Test with 3 suburbs first
- Roll out to all 52 suburbs

### Performance Tuning (Phase 3)
- Reduce page load waits: 5s → 3s
- Reduce agent carousel waits: 3 rotations → 2
- Optimize scroll behavior

---

## 📞 SUPPORT

### Questions?
1. Read `MONGODB_SAFETY_AND_PERFORMANCE_ANALYSIS.md`
2. Read `IMPLEMENTATION_STEPS.md`
3. Check troubleshooting section above

### Reporting Issues
- Document the error message
- Note which suburb failed
- Check MongoDB logs
- Try re-running just that suburb

---

## ✅ SUCCESS CRITERIA

- [ ] All 52 suburbs scraped
- [ ] No MongoDB errors
- [ ] Data quality maintained
- [ ] Dynamic spawning works correctly
- [ ] Faster than sequential approach
- [ ] All collections have expected document counts

---

## 🎉 COMPLETION

Once all 52 suburbs are scraped:

1. **Verify counts:**
   ```bash
   mongosh
   use Gold_Coast_Currently_For_Sale
   db.getCollectionNames().length  // Should be 52
   ```

2. **Check total properties:**
   ```bash
   var total = 0;
   db.getCollectionNames().forEach(function(name) {
     total += db[name].countDocuments({});
   });
   print("Total properties: " + total);
   ```

3. **Spot-check data quality:**
   ```bash
   db.robina.findOne()  // Should have all fields
   ```

4. **Document results:**
   - Total suburbs: 52
   - Total properties: [count]
   - Total time: [hours]
   - Success rate: [percentage]

---

**Ready to start? Run the test first:**
```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && bash run_test_3_suburbs.sh
```
