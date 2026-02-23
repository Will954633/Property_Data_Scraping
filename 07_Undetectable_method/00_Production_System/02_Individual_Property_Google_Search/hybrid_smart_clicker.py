#!/usr/bin/env python3
"""
Hybrid Smart Clicker - Fixed Coordinates + GPT Vision Fallback
Optimized approach: Try fixed coordinates first (90% success), use GPT Vision as fallback
"""

import subprocess
import time
import os
import json
import base64
import random
import math
from datetime import datetime
from openai import OpenAI

# Configuration
OPENAI_API_KEY = "REDACTED_OPENAI_KEY"
GPT_MODEL = "gpt-5-nano-2025-08-07"
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"
SCREENSHOT_DIR = "screenshots"

# Click strategy configuration
FIXED_CLICK_COORDINATES = (350, 247)  # First Google result position
MAX_GPT_RETRIES = 2  # Maximum GPT Vision attempts if fixed click fails
INITIAL_LOAD_DELAY = 5  # Wait for Google page to load
PAGE_LOAD_WAIT = 3  # Wait after clicking a link
VALIDATION_DELAY = 1  # Wait before URL validation
CLICK_DELAY = 2  # Wait before clicking


def run_applescript(script):
    """Execute AppleScript command"""
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()


def maximize_chrome_window():
    """Maximize Chrome window to full screen"""
    script = '''
    tell application "Google Chrome"
        activate
        tell front window
            set bounds to {0, 0, 1920, 1080}
        end tell
    end tell
    '''
    try:
        run_applescript(script)
        print("✓ Maximized Chrome window")
        time.sleep(0.5)
    except Exception as e:
        print(f"⚠ Could not maximize window: {e}")


def open_chrome_and_search(address):
    """Open Chrome, maximize window, and search for address"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    script = '''
    tell application "Google Chrome"
        activate
        make new window
        set URL of active tab of front window to "about:blank"
    end tell
    '''
    run_applescript(script)
    print(f"✓ Opened Chrome")
    time.sleep(1)
    
    maximize_chrome_window()
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(address)
    print(f"✓ Typed address: {address}")
    time.sleep(0.5)
    press_enter()
    print(f"✓ Pressed Enter - Google search initiated")
    print(f"→ Waiting {INITIAL_LOAD_DELAY} seconds for page to load...")
    time.sleep(INITIAL_LOAD_DELAY)
    
    return True


def bring_chrome_to_front():
    """Bring Chrome to foreground"""
    script = '''
    tell application "Google Chrome"
        activate
    end tell
    '''
    run_applescript(script)


def focus_address_bar():
    """Focus Chrome address bar using Command+L"""
    script = '''
    tell application "System Events"
        keystroke "l" using command down
    end tell
    '''
    run_applescript(script)


def type_text(text):
    """Type text using System Events"""
    text = text.replace('"', '\\"')
    script = f'''
    tell application "System Events"
        keystroke "{text}"
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


def get_current_url():
    """Get the URL of the active Chrome tab"""
    script = '''
    tell application "Google Chrome"
        get URL of active tab of front window
    end tell
    '''
    try:
        url = run_applescript(script)
        return url
    except:
        return None


def validate_realestate_url():
    """Check if current URL is from realestate.com.au"""
    time.sleep(VALIDATION_DELAY)
    url = get_current_url()
    
    if url and "realestate.com.au" in url.lower():
        print(f"✓ URL validation passed: {url}")
        return True, url
    else:
        print(f"✗ URL validation failed: {url}")
        return False, url


def navigate_back():
    """Navigate back to previous page"""
    print("\n→ Navigating back to Google search results...")
    script = '''
    tell application "System Events"
        keystroke "[" using command down
    end tell
    '''
    run_applescript(script)
    time.sleep(2)  # Wait for page to load
    print("✓ Navigated back")


def get_chrome_window_bounds():
    """Get Chrome window position and size"""
    script = '''
    tell application "Google Chrome"
        set windowBounds to bounds of front window
        return windowBounds
    end tell
    '''
    result = run_applescript(script)
    if result:
        try:
            bounds = [int(x.strip()) for x in result.split(',')]
            return bounds
        except:
            return None
    return None


def take_screenshot(filepath):
    """Take screenshot of Chrome window"""
    bring_chrome_to_front()
    time.sleep(0.5)
    
    bounds = get_chrome_window_bounds()
    
    if bounds:
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1
        subprocess.run(['screencapture', '-x', '-R', f'{x1},{y1},{width},{height}', filepath])
        print(f"✓ Screenshot captured")
        return bounds
    else:
        subprocess.run(['screencapture', '-x', filepath])
        print(f"✓ Screenshot captured (full screen)")
        return None


def encode_image_to_base64(image_path):
    """Encode image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_screenshot_with_gpt(screenshot_path, search_address):
    """Send screenshot to GPT Vision API and get click coordinates"""
    print(f"\n→ Analyzing screenshot with GPT Vision API...")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    base64_image = encode_image_to_base64(screenshot_path)
    
    prompt = f"""Analyze this Google search results screenshot for: "{search_address}"

Find the realestate.com.au link matching this address and provide click coordinates.

Return ONLY this JSON (no other text):
{{
    "found": true/false,
    "x": pixel_x,
    "y": pixel_y,
    "confidence": "high"/"medium"/"low",
    "reasoning": "brief explanation"
}}"""
    
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_completion_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        if not response_text:
            return {"found": False, "error": "Empty response"}
        
        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        print(f"✓ GPT found link at ({result.get('x')}, {result.get('y')}) - confidence: {result.get('confidence')}")
        return result
        
    except Exception as e:
        print(f"❌ GPT API error: {e}")
        return {"found": False, "error": str(e)}


