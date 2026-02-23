#!/usr/bin/env python3
"""
OCR Text Extractor
Extracts text from all screenshots using Tesseract OCR
"""

import os
import glob
from PIL import Image
import pytesseract
import json
from datetime import datetime

# Configuration
SCREENSHOT_DIR = "screenshots"
OUTPUT_DIR = "ocr_output"
RAW_TEXT_FILE = "raw_text_all.txt"
OCR_JSON_FILE = "ocr_data.json"

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_text_from_image(image_path):
    """
    Extract text from a single image using Tesseract OCR
    """
    try:
        # Open image
        img = Image.open(image_path)
        
        # Extract text
        text = pytesseract.image_to_string(img)
        
        return text
    except Exception as e:
        print(f"  ✗ Error processing {image_path}: {e}")
        return ""

def main():
    """Main function"""
    print("=" * 70)
    print("OCR TEXT EXTRACTOR")
    print("=" * 70)
    
    # Find all screenshot files
    screenshot_pattern = os.path.join(SCREENSHOT_DIR, "section_*.png")
    screenshot_files = sorted(glob.glob(screenshot_pattern))
    
    if not screenshot_files:
        print(f"\n✗ No screenshots found in {SCREENSHOT_DIR}/")
        print("  Run native_scroll_screenshot.py first to capture screenshots")
        return
    
    print(f"\n→ Found {len(screenshot_files)} screenshots")
    print(f"→ Extracting text using Tesseract OCR...\n")
    
    # Store all extracted data
    all_text = []
    ocr_data = {
        "extraction_date": datetime.now().isoformat(),
        "total_screenshots": len(screenshot_files),
        "screenshots": []
    }
    
    # Process each screenshot
    for i, screenshot_path in enumerate(screenshot_files, 1):
        filename = os.path.basename(screenshot_path)
        print(f"  [{i}/{len(screenshot_files)}] Processing {filename}...")
        
        # Extract text
        text = extract_text_from_image(screenshot_path)
        
        # Store in data structure
        screenshot_data = {
            "filename": filename,
            "text": text,
            "character_count": len(text),
            "line_count": len(text.split('\n'))
        }
        
        ocr_data["screenshots"].append(screenshot_data)
        all_text.append(f"\n{'='*70}\n")
        all_text.append(f"FILE: {filename}\n")
        all_text.append(f"{'='*70}\n")
        all_text.append(text)
        
        # Save individual text file
        text_filename = filename.replace('.png', '.txt')
        text_filepath = os.path.join(OUTPUT_DIR, text_filename)
        with open(text_filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    
    # Save combined text file
    combined_text_path = os.path.join(OUTPUT_DIR, RAW_TEXT_FILE)
    with open(combined_text_path, 'w', encoding='utf-8') as f:
        f.writelines(all_text)
    
    # Save JSON file
    json_path = os.path.join(OUTPUT_DIR, OCR_JSON_FILE)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_data, f, indent=2, ensure_ascii=False)
    
    # Summary
    total_chars = sum(len(s["text"]) for s in ocr_data["screenshots"])
    
    print("\n" + "=" * 70)
    print("✅ OCR EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Screenshots processed: {len(screenshot_files)}")
    print(f"Total characters extracted: {total_chars:,}")
    print(f"\nOutput files:")
    print(f"  • Combined text: {combined_text_path}")
    print(f"  • JSON data: {json_path}")
    print(f"  • Individual text files: {OUTPUT_DIR}/section_*.txt")
    print("\n→ Next step: Run data_parser.py to extract property data")
    print("=" * 70)

if __name__ == "__main__":
    main()
