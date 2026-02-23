# Testing GPT Enrichment on Scraped Data
# Last Edit: 13/02/2026, 2:43 PM (Thursday) — Brisbane Time
#
# Description: Guide for testing GPT-based enrichment approaches on actual scraped property data
#
# Edit History:
# - 13/02/2026 2:43 PM: Initial creation

---

## 📋 Overview

This test script validates our GPT-based enrichment approaches using **real scraped data** from the 12-month sold properties. It tests all 7 enrichment methods on a single property to verify accuracy and refine prompts.

---

## 🎯 What Gets Tested

The script tests these enrichment methods:

1. **Building Condition** - Assess property condition from photos
2. **Building Age** - Estimate year built from photos + description
3. **Corner Block** - Detect if property is on a corner
4. **Busy Road** - Determine if property is on a busy road
5. **Garage/Carport** - Identify parking type
6. **Outdoor Entertainment** - Score outdoor area quality (1-10)
7. **Renovation Status** - Assess renovation level

---

## 🚀 How to Run

### Prerequisites

1. **OpenAI API Key** must be set in `.env` file:
   ```bash
   # Already configured in: 01.1_Floor_Plan_Data/.env
   OPENAI_API_KEY=REDACTED_OPENAI_KEY...
   ```

2. **Python dependencies**:
   ```bash
   pip3 install openai python-dotenv
   ```

3. **Scraped data** must exist:
   ```bash
   # Test uses this file:
   02_Domain_Scaping/Sold_In_Last_12_Months_8_Suburbs/property_data/sold_scrape_robina_20260213_135837.json
   ```

### Run the Test

```bash
cd /Users/projects/Documents/Property_Data_Scraping/GapAnalysis_13thFeb && \
python3 test_enrichment_on_scraped_data.py
```

---

## 📊 What to Expect

### Test Property

The script will analyze the first property from the Robina scraped data:
- **Address**: 38 Nardoo Street, Robina, QLD 4226
- **Bedrooms**: 4
- **Bathrooms**: 2
- **Sale Price**: $1,585,000
- **Photos**: 72 images
- **Floor Plans**: 1 plan

### Processing Time

- **Per test**: ~10-15 seconds
- **Total**: ~2-3 minutes for all 7 tests
- **Cost**: ~$0.10-0.15 (7 GPT API calls)

### Output

**Console Output:**
```
================================================================================
GPT ENRICHMENT TESTING ON SCRAPED DATA
================================================================================

📂 Loading sample property from: ...
✅ Loaded property: 38 Nardoo Street, Robina, QLD 4226
   - Bedrooms: 4
   - Bathrooms: 2
   - Sale Price: $1,585,000
   - Photos: 72 images
   - Floor Plans: 1 plans

================================================================================
TEST 1: Building Condition Analysis
================================================================================

📊 Result:
{
  "overall_condition": "excellent",
  "confidence": "high",
  "observations": [
    "Modern finishes throughout",
    "Well-maintained exterior",
    "Quality presentation"
  ],
  "maintenance_level": "well-maintained",
  "evidence": "..."
}

... (continues for all 7 tests)

================================================================================
TESTING COMPLETE
================================================================================

✅ Results saved to: test_enrichment_results.json
```

**JSON Output File:**
```json
{
  "property_address": "38 Nardoo Street, Robina, QLD 4226",
  "tests": {
    "building_condition": { ... },
    "building_age": { ... },
    "corner_block": { ... },
    "busy_road": { ... },
    "garage_carport": { ... },
    "outdoor_entertainment": { ... },
    "renovation_status": { ... }
  }
}
```

---

## 🔍 Analyzing Results

### What to Look For

1. **Accuracy**: Do the results match what you can see in the photos/description?
2. **Confidence Levels**: Are confidence scores appropriate?
3. **Evidence Quality**: Does GPT provide good reasoning?
4. **Consistency**: Are results logical and consistent?

### Manual Verification

**Check the property listing:**
```
https://www.domain.com.au/38-nardoo-street-robina-qld-4226-2020534101
```

**Compare GPT results against:**
- Actual photos (72 images available)
- Property description
- Features list
- Your own assessment

### Expected Accuracy

Based on our planning:

| Test | Expected Accuracy | Confidence |
|------|------------------|------------|
| Building Condition | 90%+ | High |
| Building Age | 85%+ | Medium-High |
| Garage/Carport | 95%+ | High |
| Outdoor Entertainment | 90%+ | High |
| Renovation Status | 85%+ | High |
| Corner Block | 75%+ | Medium-High |
| Busy Road | 60-70% | Medium |

---

## 🔧 Refining Prompts

