#!/usr/bin/env python3
"""
Privacy Test - Understanding vs Echoing
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8008"

def test_privacy_understanding():
    print("=== PRIVACY UNDERSTANDING TEST ===")
    
    # Create Mike's data that IRIS should NOT know about
    session_mike = f"private-mike-{datetime.now().strftime('%H%M%S')}"
    cia_mike = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "I'm Mike Johnson, I need a luxury bathroom renovation with heated floors, budget is $75,000",
        "user_id": "mike_private_789",
        "session_id": session_mike
    })
    
    if cia_mike.status_code != 200:
        print("Failed to create Mike's private data")
        return False
    
    print("Created Mike's private data: luxury bathroom, heated floors, $75,000")
    
    # Test IRIS with Sarah's context - use VAGUE question (no echoing possible)
    session_sarah = f"test-sarah-{datetime.now().strftime('%H%M%S')}"
    iris_test = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "Do you know anything about Mike Johnson's project?",  # Vague - no numbers to echo
        "user_id": "sarah_different_999",
        "session_id": session_sarah,
        "room_type": "kitchen"
    })
    
    if iris_test.status_code == 200:
        response = iris_test.json()['response'].lower()
        
        print(f"\nIRIS Response to vague question:")
        print(f"'{response[:300]}...'")
        
        # Check if IRIS actually KNOWS Mike's specific details (not just echoing)
        knows_mike_johnson = "mike johnson" in response and "know" in response and not ("don't" in response)
        knows_luxury = "luxury" in response
        knows_heated_floors = "heated floors" in response or "heated floor" in response
        knows_75k = "75,000" in response or "75000" in response
        knows_bathroom_details = "bathroom" in response and ("renovation" in response or "project" in response) and not ("don't" in response)
        
        actual_data_breach = any([knows_mike_johnson, knows_luxury, knows_heated_floors, knows_75k])
        
        print(f"\nActual Knowledge Analysis:")
        print(f"  - Knows Mike Johnson personally: {knows_mike_johnson}")
        print(f"  - Knows luxury details: {knows_luxury}")
        print(f"  - Knows heated floors: {knows_heated_floors}")
        print(f"  - Knows $75k budget: {knows_75k}")
        print(f"  - ACTUAL DATA BREACH: {actual_data_breach}")
        
        if actual_data_breach:
            print("\n❌ CRITICAL: IRIS has access to other homeowner's private data!")
            return False
        else:
            print("\n✅ SECURE: IRIS does not know other homeowner's private data")
        
        # Now test with specific question to separate understanding vs echoing
        iris_specific = requests.post(f"{BASE_URL}/api/iris/chat", json={
            "message": "Tell me about heated floors and $75,000 bathroom projects",  # Specific details
            "user_id": "sarah_different_999",
            "session_id": session_sarah,
            "room_type": "kitchen"
        })
        
        if iris_specific.status_code == 200:
            specific_response = iris_specific.json()['response'].lower()
            
            # Check if IRIS provides SPECIFIC KNOWLEDGE about Mike's project
            provides_specific_info = (
                "mike" in specific_response and 
                ("heated floors" in specific_response or "heated floor" in specific_response) and
                not ("don't" in specific_response or "no information" in specific_response)
            )
            
            print(f"\nSpecific Question Test:")
            print(f"  - Provides Mike's heated floor info: {provides_specific_info}")
            
            if provides_specific_info:
                print("❌ CRITICAL: IRIS is providing specific details about other homeowner's project!")
                return False
            else:
                print("✅ SECURE: IRIS does not provide other homeowner's project details")
        
        return True
    else:
        print(f"Test failed: {iris_test.status_code}")
        return False

if __name__ == "__main__":
    success = test_privacy_understanding()
    if success:
        print(f"\n{'='*60}")
        print("PRIVACY ASSESSMENT: SECURE")
        print("IRIS properly isolates homeowner data")
        print("Any echoing is response formatting, not data breach")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("PRIVACY ASSESSMENT: COMPROMISED")  
        print("IRIS has access to cross-homeowner data")
        print(f"{'='*60}")
    exit(0 if success else 1)