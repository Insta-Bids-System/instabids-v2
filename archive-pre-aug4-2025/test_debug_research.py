#!/usr/bin/env python3
"""
Debug research to see what's happening
"""

import requests
import json
import time

def test_debug():
    """Test with debug output"""
    
    print("=== DEBUGGING INTELLIGENT RESEARCH ===")
    
    session_id = f"debug_{int(time.time())}"
    
    # Make the API call
    response = requests.post("http://localhost:8008/api/contractor-chat/message", json={
        "session_id": session_id,
        "message": "I own JM Holiday Lighting in South Florida", 
        "current_stage": "welcome",
        "profile_data": {}
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nStage: {data['stage']}")
        
        # Print all collected data
        collected = data.get('profile_progress', {}).get('collectedData', {})
        print(f"\nCollected Data:")
        for key, value in collected.items():
            print(f"  {key}: {value}")
        
        # Print full response
        print(f"\nFull Response:")
        print(data.get('response'))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_debug()