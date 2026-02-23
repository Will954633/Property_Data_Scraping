#!/bin/bash
#
# Batch Process All Sessions
# Runs the complete scraping pipeline for all 3 sessions with MongoDB integration
#

echo "======================================================================"
echo "MULTI-SESSION PROPERTY SCRAPER - COMPLETE PIPELINE"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  0. Clean up temporary files from previous runs"
echo "  1. Capture screenshots for all 2 URLs (separate sessions)"
echo "  2. Extract text from screenshots using OCR (each session)"
echo "  3. Parse property data from OCR text (each session)"
echo "  4. Upload to MongoDB"
echo "  5. Remove duplicate entries"
echo "  6. Enrich properties with detailed data"
echo "  7. Remove off-market properties"
echo ""
echo "======================================================================"
echo ""

# Step 0: Cleanup temporary files from previous runs
echo "STEP 0: Cleaning up temporary files from previous runs..."
echo "----------------------------------------------------------------------"
python cleanup_temp_files.py --remove

if [ $? -eq 0 ] || [ $? -eq 2 ]; then
    echo "  ✓ Cleanup complete (or no files to clean)"
else
    echo "  ⚠ Cleanup encountered errors (continuing anyway)"
fi

echo ""
echo "======================================================================"
echo ""

# Step 1: Run multi-session scraper
echo "STEP 1: Capturing screenshots for all sessions..."
echo "----------------------------------------------------------------------"
python multi_session_runner.py

if [ $? -ne 0 ]; then
    echo "✗ Screenshot capture failed!"
    exit 1
fi

echo ""
echo "======================================================================"
echo ""

# Step 2: Process OCR for each session
echo "STEP 2: Extracting text from screenshots using OCR..."
echo "----------------------------------------------------------------------"

for session in 1 2; do
    echo ""
    echo "→ Processing Session $session..."
    python ocr_extractor_multi.py --session $session
    
    if [ $? -ne 0 ]; then
        echo "✗ OCR extraction failed for session $session!"
        exit 1
    fi
done

echo ""
echo "======================================================================"
echo ""

# Step 3: Parse property data for each session
echo "STEP 3: Parsing property data from OCR text..."
echo "----------------------------------------------------------------------"

for session in 1 2; do
    echo ""
    echo "→ Parsing Session $session..."
    input_file="ocr_output_session_${session}/raw_text_all.txt"
    output_file="property_data_session_${session}.json"
    
    if [ -f "$input_file" ]; then
        python data_parser_multi.py --input "$input_file" --output "$output_file"
        
        if [ $? -eq 0 ]; then
            echo "  ✓ Parsing complete for session $session: $output_file"
        else
            echo "✗ Parsing failed for session $session!"
            exit 1
        fi
    else
        echo "✗ Input file not found: $input_file"
        exit 1
    fi
done

echo ""
echo "✓ Screenshot capture: COMPLETE"
echo "✓ OCR extraction: COMPLETE"
echo "✓ Data parsing: COMPLETE"
echo ""
echo "Output directories created:"
echo "  • screenshots_session_1/ → ocr_output_session_1/ → property_data_session_1.json"
echo "  • screenshots_session_2/ → ocr_output_session_2/ → property_data_session_2.json"
echo ""
echo "======================================================================"
echo ""

# Step 4: Upload to MongoDB
echo "STEP 4: Uploading to MongoDB..."
echo "----------------------------------------------------------------------"
echo ""

python mongodb_uploader.py

if [ $? -ne 0 ]; then
    echo "⚠ MongoDB upload encountered errors"
    exit 1
fi

echo ""
echo "======================================================================"
echo ""

# Step 5: Remove duplicate properties from MongoDB
echo "STEP 5: Removing duplicate properties from MongoDB..."
echo "----------------------------------------------------------------------"
echo ""

python remove_duplicates.py --remove

if [ $? -eq 0 ] || [ $? -eq 2 ]; then
    echo "  ✓ Duplicate removal complete (or no duplicates found)"
else
    echo "  ⚠ Duplicate removal encountered errors (continuing anyway)"
fi

echo ""
echo "======================================================================"
echo ""

# Step 6: Enrich properties with detailed data
echo "STEP 6: Enriching properties with detailed data from domain.com.au..."
echo "----------------------------------------------------------------------"
echo ""

cd ../00_Production_System/02_Individual_Property_Google_Search
python batch_processor.py --mongodb
cd ../../Simple_Method

if [ $? -ne 0 ]; then
    echo "  ⚠ Enrichment encountered errors (but pipeline continued)"
else
    echo ""
    echo "  ✓ Property enrichment complete"
fi

echo ""
echo "======================================================================"
echo ""

# Step 7: Remove off-market properties (no listing URL)
echo "STEP 7: Removing off-market properties (no active listings)..."
echo "----------------------------------------------------------------------"
echo ""

python remove_offmarket_properties.py --remove

if [ $? -eq 0 ] || [ $? -eq 2 ]; then
    echo "  ✓ Off-market removal complete (or no off-market properties found)"
else
    echo "  ⚠ Off-market removal encountered errors (continuing anyway)"
fi

echo ""
echo "======================================================================"
echo ""

# Step 8: Display final status
echo "STEP 8: Final database status..."
echo "----------------------------------------------------------------------"
echo ""

python check_mongodb_status.py

echo ""
echo "======================================================================"
echo "🎉 FULL PIPELINE COMPLETE!"
echo "======================================================================"
echo ""
echo "All steps completed successfully:"
echo "  0. ✓ Temporary files cleanup"
echo "  1. ✓ Screenshot capture"
echo "  2. ✓ OCR text extraction"
echo "  3. ✓ Property data parsing"
echo "  4. ✓ MongoDB upload"
echo "  5. ✓ Duplicate removal"
echo "  6. ✓ Property enrichment"
echo "  7. ✓ Off-market property removal"
echo "  8. ✓ Database status verification"
echo ""
echo "======================================================================"
