#!/usr/bin/env python3
"""
Simple JM Holiday Lighting Test
"""

import requests
import json
import time

def test_jm_holiday_lighting():
    """Test the JM Holiday Lighting research workflow"""
    
    print("=== JM HOLIDAY LIGHTING RESEARCH TEST ===")
    
    # Step 1: Business name input (should trigger research)
    session_id = f"jm_test_{int(time.time())}"
    
    print(f"Testing with session ID: {session_id}")
    print("Step 1: Business name input")
    
    response1 = requests.post("http://localhost:8008/api/contractor-chat/message", json={
        "session_id": session_id,
        "message": "I own JM Holiday Lighting in South Florida", 
        "current_stage": "welcome",
        "profile_data": {}
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"SUCCESS: Stage = {data1['stage']}")
        print(f"Response preview: {data1['response'][:150]}...")
        
        if data1['stage'] == 'research_confirmation':
            print("RESEARCH TRIGGERED! SUCCESS")
            
            # Step 2: Confirmation
            print("\nStep 2: Confirming research data")
            
            response2 = requests.post("http://localhost:8008/api/contractor-chat/message", json={
                "session_id": session_id,
                "message": "Yes, that information looks correct",
                "current_stage": "research_confirmation", 
                "profile_data": data1.get('profile_progress', {}).get('collectedData', {})
            })
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"SUCCESS: Stage = {data2['stage']}")
                contractor_id = data2.get('contractor_id')
                
                if contractor_id:
                    print(f"CONTRACTOR PROFILE CREATED! SUCCESS")
                    print(f"Contractor ID: {contractor_id}")
                    print(f"Final stage: {data2['stage']}")
                    return True
                else:
                    print("ERROR: No contractor ID returned")
                    print(f"Response: {data2['response'][:150]}...")
            else:
                print(f"ERROR: Confirmation failed with status {response2.status_code}")
        else:
            print("ERROR: Research was not triggered")
            print(f"Expected stage: research_confirmation, got: {data1['stage']}")
    else:
        print(f"ERROR: Initial request failed with status {response1.status_code}")
    
    return False

if __name__ == "__main__":
    success = test_jm_holiday_lighting()
    print(f"\nTest Result: {'SUCCESS' if success else 'FAILED'}")