If results are inaccurate, you can refine prompts in the test script:

### Example: Improving Building Age Detection

**Current prompt:**
```python
prompt = """Estimate the building age of this property.

Analyze:
- Description mentions of "built in YYYY" or "circa YYYY"
- Architectural style visible in photos
...
"""
```

**Refined prompt (if needed):**
```python
prompt = """Estimate the building age of this property.

PRIORITY: Look for explicit mentions in the description first:
- "Built in YYYY"
- "Circa YYYY"
- "Constructed YYYY"

ONLY if not mentioned, analyze photos for:
- Architectural style (modern/contemporary/established)
...
"""
```

---

## 📈 Next Steps After Testing

### If Results Are Good (80%+ accuracy)

1. ✅ Prompts are validated
2. ✅ Ready to scale to all 2,400 properties
3. ✅ Proceed with full enrichment pipeline

### If Results Need Improvement

1. 🔧 Refine prompts based on errors
2. 🔧 Test on 2-3 more properties
3. 🔧 Iterate until 80%+ accuracy achieved

### Scaling Up

Once validated:

1. **Create production script** based on test script
2. **Add parallel processing** (10 workers)
3. **Add MongoDB integration** to save results
4. **Add progress tracking** and logging
5. **Run on all 2,400 properties**

---

## 🚧 Troubleshooting

### Error: "OPENAI_API_KEY not set"

**Solution:**
```bash
# Check .env file exists
ls -la /Users/projects/Documents/Property_Data_Scraping/01.1_Floor_Plan_Data/.env

# Verify API key is set
grep OPENAI_API_KEY /Users/projects/Documents/Property_Data_Scraping/01.1_Floor_Plan_Data/.env
```

### Error: "No module named 'openai'"

**Solution:**
```bash
pip3 install openai python-dotenv
```

### Error: "File not found"

**Solution:**
```bash
# Check scraped data exists
ls -la /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold_In_Last_12_Months_8_Suburbs/property_data/
```

### GPT Returns Empty Response

**Possible causes:**
- API rate limit hit
- Network timeout
- Model overload

**Solution:**
- Wait 30 seconds and retry
- Check OpenAI API status
- Reduce number of images (currently limited to 5)

---

## 💰 Cost Tracking

### Per Test Run

- **7 GPT API calls** (one per test)
- **~5 images per call** (limited for testing)
- **Cost per call**: ~$0.02
- **Total cost**: ~$0.14

### For Full Pipeline (2,400 properties)

- **7 tests × 2,400 properties** = 16,800 API calls
- **Estimated cost**: ~$336-420
- **With optimizations**: ~$250-300

---

## 📝 Test Results Template

After running the test, document your findings:

```markdown
## Test Results - [Date]

**Property**: 38 Nardoo Street, Robina, QLD 4226

### Accuracy Assessment

| Test | GPT Result | Actual | Accurate? | Notes |
|------|-----------|--------|-----------|-------|
| Building Condition | excellent | ✓ | ✅ | Matches photos |
| Building Age | 2018 | ? | ❓ | Need to verify |
| Corner Block | false | ✓ | ✅ | Correct |
| Busy Road | false | ✓ | ✅ | Nardoo St is quiet |
| Garage/Carport | garage, 2 spaces | ✓ | ✅ | Correct |
| Outdoor Entertainment | 8/10 | ✓ | ✅ | Has pool, alfresco |
| Renovation Status | fully-renovated | ✓ | ✅ | Modern finishes |

### Overall Accuracy: X/7 (XX%)

### Recommendations:
- [ ] Prompt refinements needed for: [test name]
- [ ] Ready to scale: Yes/No
- [ ] Additional testing needed: Yes/No
```

---

## 🔗 Related Documentation

- **Main Pipeline Plan**: `DATA_ENRICHMENT_PIPELINE_PLAN.md`
- **Busy Road/Corner Block Strategy**: `BUSY_ROAD_AND_CORNER_BLOCK_DETECTION_STRATEGY.md`
- **Gap Analysis**: `GAP_ANALYSIS_REPORT.md`
- **Existing GPT System**: `../01.1_Floor_Plan_Data/README.md`

---

## 🎯 Success Criteria

Before proceeding to full pipeline:

- [ ] Test runs without errors
- [ ] Results saved to JSON file
- [ ] Manual verification shows 80%+ accuracy
- [ ] Confidence levels are appropriate
- [ ] Evidence/reasoning is sound
- [ ] Ready to scale to 2,400 properties

---

*Test script created: 13/02/2026, 2:43 PM Brisbane Time*
*Ready to validate enrichment approaches on real data*
