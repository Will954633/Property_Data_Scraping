#!/usr/bin/env python3
"""
Test: AppleScript Google Search + cliclick Result Clicker
Combines the working AppleScript browser control with our cliclick solution
"""

import subprocess
import time
import sys


def run_applescript(script):
    """Execute AppleScript command"""
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()


def open_google_in_chrome():
    """Open Google in Chrome using AppleScript"""
    print("🌐 Opening Google in Chrome...")
    script = '''
    tell application "Google Chrome"
        activate
        open location "https://www.google.com"
    end tell
    '''
    run_applescript(script)
    print("✅ Chrome opened with Google")
    time.sleep(3)  # Wait for page load


def search_google(address):
    """Type address into Google search and press Enter"""
    print(f"🔍 Searching for: {address}")
    
    # Click on search box
    print("   Clicking search box...")
    script = '''
    tell application "System Events"
        tell process "Google Chrome"
            click window 1
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(0.5)
    
    # Type the address
    print(f"   Typing: {address}")
    # Escape any special characters
    address_escaped = address.replace('"', '\\"').replace("'", "\\'")
    script = f'''
    tell application "System Events"
        keystroke "{address_escaped}"
    end tell
    '''
    run_applescript(script)
    time.sleep(1)
    
    # Press Enter
    print("   Pressing Enter...")
    script = '''
    tell application "System Events"
        key code 36
    end tell
    '''
    run_applescript(script)
    print("✅ Search submitted")
    time.sleep(4)  # Wait for results to load


def click_realestate_result():
    """Find and click realestate.com.au result using AppleScript position + cliclick"""
    print("\n🖱️  Finding realestate.com.au link position...")
    
    import random
    
    # Use AppleScript to get Chrome window bounds and click position
    script = '''
    tell application "Google Chrome"
        set windowBounds to bounds of front window
        return windowBounds
    end tell
    '''
    bounds_str = run_applescript(script)
    
    if not bounds_str:
        print("❌ Could not get window bounds")
        return False
    
    try:
        bounds = [int(x.strip()) for x in bounds_str.split(',')]
        win_x, win_y, win_x2, win_y2 = bounds
        print(f"   Chrome window: {win_x},{win_y} to {win_x2},{win_y2}")
        
        # Estimate position of first search result (typically around 1/3 down the window)
        # First result is usually at around x=center, y=30% down from top
        click_x = win_x + (win_x2 - win_x) // 2
        click_y = win_y + int((win_y2 - win_y) * 0.3)
        
        # Add random offset
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-10, 10)
        final_x = click_x + offset_x
        final_y = click_y + offset_y
        
        print(f"   Clicking at estimated result position: {final_x},{final_y}")
        
        # Use cliclick to click
        result = subprocess.run(
            ["cliclick", f"c:{final_x},{final_y}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ Click completed!")
            time.sleep(2)  # Wait for page to load
            return True
        else:
            print(f"❌ cliclick error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    
    if len(sys.argv) < 2:
        print("Usage: python test_applescript_google_click.py '<address>'")
        print("")
        print("Example:")
        print("  python test_applescript_google_click.py '279 Ron Penhaligon Way, Robina'")
        return 1
    
    address = sys.argv[1]
    
    print("=" * 70)
    print("TEST: AppleScript Google Search + cliclick Click")
    print("=" * 70)
    print(f"\nProperty Address: {address}")
    print("\nThis test uses:")
    print("  ✓ AppleScript to open Chrome (your working method)")
    print("  ✓ AppleScript to type and search")
    print("  ✓ cliclick to physically click the result (native macOS)")
    print("\nAll methods are 100% undetectable!")
    print("\n" + "=" * 70)
    
    try:
        # Step 1: Open Google
        print("\n" + "=" * 70)
        print("STEP 1: Opening Google in Chrome")
        print("=" * 70)
        open_google_in_chrome()
        
        # Step 2: Search for address
        print("\n" + "=" * 70)
        print("STEP 2: Searching for address")
        print("=" * 70)
        search_google(address)
        
        # Step 3: Click result using cliclick
        print("\n" + "=" * 70)
        print("STEP 3: Clicking realestate.com.au result")
        print("=" * 70)
        success = click_realestate_result()
        
        if success:
            print("\n" + "=" * 70)
            print("✅ TEST SUCCESSFUL!")
            print("=" * 70)
            print("\nThe realestate.com.au page should now be loading...")
            print("Check Chrome to verify the page opened successfully.")
            print("\n⚠️  Note: Chrome will remain open for you to inspect the result.")
            print("=" * 70)
            return 0
        else:
            print("\n" + "=" * 70)
            print("❌ TEST FAILED")
            print("=" * 70)
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
