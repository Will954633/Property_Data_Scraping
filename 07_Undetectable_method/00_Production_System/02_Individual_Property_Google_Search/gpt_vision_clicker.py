#!/usr/bin/env python3
"""
GPT Vision-Based Link Clicker
Uses OpenAI GPT-4 Vision to analyze Google search results and find realestate.com.au links
Then clicks on the identified coordinates using human-like mouse movement
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
INITIAL_LOAD_DELAY = 5
CLICK_DELAY = 2  # Wait before clicking after getting coordinates


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
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Open Chrome with new window
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
    
    # Maximize the window
    maximize_chrome_window()
    
    # Focus on the address bar (Command+L)
    bring_chrome_to_front()
    time.sleep(0.5)
    focus_address_bar()
    time.sleep(0.5)
    
    # Type the address
    type_text(address)
    print(f"✓ Typed address: {address}")
    time.sleep(0.5)
    
    # Press Enter to search
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
    # Escape any special characters for AppleScript
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
        print(f"✓ Screenshot captured (bounds: {bounds})")
        return bounds
    else:
        # Fallback to full screen
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
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Encode image
    base64_image = encode_image_to_base64(screenshot_path)
    
    # Create prompt for GPT
    prompt = f"""You are analyzing a Google search results page screenshot. 

The user searched for: "{search_address}"

Your task is to find the realestate.com.au link that matches this search address and provide the exact pixel coordinates where the user should click.

Look for:
1. A search result from realestate.com.au domain
2. The title or URL should contain or relate to the searched address
3. It should be a clickable link (usually has a blue/purple color)

IMPORTANT: Provide your response in this EXACT JSON format (no additional text):
{{
    "found": true or false,
    "x": pixel_x_coordinate,
    "y": pixel_y_coordinate,
    "confidence": "high" or "medium" or "low",
    "reasoning": "brief explanation of what you found"
}}

If you cannot find a suitable realestate.com.au link, set "found" to false.