def human_like_mouse_movement(x, y, duration=0.5):
    """Move mouse with human-like curved movement"""
    script = '''
    use framework "CoreGraphics"
    set mouseLoc to current application's NSEvent's mouseLocation()
    return (item 1 of mouseLoc as integer) & "," & (item 2 of mouseLoc as integer)
    '''
    try:
        result = run_applescript(script)
        current_x, current_y = map(int, result.split(','))
    except:
        current_x, current_y = 960, 540
    
    distance = math.sqrt((x - current_x)**2 + (y - current_y)**2)
    num_steps = int(distance / 10) + 10
    
    for i in range(1, num_steps + 1):
        progress = i / num_steps
        curve = math.sin(progress * math.pi) * random.uniform(-10, 10)
        intermediate_x = current_x + (x - current_x) * progress + curve
        intermediate_y = current_y + (y - current_y) * progress + curve * 0.5
        
        subprocess.run(['cliclick', f'm:{int(intermediate_x)},{int(intermediate_y)}'], 
                      capture_output=True)
        time.sleep(duration / num_steps + random.uniform(-0.001, 0.001))
    
    subprocess.run(['cliclick', f'm:{x},{y}'], capture_output=True)


def click_at_coordinates(x, y):
    """Click at specified coordinates"""
    subprocess.run(['cliclick', f'c:{x},{y}'], capture_output=True)
    time.sleep(1)


def try_fixed_coordinates_click():
    """Try clicking at fixed coordinates (first Google result)"""
    print(f"\n{'='*80}")
    print("ATTEMPT: Fixed Coordinates (Fast Path)")
    print(f"{'='*80}")
    
    bring_chrome_to_front()
    time.sleep(0.3)
    
    print(f"→ Clicking at fixed position {FIXED_CLICK_COORDINATES}...")
    human_like_mouse_movement(FIXED_CLICK_COORDINATES[0], FIXED_CLICK_COORDINATES[1], duration=0.8)
    click_at_coordinates(FIXED_CLICK_COORDINATES[0], FIXED_CLICK_COORDINATES[1])
    
    print(f"→ Waiting {PAGE_LOAD_WAIT} seconds for page to load...")
    time.sleep(PAGE_LOAD_WAIT)
    
    is_valid, url = validate_realestate_url()
    return is_valid, url


