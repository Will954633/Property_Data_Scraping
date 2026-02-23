#!/usr/bin/env python3
"""
SikuliX Complete Workflow
Opens Chrome, searches for address, then uses SikuliX to find and click favicon
"""

import subprocess
import time
import os
import sys
from datetime import datetime

# Address to search
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"

# Configuration
INITIAL_LOAD_DELAY = 5
SIKULIX_JAR = "sikulix.jar"
SIKULI_SCRIPT = "sikuli_clicker.sikuli"
FAVICON_IMAGE = "favicon_small.png"


def run_applescript(script):
    """Execute AppleScript"""
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()


def bring_chrome_to_front():
    """Bring Chrome to foreground"""
    script = '''
    tell application "Google Chrome"
        activate
    end tell
    '''
    run_applescript(script)


def focus_address_bar():
    """Focus Chrome address bar"""
    script = '''
    tell application "System Events"
        keystroke "l" using command down
    end tell
    '''
    run_applescript(script)


def type_text(text):
    """Type text using System Events"""
    # Escape quotes in the text
    escaped_text = text.replace('"', '\\"')
    script = f'''
    tell application "System Events"
        keystroke "{escaped_text}"
    end tell
    '''
    run_applescript(script)


def press_enter():
    """Press Enter key"""
    script = '''
    tell application "System Events"
        key code 36
    end tell
    '''
    run_applescript(script)


def open_chrome_and_search(address):
    """Open Chrome and search for address"""
    print("→ Opening Chrome...")
    script = '''
    tell application "Google Chrome"
        activate
        make new window
        set URL of active tab of front window to "about:blank"
    end tell
    '''
    run_applescript(script)
    print("✓ Chrome opened")
    time.sleep(1)
    
    bring_chrome_to_front()
    time.sleep(0.5)
    
    print("→ Focusing address bar...")
    focus_address_bar()
    time.sleep(0.5)
    
    print(f"→ Typing address: {address}")
    type_text(address)
    time.sleep(0.5)
    
    print("→ Pressing Enter...")
    press_enter()
    print(f"✓ Search initiated")
    time.sleep(INITIAL_LOAD_DELAY)


def run_sikulix(favicon_image):
    """Run SikuliX to find and click favicon"""
    print("\n→ Starting SikuliX visual recognition...")
    
    # Check if SikuliX JAR exists
    if not os.path.exists(SIKULIX_JAR):
        print(f"✗ Error: SikuliX JAR not found: {SIKULIX_JAR}")
        return False
    
    # Check if Sikuli script exists
    if not os.path.exists(SIKULI_SCRIPT):
        print(f"✗ Error: Sikuli script not found: {SIKULI_SCRIPT}")
        return False
    
    # Check if favicon image exists
    if not os.path.exists(favicon_image):
        print(f"✗ Error: Favicon image not found: {favicon_image}")
        return False
    
    # Build the SikuliX command
    # Use -r to run the script
    # Arguments after -- are passed to the script
    cmd = [
        'java',
        '-jar',
        SIKULIX_JAR,
        '-r',
        SIKULI_SCRIPT,
        '--',
        favicon_image
    ]
    
    print(f"→ Running SikuliX...")
    print(f"  JAR: {SIKULIX_JAR}")
    print(f"  Script: {SIKULI_SCRIPT}")
    print(f"  Image: {favicon_image}")
    
    try:
        # Run SikuliX
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Print output
        if result.stdout:
            print("\n--- SikuliX Output ---")
            print(result.stdout)
            print("--- End Output ---\n")
        
        if result.stderr:
            print("\n--- SikuliX Errors ---")
            print(result.stderr)
            print("--- End Errors ---\n")
        
        if result.returncode == 0:
            print("✓ SikuliX execution successful!")
            return True
        else:
            print(f"✗ SikuliX execution failed with code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ SikuliX execution timed out")
        return False
    except Exception as e:
        print(f"✗ Error running SikuliX: {e}")
        return False


def main():
    print("\n" + "=" * 70)
    print("SIKULIX COMPLETE WORKFLOW")
    print("=" * 70)
    print(f"\nAddress: {SEARCH_ADDRESS}")
    print(f"Method: SikuliX visual recognition")
    print(f"Favicon: {FAVICON_IMAGE}")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    
    # Step 1: Open Chrome and search
    print("\n→ STEP 1: Opening Chrome and searching...")
    open_chrome_and_search(SEARCH_ADDRESS)
    
    # Give page time to fully load
    print("\n→ Waiting for page to stabilize...")
    time.sleep(2)
    
    # Bring Chrome to front one more time before SikuliX runs
    bring_chrome_to_front()
    time.sleep(0.5)
    
    # Step 2: Run SikuliX to find and click
    print("\n→ STEP 2: Running SikuliX to find and click favicon...")
    success = run_sikulix(FAVICON_IMAGE)
    
    duration = datetime.now() - start_time
    
    print("\n" + "=" * 70)
    if success:
        print("✅ WORKFLOW COMPLETE!")
        print("=" * 70)
        print(f"Method: SikuliX Visual Recognition")
        print(f"Result: Successfully clicked on realestate.com.au link")
        print(f"Duration: {duration}")
    else:
        print("✗ WORKFLOW FAILED")
        print("=" * 70)
        print(f"Method: SikuliX Visual Recognition")
        print(f"Result: Failed to find or click favicon")
        print(f"Duration: {duration}")
    print("\n" + "=" * 70 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
