#!/usr/bin/env python3
"""
Test session state persistence
"""

import requests
import json
import time

def test_session_state():
    """Test if session state persists between calls"""
    
    print("=== SESSION STATE DEBUG TEST ===")
    
    session_id = f"session_test_{int(time.time())}"
    
    # Step 1: Initial message
    print(f"\nStep 1: Initial message with session {session_id}")
    response1 = requests.post("http://localhost:8008/api/contractor-chat/message", json={
        "session_id": session_id,
        "message": "I own JM Holiday Lighting in South Florida", 
        "current_stage": "welcome",
        "profile_data": {}
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"Response 1 stage: {data1['stage']}")
        print(f"Session data: {json.dumps(data1.get('session_data', {}), indent=2)}")
        
        # Step 2: Check if session persists
        print(f"\nStep 2: Second message with same session {session_id}")
        response2 = requests.post("http://localhost:8008/api/contractor-chat/message", json={
            "session_id": session_id,
            "message": "Can you repeat what you found?",
            "current_stage": data1['stage'],
            "profile_data": data1.get('profile_progress', {}).get('collectedData', {})
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Response 2 stage: {data2['stage']}")
            print(f"Response: {data2['response'][:200]}...")
            
            # Check if it remembers the research
            if "JM Holiday Lighting" in data2['response']:
                print("\nSUCCESS: Session state persisted!")
            else:
                print("\nERROR: Session state not persisted")
        else:
            print(f"Request 2 failed: {response2.status_code}")
    else:
        print(f"Request 1 failed: {response1.status_code}")

if __name__ == "__main__":
    test_session_state()