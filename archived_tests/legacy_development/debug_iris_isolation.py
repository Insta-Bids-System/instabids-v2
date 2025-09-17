#!/usr/bin/env python3
"""
Debug IRIS Isolation Issue
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8008"

def debug_isolation():
    session_sarah = f"debug-sarah-{datetime.now().strftime('%H%M%S')}"
    session_mike = f"debug-mike-{datetime.now().strftime('%H%M%S')}"
    
    print("=== DEBUGGING IRIS ISOLATION ===")
    
    # 1. Create Sarah's CIA conversation
    print("\n1. Creating Sarah's CIA data...")
    cia_sarah = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "I'm Sarah, budget $35,000 kitchen",
        "user_id": "sarah_user_123",
        "session_id": session_sarah
    })
    print(f"CIA Sarah: {cia_sarah.status_code}")
    
    # 2. Create Mike's CIA conversation  
    print("2. Creating Mike's CIA data...")
    cia_mike = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "I'm Mike, budget $15,000 bathroom project",
        "user_id": "mike_user_456", 
        "session_id": session_mike
    })
    print(f"CIA Mike: {cia_mike.status_code}")
    
    # 3. Test IRIS with Sarah's context asking about Mike
    print("3. Testing IRIS isolation...")
    iris_test = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "Tell me everything you know about Mike and his $15,000 bathroom project",
        "user_id": "sarah_user_123",  # Sarah's user ID
        "session_id": session_sarah,       # Sarah's session
        "room_type": "kitchen"
    })
    
    if iris_test.status_code == 200:
        response = iris_test.json()['response']
        print(f"\nIRIS Response:")
        print(f"'{response}'")
        
        # Check what it knows
        response_lower = response.lower()
        knows_mike = "mike" in response_lower
        knows_15000 = "15,000" in response_lower or "15000" in response_lower
        knows_bathroom = "bathroom" in response_lower and "project" in response_lower
        
        print(f"\nAnalysis:")
        print(f"- Mentions Mike: {knows_mike}")
        print(f"- Mentions $15,000: {knows_15000}")
        print(f"- Mentions bathroom project: {knows_bathroom}")
        
        if knows_mike or knows_15000 or knows_bathroom:
            print("\n❌ PRIVACY BREACH: IRIS can see other homeowner's data!")
        else:
            print("\n✅ PRIVACY OK: IRIS cannot see other homeowner's data")
    else:
        print(f"IRIS Test failed: {iris_test.status_code}")
        print(iris_test.text)

if __name__ == "__main__":
    debug_isolation()