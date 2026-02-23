#!/usr/bin/env python3
"""
Test GPT Vision API with Existing Screenshot
Tests the GPT Vision API using a saved screenshot to debug and verify responses
"""

import base64
import json
from openai import OpenAI

# Configuration
OPENAI_API_KEY = "REDACTED_OPENAI_KEY"
GPT_MODEL = "gpt-5-nano-2025-08-07"
SCREENSHOT_PATH = "screenshots/google_search_20251113_144509.png"
SEARCH_ADDRESS = "279 Ron Penhaligon Way, Robina"


def encode_image_to_base64(image_path):
    """Encode image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def test_gpt_vision():
    """Test GPT Vision API with the screenshot"""
    print("=" * 80)
    print("GPT VISION API TEST WITH SCREENSHOT")
    print("=" * 80)
    print(f"\nScreenshot: {SCREENSHOT_PATH}")
    print(f"Search Address: {SEARCH_ADDRESS}")
    print(f"Model: {GPT_MODEL}")
    print("\n" + "-" * 80)
    
    # Encode image
    print("\n→ Encoding screenshot to base64...")
    try:
        base64_image = encode_image_to_base64(SCREENSHOT_PATH)
        print(f"✓ Image encoded successfully")
        print(f"  Base64 length: {len(base64_image)} characters")
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return
    
    # Initialize OpenAI client
    print("\n→ Initializing OpenAI client...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("✓ Client initialized")
    
    # Create prompt
    prompt = f"""You are analyzing a Google search results page screenshot. 

The user searched for: "{SEARCH_ADDRESS}"

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
    
    print("\n→ Sending request to GPT Vision API...")
    print(f"  Prompt length: {len(prompt)} characters")
    
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
        
        print("✓ API call successful")
        
        # Extract response
        response_content = response.choices[0].message.content
        
        print("\n" + "=" * 80)
        print("GPT RESPONSE")
        print("=" * 80)
        
        # Print raw response details
        print(f"\nResponse type: {type(response_content)}")
        print(f"Response is None: {response_content is None}")
        print(f"Response length: {len(response_content) if response_content else 0}")
        print(f"\nRaw response content:")
        print(f"'{response_content}'")
        
        # Check response metadata
        print(f"\n" + "-" * 80)
        print("Response Metadata:")
        print(f"  Model: {response.model}")
        print(f"  Finish reason: {response.choices[0].finish_reason}")
        if hasattr(response, 'usage'):
            print(f"  Tokens used: {response.usage.total_tokens}")
            print(f"    Prompt tokens: {response.usage.prompt_tokens}")
            print(f"    Completion tokens: {response.usage.completion_tokens}")
        
        # Try to parse if not empty
        if response_content and response_content.strip():
            print(f"\n" + "-" * 80)
            print("Attempting to parse JSON...")
            
            cleaned = response_content.strip()
            
            # Remove code blocks if present
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            print(f"Cleaned response: '{cleaned}'")
            
            try:
                result = json.loads(cleaned)
                print("\n✓ JSON parsed successfully!")
                print(json.dumps(result, indent=2))
                
                if result.get("found"):
                    print(f"\n" + "=" * 80)
                    print("✅ SUCCESS! Link found!")
                    print("=" * 80)
                    print(f"  Coordinates: ({result['x']}, {result['y']})")
                    print(f"  Confidence: {result.get('confidence', 'unknown')}")
                    print(f"  Reasoning: {result.get('reasoning', 'N/A')}")
                else:
                    print(f"\n⚠ Link not found in image")
                    print(f"  Reasoning: {result.get('reasoning', 'N/A')}")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON parsing failed: {e}")
        else:
            print(f"\n" + "-" * 80)
            print("❌ EMPTY RESPONSE FROM GPT")
            print("\nPossible reasons:")
            print("  1. Model doesn't support vision properly")
            print("  2. Content policy violation")
            print("  3. Image too large or format issue")
            print("  4. Model configuration issue")
            
    except Exception as e:
        print(f"\n❌ Error during API call: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n")
    test_gpt_vision()
    print("\n")
