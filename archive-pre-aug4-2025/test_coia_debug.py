#!/usr/bin/env python3
"""
Debug test for CoIA agent
"""

import requests
import json

def test_coia_debug():
    """Test CoIA with detailed output"""
    
    print("=== COIA DEBUG TEST ===")
    
    # Test 1: Basic health check
    print("\n1. Health check...")
    health = requests.get("http://localhost:8008/")
    if health.status_code == 200:
        data = health.json()
        print(f"Server status: {data['status']}")
        print(f"CoIA agent: {data['agents']['coia']}")
    else:
        print(f"ERROR: Server not responding (status {health.status_code})")
        return
    
    # Test 2: Send business name
    print("\n2. Sending business name...")
    
    response = requests.post("http://localhost:8008/api/contractor-chat/message", json={
        "session_id": "test_coia_debug",
        "message": "I own JM Holiday Lighting in South Florida", 
        "current_stage": "welcome",
        "profile_data": {}
    })
    
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Stage: {data.get('stage', 'unknown')}")
            print(f"Response: {data.get('response', 'No response')[:200]}...")
            print(f"Profile progress: {json.dumps(data.get('profile_progress', {}), indent=2)}")
        except Exception as e:
            print(f"ERROR parsing response: {e}")
            print(f"Raw response: {response.text[:500]}")
    else:
        print(f"ERROR: Request failed")
        print(f"Response: {response.text[:500]}")

if __name__ == "__main__":
    test_coia_debug()