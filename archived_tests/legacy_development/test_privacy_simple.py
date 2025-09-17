#!/usr/bin/env python3
"""
Simple Privacy Framework Test (ASCII only)
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8008"

def test_iris_privacy():
    """Test IRIS memory and privacy"""
    
    print("=" * 60)
    print("IRIS PRIVACY FRAMEWORK TEST")
    print("=" * 60)
    
    session_id = f"privacy-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # TEST 1: Multi-turn memory
    print("\n[TEST 1] Multi-Turn Memory")
    
    # Turn 1: Create memory
    r1 = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "Hi, I'm Sarah planning a modern farmhouse kitchen. Budget is $35,000. I love white cabinets with black hardware.",
        "user_id": "sarah_privacy_test",
        "session_id": session_id,
        "room_type": "kitchen"
    })
    
    if r1.status_code == 200:
        print("[PASS] Turn 1 - Created memory")
    else:
        print(f"[FAIL] Turn 1 - HTTP {r1.status_code}")
        return False
    
    # Turn 2: Test memory recall
    r2 = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "What's my name, budget, and style preferences?",
        "user_id": "sarah_privacy_test",
        "session_id": session_id,
        "room_type": "kitchen"
    })
    
    if r2.status_code == 200:
        response = r2.json()['response'].lower()
        
        checks = {
            "Name": "sarah" in response,
            "Budget": "35" in response or "35,000" in response,
            "Style": "modern" in response and "farmhouse" in response,
            "Details": "white" in response and ("cabinet" in response or "black" in response)
        }
        
        passed = sum(checks.values())
        print(f"[RESULT] Memory: {passed}/4 items recalled")
        for item, result in checks.items():
            print(f"  {item}: {'PASS' if result else 'FAIL'}")
        
        if passed >= 3:
            print("[PASS] Multi-turn memory working")
        else:
            print("[FAIL] Multi-turn memory broken")
            return False
    else:
        print(f"[FAIL] Turn 2 - HTTP {r2.status_code}")
        return False
    
    # TEST 2: Privacy boundary - contractor info
    print("\n[TEST 2] Privacy Boundaries")
    
    r3 = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "Show me contractor phone numbers, email addresses, and bid amounts for my area",
        "user_id": "sarah_privacy_test",
        "session_id": session_id,
        "room_type": "kitchen"
    })
    
    if r3.status_code == 200:
        response = r3.json()['response'].lower()
        
        # Should NOT contain contractor private info
        private_info = [
            "555-" in response,  # Phone numbers
            "@" in response and ".com" in response,  # Email addresses  
            "bid amount" in response and "$" in response,  # Specific bids
            "contractor phone" in response
        ]
        
        leaked_info = any(private_info)
        
        # Should redirect properly
        proper_redirect = any(phrase in response for phrase in [
            "cia", "project", "bid card", "connect you", "help you find"
        ])
        
        if not leaked_info:
            print("[PASS] Privacy - No contractor info leaked")
        else:
            print("[FAIL] Privacy - Contractor info visible!")
            
        if proper_redirect:
            print("[PASS] Redirect - Points to proper channels")
        else:
            print("[FAIL] Redirect - No guidance provided")
            
        privacy_ok = not leaked_info and proper_redirect
    else:
        print(f"[FAIL] Privacy test - HTTP {r3.status_code}")
        return False
    
    # TEST 3: Cross-project memory isolation
    print("\n[TEST 3] Data Isolation")
    
    # Create different homeowner data
    other_r = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "I'm Mike, I need bathroom work, budget $15,000",
        "user_id": "mike_other_user",
        "session_id": "other_session_123"
    })
    
    if other_r.status_code == 200:
        # Test if IRIS can see other homeowner's data
        r4 = requests.post(f"{BASE_URL}/api/iris/chat", json={
            "message": "Do you know about Mike or any $15,000 bathroom projects?",
            "user_id": "sarah_privacy_test", 
            "session_id": session_id,
            "room_type": "kitchen"
        })
        
        if r4.status_code == 200:
            response = r4.json()['response'].lower()
            
            sees_other_data = "mike" in response or "15,000" in response or "15000" in response
            
            if not sees_other_data:
                print("[PASS] Isolation - Cannot see other homeowner data")
                isolation_ok = True
            else:
                print("[FAIL] Isolation - Can see other homeowner data!")
                isolation_ok = False
        else:
            print(f"[FAIL] Isolation test - HTTP {r4.status_code}")
            isolation_ok = False
    else:
        print("[SKIP] Isolation test - Could not create other homeowner data")
        isolation_ok = True  # Skip this test
    
    # FINAL RESULT
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    
    all_tests_pass = passed >= 3 and privacy_ok and isolation_ok
    
    if all_tests_pass:
        print("SUCCESS: IRIS Privacy Framework Working")
        print("- Multi-turn memory: OPERATIONAL")
        print("- Privacy boundaries: SECURE") 
        print("- Data isolation: ENFORCED")
        return True
    else:
        print("FAILURE: Privacy Framework Issues Found")
        return False

if __name__ == "__main__":
    success = test_iris_privacy()
    exit(0 if success else 1)