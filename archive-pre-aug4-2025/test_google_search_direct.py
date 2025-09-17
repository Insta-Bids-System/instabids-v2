#!/usr/bin/env python3
"""
Test Google Maps API directly to debug search
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
print(f"Google API Key: {'Found' if google_api_key else 'NOT FOUND'}")

if not google_api_key:
    print("No API key found!")
    exit(1)

# Test different search variations
search_variations = [
    "JM Holiday Lighting South Florida",
    "JM Holiday Lighting",
    "J M Holiday Lighting",
    "jmholidaylighting.com",
    "JM Holiday Lighting Christmas lights South Florida"
]

url = "https://places.googleapis.com/v1/places:searchText"

headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': google_api_key,
    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount'
}

for query in search_variations:
    print(f"\n{'='*60}")
    print(f"Testing query: '{query}'")
    print(f"{'='*60}")
    
    request_body = {
        'textQuery': query,
        'pageSize': 3,
        'locationBias': {
            'circle': {
                'center': {
                    'latitude': 26.3683,  # South Florida
                    'longitude': -80.1289
                },
                'radius': 50000  # 50km (max allowed)
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=request_body)
    
    if response.status_code == 200:
        data = response.json()
        places = data.get('places', [])
        
        if places:
            print(f"Found {len(places)} results:")
            for i, place in enumerate(places, 1):
                name = place.get('displayName', {}).get('text', 'Unknown')
                phone = place.get('nationalPhoneNumber', 'No phone')
                website = place.get('websiteUri', 'No website')
                address = place.get('formattedAddress', 'No address')
                
                print(f"\n{i}. {name}")
                print(f"   Phone: {phone}")
                print(f"   Website: {website}")
                print(f"   Address: {address}")
        else:
            print("No results found")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Also try legacy Places API
print("\n\n=== TRYING LEGACY PLACES API ===")
legacy_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

for query in search_variations[:2]:
    print(f"\nQuery: '{query}'")
    
    params = {
        'query': query,
        'key': google_api_key
    }
    
    response = requests.get(legacy_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'OK' and data.get('results'):
            print(f"Found {len(data['results'])} results")
            result = data['results'][0]
            print(f"Name: {result.get('name')}")
            print(f"Address: {result.get('formatted_address')}")
        else:
            print(f"Status: {data.get('status')}")
    else:
        print(f"Error: {response.status_code}")