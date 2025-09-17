"""
Test fixing expired OpenAI image URLs
"""

import requests
import json

BASE_URL = "http://localhost:8008"

def test_fix_expired_images():
    print("=== TESTING IMAGE URL FIX ===")
    
    # Call the fix endpoint
    response = requests.post(f"{BASE_URL}/api/iris/fix-expired-images")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_fix_expired_images()