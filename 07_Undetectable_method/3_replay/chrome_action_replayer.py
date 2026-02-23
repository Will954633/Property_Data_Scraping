#!/usr/bin/env python3
"""
Chrome Action Replayer - Replays Chrome browser actions with OCR extraction

This improved workflow:
1. Checks Chrome is closed
2. Opens Chrome via system command (matching recording)
3. Navigates to URL (matching recording)
4. Replays your recorded actions
5. Takes screenshots after property clicks
6. OCR extracts data from screenshots
7. Saves to MongoDB

This ensures replay happens in the correct app (Chrome, not VS Code/Outlook).
"""

import argparse
import sys
import json
import random
import time
import subprocess
from pathlib import Path
from datetime import datetime
import pyautogui
import mss
from PIL import Image
import pytesseract
import re

sys.path.append(str(Path(__file__).parent.parent))

try:
    from mongodb_saver import MongoDBSaver
except ImportError:
    MongoDBSaver = None


class ChromeActionReplayer:
    """Replays recorded Chrome actions and extracts data via OCR"""
    
    def __init__(self, suburb, session_number):
        self.suburb = suburb.lower()
        self.session_number = session_number
        
        # Paths
        self.recordings_dir = Path(__file__).parent.parent / "2_recordings"
        self.data_dir = Path(__file__).parent.parent / "4_data"
        self.screenshots_dir = self.data_dir / "screenshots"
        
        # Create directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Recording file
        self.action_file = self.recordings_dir / self.suburb / f"session_{session_number:02d}_chrome_actions.json"
        
        # Session ID
        self.session_id = f"{self.suburb}_session_{session_number:02d}"
        
        # Results
        self.properties_extracted = []
        self.screenshot_count = 0
        
        # Settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def prepare_chrome(self):
        """Ensure Chrome is ready (running but with all tabs closed)"""
        print("🔍 Preparing Chrome...")
        
        print("\n📋 Please ensure:")
        print("   1. Chrome is RUNNING (keeps your login/session)")
        print("   2. Close ALL tabs (Cmd+W until no tabs remain)")  
        print("   3. Chrome window should be empty/blank")
        print("   4. Press ENTER when ready")
        
        input("\nPress ENTER when Chrome is ready (running but no tabs)...")
        
        print("✅ Chrome ready\n")
        return True
    
    def open_chrome_and_navigate(self, url):
        """Open Chrome and navigate to URL"""
        print("🚀 Opening Chrome...")
        
        # Open Chrome
        subprocess.run(['open', '-a', 'Google Chrome'], check=True)
        time.sleep(3)
        
        print("✅ Chrome opened")
        
        # Navigate to URL
        print(f"🌐 Navigating to: {url[:80]}...")
        
        applescript = f'''
        tell application "Google Chrome"
            activate
            open location "{url}"
        end tell
        '''
        
        subprocess.run(['osascript', '-e', applescript], check=True)
        time.sleep(5)  # Wait for page load
        
        print("✅ Page loaded\n")
        return True
    
    def replay_actions(self, speed_multiplier=1.0, take_screenshots=True):
        """Replay recorded actions with OCR extraction"""
        print("\n" + "="*70)
        print(f"  CHROME ACTION REPLAYER - {self.suburb.upper()} - Session {self.session_number}")
        print("="*70)
        
        # Load recording
        if not self.action_file.exists():
            raise FileNotFoundError(f"Recording not found: {self.action_file}")
        
        with open(self.action_file, 'r') as f:
            recording = json.load(f)
        
        actions = recording['actions']
        url = recording['url']
        
        print(f"\n📂 Loaded recording:")
        print(f"   File: {self.action_file}")
        print(f"   Actions: {len(actions)}")
        print(f"   Duration: {recording['duration']:.1f}s")
        print(f"   URL: {url[:80]}...")
        
        # DEBUG: Show first few actions
        clicks = [a for a in actions if a['type'] == 'mouse_click']
        print(f"\n🐛 DEBUG - Recording Content:")
        print(f"   Total clicks in recording: {len(clicks)}")
        if clicks:
            print(f"   First click will be at: ({clicks[0]['x']:.0f}, {clicks[0]['y']:.0f}) at {clicks[0]['timestamp']:.1f}s")
            print(f"   Last click will be at: ({clicks[-1]['x']:.0f}, {clicks[-1]['y']:.0f}) at {clicks[-1]['timestamp']:.1f}s")
        
        # Check screen resolution
        current_res = pyautogui.size()
        recorded_res = tuple(recording['screen_resolution'])
        if current_res != recorded_res:
            print(f"\n⚠️  Screen resolution mismatch!")
            print(f"   Recorded: {recorded_res}, Current: {current_res}")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        
        # Step 1: Prepare Chrome (running but no tabs)
        if not self.prepare_chrome():
            return False
        
        # Step 2: Navigate to URL (opens in new tab)
        if not self.open_chrome_and_navigate(url):
            return False
        
        # Step 3: Replay actions
        print("🔄 Replaying your actions...")
        print(f"   Speed: {speed_multiplier}x")
        print(f"   Screenshots: {'Yes' if take_screenshots else 'No'}")
        
        # Auto-start after countdown (no ENTER needed!)
        print("\n⏱️  Replay will start automatically in:")
        for i in range(5, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n🎬 REPLAYING!\n")
        
        prev_time = 0
        click_count = 0
        
        try:
            for i, action in enumerate(actions):
                # Timing with variation
                delay = (action['timestamp'] - prev_time) * speed_multiplier
                delay = delay * random.uniform(0.85, 1.15)
                delay = max(0, min(delay, 5))
                
                if delay > 0:
                    time.sleep(delay)
                
                # Execute action
                if action['type'] == 'mouse_move':
                    # Move instantly to follow exact path (no interpolation)
                    pyautogui.moveTo(action['x'], action['y'], duration=0)
                
                elif action['type'] == 'mouse_click':
                    click_count += 1
                    print(f"   🖱️  Click {click_count} at ({action['x']:.0f}, {action['y']:.0f})")
                    pyautogui.click(action['x'], action['y'])
                    
                    # Screenshot after click
                    if take_screenshots:
                        time.sleep(2)  # Wait for page
                        self._capture_and_extract(f"click_{click_count}")
                
                elif action['type'] == 'mouse_scroll':
                    pyautogui.scroll(int(action['dy'] * 10))
                
                elif action['type'] == 'key_press':
                    key = action['key']
                    if key.startswith('Key.'):
                        pyautogui.press(key.replace('Key.', ''))
                    else:
                        pyautogui.write(key)
                
                prev_time = action['timestamp']
                
                # Progress every 100 actions
                if (i + 1) % 100 == 0:
                    print(f"   Progress: {(i+1)/len(actions)*100:.0f}%")
        
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted")
            return False
        
        print(f"\n✅ Replay complete!")
        print(f"   Clicks: {click_count}")
        print(f"   Screenshots: {self.screenshot_count}")
        print(f"   Properties extracted: {len(self.properties_extracted)}")
        
        return True
    
    def _capture_and_extract(self, label):
        """Capture screenshot and extract data"""
        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.session_id}_{label}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
        
        self.screenshot_count += 1
        print(f"   📸 Screenshot: {filename}")
        
        # OCR extraction
        try:
            image = Image.open(filepath).convert('L')
            text = pytesseract.image_to_string(image, lang='eng')
            
            # Parse property data
            property_data = self._parse_ocr_text(text, str(filepath))
            
            if property_data:
                # Save to MongoDB
                if MongoDBSaver:
                    saver = MongoDBSaver()
                    if saver.save_property(property_data):
                        self.properties_extracted.append(property_data)
                        print(f"   ✓ Extracted: {property_data.get('address', {}).get('full', 'Unknown')[:50]}")
                    saver.close()
        
        except Exception as e:
            print(f"   ⚠️  OCR error: {e}")
    
    def _parse_ocr_text(self, text, screenshot_path):
        """Parse OCR text into property data"""
        # Check if property page
        if not any(kw in text.lower() for kw in ['bed', 'bath', '$', 'qld']):
            return None
        
        data = {
            'property_url': screenshot_path,
            'suburb': self.suburb,
            'session_used': self.session_id,
            'scraped_at': datetime.now().isoformat(),
            'raw_ocr_text': text[:500]
        }
        
        # Address
        addr_match = re.search(r'([^\n]+(?:QLD|Queensland)\s+\d{4})', text, re.I)
        data['address'] = {
            'full': addr_match.group(1).strip() if addr_match else None,
            'suburb': self.suburb.title(),
            'state': 'QLD'
        }
        
        # Price
        price_match = re.search(r'\$\s*(\d{1,3}(?:,\d{3})*)', text)
        data['price'] = {
            'display': price_match.group(0) if price_match else None
        }
        
        # Features
        features = {}
        if m := re.search(r'(\d+)\s*bed', text, re.I):
            features['bedrooms'] = int(m.group(1))
        if m := re.search(r'(\d+)\s*bath', text, re.I):
            features['bathrooms'] = int(m.group(1))
        if m := re.search(r'(\d+)\s*car', text, re.I):
            features['parking'] = int(m.group(1))
        
        data['features'] = features
        
        return data


def main():
    parser = argparse.ArgumentParser(description="Replay Chrome actions with OCR")
    parser.add_argument('--suburb', required=True)
    parser.add_argument('--session', type=int, required=True)
    parser.add_argument('--speed', type=float, default=1.0)
    
    args = parser.parse_args()
    
    try:
        replayer = ChromeActionReplayer(args.suburb, args.session)
        success = replayer.replay_actions(speed_multiplier=args.speed)
        
        if not success:
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
