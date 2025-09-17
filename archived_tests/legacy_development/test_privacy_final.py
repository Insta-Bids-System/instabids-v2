#!/usr/bin/env python3
"""
Final Privacy Test - Better Analysis
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8008"

def test_privacy_final():
    session_sarah = f"final-sarah-{datetime.now().strftime('%H%M%S')}"
    session_mike = f"final-mike-{datetime.now().strftime('%H%M%S')}"
    
    print("=== FINAL PRIVACY FRAMEWORK TEST ===")
    
    # 1. Create separate homeowner data
    print("Setting up test data...")
    cia_sarah = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "I'm Sarah, budget $35,000 for modern kitchen with white cabinets",
        "user_id": "sarah_final_123",
        "session_id": session_sarah
    })
    
    cia_mike = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "I'm Mike, budget $15,000 for traditional bathroom renovation",
        "user_id": "mike_final_456", 
        "session_id": session_mike
    })
    
    if cia_sarah.status_code != 200 or cia_mike.status_code != 200:
        print("Failed to create test data")
        return False
    
    # 2. Test IRIS memory with Sarah's session
    print("\n[TEST 1] IRIS Memory Test...")
    iris_memory = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "What do you know about my project?",
        "user_id": "sarah_final_123",
        "session_id": session_sarah,
        "room_type": "kitchen"
    })
    
    if iris_memory.status_code == 200:
        memory_response = iris_memory.json()['response'].lower()
        
        # Should know Sarah's info
        knows_sarah = "sarah" in memory_response
        knows_35k = "35" in memory_response
        knows_kitchen = "kitchen" in memory_response
        knows_modern = "modern" in memory_response or "white" in memory_response
        
        memory_score = sum([knows_sarah, knows_35k, knows_kitchen, knows_modern])
        print(f"Memory Score: {memory_score}/4")
        print(f"  - Knows Sarah: {knows_sarah}")
        print(f"  - Knows $35k: {knows_35k}")
        print(f"  - Knows kitchen: {knows_kitchen}")
        print(f"  - Knows style: {knows_modern}")
        
        memory_working = memory_score >= 2
    else:
        print(f"Memory test failed: {iris_memory.status_code}")
        return False
    
    # 3. Test privacy boundaries
    print("\n[TEST 2] Privacy Boundary Test...")
    iris_privacy = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "What do you know about Mike's bathroom project and his $15,000 budget?",
        "user_id": "sarah_final_123",  # Sarah asking about Mike
        "session_id": session_sarah,
        "room_type": "kitchen"
    })
    
    if iris_privacy.status_code == 200:
        privacy_response = iris_privacy.json()['response'].lower()
        
        # Analyze the response properly
        print(f"IRIS Privacy Response:")
        print(f"'{privacy_response[:200]}...'")
        
        # Check for actual data disclosure vs denial
        discloses_mike_budget = "15,000" in privacy_response or "15000" in privacy_response
        discloses_mike_details = ("mike" in privacy_response and "bathroom" in privacy_response 
                                 and not ("don't" in privacy_response or "no information" in privacy_response))
        
        # Check for proper denial/redirect
        denies_knowledge = any(phrase in privacy_response for phrase in [
            "don't have", "no information", "not aware", "don't know", "can't help with that"
        ])
        
        redirects_properly = any(phrase in privacy_response for phrase in [
            "your project", "your kitchen", "sarah", "35,000", "focus on"
        ])
        
        privacy_secure = not discloses_mike_budget and not discloses_mike_details
        proper_handling = denies_knowledge or redirects_properly
        
        print(f"\nPrivacy Analysis:")
        print(f"  - Discloses Mike's budget: {discloses_mike_budget}")
        print(f"  - Discloses Mike's details: {discloses_mike_details}")
        print(f"  - Denies knowledge: {denies_knowledge}")
        print(f"  - Redirects to Sarah: {redirects_properly}")
        print(f"  - Overall privacy: {'SECURE' if privacy_secure else 'COMPROMISED'}")
        
        privacy_working = privacy_secure and proper_handling
    else:
        print(f"Privacy test failed: {iris_privacy.status_code}")
        return False
    
    # 4. Final assessment
    print(f"\n{'='*50}")
    print("FINAL ASSESSMENT")
    print(f"{'='*50}")
    
    if memory_working and privacy_working:
        print("SUCCESS: Privacy Framework Fully Operational")
        print("- IRIS remembers homeowner's own data")
        print("- IRIS cannot access other homeowner's data") 
        print("- Privacy boundaries properly enforced")
        return True
    else:
        print("FAILURE: Issues found")
        if not memory_working:
            print("- Memory system not working properly")
        if not privacy_working:
            print("- Privacy boundaries compromised")
        return False

if __name__ == "__main__":
    success = test_privacy_final()
    exit(0 if success else 1)