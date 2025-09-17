#!/usr/bin/env python3
"""
Simple test of IRIS storage with JJ Thompson
"""

import requests
import json
import time
import base64
from datetime import datetime

# JJ Thompson's credentials
JJ_USER_ID = "01087874-747b-4159-8735-5ebb8715ff84"
BASE_URL = "http://localhost:8008"

def test_simple_storage():
    """Simple test - just try to store a photo"""
    
    print("SIMPLE IRIS STORAGE TEST")
    print("=" * 40)
    
    session_id = f"jj_simple_{int(time.time())}"
    timestamp = int(time.time())
    
    # Create test image
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
    test_image = "data:image/png;base64," + base64.b64encode(png_data).decode('utf-8')
    
    # Send request
    print(f"Sending: 'Add this roof photo to my backyard'")
    
    response = requests.post(
        f"{BASE_URL}/api/iris/unified-chat",
        json={
            "message": "Add this roof photo to my backyard",
            "user_id": JJ_USER_ID,
            "session_id": session_id,
            "context_type": "property",
            "images": [{
                "data": test_image,
                "filename": f"roof_{timestamp}.png",
                "size": 1000,
                "type": "image/png"
            }]
        },
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        response_text = data.get('response', '')
        print(f"Response: {response_text[:300]}")
        
        # Check for success indicators
        if "Successfully added" in response_text or "saved" in response_text.lower():
            print("\nSUCCESS: IRIS confirmed storage!")
            return True
        else:
            print("\nFAILED: IRIS didn't confirm storage")
            print("Full response:", response_text)
    else:
        print(f"ERROR: {response.text[:200]}")
    
    return False

if __name__ == "__main__":
    success = test_simple_storage()
    print("\n" + "=" * 40)
    print("Result:", "PASSED" if success else "FAILED")