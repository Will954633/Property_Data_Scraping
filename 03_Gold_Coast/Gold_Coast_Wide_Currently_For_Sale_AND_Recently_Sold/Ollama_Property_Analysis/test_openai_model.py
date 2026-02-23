#!/usr/bin/env python3
"""
Test OpenAI GPT-5-nano model for floor plan analysis
Last Updated: 06/02/2026, Thursday, 11:08 AM (Brisbane)
"""
import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-nano-2025-08-07")

print("="*80)
print("TESTING OPENAI GPT-5-NANO MODEL")
print("="*80)
print(f"Model: {OPENAI_MODEL}")
print(f"API Key: {OPENAI_API_KEY[:20]}..." if OPENAI_API_KEY else "API Key: NOT FOUND")
print("="*80)

# Test with a simple text prompt first
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

payload = {
    "model": OPENAI_MODEL,
    "messages": [
        {
            "role": "user",
            "content": "Hello! Please respond with a simple JSON object containing your model name and a test message."
        }
    ],
    # gpt-5-nano only supports temperature=1 (default), so we omit it
    "max_completion_tokens": 100  # gpt-5-nano uses max_completion_tokens instead of max_tokens
}

print("\nSending test request to OpenAI API...")
print(f"URL: https://api.openai.com/v1/chat/completions")
print(f"Model: {OPENAI_MODEL}")
print("\n" + "="*80)

try:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print("\nFull Response:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n" + "="*80)
        print("✅ SUCCESS - Model is accessible")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ ERROR - Check the response above for details")
        print("="*80)
        
except Exception as e:
    print(f"\n❌ Exception occurred: {e}")
    print("\n" + "="*80)
    print("ERROR DETAILS")
    print("="*80)
    import traceback
    traceback.print_exc()
