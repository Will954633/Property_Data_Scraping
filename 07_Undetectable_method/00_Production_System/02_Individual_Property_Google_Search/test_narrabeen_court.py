#!/usr/bin/env python3
"""
Test Script for 13 Narrabeen Court, Robina
Direct GPT Vision test for this specific address
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
TEST_ADDRESS = "13 Narrabeen Court, Robina"
SCREENSHOT_DIR = "screenshots"
INITIAL_LOAD_DELAY = 5
PAGE_LOAD_WAIT = 3
VALIDATION_DELAY = 1


def run_applescript(script):
    process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return process.stdout.strip()


def maximize_chrome_window():
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
        time.sleep(0.5)
    except:
        pass


def bring_chrome_to_front():
    script = 'tell application "Google Chrome" to activate'
    run_applescript(script)


def focus_address_bar():
    script = '''
    tell application "System Events"
        keystroke "l" using command down
    end tell
    '''
    run_applescript(script)


def type_text(text):
    text = text.replace('"', '\\"')
    script = f'''
    tell application "System Events"
        keystroke "{text}"
    end tell
    '''
    run_applescript(script)


def press_enter():
    script = '''
    tell application "System Events"
        key code 36
    end tell
    '''
    run_applescript(script)


def get_current_url():
    script = '''
    tell application "Google Chrome"
        get URL of active tab of front window
    end tell
    '''
    try:
        return run_applescript(script)
    except:
        return None


def validate_realestate_url():
    time.sleep(VALIDATION_DELAY)
    url = get_current_url()
    if url and "realestate.com.au" in url.lower():
        return True, url
    else:
        return False, url


def get_chrome_window_bounds():
    script = '''
    tell application "Google Chrome"
        set windowBounds to bounds of front window
        return windowBounds
    end tell
    '''
    result = run_applescript(script)
    if result:
        try:
            return [int(x.strip()) for x in result.split(',')]
        except:
            return None
    return None


def take_screenshot(filepath):
    bring_chrome_to_front()
    time.sleep(0.5)
    bounds = get_chrome_window_bounds()
    if bounds:
        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1
        subprocess.run(['screencapture', '-x', '-R', f'{x1},{y1},{width},{height}', filepath])
        return bounds
    else:
        subprocess.run(['screencapture', '-x', filepath])
        return None


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_with_gpt(screenshot_path, address):
    print(f"\n→ Sending screenshot to GPT Vision API...")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    base64_image = encode_image_to_base64(screenshot_path)
    
    prompt = f"""Analyze this Google search results screenshot for: "{address}"
Find the realestate.com.au link matching this address and provide click coordinates.
Return ONLY this JSON (no other text):
{{
    "found": true/false,
    "x": pixel_x,
    "y": pixel_y,
    "confidence": "high"/"medium"/"low",
    "reasoning": "brief explanation"
}}"""
    
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        max_completion_tokens=2000
    )
    
    response_text = response.choices[0].message.content.strip()
    
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    
    result = json.loads(response_text)
    
    print(f"\n✓ GPT Response:")
    print(json.dumps(result, indent=2))
    
    return result


def human_like_mouse_movement(x, y, duration=0.5):
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
        subprocess.run(['cliclick', f'm:{int(intermediate_x)},{int(intermediate_y)}'], capture_output=True)
        time.sleep(duration / num_steps + random.uniform(-0.001, 0.001))
    
    subprocess.run(['cliclick', f'm:{x},{y}'], capture_output=True)


def click_at_coordinates(x, y):
    subprocess.run(['cliclick', f'c:{x},{y}'], capture_output=True)
    time.sleep(1)


def main():
    print("\n" + "=" * 80)
    print("TESTING: 13 Narrabeen Court, Robina")
    print("Direct GPT Vision Test")
    print("=" * 80)
    
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Open Chrome and search
    print(f"\n→ Opening Chrome and searching for: {TEST_ADDRESS}")
    script = '''
    tell application "Google Chrome"
        activate
        make new window
        set URL of active tab of front window to "about:blank"
    end tell
    '''
    run_applescript(script)
    time.sleep(1)
    
    maximize_chrome_window()
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    type_text(TEST_ADDRESS)
    time.sleep(0.5)
    press_enter()
    
    print(f"→ Waiting {INITIAL_LOAD_DELAY} seconds for Google results...")
    time.sleep(INITIAL_LOAD_DELAY)
    
    # Take screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"narrabeen_court_{timestamp}.png")
    
    print(f"\n→ Taking screenshot...")
    window_bounds = take_screenshot(screenshot_path)
    print(f"✓ Screenshot saved: {screenshot_path}")
    
    # Analyze with GPT
    print(f"\n{'='*80}")
    print("GPT VISION ANALYSIS")
    print(f"{'='*80}")
    
    try:
        gpt_result = analyze_with_gpt(screenshot_path, TEST_ADDRESS)
        
        if not gpt_result.get("found"):
            print(f"\n❌ GPT could not find link")
            print(f"Reasoning: {gpt_result.get('reasoning', 'N/A')}")
            return
        
        # Get coordinates
        click_x = gpt_result.get("x")
        click_y = gpt_result.get("y")
        
        print(f"\n✓ GPT found link!")
        print(f"  Screenshot coordinates: ({click_x}, {click_y})")
        print(f"  Confidence: {gpt_result.get('confidence')}")
        print(f"  Reasoning: {gpt_result.get('reasoning')}")
        
        # Adjust for window bounds if needed
        if window_bounds:
            x1, y1, x2, y2 = window_bounds
            adjusted_x = click_x + x1
            adjusted_y = click_y + y1
            print(f"  Adjusted coordinates (with window offset): ({adjusted_x}, {adjusted_y})")
        else:
            adjusted_x = click_x
            adjusted_y = click_y
        
        # Click
        print(f"\n→ Moving mouse and clicking...")
        bring_chrome_to_front()
        time.sleep(0.3)
        human_like_mouse_movement(adjusted_x, adjusted_y, duration=0.8)
        time.sleep(0.3)
        click_at_coordinates(adjusted_x, adjusted_y)
        
        print(f"→ Waiting {PAGE_LOAD_WAIT} seconds for page to load...")
        time.sleep(PAGE_LOAD_WAIT)
        
        # Validate
        print(f"\n{'='*80}")
        print("URL VALIDATION")
        print(f"{'='*80}")
        
        is_valid, final_url = validate_realestate_url()
        
        if is_valid:
            print(f"\n✅ SUCCESS!")
            print(f"  Final URL: {final_url}")
            print(f"  ✓ URL contains 'realestate.com.au'")
        else:
            print(f"\n❌ FAILED!")
            print(f"  Actual URL: {final_url}")
            print(f"  ✗ URL does NOT contain 'realestate.com.au'")
            print(f"\n  GPT provided coordinates: ({click_x}, {click_y})")
            print(f"  These coordinates did not lead to correct page")
        
        # Take final screenshot
        final_screenshot = os.path.join(SCREENSHOT_DIR, f"narrabeen_final_{timestamp}.png")
        take_screenshot(final_screenshot)
        print(f"\n  Final screenshot: {final_screenshot}")
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
