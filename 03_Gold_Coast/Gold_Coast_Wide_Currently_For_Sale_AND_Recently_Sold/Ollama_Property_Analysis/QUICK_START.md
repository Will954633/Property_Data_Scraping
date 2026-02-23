# Last Edit: 31/01/2026, Friday, 7:45 pm (Brisbane Time)

# Quick Start Guide - Ollama Property Analysis

## 🚀 Get Started in 5 Minutes

### Step 1: Install Ollama

```bash
# macOS
brew install ollama
```

### Step 2: Download the Vision Model

```bash
ollama pull llama3.2-vision:11b
```

This will download ~7GB. Wait for it to complete.

### Step 3: Start Ollama Server

```bash
ollama serve
```

Keep this terminal window open. Ollama will run on `http://localhost:11434`

### Step 4: Install Python Dependencies

Open a new terminal:

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && pip install -r requirements.txt
```

### Step 5: Run Test

```bash
cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 run_production.py
```

This will process 2 batches (up to 100 properties) as a test.

---

## ✅ What to Expect

### Initial Output
```
================================================================================
OLLAMA PROPERTY ANALYSIS - PRODUCTION RUN
================================================================================
Mode: TEST
Batch size: 50
Max batches: 2

================================================================================
INITIAL STATISTICS
================================================================================
Total documents in target suburbs: 450
Already processed: 0
Unprocessed: 450
Properties with water views: 0

By suburb:
  Robina: 120 properties
  Mudgeeraba: 45 properties
  Varsity Lakes: 95 properties
  Reedy Creek: 38 properties
  Burleigh Waters: 87 properties
  Merimac: 32 properties
  Warongary: 33 properties
```

### During Processing
```
Worker main_worker: Processing 123 Main St, Robina
Worker main_worker: Found 18 images
Downloading and encoding 18 images...
Successfully encoded 18 images
Sending request to Ollama (attempt 1/3)...
Ollama analysis complete for 123 Main St, Robina (142.3s)
Worker main_worker: Successfully processed 123 Main St, Robina (142.3s)
```

### Completion
```
================================================================================
PROCESSING COMPLETE
================================================================================
Total documents processed: 100
Successful: 98
Failed: 2
Total time: 14250.5s (237.5 minutes)
Average time per property: 145.4s
```

---

## 📊 Check Results

### View in MongoDB

```bash
mongosh
use Gold_Coast_Currently_For_Sale
db.properties.findOne({"ollama_analysis.processed": true})
```

### Check Logs

```bash
tail -f logs/ollama_processing.log
```

---

## 🎯 Next Steps

### Run Full Production

1. Edit `config.py`:
   ```python
   TEST_RUN = False
   MAX_BATCHES = 0
   ```

2. Run:
   ```bash
   cd /Users/projects/Documents/Property_Data_Scraping/03_Gold_Coast/Gold_Coast_Wide_Currently_For_Sale_AND_Recently_Sold/Ollama_Property_Analysis && python3 run_production.py
   ```

---

## ⚠️ Troubleshooting

### "Failed to connect to Ollama"
- Make sure `ollama serve` is running in another terminal

### "Model not found"
- Run: `ollama pull llama3.2-vision:11b`

### "Failed to connect to MongoDB"
- Start MongoDB: `brew services start mongodb-community`

### Slow Performance
- Normal! Ollama is slower than GPT but free
- Expected: 60-180 seconds per property
- Use GPU if available for faster processing

---

## 📖 Full Documentation

See [README.md](README.md) for complete documentation.

---

## 🎉 Success!

You're now analyzing properties with local AI! 

The system will:
- ✅ Extract detailed property features
- ✅ Rank images by marketing value
- ✅ Detect water views
- ✅ Score condition and quality
- ✅ Store everything in MongoDB

All without sending data to external APIs! 🔒
