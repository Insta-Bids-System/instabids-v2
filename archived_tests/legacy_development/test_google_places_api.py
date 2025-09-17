#!/usr/bin/env python3
"""
Test Google Places API for JM Holiday Lighting
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
root_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path, override=True)

def test_google_places():
    """Test Google Places API directly"""
    
    # Get API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    print(f"API Key loaded: {api_key[:20]}..." if api_key else "NO API KEY FOUND")
    
    if not api_key:
        print("ERROR: GOOGLE_MAPS_API_KEY not found in .env file")
        return
    
    # Search for JM Holiday Lighting
    query = "JM Holiday Lighting"
    
    print(f"\nSearching Google Places for: {query}")
    
    # Use Google Places API (New) Text Search
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.websiteUri,places.nationalPhoneNumber,places.businessStatus,places.rating,places.userRatingCount,places.regularOpeningHours,places.types,places.googleMapsUri,places.id"
    }
    
    data = {
        "textQuery": query,
        "languageCode": "en",
        "maxResultCount": 5  # Get top 5 results
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("places"):
                print(f"\nFound {len(result['places'])} results!\n")
                
                for i, place in enumerate(result["places"], 1):
                    print(f"Result #{i}:")
                    print(f"  Name: {place.get('displayName', {}).get('text', 'Unknown')}")
                    print(f"  Address: {place.get('formattedAddress', 'N/A')}")
                    print(f"  Phone: {place.get('nationalPhoneNumber', 'N/A')}")
                    print(f"  Website: {place.get('websiteUri', 'N/A')}")
                    print(f"  Rating: {place.get('rating', 'N/A')} ({place.get('userRatingCount', 0)} reviews)")
                    print(f"  Status: {place.get('businessStatus', 'N/A')}")
                    print(f"  Google Maps: {place.get('googleMapsUri', 'N/A')}")
                    print(f"  Types: {', '.join(place.get('types', []))}")
                    print()
            else:
                print("No results found")
                print("Response:", result)
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_google_places()