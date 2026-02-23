#!/usr/bin/env python3
"""
Mouse & Keyboard Action Recorder

Records all your mouse movements, clicks, scrolls, and keyboard inputs
to create a reproducible automation sequence.

This is 100% undetectable because YOU are doing the actions - we're just recording them.
"""

import pyautogui
import time
import json
import sys
from pathlib import Path
from datetime import datetime
from pynput import mouse, keyboard
import threading

sys.path.append(str(Path(__file__).parent.parent))


class MouseActionRecorder:
    """Records mouse and keyboard actions"""
    
    def __init__(self, suburb, session_number):
        self.suburb = suburb.lower()
        self.session_number = session_number
        self.recordings_dir = Path(__file__).parent.parent / "2_recordings"
        
        # Create directories
        self.recordings_dir.mkdir(exist_ok=True)
        self.suburb_dir = self.recordings_dir / self.suburb
        self.suburb_dir.mkdir(exist_ok=True)
        
        # Recording file
        self.recording_file = self.suburb_dir / f"session_{session_number:02d}_actions.json"
        
        # Actions list
        self.actions = []
        self.start_time = None
        self.recording = False
        
        # Listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Settings
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0  # No delay between actions during replay
    
    def start_recording(self):
        """Start recording actions"""
        print("\n" + "="*70)
        print(f"  MOUSE ACTION RECORDER - {self.suburb.upper()} - Session {self.session_number}")
        print("="*70)
        print("\nThis will record ALL your mouse and keyboard actions.")
        print("\nINSTRUCTIONS:")
        print("1. Click 'Start Recording' when prompted")
        print("2. Open Chrome normally (Cmd+Space, type 'chrome', Enter)")
        print("3. Navigate to the URL:")
        print("   https://www.realestate.com.au/buy/property-house-in-robina,...")
        print("4. Scroll through the property listings")
        print("5. Click on EACH property card (we'll record the positions)")
        print("6. For each property: view it, scroll, then GO BACK")
        print("7. When done, press ESC to stop recording")
        print("\n" + "="*70)
        
        input("\nPress ENTER to start recording...")
        
        self.recording = True
        self.start_time = time.time()
        
        print("\n🔴 RECORDING STARTED!")
        print("   Perform your actions now...")
        print("   Press ESC to stop\n")
        
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
        
        # Only record every 10th move to reduce data size
        if len(self.actions) == 0 or len(self.actions) % 10 == 0:
            self.actions.append({
                'type': 'mouse_move',
                'x': x,
                'y': y,
                'timestamp': self._get_timestamp()
            })
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Record mouse clicks"""
        if not self.recording or not pressed:  # Only record press, not release
            return
        
        action = {
            'type': 'mouse_click',
            'x': x,
            'y': y,
            'button': str(button),
            'timestamp': self._get_timestamp()
        }
        
        self.actions.append(action)
        print(f"   📍 Click recorded at ({x}, {y}) - {str(button)}")
    
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
        
        # Check for ESC to stop recording
        if key == keyboard.Key.esc:
            print("\n🛑 ESC pressed - stopping recording...")
            self.stop_recording()
            return False  # Stop listener
        
        # Record the key
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key)
        
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
        print(f"   Duration: {self._get_timestamp():.1f} seconds")
        print(f"   Saved to: {self.recording_file}")
        
        # Count action types
        clicks = len([a for a in self.actions if a['type'] == 'mouse_click'])
        scrolls = len([a for a in self.actions if a['type'] == 'mouse_scroll'])
        keys = len([a for a in self.actions if a['type'] == 'key_press'])
        
        print(f"\n📋 Actions breakdown:")
        print(f"   Clicks: {clicks}")
        print(f"   Scrolls: {scrolls}")
        print(f"   Keystrokes: {keys}")
        
        print(f"\n🚀 Next steps:")
        print(f"1. Review the recording (optional)")
        print(f"2. Test replay:")
        print(f"   python 3_replay/mouse_action_replayer.py --suburb {self.suburb} --session {self.session_number}")
        print()
    
    def _save_actions(self):
        """Save actions to JSON file"""
        data = {
            'suburb': self.suburb,
            'session': self.session_number,
            'recorded_at': datetime.now().isoformat(),
            'duration': self._get_timestamp(),
            'action_count': len(self.actions),
            'screen_resolution': pyautogui.size(),
            'actions': self.actions
        }
        
        with open(self.recording_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update metadata
        self._update_metadata()
    
    def _update_metadata(self):
        """Update metadata.json"""
        metadata_file = self.recordings_dir / "metadata.json"
        
        # Load existing
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Add this recording
        if self.suburb not in metadata:
            metadata[self.suburb] = {}
        
        session_key = f"session_{self.session_number:02d}"
        metadata[self.suburb][session_key] = {
            "recorded_at": datetime.now().isoformat(),
            "file": str(self.recording_file.name),
            "action_count": len(self.actions),
            "duration": self._get_timestamp(),
            "method": "mouse_actions"
        }
        
        # Save
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Record mouse and keyboard actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python mouse_action_recorder.py --suburb robina --session 1

This will record ALL your actions including:
- Opening Chrome
- Navigating to the URL
- Clicking on properties
- Scrolling
- Viewing property details

These actions can be replayed later for automation.
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
    
    args = parser.parse_args()
    
    if args.session < 1:
        print("❌ Error: Session number must be 1 or greater")
        sys.exit(1)
    
    try:
        recorder = MouseActionRecorder(args.suburb, args.session)
        recorder.start_recording()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Recording cancelled")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
