#!/usr/bin/env python3
"""
Test IRIS entry point debug logging with simple text message
"""

import requests
import json

def test_iris_entry_debug():
    """Test that we can see our entry point debug messages"""
    base_url = "http://localhost:8008"
    
    print("IRIS ENTRY DEBUG TEST")
    print("=" * 40)
    print("Testing simple text message to verify entry point...")
    
    # Simple text message - no images
    response = requests.post(f"{base_url}/api/iris/unified-chat", json={
        "user_id": "01087874-747b-4159-8735-5ebb8715ff84",  # JJ Thompson
        "session_id": "debug_entry_test_v2", 
        "message": "Test updated code version",
        "context_type": "property"
    }, timeout=30)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:100]}...")
    
    if response.status_code == 200:
        print("SUCCESS: Request reached backend successfully")
        print("Check backend logs for 'NEW CODE LOADED' messages")
    else:
        print(f"FAILED: Request failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_iris_entry_debug()