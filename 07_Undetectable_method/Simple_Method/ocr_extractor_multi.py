#!/usr/bin/env python3
"""
OCR Text Extractor - Multi-Session Support
Extracts text from all screenshots using Tesseract OCR
Supports processing multiple screenshot directories
"""

import os
import glob
import argparse
from PIL import Image
import pytesseract
import json
from datetime import datetime

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

def process_directory(screenshot_dir, output_dir):
    """
    Process all screenshots in a directory
    """
    print("=" * 70)
    print("OCR TEXT EXTRACTOR")
    print("=" * 70)
    print(f"Screenshot directory: {screenshot_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all screenshot files
    screenshot_pattern = os.path.join(screenshot_dir, "section_*.png")
    screenshot_files = sorted(glob.glob(screenshot_pattern))
    
    if not screenshot_files:
        print(f"\n✗ No screenshots found in {screenshot_dir}/")
        print("  Run the scraper first to capture screenshots")
        return False
    
    print(f"\n→ Found {len(screenshot_files)} screenshots")
    print(f"→ Extracting text using Tesseract OCR...\n")
    
    # Store all extracted data
    all_text = []
    ocr_data = {
        "extraction_date": datetime.now().isoformat(),
        "screenshot_directory": screenshot_dir,
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
        text_filepath = os.path.join(output_dir, text_filename)
        with open(text_filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    
    # Save combined text file
    combined_text_path = os.path.join(output_dir, "raw_text_all.txt")
    with open(combined_text_path, 'w', encoding='utf-8') as f:
        f.writelines(all_text)
    
    # Save JSON file
    json_path = os.path.join(output_dir, "ocr_data.json")
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
    print(f"  • Individual text files: {output_dir}/section_*.txt")
    print("=" * 70)
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Extract text from screenshots using OCR')
    parser.add_argument('--screenshot-dir', default='screenshots',
                        help='Directory containing screenshots (default: screenshots)')
    parser.add_argument('--output-dir', default='ocr_output',
                        help='Directory for OCR output (default: ocr_output)')
    parser.add_argument('--session', type=int,
                        help='Process specific session number (1, 2, or 3)')
    
    args = parser.parse_args()
    
    if args.session:
        # Process a specific session
        screenshot_dir = f"screenshots_session_{args.session}"
        output_dir = f"ocr_output_session_{args.session}"
        print(f"\n→ Processing Session {args.session}")
        success = process_directory(screenshot_dir, output_dir)
        if success:
            print(f"\n→ Next step: Run data parser on {output_dir}")
    else:
        # Process specified directories
        success = process_directory(args.screenshot_dir, args.output_dir)
        if success:
            print(f"\n→ Next step: Run data_parser.py to extract property data")

if __name__ == "__main__":
    main()
