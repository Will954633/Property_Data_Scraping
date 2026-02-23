# Property Data Collection - Process Sequence Guide

**Last Updated:** 26/01/2026, 7:33 PM (Brisbane Time)

---

## Overview

This document outlines the complete sequence of processes required to collect and enrich property data for the `property_data` database. The system uses two main MongoDB collections:

1. **`properties_for_sale`** - Currently listed properties
2. **`sold_last_6_months`** - Properties sold in the last 6 months

---

## Data Fields Collected Per Collection

### `properties_for_sale` Collection
| Field | Source Process | Description |
|-------|---------------|-------------|
| `address`, `beds`, `baths`, `parking`, `price`, `description`, `images`, `floor_plans`, `features`, `listing_url` | 01_Scraping_For_Sale | Base property data from Domain.com.au |
| `image_analysis` | 02_GPT_Photo_Organiser | GPT Vision analysis of all photos (quality scores, room identification, floor plan detection) |
| `photo_tour_order` | 03_GPT_Photo_Reorder | Optimal photo sequence for virtual tours (1-15 photos) |
| `floor_plan_analysis` | 03.5_Floor_Plan_Data_Enrichment | Detailed floor plan extraction (room dimensions, areas, orientation) |

### `sold_last_6_months` Collection
| Field | Source Process | Description |
|-------|---------------|-------------|
| `address`, `beds`, `baths`, `parking`, `sold_price`, `sold_date`, `images`, `floor_plans` | 05_Sold_In_Last_Six_Months | Sold property data from Domain.com.au |
| `floor_plan_analysis` | 03.6_Floor_Plan_Data_Enrichment_Sold | Detailed floor plan extraction |

### `properties_sold` Collection (Transition)
| Field | Source Process | Description |
|-------|---------------|-------------|
| All fields from `properties_for_sale` + `sold_date`, `sold_price`, `detection_date` | 04_Sold_Properties_Monitor | Properties that transitioned from for-sale to sold |

---

## Recommended Process Sequence

### PART A: For-Sale Properties Pipeline

Run these processes in order to build the `properties_for_sale` collection:

#### Step 1: Scrape For-Sale Properties
**Process:** `01_Scraping_For_Sale_Properties`
**Location:** `07_Undetectable_method/Simple_Method/`

```bash
cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/Simple_Method && ./process_forsale_properties.sh
```

**What it does:**
- Extracts property URLs from Domain.com.au search pages
- Scrapes detailed property data (beds, baths, price, images, floor plans, etc.)
- Uploads to MongoDB `properties_for_sale` collection
- Removes duplicates

**Output:** Base property documents in `properties_for_sale`

---

#### Step 2: GPT Photo Analysis (Teleprompter)
**Process:** `02_GPT_Photo_Organiser_For_Teleprompter`
**Location:** `01_House_Plan_Data/`

```bash
cd /Users/projects/Documents/Property_Data_Scraping/01_House_Plan_Data && python src/main_parallel.py
```

**What it does:**
- Analyzes all property images using GPT-5-nano Vision API
- Identifies floor plans vs regular photos
- Scores image quality and usefulness
- Extracts property features from photos

**Output:** Adds `image_analysis` field to each property document

**Prerequisite:** Step 1 must be complete (properties must exist in DB)

---

#### Step 3: GPT Photo Reorder (Recorder)
**Process:** `03_GPT_Photo_Reorder_For_Recorder`
**Location:** `01_House_Plan_Data/`

```bash
cd /Users/projects/Documents/Property_Data_Scraping/01_House_Plan_Data && python src/photo_reorder_parallel.py
```

**What it does:**
- Creates optimal photo tour sequence (up to 15 photos)
- Orders photos: Front → Entrance → Kitchen → Living → Bedrooms → Laundry → Backyard → Pool
- Selects highest quality photos for each room type

**Output:** Adds `photo_tour_order` field with `reorder_position` (1-15) to each photo

**Prerequisite:** Step 2 must be complete (`image_analysis` must exist)

