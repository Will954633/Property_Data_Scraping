#!/usr/bin/env python3
"""
Debug Recording - Analyze a recording in detail

Shows the exact sequence of actions with timestamps to help debug replay issues.
"""

import json
import sys
from pathlib import Path

def debug_recording(suburb, session):
    """Show detailed recording analysis"""
    recordings_dir = Path("2_recordings")
    action_file = recordings_dir / suburb / f"session_{session:02d}_chrome_actions.json"
    
    if not action_file.exists():
        print(f"❌ Recording not found: {action_file}")
        return
    
    with open(action_file, 'r') as f:
        data = json.load(f)
    
    actions = data['actions']
    
    print("\n" + "="*80)
    print(f"  RECORDING DEBUG - {suburb.upper()} - Session {session}")
    print("="*80)
    
    print(f"\n📊 Recording Summary:")
    print(f"   File: {action_file.name}")
    print(f"   Total actions: {len(actions)}")
    print(f"   Duration: {data['duration']:.1f}s")
    print(f"   Screen: {data['screen_resolution']}")
    
    # Show first 50 actions in detail
    print(f"\n📋 First 50 Actions (chronological):")
    print(f"{'#':<5} {'Time':<8} {'Type':<15} {'Details'}")
    print("-" * 80)
    
    for i, action in enumerate(actions[:50], 1):
        action_type = action['type']
        time_str = f"{action['timestamp']:.2f}s"
        
        if action_type == 'mouse_click':
            details = f"({action['x']:.0f}, {action['y']:.0f}) - {action['button']}"
        elif action_type == 'mouse_scroll':
            details = f"dy={action['dy']}"
        elif action_type == 'key_press':
            details = f"'{action['key']}'"
        elif action_type == 'mouse_move':
            details = f"({action['x']:.0f}, {action['y']:.0f})"
        else:
            details = str(action)
        
        print(f"{i:<5} {time_str:<8} {action_type:<15} {details}")
    
    if len(actions) > 50:
        print(f"\n... ({len(actions) - 50} more actions)")
    
    # Show all clicks
    clicks = [a for a in actions if a['type'] == 'mouse_click']
    print(f"\n🖱️  All {len(clicks)} Clicks:")
    for i, click in enumerate(clicks, 1):
        print(f"   {i}. Time: {click['timestamp']:.1f}s → Position: ({click['x']:.0f}, {click['y']:.0f})")
    
    # Check for issues
    print(f"\n🔍 Potential Issues:")
    
    # Check if first action is delayed
    if actions and actions[0]['timestamp'] > 2:
        print(f"   ⚠️  First action starts at {actions[0]['timestamp']:.1f}s (late start)")
        print(f"       During replay, this delay will be added before first action")
    
    # Check if all actions are in Chrome (they should be after page load)
    print(f"\n   ℹ️  All recorded actions should happen in Chrome window")
    print(f"   ℹ️  First click at {clicks[0]['timestamp']:.1f}s should be on a property")
    
    print("\n" + "="*80)
    print("\n💡 Replay Tips:")
    print("1. Ensure screen resolution matches: {data['screen_resolution']}")
    print("2. Make sure Chrome window is same size as during recording")
    print("3. Page should be scrolled to TOP when replay starts")
    print("4. Use --speed 0.5 for slower replay to debug")
    print("\n" + "="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug a recording")
    parser.add_argument('--suburb', type=str, required=True)
    parser.add_argument('--session', type=int, required=True)
    
    args = parser.parse_args()
    debug_recording(args.suburb.lower(), args.session)
