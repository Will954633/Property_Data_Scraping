# Gold Coast Database Update Implementation Plan
**Created:** 30/01/2026, 7:35 pm (Brisbane Time)

## Goal
Create `update_gold_coast_database.py` that updates the Gold Coast database with fresh Domain data while preserving historical valuations and rental estimates.

## Simple Step-by-Step Plan

### MILESTONE 1: Create Basic Update Script Structure
- [ ] Step 1.1: Create empty update_gold_coast_database.py file
- [ ] Step 1.2: Add file header with description and timestamp
- [ ] Step 1.3: Add imports (copy from domain_scraper_multi_suburb_mongodb.py)
- [ ] Step 1.4: Create main class `GoldCoastDatabaseUpdater`
- [ ] Step 1.5: Add __init__ method with MongoDB connection

### MILESTONE 2: Add Core Scraping Functions
- [ ] Step 2.1: Copy `transform_timeline_event()` method from original scraper
- [ ] Step 2.2: Copy `setup_driver()` method from original scraper
- [ ] Step 2.3: Copy `build_domain_url()` method from original scraper
- [ ] Step 2.4: Copy `extract_property_data()` method from original scraper

### MILESTONE 3: Add History Preservation Logic
- [ ] Step 3.1: Create `has_valuation_changed()` helper method
- [ ] Step 3.2: Create `has_rental_estimate_changed()` helper method
- [ ] Step 3.3: Create `append_to_valuation_history()` method
- [ ] Step 3.4: Create `append_to_rental_history()` method

### MILESTONE 4: Add Update Logic
- [ ] Step 4.1: Create `get_all_scraped_addresses()` method to find properties with existing scraped_data
- [ ] Step 4.2: Create `update_property()` method that:
  - Scrapes fresh data
  - Replaces timeline and images
  - Appends to history if changed
  - Updates MongoDB
- [ ] Step 4.3: Create `run()` method with main loop

### MILESTONE 5: Add Configuration and Monitoring
- [ ] Step 5.1: Add worker configuration (WORKER_ID, TOTAL_WORKERS)
- [ ] Step 5.2: Add progress tracking and statistics
- [ ] Step 5.3: Add error handling and retry logic
- [ ] Step 5.4: Add logging output

### MILESTONE 6: Create Documentation
- [ ] Step 6.1: Create UPDATE_DATABASE_README.md with usage instructions
- [ ] Step 6.2: Add example run commands
- [ ] Step 6.3: Document the update strategy
- [ ] Step 6.4: Add troubleshooting section

### MILESTONE 7: Create Helper Scripts
- [ ] Step 7.1: Create monitor_update_progress.sh for tracking
- [ ] Step 7.2: Create deploy_update_workers.sh for multi-worker deployment
- [ ] Step 7.3: Add example .env configuration

## Implementation Order
1. Start with Milestone 1 (basic structure)
2. Then Milestone 2 (copy working code)
3. Then Milestone 3 (new history logic)
4. Then Milestone 4 (update logic)
5. Then Milestone 5 (configuration)
6. Finally Milestones 6-7 (documentation and helpers)

## Success Criteria
- Script can connect to MongoDB
- Script can scrape fresh data from Domain
- Script replaces timeline and images
- Script preserves valuation/rental history
- Script works with multi-worker deployment
- Documentation is clear and complete
