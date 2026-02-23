#!/usr/bin/env python3
"""
Keyboard Maestro Screenshot Processor
Processes screenshots taken during KM macro execution and extracts property data
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
import pytesseract
from PIL import Image
import re
from km_ocr_extractor import PropertyExtractor
from km_mongodb_saver import MongoDBSaver

class ScreenshotProcessor:
    def __init__(self, suburb, base_dir=None):
        self.suburb = suburb.lower()
        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = Path(base_dir)
        
        self.screenshot_dir = self.base_dir / "screenshots" / self.suburb
        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        self.extractor = PropertyExtractor()
        self.saver = MongoDBSaver()
        
        # Set up logging
        self.log_file = self.log_dir / f"processing_{self.suburb}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')
    
    def process_all_screenshots(self):
        """Process all screenshots in the suburb directory"""
        if not self.screenshot_dir.exists():
            self.log(f"ERROR: Screenshot directory not found: {self.screenshot_dir}")
            return
        
        screenshots = sorted([f for f in self.screenshot_dir.glob("*.png")])
        
        if not screenshots:
            self.log(f"WARNING: No screenshots found in {self.screenshot_dir}")
            return
        
        self.log(f"Found {len(screenshots)} screenshots to process")
        
        processed_count = 0
        error_count = 0
        
        for screenshot_path in screenshots:
            try:
                self.log(f"Processing: {screenshot_path.name}")
                property_data = self.process_screenshot(screenshot_path)
                
                if property_data:
                    # Save to MongoDB
                    success = self.saver.save_property(property_data)
                    if success:
                        processed_count += 1
                        self.log(f"✓ Successfully processed and saved: {screenshot_path.name}")
                    else:
                        error_count += 1
                        self.log(f"✗ Failed to save to MongoDB: {screenshot_path.name}")
                else:
                    error_count += 1
                    self.log(f"✗ Failed to extract data from: {screenshot_path.name}")
            
            except Exception as e:
                error_count += 1
                self.log(f"✗ Error processing {screenshot_path.name}: {str(e)}")
        
        self.log(f"\n=== Processing Complete ===")
        self.log(f"Successfully processed: {processed_count}")
        self.log(f"Errors: {error_count}")
        self.log(f"Total: {len(screenshots)}")
    
    def process_screenshot(self, screenshot_path):
        """Process a single screenshot and extract property data"""
        try:
            # Open image
            img = Image.open(screenshot_path)
            
            # Perform OCR
            ocr_text = pytesseract.image_to_string(img)
            
            # Extract property data
            property_data = self.extractor.extract_property_info(ocr_text)
            
            # Add metadata
            property_data['suburb'] = self.suburb
            property_data['screenshot_file'] = screenshot_path.name
            property_data['scraped_at'] = datetime.now().isoformat()
            property_data['scraping_method'] = 'keyboard_maestro'
            
            # Save OCR text for debugging
            self.save_ocr_debug(screenshot_path.stem, ocr_text, property_data)
            
            return property_data
        
        except Exception as e:
            self.log(f"Error in process_screenshot: {str(e)}")
            return None
    
    def save_ocr_debug(self, filename, ocr_text, extracted_data):
        """Save OCR text and extracted data for debugging"""
        debug_dir = self.log_dir / "ocr_debug"
        debug_dir.mkdir(exist_ok=True)
        
        debug_file = debug_dir / f"{filename}_debug.json"
        
        debug_data = {
            'filename': filename,
            'ocr_text': ocr_text,
            'extracted_data': extracted_data,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(debug_file, 'w') as f:
            json.dump(debug_data, f, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Usage: python km_screenshot_processor.py <suburb>")
        print("Example: python km_screenshot_processor.py robina")
        sys.exit(1)
    
    suburb = sys.argv[1]
    
    processor = ScreenshotProcessor(suburb)
    processor.process_all_screenshots()

if __name__ == "__main__":
    main()
