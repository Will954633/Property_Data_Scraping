#!/usr/bin/env python3
"""Test Google Places API to see detailed error"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

url = "https://places.googleapis.com/v1/places:searchNearby"

headers = {
    'X-Goog-Api-Key': GOOGLE_API_KEY,
    'X-Goog-FieldMask': 'places.displayName,places.id,places.location,places.rating,places.userRatingCount',
    'Content-Type': 'application/json'
}

payload = {
    "includedTypes": ["primary_school"],
    "maxResultCount": 5,
    "locationRestriction": {
        "circle": {
            "center": {
                "latitude": -28.110,
                "longitude": 153.407
            },
            "radius": 5000
        }
    },
    "rankPreference": "DISTANCE"
}

print("Testing Google Places API...")
print(f"URL: {url}")
print(f"API Key: {GOOGLE_API_KEY[:20]}...")
print(f"\nPayload: {payload}")

response = requests.post(url, json=payload, headers=headers)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("\n✓ API call successful!")
    data = response.json()
    print(f"Found {len(data.get('places', []))} places")
else:
    print("\n✗ API call failed!")
    print(f"Error details: {response.text}")
