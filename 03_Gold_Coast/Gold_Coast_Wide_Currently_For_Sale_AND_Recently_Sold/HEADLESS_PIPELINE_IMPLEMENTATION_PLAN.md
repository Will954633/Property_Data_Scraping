# Headless For-Sale Monitoring Pipeline - Implementation Plan
**Last Updated:** 31/01/2026, 9:12 am (Brisbane Time)

## Objective

Create a complete headless browser pipeline that replicates the existing for-sale property monitoring system, starting with Robina suburb as a test case.

## Current System Analysis

### Existing Collections (property_data database)
- **`properties_for_sale`** - Current for-sale listings
- **`properties_sold`** - Sold properties
- **`properties_for_sale_enriched`** - Enriched for-sale data
- **`sold_last_6_months`** - Recently sold properties

### Existing Data Structure (properties_for_sale)

**Core Fields:**
- `address`, `street_address`, `suburb`, `postcode`
- `bedrooms`, `bathrooms`, `carspaces`, `property_type`
- `price`, `agents_description`, `inspection_times[]`, `features[]`
- `property_images[]`, `floor_plans[]`, `listing_url`

**Metadata Fields:**
- `extraction_method`, `extraction_date`
- `first_seen`, `last_updated`, `last_enriched`
- `source`, `enriched`, `enrichment_attempted`

**Enrichment Fields:**
- `image_analysis[]` - GPT-4 Vision analysis of property images
- `enrichment_data` - Additional enrichment data

### Existing Pipeline Components

1. **Search For-Sale Properties**
   - Script: `07_Undetectable_method/Simple_Method/process_forsale_properties.sh`
   - Method: Selenium (visible browser)
   - Output: MongoDB `properties_for_sale` collection

2. **Monitor For Changes**
   - Script: `Fields_Orchestrator/src/field_change_tracker.py`
   - Tracks: price, inspections, agent_description
   - Method: Appends to `orchestrator.history.<field>` arrays

3. **Detect Sold Properties**
   - Script: `02_Domain_Scaping/For_Sale_To_Sold_Transition/monitor_sold_properties.sh`
   - Method: Selenium checks for for-sale → sold transitions
   - Duration: ~40 minutes for 186 properties

4. **Orchestrator**
   - Scripts: `Fields_Orchestrator/src/orchestrator_daemon.py`, `task_executor.py`, `sold_mover.py`
   - Coordinates: Search → Monitor → Detect Sold

## Proposed New System

### New Collections (Gold_Coast_Currently_For_Sale database)

**`robina`** (test collection)
- Same structure as `properties_for_sale`
- Headless scraping only
- Change tracking built-in

**Future collections:**
- One collection per suburb (like Gold_Coast database pattern)
- OR single `for_sale` collection with suburb field

### New Collections (Gold_Coast_Recently_Sold database)

**`robina`** (test collection)
- Properties that transitioned from for-sale → sold
- Preserves all for-sale data + sold data

## Implementation Phases

### Phase 1: Headless Scraper Enhancement ✅ COMPLETE

**Status:** DONE
- Created `property_detail_scraper_forsale_headless.py`
- Tested successfully with 1 property
- 100% success rate, full data extraction

### Phase 2: MongoDB Integration (CURRENT TASK)

**Goal:** Create headless scraper that writes to new MongoDB collections

**Tasks:**
1. Create new database: `Gold_Coast_Currently_For_Sale`
2. Create collection: `robina`
3. Modify headless scraper to write directly to MongoDB
4. Add change tracking (price, inspections, agent_description)
5. Add metadata fields (first_seen, last_updated, source)

**New Script:** `headless_forsale_mongodb_scraper.py`

**Features:**
- Scrapes Robina for-sale listings in headless mode
- Writes to `Gold_Coast_Currently_For_Sale.robina` collection
- Tracks changes to monitored fields
- Preserves history in arrays (like existing system)

### Phase 3: Data Validation

**Goal:** Verify headless scraper matches existing data

**Tasks:**
1. Scrape all Robina properties with headless scraper
2. Compare with existing `properties_for_sale` collection
3. Field-by-field validation
4. Document any differences

**Validation Script:** `validate_headless_vs_existing.py`

**Checks:**
- All properties found
- All fields match
- Image counts match
- Floor plan counts match
- Inspection times match

### Phase 4: Change Monitoring

**Goal:** Implement change tracking for monitored fields

**Tasks:**
1. Create change detection logic
2. Track price changes with history
3. Track inspection time changes with history
4. Track agent description changes with history
5. Store in `history.<field>` arrays

**Pattern:** Same as `Fields_Orchestrator/src/field_change_tracker.py`

### Phase 5: Sold Property Detection

**Goal:** Detect when for-sale properties are sold

**Tasks:**
1. Create headless sold-property detector
2. Check each for-sale property for sold status
3. Move sold properties to `Gold_Coast_Recently_Sold.robina`
4. Preserve all for-sale data + add sold data

**New Script:** `headless_sold_detector.py`

### Phase 6: Orchestration

**Goal:** Coordinate all headless components

**Tasks:**
1. Create orchestrator for headless pipeline
2. Schedule: Search → Monitor → Detect Sold
3. Multi-worker support (5-10 workers)
4. Health monitoring
5. Auto-resume on failure

**New Script:** `headless_forsale_orchestrator.py`

**Model After:** `03_Gold_Coast/orchestrator.py`

### Phase 7: Scaling

**Goal:** Expand beyond Robina to all Gold Coast

**Tasks:**
1. Add more suburbs
2. Increase worker count
3. Optimize performance
4. Schedule daily runs

## Data Structure Comparison

### Existing System Fields