Analyze the image carefully and provide the click coordinates for the CENTER of the clickable link text or title."""
    
    try:
        # Make API call
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=2000
        )
        
        # Parse response
        response_text = response.choices[0].message.content
        
        print(f"\n✓ GPT Response received:")
        print(f"Raw response: '{response_text}'")
        print(f"Response length: {len(response_text) if response_text else 0} characters")
        
        # Check if response is empty or None
        if not response_text or response_text.strip() == "":
            print("\n❌ GPT returned an empty response")
            print("This may indicate:")
            print("  - The model doesn't support vision capabilities properly")
            print("  - The image was too large")
            print("  - Content policy restrictions")
            return {
                "found": False,
                "error": "Empty response from GPT",
                "raw_response": response_text
            }
        
        response_text = response_text.strip()
        print(f"\nCleaned response: '{response_text}'")
        
        # Try to extract JSON from response
        # Remove code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as json_err:
            print(f"\n❌ Failed to parse JSON: {json_err}")
            print(f"Attempted to parse: '{response_text}'")
            return {
                "found": False,
                "error": f"JSON parse error: {json_err}",
                "raw_response": response_text
            }
        
    except Exception as e:
        print(f"\n❌ Error calling GPT API: {e}")
        import traceback
        traceback.print_exc()
        return {
            "found": False,
            "error": str(e)
        }


def human_like_mouse_movement(x, y, duration=0.5):
    """Move mouse to coordinates with human-like curved movement"""
    print(f"\n→ Moving mouse to coordinates ({x}, {y}) with human-like movement...")
    
    # Get current mouse position
    script = '''
    use framework "CoreGraphics"
    set mouseLoc to current application's NSEvent's mouseLocation()
    return (item 1 of mouseLoc as integer) & "," & (item 2 of mouseLoc as integer)
    '''
    try:
        result = run_applescript(script)
        current_x, current_y = map(int, result.split(','))
    except:
        # Default to center of screen if we can't get current position
        current_x, current_y = 960, 540
    
    print(f"  Current position: ({current_x}, {current_y})")
    
    # Calculate number of steps based on distance
    distance = math.sqrt((x - current_x)**2 + (y - current_y)**2)
    num_steps = int(distance / 10) + 10  # At least 10 steps
    
    # Generate points along a curved path
    for i in range(1, num_steps + 1):
        progress = i / num_steps
        
        # Add some curve to the movement
        curve = math.sin(progress * math.pi) * random.uniform(-10, 10)
        
        # Calculate intermediate position
        intermediate_x = current_x + (x - current_x) * progress + curve
        intermediate_y = current_y + (y - current_y) * progress + curve * 0.5
        
        # Move mouse using cliclick
        subprocess.run(['cliclick', f'm:{int(intermediate_x)},{int(intermediate_y)}'], 
                      capture_output=True)
        
        # Variable delay to simulate human movement
        time.sleep(duration / num_steps + random.uniform(-0.001, 0.001))
    
    # Final precise movement to exact coordinates
    subprocess.run(['cliclick', f'm:{x},{y}'], capture_output=True)
    print(f"✓ Mouse moved to target position")


def click_at_coordinates(x, y):
    """Click at the specified coordinates using cliclick"""
    print(f"\n→ Clicking at coordinates ({x}, {y})...")
    
    # Single click
    subprocess.run(['cliclick', f'c:{x},{y}'], capture_output=True)
    print(f"✓ Clicked!")
    time.sleep(1)


def check_cliclick_installed():
    """Check if cliclick is installed"""
    try:
        result = subprocess.run(['which', 'cliclick'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ cliclick is installed")
            return True
        else:
            print("\n❌ cliclick is not installed!")
            print("\nTo install cliclick, run:")
            print("  brew install cliclick")
            return False
    except Exception as e:
        print(f"\n❌ Error checking for cliclick: {e}")
        return False


def main():
    """Main workflow"""
    print("\n" + "=" * 80)
    print("GPT VISION-BASED LINK CLICKER")
    print("REALESTATE.COM.AU LINK DETECTION AND CLICKING")
    print("=" * 80)
    print(f"\nSearch Address: {SEARCH_ADDRESS}")
    print(f"GPT Model: {GPT_MODEL}")
    print(f"\nWorkflow:")
    print("  1. Open Chrome in maximized window")
    print("  2. Search for address on Google")
    print("  3. Take screenshot of results")
    print("  4. Send screenshot to GPT Vision API")
    print("  5. Get click coordinates from GPT")
    print("  6. Move mouse naturally to coordinates")
    print("  7. Click on the realestate.com.au link")
    print("\n" + "=" * 80)
    
    # Check for cliclick
    if not check_cliclick_installed():
        return
    
    start_time = datetime.now()
    
    try:
        # Step 1 & 2: Open Chrome and search
        print("\n→ Step 1-2: Opening Chrome and searching...")
        open_chrome_and_search(SEARCH_ADDRESS)
        
        # Step 3: Take screenshot
        print("\n→ Step 3: Taking screenshot...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"google_search_{timestamp}.png")
        window_bounds = take_screenshot(screenshot_path)
        
        # Step 4 & 5: Analyze with GPT and get coordinates
        print("\n→ Step 4-5: Analyzing with GPT Vision...")
        gpt_result = analyze_screenshot_with_gpt(screenshot_path, SEARCH_ADDRESS)
        
        # Check if link was found
        if not gpt_result.get("found", False):
            print("\n❌ GPT could not find a suitable realestate.com.au link")
            if "reasoning" in gpt_result:
                print(f"Reasoning: {gpt_result['reasoning']}")
            return
        
        # Get coordinates
        click_x = gpt_result.get("x")
        click_y = gpt_result.get("y")
        confidence = gpt_result.get("confidence", "unknown")
        reasoning = gpt_result.get("reasoning", "")
        
        print(f"\n✓ Link found!")
        print(f"  Coordinates: ({click_x}, {click_y})")
        print(f"  Confidence: {confidence}")
        print(f"  Reasoning: {reasoning}")
        
        # Adjust coordinates if screenshot was taken with bounds
        if window_bounds:
            x1, y1, x2, y2 = window_bounds
            click_x += x1
            click_y += y1
            print(f"  Adjusted coordinates (with window offset): ({click_x}, {click_y})")
        
        # Wait before clicking
        print(f"\n→ Waiting {CLICK_DELAY} seconds before clicking...")
        time.sleep(CLICK_DELAY)
        
        # Step 6 & 7: Move mouse and click
        bring_chrome_to_front()
        time.sleep(0.3)
        human_like_mouse_movement(click_x, click_y, duration=0.8)
        time.sleep(0.3)
        click_at_coordinates(click_x, click_y)
        
        # Wait for page to load
        print("\n→ Waiting for realestate.com.au page to load...")
        time.sleep(3)
        
        # Take final screenshot
        final_screenshot_path = os.path.join(SCREENSHOT_DIR, f"after_click_{timestamp}.png")
        take_screenshot(final_screenshot_path)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\nSearch Address: {SEARCH_ADDRESS}")
        print(f"Screenshot: {os.path.abspath(screenshot_path)}")
        print(f"After Click: {os.path.abspath(final_screenshot_path)}")
        print(f"Total Time: {duration}")
        print(f"\nThe realestate.com.au page should now be loaded in Chrome.")
        print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error in workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
