#!/usr/bin/env python3
"""
Test OpenAI API Connection
Verifies API key and model availability
"""

from openai import OpenAI
import sys

# Configuration
OPENAI_API_KEY = "REDACTED_OPENAI_KEY"
GPT_MODEL = "gpt-5-nano-2025-08-07"

def test_api_connection():
    """Test basic API connection"""
    print("=" * 70)
    print("OpenAI API Connection Test")
    print("=" * 70)
    print(f"\nAPI Key: {OPENAI_API_KEY[:20]}...{OPENAI_API_KEY[-10:]}")
    print(f"Model: {GPT_MODEL}")
    print("\n" + "-" * 70)
    
    try:
        # Initialize client
        print("\n→ Initializing OpenAI client...")
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✓ Client initialized")
        
        # Test simple completion
        print("\n→ Testing basic text completion...")
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'API connection successful' if you receive this message."
                }
            ],
            max_completion_tokens=50
        )
        
        print("✓ Text completion successful")
        print(f"\nResponse: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens}")
        
        print("\n" + "=" * 70)
        print("✅ API CONNECTION TEST PASSED")
        print("=" * 70)
        print("\nThe API key and model are working correctly.")
        print("You can now proceed with vision API testing.")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ API CONNECTION TEST FAILED")
        print("=" * 70)
        print(f"\nError: {str(e)}")
        print("\nPossible issues:")
        print("1. Invalid API key")
        print("2. Model name incorrect")
        print("3. Insufficient API credits")
        print("4. Network connectivity issues")
        print("5. API endpoint not available")
        
        # Check for specific error types
        error_str = str(e).lower()
        if "authentication" in error_str or "api key" in error_str:
            print("\n→ Issue appears to be with API authentication")
            print("   Please verify your API key is correct and active")
        elif "model" in error_str or "not found" in error_str:
            print("\n→ Issue appears to be with the model name")
            print("   The model 'gpt-5-nano-2025-08-07' may not exist")
            print("   Try using a standard model like 'gpt-4-vision-preview' or 'gpt-4o'")
        
        return False


def test_vision_api():
    """Test vision API with a simple base64 encoded test"""
    print("\n" + "=" * 70)
    print("Testing Vision API (if basic test passed)")
    print("=" * 70)
    
    # Create a minimal test image (1x1 pixel PNG in base64)
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    try:
        print("\n→ Testing vision API with minimal image...")
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What do you see in this image? Just say 'Vision API working'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{test_image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=50
        )
        
        print("✓ Vision API test successful")
        print(f"\nResponse: {response.choices[0].message.content}")
        print("\n" + "=" * 70)
        print("✅ VISION API TEST PASSED")
        print("=" * 70)
        print("\nThe script is ready to use with screenshot analysis!")
        
        return True
        
    except Exception as e:
        print("\n❌ Vision API test failed")
        print(f"Error: {str(e)}")
        print("\nNote: The model may not support vision capabilities.")
        print("For vision tasks, use models like:")
        print("  - gpt-4-vision-preview")
        print("  - gpt-4o")
        print("  - gpt-4o-mini")
        
        return False


if __name__ == "__main__":
    print("\n")
    
    # Test basic API connection
    basic_test_passed = test_api_connection()
    
    if basic_test_passed:
        # If basic test passed, try vision API
        vision_test_passed = test_vision_api()
        
        if vision_test_passed:
            sys.exit(0)
        else:
            print("\n⚠ Vision API test failed but basic API works.")
            print("You may need to use a different model for vision tasks.")
            sys.exit(1)
    else:
        print("\n⚠ Basic API test failed. Please fix the API configuration first.")
        sys.exit(1)