---

#### Step 4: Floor Plan Data Enrichment
**Process:** `03.5_Floor_Plan_Data_Enrichment_For_Listed_Properties`
**Location:** `01.1_Floor_Plan_Data/`

```bash
cd /Users/projects/Documents/Property_Data_Scraping/01.1_Floor_Plan_Data && python run_production.py
```

**What it does:**
- Analyzes floor plan images using GPT-5-nano Vision API
- Extracts room dimensions (length, width, area)
- Detects window orientation (compass rose/north arrow)
- Calculates total floor area and land area

**Output:** Adds `floor_plan_analysis` field with detailed room data

**Prerequisite:** Step 1 must be complete (properties with `floor_plans` array must exist)

---

### PART B: Sold Properties Pipeline

Run these processes to build the `sold_last_6_months` collection:

#### Step 5: Scrape Sold Properties (Last 6 Months)
**Process:** `05_Sold_In_Last_Six_Months`
**Location:** `02_Domain_Scaping/Sold_In_Last_6_Months/`

```bash
cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold_In_Last_6_Months && ./process_sold_properties.sh
```

**What it does:**
- Scrapes sold properties from Domain.com.au (5 suburbs)
- Extracts sale date and sale price
- Uses intelligent stop conditions (3 consecutive >6 months old OR 3 consecutive duplicates)
- Uploads to MongoDB `sold_last_6_months` collection

**Output:** Base property documents in `sold_last_6_months`

---

#### Step 6: Floor Plan Data Enrichment (Sold)
**Process:** `03.6_Floor_Plan_Data_Enrichment_For_Sold_Last_6_Months`
**Location:** `01.1_Floor_Plan_Data/`

```bash
cd /Users/projects/Documents/Property_Data_Scraping/01.1_Floor_Plan_Data && python run_production_sold.py
```

**What it does:**
- Same as Step 4 but targets `sold_last_6_months` collection
- Analyzes floor plans for sold properties

**Output:** Adds `floor_plan_analysis` field to sold property documents

**Prerequisite:** Step 5 must be complete

---

### PART C: Monitoring Pipeline (Ongoing)

Run this process periodically to track properties that sell:

#### Step 7: Monitor For-Sale → Sold Transitions
**Process:** `04_Sold_Properties_Monitor`
**Location:** `02_Domain_Scaping/For_Sale_To_Sold_Transition/`

```bash
cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/For_Sale_To_Sold_Transition && ./monitor_sold_properties.sh
```

**What it does:**
- Checks each property in `properties_for_sale` to see if it has sold
- Extracts sold date and sale price from Domain.com.au
- Moves sold properties from `properties_for_sale` to `properties_sold`
- Preserves all enrichment data (image_analysis, photo_tour_order, floor_plan_analysis)

**Output:** Moves sold properties to `properties_sold` collection

**Prerequisite:** Step 1 must be complete

---

## Complete Execution Order Summary

### Initial Data Collection (Run Once)
```
1. 01_Scraping_For_Sale_Properties     → properties_for_sale (base data)
2. 02_GPT_Photo_Organiser              → properties_for_sale + image_analysis
3. 03_GPT_Photo_Reorder                → properties_for_sale + photo_tour_order
4. 03.5_Floor_Plan_Data_Enrichment     → properties_for_sale + floor_plan_analysis
5. 05_Sold_In_Last_Six_Months          → sold_last_6_months (base data)
6. 03.6_Floor_Plan_Data_Enrichment_Sold → sold_last_6_months + floor_plan_analysis
```

### Ongoing Maintenance (Run Weekly/Daily)
```
7. 04_Sold_Properties_Monitor          → Move sold properties to properties_sold
   Then repeat 1-4 for new listings
   Then repeat 5-6 for new sold properties
```

---

## Quick Reference Commands

