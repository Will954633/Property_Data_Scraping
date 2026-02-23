# Agent & Agency Extraction Update

**Last Updated:** 31/01/2026, 9:44 am (Brisbane Time)

## Overview

Updated the scraping system to properly extract **Agency Name** and **Agent Names** from Domain.com.au listing pages.

## Changes Made

### 1. Enhanced `html_parser.py`

**File:** `07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/html_parser.py`

**Function Updated:** `extract_agent_info(soup)`

#### New Features:
- **Priority 1:** Uses `data-testid` attributes for reliable extraction
  - `listing-details__agent-agency-name` for agency
  - `listing-details__agent-card` and `listing-details__agent-name` for agents
  
- **Priority 2:** Fallback to agent profile links (`/real-estate-agent/`)
  
- **Priority 3:** Fallback to class-based selectors for agency

#### Data Structure:
The function now returns:
```python
{
    'agency': 'Ray White',                    # Agency name
    'agent_names': ['Ricky Agent', 'Shaquille Gafa'],  # Array of agent names
    'agent_name': 'Ricky Agent, Shaquille Gafa'        # Comma-separated string
}
```

### 2. Automatic Integration

The changes are **automatically integrated** into the existing scraping pipeline:

- ✅ `headless_forsale_mongodb_scraper.py` already imports and uses `html_parser.py`
- ✅ The `parse_listing_html()` function calls `extract_agent_info()`
- ✅ All extracted data (including agency/agents) is saved to MongoDB
- ✅ No changes needed to the main scraper script

### 3. Test Script Created

**File:** `test_agent_extraction.py`

A comprehensive test script to verify agent/agency extraction:
- Tests with real Domain.com.au URLs
- Validates against expected values
- Saves results to JSON for review
- Provides detailed output

## How to Use

### Running the Scraper (Normal Operation)

The scraper will now automatically extract agency and agent information:

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 headless_forsale_mongodb_scraper.py --suburb robina --input test_robina_single.json --limit 1
```

### Testing Agent Extraction

To specifically test the agent extraction feature:

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold && python3 test_agent_extraction.py
```

You'll be prompted to enter a Domain.com.au URL, or it will use the first URL from `test_robina_single.json`.

## MongoDB Data Structure

Properties in the database will now include:

```json
{
  "listing_url": "https://www.domain.com.au/...",
  "address": "7 Turnberry Court, Robina QLD 4226",
  "agency": "Ray White",
  "agent_names": ["Ricky Agent", "Shaquille Gafa"],
  "agent_name": "Ricky Agent, Shaquille Gafa",
  "bedrooms": 4,
  "bathrooms": 2,
  "price": "$850,000",
  ...
}
```

## Example: 7 Turnberry Court, Robina

For the property mentioned in your request:
- **Address:** 7 Turnberry Court, Robina QLD 4226
- **Expected Agency:** Ray White
- **Expected Agents:** Ricky Agent, Shaquille Gafa

The scraper will now extract this information automatically.

## Backward Compatibility

- ✅ Existing fields remain unchanged
- ✅ New fields are added alongside existing data
- ✅ Both `agent_name` (string) and `agent_names` (array) are provided
- ✅ Works with single or multiple agents per listing

## Validation

The extraction uses multiple fallback strategies to ensure reliability:

1. **Primary:** `data-testid` attributes (most reliable)
2. **Secondary:** Agent profile links
3. **Tertiary:** Class-based selectors

This ensures agent/agency information is captured even if Domain.com.au changes their HTML structure.

## Next Steps

1. **Test with real property:** Run the test script with the actual URL for 7 Turnberry Court, Robina
2. **Verify MongoDB storage:** Check that the data is properly saved to the database
3. **Run full scrape:** Use the scraper on multiple properties to verify consistency

## Files Modified

1. `07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search/html_parser.py`
   - Enhanced `extract_agent_info()` function
   - Added documentation header

## Files Created

1. `03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/test_agent_extraction.py`
   - Test script for agent extraction
   
2. `03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/AGENT_EXTRACTION_UPDATE.md`
   - This documentation file

## Support for Multiple Agents

The system now properly handles listings with multiple agents:
- Extracts all agent names from the listing
- Stores them as an array (`agent_names`)
- Also provides a comma-separated string (`agent_name`) for backward compatibility

## Notes

- The scraper uses headless Chrome to load pages
- Agent information is extracted from the HTML after page load
- The extraction is non-blocking and won't fail if agent info is missing
- All existing functionality remains intact
