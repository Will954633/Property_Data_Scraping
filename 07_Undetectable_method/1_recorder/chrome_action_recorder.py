#!/usr/bin/env python3
"""
Chrome Action Recorder - Records actions AFTER opening Chrome

This improved workflow:
1. Checks that Chrome is closed
2. Opens Chrome via system command (not recorded)
3. Navigates to the URL (not recorded)
4. THEN records your actions (clicks, scrolls, typing)
5. Replay does the same: opens Chrome → replays your actions

This ensures replay happens in the correct application.
"""

import argparse
import pyautogui
import time
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from pynput import mouse, keyboard

sys.path.append(str(Path(__file__).parent.parent))


class ChromeActionRecorder:
    """Records actions in Chrome browser"""
    
    def __init__(self, suburb, session_number):
        self.suburb = suburb.lower()
        self.session_number = session_number
        self.recordings_dir = Path(__file__).parent.parent / "2_recordings"
        
        # Create directories
        self.recordings_dir.mkdir(exist_ok=True)
        self.suburb_dir = self.recordings_dir / self.suburb
        self.suburb_dir.mkdir(exist_ok=True)
        
        # Recording file
        self.recording_file = self.suburb_dir / f"session_{session_number:02d}_chrome_actions.json"
        
        # Actions list
        self.actions = []
        self.start_time = None
        self.recording = False
        
        # Listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # URL for this suburb
        self.url = self._get_suburb_url()
    
    def _get_suburb_url(self):
        """Get URL from config"""
        import yaml
        config_file = Path(__file__).parent.parent / "config.yaml"
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config['suburbs'][self.suburb]['url']
    
    def prepare_chrome(self):
        """Ensure Chrome is ready (running but with closed tabs)"""
        print("\n" + "="*70)
        print(f"  CHROME ACTION RECORDER - {self.suburb.upper()} - Session {self.session_number}")
        print("="*70)
        print("\n🔍 Preparing Chrome...")
        
        print("\n📋 Please ensure:")
        print("   1. Chrome is RUNNING (keep it open for login/cookies)")
        print("   2. Close ALL tabs (Cmd+W until no tabs remain)")
        print("   3. Chrome window should be empty/blank")
        print("   4. Press ENTER when ready")
        
        input("\nPress ENTER when Chrome is ready (running but no tabs)...")
        
        print("✅ Chrome ready\n")
        return True
    
    def open_chrome_and_navigate(self):
        """Open Chrome and navigate to the URL"""
        print("🚀 Opening Chrome...")
        
        try:
            # Open Chrome
            subprocess.run(['open', '-a', 'Google Chrome'], check=True)
            time.sleep(3)  # Wait for Chrome to fully open
            
            print("✅ Chrome opened")
            
            # Navigate to URL using AppleScript
            print(f"🌐 Navigating to: {self.url[:80]}...")
            
            applescript = f'''
            tell application "Google Chrome"
                activate
                open location "{self.url}"
            end tell
            '''
            
            subprocess.run(['osascript', '-e', applescript], check=True)
            time.sleep(5)  # Wait for page to load
            
            print("✅ Page loaded")
            
            return True
            
        except Exception as e:
            print(f"❌ Error opening Chrome: {e}")
            return False
    
    def start_recording(self):
        """Start recording user actions in Chrome"""
        print("\n" + "="*70)
        print("  RECORDING YOUR CHROME ACTIONS")
        print("="*70)
        print("\nINSTRUCTIONS:")
        print("1. Chrome is now open at the property listings page")
        print("2. Recording will start automatically in 5 seconds")
        print("3. Then interact naturally:")
        print("   - Scroll through properties")
        print("   - Click on 3 properties to view them")
        print("   - For each: view details, scroll, click BACK") 
        print("   - Type in search fields if needed")
        print("4. When finished, press ESC to stop recording")
        print("\n💡 TIP: Take your time, browse naturally")
        print("="*70)
        
        # Auto-start after countdown (no ENTER needed!)
        print("\n⏱️  Recording will start automatically in:")
        for i in range(5, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        self.recording = True
        self.start_time = time.time()
        
        print("\n🔴 RECORDING STARTED!")
        print("   Your actions are being recorded...")
        print("   Press ESC when done\n")
        
        # Start listeners
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        # Wait for recording to complete
        try:
            self.keyboard_listener.join()
            self.mouse_listener.join()
        except KeyboardInterrupt:
            self.stop_recording()
        
        return True
    
    def _get_timestamp(self):
        """Get timestamp relative to start"""
        if not self.start_time:
            return 0
        return time.time() - self.start_time
    
    def _on_mouse_move(self, x, y):
        """Record mouse movement"""
        if not self.recording:
            return
        
        # Record EVERY move for accurate replay (don't skip)
        self.actions.append({
            'type': 'mouse_move',
            'x': x,
            'y': y,
            'timestamp': self._get_timestamp()
        })
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Record mouse clicks"""
        if not self.recording or not pressed:
            return
        
        self.actions.append({
            'type': 'mouse_click',
            'x': x,
            'y': y,
            'button': str(button),
            'timestamp': self._get_timestamp()
        })
        
        print(f"   📍 Click: ({x:.0f}, {y:.0f})")
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Record mouse scroll"""
        if not self.recording:
            return
        
        self.actions.append({
            'type': 'mouse_scroll',
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'timestamp': self._get_timestamp()
        })
    
    def _on_key_press(self, key):
        """Record keyboard presses"""
        if not self.recording:
            return
        
        # Check for ESC to stop
        if key == keyboard.Key.esc:
            print("\n🛑 ESC pressed - stopping...")
            self.stop_recording()
            return False
        
        # Record the key
        try:
            key_char = key.char
            print(f"   ⌨️  Typed: '{key_char}'", end='', flush=True)
        except AttributeError:
            key_char = str(key)
            if key not in [keyboard.Key.shift, keyboard.Key.shift_r]:  # Don't print modifiers
                print(f"   ⌨️  Key: {key_char}")
        
        self.actions.append({
            'type': 'key_press',
            'key': key_char,
            'timestamp': self._get_timestamp()
        })
    
    def stop_recording(self):
        """Stop recording and save"""
        if not self.recording:
            return
        
        self.recording = False
        
        # Stop listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        # Save actions
        self._save_actions()
        
        print("\n" + "="*70)
        print("✅ RECORDING COMPLETE!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   Total actions: {len(self.actions)}")
        print(f"   Duration: {self._get_timestamp():.1f}s")
        print(f"   Saved to: {self.recording_file}")
        
        # Count types
        clicks = len([a for a in self.actions if a['type'] == 'mouse_click'])
        scrolls = len([a for a in self.actions if a['type'] == 'mouse_scroll'])
        keys = len([a for a in self.actions if a['type'] == 'key_press'])
        
        print(f"\n📋 Captured:")
        print(f"   Clicks: {clicks}")
        print(f"   Scrolls: {scrolls}")
        print(f"   Keystrokes: {keys}")
        
        print(f"\n🚀 Test replay:")
        print(f"   python 3_replay/chrome_action_replayer.py --suburb {self.suburb} --session {self.session_number}")
        print()
    
    def _save_actions(self):
        """Save actions to JSON"""
        data = {
            'suburb': self.suburb,
            'session': self.session_number,
            'url': self.url,
            'recorded_at': datetime.now().isoformat(),
            'duration': self._get_timestamp(),
            'action_count': len(self.actions),
            'screen_resolution': list(pyautogui.size()),
            'method': 'chrome_actions',
            'actions': self.actions
        }
        
        with open(self.recording_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update metadata
        metadata_file = self.recordings_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        if self.suburb not in metadata:
            metadata[self.suburb] = {}
        
        metadata[self.suburb][f"session_{self.session_number:02d}"] = {
            "recorded_at": datetime.now().isoformat(),
            "file": str(self.recording_file.name),
            "action_count": len(self.actions),
            "duration": self._get_timestamp(),
            "method": "chrome_actions"
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Record actions in Chrome browser",
        epilog="Example: python chrome_action_recorder.py --suburb robina --session 1"
    )
    
    parser.add_argument('--suburb', type=str, required=True, help='Suburb name')
    parser.add_argument('--session', type=int, required=True, help='Session number')
    
    args = parser.parse_args()
    
    if args.session < 1:
        print("❌ Session must be >= 1")
        sys.exit(1)
    
    try:
        recorder = ChromeActionRecorder(args.suburb, args.session)
        
        # Step 1: Prepare Chrome (running but no tabs)
        if not recorder.prepare_chrome():
            print("\n❌ Please prepare Chrome and try again")
            sys.exit(1)
        
        # Step 2: Open URL in new tab
        if not recorder.open_chrome_and_navigate():
            print("\n❌ Failed to navigate")
            sys.exit(1)
        
        # Step 3: Record user actions
        recorder.start_recording()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
