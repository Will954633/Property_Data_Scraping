#!/usr/bin/env python3
"""
Mouse Action Replayer - Replays recorded mouse/keyboard actions

This system:
1. Loads recorded actions from JSON
2. Replays them with timing variations (±15%)
3. Takes screenshots at key moments (property detail pages)
4. Uses OCR to extract property data from screenshots
5. Saves structured data to MongoDB
"""

import argparse
import asyncio
import sys
import json
import random
import time
from pathlib import Path
from datetime import datetime
import pyautogui
import mss
from PIL import Image
import pytesseract
import re

sys.path.append(str(Path(__file__).parent.parent))

# Import MongoDB saver (reusing from existing code)
try:
    from mongodb_saver import MongoDBSaver
except ImportError:
    print("⚠️  MongoDB saver not found - data won't be saved to database")
    MongoDBSaver = None


class MouseActionReplayer:
    """Replays recorded mouse/keyboard actions and extracts data"""
    
    def __init__(self, suburb, session_number):
        self.suburb = suburb.lower()
        self.session_number = session_number
        
        # Paths
        self.recordings_dir = Path(__file__).parent.parent / "2_recordings"
        self.data_dir = Path(__file__).parent.parent / "4_data"
        self.screenshots_dir = self.data_dir / "screenshots"
        
        # Create directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "extraction_logs").mkdir(exist_ok=True)
        
        # Recording file
        self.action_file = self.recordings_dir / self.suburb / f"session_{session_number:02d}_actions.json"
        
        # Session ID
        self.session_id = f"{self.suburb}_session_{session_number:02d}"
        
        # Results
        self.properties_extracted = []
        self.screenshot_count = 0
        
        # Settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def load_actions(self):
        """Load recorded actions from JSON"""
        if not self.action_file.exists():
            raise FileNotFoundError(f"Recording not found: {self.action_file}")
        
        with open(self.action_file, 'r') as f:
            data = json.load(f)
        
        return data
    
    def replay_actions(self, speed_multiplier=1.0, take_screenshots=True):
        """
        Replay recorded actions
        
        Args:
            speed_multiplier: Speed adjustment (1.0 = normal, 0.5 = half speed)
            take_screenshots: Whether to take screenshots during replay
        """
        print("\n" + "="*70)
        print(f"  MOUSE ACTION REPLAYER - {self.suburb.upper()} - Session {self.session_number}")
        print("="*70)
        
        # Load actions
        recording_data = self.load_actions()
        actions = recording_data['actions']
        
        print(f"\n📂 Loaded recording:")
        print(f"   Actions: {len(actions)}")
        print(f"   Duration: {recording_data['duration']:.1f}s")
        print(f"   Recorded: {recording_data['recorded_at']}")
        print(f"   Screen: {recording_data['screen_resolution']}")
        
        # Verify screen resolution matches
        current_res = pyautogui.size()
        recorded_res = tuple(recording_data['screen_resolution'])
        if current_res != recorded_res:
            print(f"\n⚠️  WARNING: Screen resolution mismatch!")
            print(f"   Recorded: {recorded_res}")
            print(f"   Current: {current_res}")
            print(f"   Actions may not click in the right places!")
            
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        
        print(f"\n🔄 Replaying actions...")
        print(f"   Speed multiplier: {speed_multiplier}x")
        print(f"   Screenshots: {'Enabled' if take_screenshots else 'Disabled'}")
        print("   Press Ctrl+C to stop\n")
        
        input("Press ENTER to start replay...")
        
        # Activate Chrome browser first
        print("\n🌐 Activating Chrome browser...")
        try:
            import subprocess
            # Use AppleScript to activate Chrome
            subprocess.run(['osascript', '-e', 'tell application "Google Chrome" to activate'], check=True)
            time.sleep(2)  # Wait for Chrome to come to front
            print("   ✓ Chrome activated")
        except Exception as e:
            print(f"   ⚠️  Could not activate Chrome: {e}")
            print("   Please manually click on Chrome and press ENTER")
            input()
        
        # Give user time to prepare
        print("\n⏱️  Starting replay in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n🎬 REPLAY STARTING!\n")
        
        prev_timestamp = 0
        click_count = 0
        last_screenshot_time = 0
        
        try:
            for i, action in enumerate(actions):
                # Calculate delay with variation
                time_delta = (action['timestamp'] - prev_timestamp) * speed_multiplier
                # Add ±15% variation
                time_delta = time_delta * random.uniform(0.85, 1.15)
                
                # Clamp to reasonable values
                time_delta = max(0, min(time_delta, 5))
                
                if time_delta > 0:
                    time.sleep(time_delta)
                
                # Execute action
                action_type = action['type']
                
                if action_type == 'mouse_move':
                    pyautogui.moveTo(action['x'], action['y'], duration=0.2)
                
                elif action_type == 'mouse_click':
                    print(f"   🖱️  Click {click_count + 1} at ({action['x']:.0f}, {action['y']:.0f})")
                    pyautogui.click(action['x'], action['y'])
                    click_count += 1
                    
                    # Take screenshot after click (property page might load)
                    if take_screenshots:
                        time.sleep(2)  # Wait for page load
                        self._take_screenshot(f"click_{click_count}")
                        last_screenshot_time = time.time()
                
                elif action_type == 'mouse_scroll':
                    pyautogui.scroll(int(action['dy'] * 10))
                    
                    # Periodically take screenshots while scrolling
                    if take_screenshots and (time.time() - last_screenshot_time) > 5:
                        self._take_screenshot(f"scroll_{i}")
                        last_screenshot_time = time.time()
                
                elif action_type == 'key_press':
                    try:
                        # Handle special keys
                        key = action['key']
                        if key.startswith('Key.'):
                            key_name = key.replace('Key.', '')
                            pyautogui.press(key_name)
                        else:
                            pyautogui.write(key)
                    except Exception as e:
                        print(f"   ⚠️  Key press error: {e}")
                
                prev_timestamp = action['timestamp']
                
                # Progress update every 100 actions
                if (i + 1) % 100 == 0:
                    progress = (i + 1) / len(actions) * 100
                    print(f"   Progress: {progress:.1f}% ({i+1}/{len(actions)} actions)")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Replay interrupted by user")
            return False
        
        print(f"\n✅ Replay complete!")
        print(f"   Clicks executed: {click_count}")
        print(f"   Screenshots taken: {self.screenshot_count}")
        
        # Now extract data from screenshots
        if take_screenshots and self.screenshot_count > 0:
            print(f"\n📊 Extracting data from screenshots...")
            self._extract_data_from_screenshots()
        
        return True
    
    def _take_screenshot(self, label):
        """Take a screenshot of the current screen"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.session_id}_{label}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        
        # Take screenshot using mss (faster than pyautogui)
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            
            # Save as PNG
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
        
        self.screenshot_count += 1
        print(f"   📸 Screenshot saved: {filename}")
        
        return filepath
    
    def _extract_data_from_screenshots(self):
        """Extract property data from all screenshots using OCR"""
        screenshots = sorted(self.screenshots_dir.glob(f"{self.session_id}_*.png"))
        
        if not screenshots:
            print("   ⚠️  No screenshots found")
            return
        
        print(f"   Found {len(screenshots)} screenshots")
        print(f"   Processing with OCR...")
        
        # Connect to MongoDB if available
        saver = MongoDBSaver() if MongoDBSaver else None
        
        for i, screenshot_path in enumerate(screenshots, 1):
            print(f"\n   Screenshot {i}/{len(screenshots)}: {screenshot_path.name}")
            
            try:
                # Extract text from screenshot
                text = self._ocr_screenshot(screenshot_path)
                
                # Parse property data from text
                property_data = self._parse_property_data(text, screenshot_path.name)
                
                if property_data:
                    # Add metadata
                    property_data['suburb'] = self.suburb
                    property_data['session_used'] = self.session_id
                    property_data['scraped_at'] = datetime.now().isoformat()
                    property_data['screenshot_file'] = screenshot_path.name
                    
                    # Save to MongoDB
                    if saver:
                        saver.save_property(property_data)
                    
                    self.properties_extracted.append(property_data)
                    
                    print(f"   ✓ Data extracted: {property_data.get('address', {}).get('full', 'Unknown')}")
                else:
                    print(f"   ⚠️  No property data found in screenshot")
            
            except Exception as e:
                print(f"   ✗ Error processing screenshot: {e}")
        
        if saver:
            saver.close()
        
        # Summary
        print(f"\n📊 Extraction Summary:")
        print(f"   Screenshots processed: {len(screenshots)}")
        print(f"   Properties extracted: {len(self.properties_extracted)}")
    
    def _ocr_screenshot(self, image_path):
        """Extract text from screenshot using Tesseract OCR"""
        # Load image
        image = Image.open(image_path)
        
        # Convert to grayscale for better OCR
        image = image.convert('L')
        
        # Extract text
        text = pytesseract.image_to_string(image, lang='eng')
        
        return text
    
    def _parse_property_data(self, text, screenshot_name):
        """
        Parse property data from OCR text
        
        Args:
            text: OCR extracted text
            screenshot_name: Name of screenshot file
            
        Returns:
            Dict: Property data or None
        """
        # Check if this looks like a property page
        if not any(keyword in text.lower() for keyword in ['bed', 'bath', '$', 'qld', 'property']):
            return None
        
        property_data = {
            'property_url': f"screenshot_{screenshot_name}",  # Placeholder
            'raw_ocr_text': text[:1000]  # First 1000 chars for debugging
        }
        
        # Extract address (usually contains QLD and postcode)
        address_match = re.search(r'([^\n]+(?:QLD|Queensland)\s+\d{4})', text, re.IGNORECASE)
        if address_match:
            property_data['address'] = {
                'full': address_match.group(1).strip(),
                'suburb': self.suburb.title(),
                'state': 'QLD'
            }
        else:
            property_data['address'] = {
              'full': None,
                'suburb': self.suburb.title(),
                'state': 'QLD'
            }
        
        # Extract price
        price_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:M|million)?',
            r'(\d{1,3}(?:,\d{3})+)',
        ]
        
        for pattern in price_patterns:
            price_match = re.search(pattern, text)
            if price_match:
                price_str = price_match.group(0)
                property_data['price'] = {
                    'display': price_str,
                    'value': None  # Could parse to int
                }
                break
        
        if 'price' not in property_data:
            property_data['price'] = {'display': None, 'value': None}
        
        # Extract features
        features = {}
        
        bed_match = re.search(r'(\d+)\s*(?:bed|bedroom|br)', text, re.IGNORECASE)
        if bed_match:
            features['bedrooms'] = int(bed_match.group(1))
        
        bath_match = re.search(r'(\d+)\s*(?:bath|bathroom)', text, re.IGNORECASE)
        if bath_match:
            features['bathrooms'] = int(bath_match.group(1))
        
        car_match = re.search(r'(\d+)\s*(?:car|parking|garage)', text, re.IGNORECASE)
        if car_match:
            features['parking'] = int(car_match.group(1))
        
        property_data['features'] = features
        
        # Extract property type
        if 'house' in text.lower() and 'townhouse' not in text.lower():
            property_data['property_type'] = 'House'
        elif 'townhouse' in text.lower():
            property_data['property_type'] = 'Townhouse'
        elif 'unit' in text.lower() or 'apartment' in text.lower():
            property_data['property_type'] = 'Unit'
        else:
            property_data['property_type'] = None
        
        return property_data


def main():
    parser = argparse.ArgumentParser(
        description="Replay recorded mouse/keyboard actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mouse_action_replayer.py --suburb robina --session 1
  python mouse_action_replayer.py --suburb mudgeeraba --session 2 --speed 0.5

This will replay the recorded actions, take screenshots,
extract data using OCR, and save to MongoDB.
        """
    )
    
    parser.add_argument(
        '--suburb',
        type=str,
        required=True,
        help='Suburb name (e.g., robina, mudgeeraba)'
    )
    
    parser.add_argument(
        '--session',
        type=int,
        required=True,
        help='Session number (1, 2, 3, etc.)'
    )
    
    parser.add_argument(
        '--speed',
        type=float,
        default=1.0,
        help='Speed multiplier (1.0 = normal, 0.5 = half speed, 2.0 = double speed)'
    )
    
    parser.add_argument(
        '--no-screenshots',
        action='store_true',
        help='Disable screenshot capture (just replay actions)'
    )
    
    args = parser.parse_args()
    
    try:
        replayer = MouseActionReplayer(args.suburb, args.session)
        
        success = replayer.replay_actions(
            speed_multiplier=args.speed,
            take_screenshots=not args.no_screenshots
        )
        
        if success:
            print("\n✅ Replay completed successfully!")
        else:
            print("\n❌ Replay failed or was interrupted")
            sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\nCreate the recording first:")
        print(f"  python 1_recorder/mouse_action_recorder.py --suburb {args.suburb} --session {args.session}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Replay interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