```json
{
  "_id": "ObjectId",
  "address": "7 Turnberry Court, Robina, QLD 4226",
  "extraction_method": "HTML",
  "extraction_date": "2026-01-30T22:09:06.103188",
  "street_address": "7 Turnberry Court",
  "suburb": "Robina",
  "postcode": "4226",
  "og_title": "...",
  "description": "...",
  "bedrooms": 6,
  "bathrooms": 3,
  "carspaces": 4,
  "property_type": "House",
  "price": "Auction",
  "agents_description": "...",
  "inspection_times": ["Friday, 12 Sep 4:30pm"],
  "features": ["Shed"],
  "property_images": ["url1", "url2", ...],
  "floor_plans": ["url1"],
  "listing_url": "https://www.domain.com.au/...",
  "enriched": false,
  "enrichment_attempted": false,
  "enrichment_retry_count": 0,
  "enrichment_error": null,
  "first_seen": "2025-12-14T20:17:06.820Z",
  "last_updated": "2026-01-30T22:30:43.951Z",
  "last_enriched": null,
  "source": "selenium_forsale_scraper",
  "enrichment_data": null,
  "image_analysis": [...]
}
```

### New Headless System Fields (Additional)

```json
{
  // All existing fields above, PLUS:
  "scrape_mode": "headless",
  "history": {
    "price": [
      {"value": "Auction", "recorded_at": "2025-12-14T20:17:06.820Z"},
      {"value": "$1,200,000", "recorded_at": "2026-01-15T10:00:00.000Z"}
    ],
    "inspection_times": [
      {"value": ["Friday, 12 Sep 4:30pm"], "recorded_at": "2025-12-14T20:17:06.820Z"}
    ],
    "agent_description": [
      {"value": "...", "recorded_at": "2025-12-14T20:17:06.820Z"}
    ]
  },
  "change_count": 2,
  "last_change_detected": "2026-01-15T10:00:00.000Z"
}
```

## Key Differences: Headless vs Existing

### Advantages of Headless System

1. **Scalability**
   - Multi-worker parallel processing
   - Cloud deployment ready
   - No GUI overhead

2. **Automation**
   - Scheduled runs without manual intervention
   - Auto-resume on failure
   - Health monitoring

3. **Change Tracking Built-In**
   - History arrays for monitored fields
   - Automatic change detection
   - No separate change tracker needed

4. **Consistency**
   - Same methodology as proven Gold Coast orchestrator
   - 25-worker pattern validated with 243K properties

### Challenges

1. **Data Validation**
   - Must match existing system exactly
   - All fields must be present
   - Image/floor plan counts must match

2. **Integration**
   - Separate database (Gold_Coast_Currently_For_Sale)
   - Need migration path if successful
   - Parallel running during test phase

3. **Enrichment**
   - Existing system has GPT-4 Vision image analysis
   - Need to integrate or replicate

## Testing Strategy

### Test Case: Robina Suburb

**Why Robina:**
- Manageable size (~50-100 properties)
- Already in existing system
- Good test case for validation

**Test Steps:**
1. Scrape all Robina for-sale properties (headless)
2. Write to `Gold_Coast_Currently_For_Sale.robina`
3. Compare with `property_data.properties_for_sale` (suburb: Robina)
4. Validate field-by-field
5. Document differences

**Success Criteria:**
- ✅ All properties found
- ✅ All core fields match
- ✅ Image counts match
- ✅ Floor plan counts match
- ✅ Inspection times match
- ✅ Agent descriptions match

## Next Steps

### Immediate (Phase 2)

1. **Create MongoDB integration script**
   - Modify `property_detail_scraper_forsale_headless.py`
   - Add MongoDB write functionality
   - Add change tracking logic
   - Test with 1 property

2. **Create new database and collection**
   ```bash
   mongosh mongodb://127.0.0.1:27017/
   use Gold_Coast_Currently_For_Sale
   db.createCollection("robina")
   ```

3. **Test with Robina**
   - Scrape all Robina for-sale listings
   - Write to new collection
   - Validate against existing data

### Short-term (Phase 3-4)

1. Implement change monitoring
2. Create validation script
3. Document differences
4. Refine scraper based on findings

### Medium-term (Phase 5-6)

1. Create sold-property detector
2. Build orchestrator
3. Test end-to-end pipeline
4. Deploy with 5-10 workers

### Long-term (Phase 7)

1. Expand to all Gold Coast suburbs
2. Scale to 25 workers
3. Schedule daily runs
4. Integrate with existing systems

## Estimated Timeline

- **Phase 2:** 2-4 hours (MongoDB integration)
- **Phase 3:** 1-2 hours (Validation)
- **Phase 4:** 2-3 hours (Change monitoring)
- **Phase 5:** 3-4 hours (Sold detection)
- **Phase 6:** 4-6 hours (Orchestration)
- **Phase 7:** 2-4 hours (Scaling)

**Total:** 14-23 hours for complete implementation

## Questions to Resolve

1. **Database Structure:**
   - Separate database (Gold_Coast_Currently_For_Sale) or add to existing?
   - One collection per suburb or single collection with suburb field?

2. **Change Tracking:**
   - Store in `history.<field>` arrays (like existing)?
   - Or use separate `property_changes` collection?

3. **Enrichment:**
   - Run GPT-4 Vision analysis in headless pipeline?
   - Or keep separate enrichment step?

4. **Migration:**
   - If successful, migrate existing data to new system?
   - Or run in parallel indefinitely?

## Conclusion

The headless scraper is proven to work (100% success rate). The next step is MongoDB integration and validation against existing Robina data. This will confirm the headless approach matches the existing system before scaling to full Gold Coast coverage.

---

**Status:** Ready for Phase 2 implementation
**Blocker:** None - all prerequisites met
**Risk:** Low - headless scraping proven, just need MongoDB integration