def try_gpt_vision_click(attempt_num):
    """Try clicking using GPT Vision"""
    print(f"\n{'='*80}")
    print(f"ATTEMPT {attempt_num}: GPT Vision Analysis (Fallback Path)")
    print(f"{'='*80}")
    
    # Take screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"gpt_attempt_{attempt_num}_{timestamp}.png")
    window_bounds = take_screenshot(screenshot_path)
    
    # Analyze with GPT
    gpt_result = analyze_screenshot_with_gpt(screenshot_path, SEARCH_ADDRESS)
    
    if not gpt_result.get("found", False):
        print("✗ GPT could not find suitable link")
        return False, None
    
    # Get and adjust coordinates
    click_x = gpt_result.get("x")
    click_y = gpt_result.get("y")
    
    if window_bounds:
        x1, y1, x2, y2 = window_bounds
        click_x += x1
        click_y += y1
    
    print(f"→ Moving mouse to GPT coordinates ({click_x}, {click_y})...")
    bring_chrome_to_front()
    time.sleep(0.3)
    human_like_mouse_movement(click_x, click_y, duration=0.8)
    time.sleep(0.3)
    click_at_coordinates(click_x, click_y)
    
    print(f"→ Waiting {PAGE_LOAD_WAIT} seconds for page to load...")
    time.sleep(PAGE_LOAD_WAIT)
    
    is_valid, url = validate_realestate_url()
    return is_valid, url


def main():
    """Main hybrid workflow"""
    print("\n" + "=" * 80)
    print("HYBRID SMART CLICKER - PRODUCTION SYSTEM")
    print("Fixed Coordinates First + GPT Vision Fallback")
    print("=" * 80)
    print(f"\nSearch Address: {SEARCH_ADDRESS}")
    print(f"Strategy: Try fixed position first, fallback to GPT Vision if needed")
    print(f"Max GPT Retries: {MAX_GPT_RETRIES}")
    print("\n" + "=" * 80)
    
    start_time = datetime.now()
    success_method = None
    final_url = None
    
    try:
        # Open Chrome and search
        print("\n→ Opening Chrome and searching...")
        open_chrome_and_search(SEARCH_ADDRESS)
        
        # STEP 1: Try fixed coordinates (90% success rate)
        is_valid, url = try_fixed_coordinates_click()
        
        if is_valid:
            success_method = "FIXED_COORDINATES"
            final_url = url
            print(f"\n{'='*80}")
            print("✅ SUCCESS WITH FIXED COORDINATES!")
            print(f"{'='*80}")
        else:
            # STEP 2: Fallback to GPT Vision
            print(f"\n⚠ Fixed coordinates failed, starting GPT Vision fallback...")
            
            for attempt in range(1, MAX_GPT_RETRIES + 1):
                navigate_back()
                
                is_valid, url = try_gpt_vision_click(attempt)
                
                if is_valid:
                    success_method = f"GPT_VISION_ATTEMPT_{attempt}"
                    final_url = url
                    print(f"\n{'='*80}")
                    print(f"✅ SUCCESS WITH GPT VISION (Attempt {attempt})!")
                    print(f"{'='*80}")
                    break
            
            if not success_method:
                print(f"\n{'='*80}")
                print("❌ ALL ATTEMPTS FAILED")
                print(f"{'='*80}")
                return
        
        # Take final screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = os.path.join(SCREENSHOT_DIR, f"final_success_{timestamp}.png")
        take_screenshot(final_screenshot)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Success summary
        print(f"\n{'='*80}")
        print("WORKFLOW COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")
        print(f"\nSearch Address: {SEARCH_ADDRESS}")
        print(f"Success Method: {success_method}")
        print(f"Final URL: {final_url}")
        print(f"Total Time: {duration}")
        print(f"Screenshot: {os.path.abspath(final_screenshot)}")
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ Error in workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
