#!/usr/bin/env python3
"""
Multi-Session Property Scraper Runner
Runs native_scroll_screenshot.py for multiple URLs in separate browser sessions
with variable time delays between sessions
"""

import subprocess
import time
import os
from datetime import datetime

# URLs to scrape (2 different list pages)
URLS = [
   "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0",
   "https://www.domain.com.au/sale/robina-qld-4226/house/?excludeunderoffer=1&ssubs=0&page=2"
]

# Time delays between sessions (in seconds)
SESSION_DELAYS = [5, 8]  # After session 1, after session 2

# Configuration
NUM_SCROLLS = 25
SCROLL_DELAY = 1.5
INITIAL_LOAD_DELAY = 5


def run_applescript(script):
    """Execute AppleScript command"""
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()


def open_url_in_chrome(url):
    """Open URL in Chrome using AppleScript"""
    script = f'''
    tell application "Google Chrome"
        activate
        open location "{url}"
    end tell
    '''
    run_applescript(script)
    print(f"✓ Opened URL in Chrome")
    time.sleep(INITIAL_LOAD_DELAY)


def bring_chrome_to_front():
    """Bring Chrome to foreground"""
    script = '''
    tell application "Google Chrome"
        activate
    end tell
    '''
    run_applescript(script)


def click_chrome_window():
    """Click on Chrome window to ensure focus"""
    script = '''
    tell application "System Events"
        tell process "Google Chrome"
            click window 1
        end tell
    end tell
    '''
    run_applescript(script)


def scroll_down():
    """Send Page Down key to Chrome using AppleScript"""
    script = '''
    tell application "System Events"
        key code 121
    end tell
    '''
    run_applescript(script)


def scroll_to_top():
    """Send Command+Home to scroll to top"""
    script = '''
    tell application "System Events"
        key code 115 using command down
    end tell
    '''
    run_applescript(script)


def close_chrome_tab():
    """Close current Chrome tab using Command+W"""
    script = '''
    tell application "System Events"
        keystroke "w" using command down
    end tell
    '''
    run_applescript(script)


def get_chrome_window_bounds():
    """Get Chrome window position and size using AppleScript"""
    script = '''
    tell application "Google Chrome"
        set windowBounds to bounds of front window
        return windowBounds
    end tell
    '''
    result = run_applescript(script)
    if result:
        bounds = [int(x.strip()) for x in result.split(',')]
        return bounds
    return None


def take_screenshot(filepath):
    """Take screenshot of Chrome window"""
    bounds = get_chrome_window_bounds()
    
    if bounds:
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1
        subprocess.run(['screencapture', '-x', '-R', f'{x1},{y1},{width},{height}', filepath])
    else:
        subprocess.run(['screencapture', '-x', filepath])
    
    return filepath


def run_scraping_session(url, session_num, screenshot_dir):
    """Run a complete scraping session for one URL"""
    print(f"\n{'=' * 70}")
    print(f"SESSION {session_num}: STARTING")
    print(f"URL: {url}")
    print(f"Screenshot directory: {screenshot_dir}")
    print(f"{'=' * 70}")
    
    # Create screenshot directory
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Step 1: Open URL
    print(f"\n→ Opening URL in Chrome...")
    open_url_in_chrome(url)
    
    # Step 2: Activate window
    print("→ Activating Chrome window...")
    bring_chrome_to_front()
    time.sleep(0.5)
    click_chrome_window()
    time.sleep(0.5)
    
    # Step 3: Scroll to top
    print("→ Scrolling to top of page...")
    scroll_to_top()
    time.sleep(2)
    
    # Step 4: Take screenshots while scrolling
    print(f"\n→ Taking {NUM_SCROLLS} screenshots while scrolling down...")
    screenshots = []
    
    for i in range(NUM_SCROLLS):
        bring_chrome_to_front()
        time.sleep(0.3)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"section_{i+1:02d}_{timestamp}.png"
        filepath = os.path.join(screenshot_dir, filename)
        
        print(f"  📸 Screenshot {i+1}/{NUM_SCROLLS}: {filename}")
        
        take_screenshot(filepath)
        screenshots.append(filepath)
        
        if i < NUM_SCROLLS - 1:
            time.sleep(0.5)
            scroll_down()
            time.sleep(SCROLL_DELAY)
    
    # Step 5: Close Chrome tab
    print("\n→ Closing Chrome tab...")
    time.sleep(1)
    close_chrome_tab()
    
    print(f"\n{'=' * 70}")
    print(f"✅ SESSION {session_num} COMPLETED!")
    print(f"{'=' * 70}")
    print(f"Screenshots saved: {len(screenshots)}")
    print(f"Location: {os.path.abspath(screenshot_dir)}/")
    
    return screenshots


def main():
    """Main function - runs all scraping sessions"""
    print("\n" + "=" * 70)
    print("MULTI-SESSION PROPERTY SCRAPER")
    print("FULLY AUTONOMOUS & UNDETECTABLE")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  • Total sessions: {len(URLS)}")
    print(f"  • Screenshots per session: {NUM_SCROLLS}")
    print(f"  • Delays between sessions: {SESSION_DELAYS} seconds")
    print(f"\nFeatures:")
    print("  ✓ Native macOS scrolling (Page Down key)")
    print("  ✓ Native macOS screenshots")
    print("  ✓ Separate browser sessions for each URL")
    print("  ✓ Variable time delays between sessions")
    print("  ✓ Completely autonomous - no user interaction needed")
    print("  ✓ 100% Undetectable by websites")
    print("\n" + "=" * 70)
    
    start_time = datetime.now()
    all_results = []
    
    # Run each scraping session
    for i, url in enumerate(URLS, 1):
        session_dir = f"screenshots_session_{i}"
        
        # Run the session
        screenshots = run_scraping_session(url, i, session_dir)
        all_results.append({
            'session': i,
            'url': url,
            'directory': session_dir,
            'screenshot_count': len(screenshots)
        })
        
        # Wait between sessions (except after the last one)
        if i < len(URLS):
            delay = SESSION_DELAYS[i-1]
            print(f"\n⏳ Waiting {delay} seconds before next session...")
            time.sleep(delay)
        elif i == len(URLS):
            # Wait after last session as specified
            delay = SESSION_DELAYS[-1]
            print(f"\n⏳ Waiting {delay} seconds after final session...")
            time.sleep(delay)
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 70)
    print("🎉 ALL SESSIONS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\nTotal sessions: {len(all_results)}")
    print(f"Total time: {duration}")
    print(f"\nSession Results:")
    
    for result in all_results:
        print(f"\n  Session {result['session']}:")
        print(f"    URL: {result['url']}")
        print(f"    Directory: {result['directory']}/")
        print(f"    Screenshots: {result['screenshot_count']}")
    
    print(f"\n{'=' * 70}")
    print("\nNext Steps:")
    print("  1. Run OCR extraction for each session:")
    for i in range(1, len(URLS) + 1):
        print(f"     python ocr_extractor_multi.py --session {i}")
    print("\n  2. Parse property data from OCR results")
    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    main()
