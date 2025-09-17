#!/usr/bin/env python3
"""
Full JM Holiday Lighting Test with Debug
"""

import requests
import json
import time

def test_jm_holiday_lighting_debug():
    """Test the JM Holiday Lighting research workflow with full debugging"""
    
    print("=== JM HOLIDAY LIGHTING FULL DEBUG TEST ===")
    
    # Step 1: Business name input (should trigger research)
    session_id = f"jm_test_{int(time.time())}"
    
    print(f"Testing with session ID: {session_id}")
    print("\nStep 1: Business name input")
    
    response1 = requests.post("http://localhost:8008/api/contractor-chat/message", json={
        "session_id": session_id,
        "message": "I own JM Holiday Lighting in South Florida", 
        "current_stage": "welcome",
        "profile_data": {}
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"SUCCESS: Stage = {data1['stage']}")
        print(f"\nFull response:")
        print(data1['response'])
        print(f"\nProfile progress:")
        print(json.dumps(data1.get('profile_progress', {}), indent=2))
        
        if data1['stage'] == 'research_confirmation':
            print("\nRESEARCH TRIGGERED! SUCCESS")
            
            # Show collected data
            collected = data1.get('profile_progress', {}).get('collectedData', {})
            print(f"\nCollected data:")
            print(f"- Company: {collected.get('company_name')}")
            print(f"- Email: {collected.get('email')}")
            print(f"- Phone: {collected.get('phone')}")
            print(f"- Website: {collected.get('website')}")
            print(f"- Services: {collected.get('services')}")
            
            # Step 2: Confirmation
            print("\n\nStep 2: Confirming research data")
            print("Sending: 'Yes, that information looks correct'")
            
            response2 = requests.post("http://localhost:8008/api/contractor-chat/message", json={
                "session_id": session_id,
                "message": "Yes, that information looks correct",
                "current_stage": "research_confirmation", 
                "profile_data": data1.get('profile_progress', {}).get('collectedData', {})
            })
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"\nSUCCESS: Stage = {data2['stage']}")
                print(f"\nFull response:")
                print(data2['response'])
                
                contractor_id = data2.get('contractor_id')
                
                if contractor_id:
                    print(f"\nCONTRACTOR PROFILE CREATED! SUCCESS")
                    print(f"Contractor ID: {contractor_id}")
                    print(f"Final stage: {data2['stage']}")
                    
                    # Verify in database
                    print("\nVerifying in database...")
                    verify_response = requests.get(f"http://localhost:8008/api/contractor/{contractor_id}")
                    if verify_response.status_code == 200:
                        contractor_data = verify_response.json()
                        print("Database verification: SUCCESS")
                        print(f"Company name: {contractor_data.get('company_name')}")
                    else:
                        print("Database verification: FAILED")
                    
                    return True
                else:
                    print("\nERROR: No contractor ID returned")
                    print(f"Stage: {data2['stage']}")
                    print(f"Session data: {json.dumps(data2.get('session_data', {}), indent=2)}")
            else:
                print(f"\nERROR: Confirmation failed with status {response2.status_code}")
                print(f"Response: {response2.text}")
        else:
            print("\nERROR: Research was not triggered")
            print(f"Expected stage: research_confirmation, got: {data1['stage']}")
    else:
        print(f"\nERROR: Initial request failed with status {response1.status_code}")
        print(f"Response: {response1.text}")
    
    return False

if __name__ == "__main__":
    success = test_jm_holiday_lighting_debug()
    print(f"\n\nTest Result: {'SUCCESS' if success else 'FAILED'}")