### For-Sale Properties (Full Pipeline)
```bash
# Step 1: Scrape for-sale properties
cd /Users/projects/Documents/Property_Data_Scraping/07_Undetectable_method/Simple_Method && ./process_forsale_properties.sh

# Step 2: GPT Photo Analysis
cd /Users/projects/Documents/Property_Data_Scraping/01_House_Plan_Data && python src/main_parallel.py

# Step 3: GPT Photo Reorder
cd /Users/projects/Documents/Property_Data_Scraping/01_House_Plan_Data && python src/photo_reorder_parallel.py

# Step 4: Floor Plan Enrichment
cd /Users/projects/Documents/Property_Data_Scraping/01.1_Floor_Plan_Data && python run_production.py
```

### Sold Properties (Full Pipeline)
```bash
# Step 5: Scrape sold properties
cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/Sold_In_Last_6_Months && ./process_sold_properties.sh

# Step 6: Floor Plan Enrichment (Sold)
cd /Users/projects/Documents/Property_Data_Scraping/01.1_Floor_Plan_Data && python run_production_sold.py
```

### Monitoring
```bash
# Step 7: Monitor for sold properties
cd /Users/projects/Documents/Property_Data_Scraping/02_Domain_Scaping/For_Sale_To_Sold_Transition && ./monitor_sold_properties.sh
```

---

## Process Dependencies Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FOR-SALE PROPERTIES PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐                                                   │
│  │ 01_Scraping_For_Sale │                                                   │
│  │ (Base Property Data) │                                                   │
│  └──────────┬───────────┘                                                   │
│             │                                                                │
│             ▼                                                                │
│  ┌──────────────────────┐    ┌──────────────────────────┐                   │
│  │ 02_GPT_Photo_Organiser│───▶│ 03_GPT_Photo_Reorder     │                   │
│  │ (image_analysis)      │    │ (photo_tour_order)       │                   │
│  └──────────────────────┘    └──────────────────────────┘                   │
│             │                                                                │
│             ▼                                                                │
│  ┌──────────────────────────┐                                               │
│  │ 03.5_Floor_Plan_Enrichment│                                               │
│  │ (floor_plan_analysis)     │                                               │
│  └──────────────────────────┘                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        SOLD PROPERTIES PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────┐                                               │
│  │ 05_Sold_In_Last_6_Months │                                               │
│  │ (Base Sold Data)         │                                               │
│  └──────────┬───────────────┘                                               │
│             │                                                                │
│             ▼                                                                │
│  ┌────────────────────────────────┐                                         │
│  │ 03.6_Floor_Plan_Enrichment_Sold│                                         │
│  │ (floor_plan_analysis)          │                                         │
│  └────────────────────────────────┘                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        MONITORING PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────┐    ┌──────────────────────┐                   │
│  │ properties_for_sale      │───▶│ 04_Sold_Monitor      │                   │
│  │ (with all enrichments)   │    │ (detect sold status) │                   │
│  └──────────────────────────┘    └──────────┬───────────┘                   │
│                                             │                                │
│                                             ▼                                │
│                                  ┌──────────────────────┐                   │
│                                  │ properties_sold      │                   │
│                                  │ (archived with data) │                   │
│                                  └──────────────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Notes

1. **GPT API Costs:** Steps 2, 3, 4, and 6 use GPT-5-nano Vision API which incurs costs per image analyzed.

2. **Processing Time:**
   - Step 1: ~20-30 minutes for 100+ properties
   - Step 2: ~30-60 seconds per property (parallel processing)
   - Step 3: ~15-30 seconds per property (parallel processing)
   - Step 4: ~30-60 seconds per property with floor plans
   - Step 5: ~20-30 minutes for 175-350 properties
   - Step 6: ~30-60 seconds per property with floor plans

3. **Suburbs Covered:**
   - Robina, QLD 4226
   - Mudgeeraba, QLD 4213
   - Varsity Lakes, QLD 4227
   - Reedy Creek, QLD 4227
   - Burleigh Waters, QLD 4220

4. **MongoDB Connection:** All scripts connect to `property_data` database on localhost:27017
