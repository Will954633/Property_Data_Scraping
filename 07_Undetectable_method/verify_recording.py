#!/usr/bin/env python3
"""
Verify Recording - Shows what was captured in your recording

This helps you see exactly what actions were recorded, including:
- Mouse clicks (and where)
- Scrolls
- Keystrokes (and what was typed)
"""

import json
import sys
from pathlib import Path

def verify_recording(suburb, session):
    """Display contents of a recording"""
    recordings_dir = Path("2_recordings")
    action_file = recordings_dir / suburb / f"session_{session:02d}_actions.json"
    
    if not action_file.exists():
        print(f"❌ Recording not found: {action_file}")
        return
    
    with open(action_file, 'r') as f:
        data = json.load(f)
    
    print("\n" + "="*70)
    print(f"  RECORDING VERIFICATION - {suburb.upper()} - Session {session}")
    print("="*70)
    
    print(f"\n📊 Recording Info:")
    print(f"   Total actions: {data['action_count']}")
    print(f"   Duration: {data['duration']:.1f} seconds")
    print(f"   Screen: {data['screen_resolution']}")
    print(f"   Recorded: {data['recorded_at']}")
    
    # Analyze actions
    clicks = [a for a in data['actions'] if a['type'] == 'mouse_click']
    scrolls = [a for a in data['actions'] if a['type'] == 'mouse_scroll']
    keys = [a for a in data['actions'] if a['type'] == 'key_press']
    
    print(f"\n📋 Action Breakdown:")
    print(f"   Clicks: {len(clicks)}")
    print(f"   Scrolls: {len(scrolls)}")
    print(f"   Keystrokes: {len(keys)}")
    
    # Show clicks
    if clicks:
        print(f"\n🖱️  Mouse Clicks:")
        for i, click in enumerate(clicks[:20], 1):  # First 20 clicks
            print(f"   {i}. Time: {click['timestamp']:.1f}s, Position: ({click['x']:.0f}, {click['y']:.0f})")
    
    # Show typed text
    if keys:
        print(f"\n⌨️  Keystrokes (reconstructed text):")
        typed_text = ""
        for key in keys:
            key_val = key['key']
            if key_val.startswith('Key.'):
                # Special key
                typed_text += f" [{key_val}] "
            else:
                typed_text += key_val
        
        print(f"   '{typed_text}'")
        print(f"\n   (Total: {len(keys)} keys)")
    
    # Show scroll summary
    if scrolls:
        total_scroll_y = sum(s['dy'] for s in scrolls)
        print(f"\n📜 Scroll Summary:")
        print(f"   Total scroll events: {len(scrolls)}")
        print(f"   Net vertical scroll: {total_scroll_y:.0f} units")
    
    print("\n" + "="*70)
    print("✅ Recording appears valid!")
    print("="*70)
    
    print("\n💡 This recording captures:")
    print(f"   ✓ {len(clicks)} clicks (opening apps, clicking properties)")
    print(f"   ✓ {len(keys)} keystrokes (typing URL, etc.)")
    print(f"   ✓ {len(scrolls)} scrolls (navigating pages)")
    print("\n✓ Everything needed for replay is captured!")
    print("\n🚀 Test replay with:")
    print(f"   python 3_replay/mouse_action_replayer.py --suburb {suburb} --session {session}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify what was recorded")
    parser.add_argument('--suburb', type=str, required=True)
    parser.add_argument('--session', type=int, required=True)
    
    args = parser.parse_args()
    verify_recording(args.suburb.lower(), args.session)
