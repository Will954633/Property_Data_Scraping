#!/usr/bin/env python3
"""Test childcare and medical_center types"""

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

# Test child_care
print("Testing 'child_care' type...")
payload1 = {
    "includedTypes": ["child_care"],
    "maxResultCount": 5,
    "locationRestriction": {
        "circle": {
            "center": {"latitude": -28.110, "longitude": 153.407},
            "radius": 5000
        }
    }
}

response1 = requests.post(url, json=payload1, headers=headers)
print(f"Status: {response1.status_code}")
print(f"Response: {response1.text}\n")

# Test medical_center
print("Testing 'medical_center' type...")
payload2 = {
    "includedTypes": ["medical_center"],
    "maxResultCount": 5,
    "locationRestriction": {
        "circle": {
            "center": {"latitude": -28.110, "longitude": 153.407},
            "radius": 5000
        }
    }
}

response2 = requests.post(url, json=payload2, headers=headers)
print(f"Status: {response2.status_code}")
print(f"Response: {response2.text}\n")

# Test alternative: day_care
print("Testing 'day_care' as alternative...")
payload3 = {
    "includedTypes": ["day_care"],
    "maxResultCount": 5,
    "locationRestriction": {
        "circle": {
            "center": {"latitude": -28.110, "longitude": 153.407},
            "radius": 5000
        }
    }
}

response3 = requests.post(url, json=payload3, headers=headers)
print(f"Status: {response3.status_code}")
print(f"Response: {response3.text}\n")

# Test alternative: doctor
print("Testing 'doctor' as alternative to medical_center...")
payload4 = {
    "includedTypes": ["doctor"],
    "maxResultCount": 5,
    "locationRestriction": {
        "circle": {
            "center": {"latitude": -28.110, "longitude": 153.407},
            "radius": 5000
        }
    }
}

response4 = requests.post(url, json=payload4, headers=headers)
print(f"Status: {response4.status_code}")
print(f"Response: {response4.text}")
