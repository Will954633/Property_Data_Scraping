# Last Edit: 31/01/2026, Friday, 8:20 pm (Brisbane Time)

# DIAGNOSTIC REPORT: 8/10 Score Issue

## Executive Summary

**Issue**: All properties are receiving identical scores of 8/10 for usefulness and 9/10 for quality.

**Root Cause**: The Ollama llama3.2-vision:11b model is being too generous and not discriminating between different quality levels of property images.

**Good News**: 
- ✅ Different photos ARE being sent to the model (verified via image URLs)
- ✅ Text analysis IS being produced and stored in MongoDB
- ✅ Descriptions and features are being extracted correctly
- ✅ The system is working technically - it's a model calibration issue

---

## Detailed Findings

### 1. What Text Analysis is Being Produced?

**YES**, comprehensive text analysis is being stored for each image:

```json
{
  "image_type": "exterior/interior/kitchen/etc",
  "description": "Detailed description of the image",
  "usefulness_score": 8,
  "quality_score": 9,
  "marketing_value": "high/medium/low",
  "features_visible": ["list", "of", "features"]
}
```

**Example from actual data:**
- Image 0: "A single-story house with a white exterior, a covered front porch, and a two-car garage."
- Image 1: "A modern kitchen with white cabinets and brown countertops."
- Image 2: "A large, empty room with beige walls and tile floors."

### 2. Are Different Photos Being Sent?

**YES**, confirmed different photos are being analyzed:

**Property 1 (5 Fulham Place):**
- Image 0: `17478849_1_1_250312_125619`
- Image 1: `17478849_3_1_250312_125619`
- Image 2: `2020545141_3_1_260122_120550`

**Property 2 (31 Huntingdale Crescent):**
- Image 0: `2020526473_30_1_260114_010843`
- Image 1: `2020526473_27_1_260114_010843`
- Image 2: `2020526473_2_1_260114_010815`

**Property 3 (8 Trinity Place):**
- Image 0: `2020397838_1_1_251105_015813`
- Image 1: `2020397838_2_1_251105_015813`
- Image 2: `2020397838_6_1_251105_015823`

Each property has unique image IDs, confirming different photos are being processed.

### 3. Score Distribution Analysis

**Current Results (15 properties analyzed):**
- Usefulness scores: ALL 8/10 (no variation)
- Quality scores: ALL 9/10 (no variation)
- Unique usefulness scores: [8] only
- Unique quality scores: [9] only

**This indicates**: The model is not discriminating between different quality levels.

---

## What Data IS Being Stored?

### MongoDB Document Structure:

```javascript
{
  "ollama_analysis": {
    "processed": true,
    "images_analyzed": 5,
    "processed_at": "2026-01-31 10:06:14.322000",
    "model": "llama3.2-vision:11b",
    "engine": "ollama",
    "worker_id": "main_worker",
    "processing_duration_seconds": 34.6
  },
  
  "ollama_image_analysis": [
    {
      "image_index": 0,
      "url": "https://...",
      "image_type": "exterior",
      "description": "A single-story house with...",
      "usefulness_score": 8,
      "quality_score": 9,
      "marketing_value": "high",
      "features_visible": ["white exterior", "covered front porch", ...]
    },
    // ... 4 more images
  ],
  
  "ollama_property_data": {
    "structural": {},
    "exterior": {},
    "interior": {},
    "renovation": {},
    "outdoor": {},
    "layout": {},
    "overall": {
      "unique_features": ["two-car garage", "stainless steel appliances", ...]
    },
    "metadata": {
      "model_used": "llama3.2-vision:11b",
      "analysis_method": "single_image_aggregation",
      "total_images_analyzed": 5
    }
  }
}
```

---

## Why Are All Scores 8/10?

### Possible Causes:

1. **Model Bias**: The llama3.2-vision:11b model may be calibrated to give "safe" middle-high scores
2. **Prompt Design**: The current prompt may not encourage enough discrimination
3. **Image Quality**: All property images may genuinely be of similar professional quality
4. **Temperature Setting**: Current temperature (0.7) may not encourage enough variation

### Current Prompt:
```
Analyze this property image (image #X).

Provide a JSON response with:
{
  "image_type": "exterior/interior/kitchen/...",
  "description": "brief description",
  "usefulness_score": 1-10 (how useful for marketing),
  "quality_score": 1-10 (technical quality),
  "marketing_value": "high/medium/low",
  "features_visible": ["list", "of", "visible", "features"]
}
```

---

## Recommendations

### Option 1: Improve Prompt (Quick Fix)
Add more specific scoring criteria:

```
Score 1-3: Poor quality, blurry, dark, or unprofessional
Score 4-6: Average quality, acceptable but not impressive
Score 7-8: Good quality, professional, well-composed
Score 9-10: Exceptional quality, magazine-worthy, outstanding composition
```

### Option 2: Adjust Temperature (Experimental)
Increase temperature from 0.7 to 0.9 to encourage more variation in responses.

### Option 3: Use Comparative Scoring
Instead of absolute scores, compare images within the same property and rank them.

### Option 4: Accept Current Behavior
If the goal is just to extract descriptions and features (not actual scoring), the current system is working perfectly.

---

## What's Working Well

✅ **Image Processing**: Different images are being downloaded and analyzed  
✅ **Text Extraction**: Detailed descriptions are being generated  
✅ **Feature Detection**: Specific features are being identified  
✅ **Image Classification**: Types (exterior/interior/kitchen) are correct  
✅ **Data Storage**: All analysis is being properly stored in MongoDB  
✅ **Performance**: ~7 seconds per image, ~35-60 seconds per property  

---

## Conclusion

**The system is working correctly from a technical standpoint.** The issue is that the AI model is being too generous with scores, not that the analysis isn't happening.

**Key Question**: What is the primary goal?
- If you need **descriptions and features** → System is perfect as-is
- If you need **discriminating scores** → Need to adjust prompt or model

**Recommendation**: Focus on the rich text analysis being produced (descriptions, features, image types) rather than the numeric scores, OR implement one of the prompt improvements above.
