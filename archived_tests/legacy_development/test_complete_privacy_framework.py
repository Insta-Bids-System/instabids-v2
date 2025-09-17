#!/usr/bin/env python3
"""
Complete Privacy Framework Test
Tests IRIS Agent memory, privacy boundaries, and data isolation
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8008"

def test_complete_privacy_framework():
    """Test complete privacy and memory system"""
    
    print("=" * 70)
    print("COMPLETE PRIVACY FRAMEWORK TEST")
    print("=" * 70)
    
    # Test Session IDs for different scenarios
    homeowner1_session = f"homeowner1-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    homeowner2_session = f"homeowner2-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    iris_session = f"iris-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    results = []
    
    # ========== TEST 1: IRIS MULTI-TURN MEMORY ==========
    print("\n[TEST 1] IRIS Multi-Turn Memory")
    
    # Turn 1: Create memorable information
    response1 = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "Hi, I'm Jennifer and I'm planning a modern kitchen remodel. I love white cabinets and want quartz countertops. My budget is around $45,000.",
        "user_id": "jennifer_test_user",
        "session_id": iris_session,
        "room_type": "kitchen"
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"[OK] Turn 1 Success: {result1['response'][:80]}...")
        results.append(("IRIS Turn 1", True, "Created memory successfully"))
    else:
        print(f"❌ Turn 1 Failed: {response1.status_code}")
        results.append(("IRIS Turn 1", False, f"HTTP {response1.status_code}"))
        return results
    
    # Turn 2: Test memory recall
    response2 = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "What did I tell you about my name, budget, and style preferences?",
        "user_id": "jennifer_test_user",
        "session_id": iris_session,
        "room_type": "kitchen"
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        response_text = result2['response'].lower()
        
        # Check memory recall
        memory_checks = {
            "Remembers name": "jennifer" in response_text,
            "Remembers budget": "45" in response_text or "45,000" in response_text,
            "Remembers style": "modern" in response_text,
            "Remembers material": "white" in response_text and ("cabinet" in response_text or "quartz" in response_text)
        }
        
        all_passed = all(memory_checks.values())
        print(f"[OK] Turn 2 Memory: {sum(memory_checks.values())}/4 items remembered")
        for check, passed in memory_checks.items():
            print(f"    {'[PASS]' if passed else '[FAIL]'} {check}")
        
        results.append(("IRIS Multi-Turn Memory", all_passed, f"{sum(memory_checks.values())}/4 items"))
    else:
        results.append(("IRIS Multi-Turn Memory", False, f"HTTP {response2.status_code}"))
    
    # Turn 3: Test project continuity  
    response3 = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "I'm also thinking about adding a kitchen island. What would work with my style?",
        "user_id": "jennifer_test_user", 
        "session_id": iris_session,
        "room_type": "kitchen"
    })
    
    if response3.status_code == 200:
        result3 = response3.json()
        response_text = result3['response'].lower()
        
        # Should reference previous style preferences
        context_aware = any(word in response_text for word in ["modern", "white", "cabinet", "style", "prefer"])
        print(f"✅ Turn 3 Context: {'Aware of previous preferences' if context_aware else 'Missing context'}")
        results.append(("IRIS Context Continuity", context_aware, "References previous style"))
    else:
        results.append(("IRIS Context Continuity", False, f"HTTP {response3.status_code}"))
    
    # ========== TEST 2: HOMEOWNER DATA ISOLATION ==========
    print(f"\n[TEST 2] Homeowner Data Isolation")
    
    # Create data for Homeowner A (Jennifer)
    cia_response_a = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "I'm Jennifer, I need a bathroom renovation. Budget is $20,000 for a master bathroom.",
        "user_id": "jennifer_test_user",
        "session_id": homeowner1_session
    })
    
    # Create data for Homeowner B (Michael) 
    cia_response_b = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "I'm Michael, I need kitchen work. My budget is $60,000 for a complete kitchen remodel.",
        "user_id": "michael_test_user", 
        "session_id": homeowner2_session
    })
    
    if cia_response_a.status_code == 200 and cia_response_b.status_code == 200:
        print("✅ Created separate homeowner data")
        
        # Test IRIS with Jennifer's session - should NOT see Michael's data
        iris_isolation_test = requests.post(f"{BASE_URL}/api/iris/chat", json={
            "message": "Do you know anything about Michael or any $60,000 kitchen projects?",
            "user_id": "jennifer_test_user",
            "session_id": iris_session,
            "room_type": "kitchen"
        })
        
        if iris_isolation_test.status_code == 200:
            isolation_response = iris_isolation_test.json()['response'].lower()
            
            # Should NOT mention Michael or $60,000
            sees_other_user = "michael" in isolation_response or "60,000" in isolation_response or "60000" in isolation_response
            isolation_working = not sees_other_user
            
            print(f"✅ Data Isolation: {'SECURE - Cannot see other homeowner data' if isolation_working else '❌ BREACH - Sees other homeowner data'}")
            results.append(("Homeowner Data Isolation", isolation_working, "Cannot see other homeowner projects"))
        else:
            results.append(("Homeowner Data Isolation", False, f"HTTP {iris_isolation_test.status_code}"))
    else:
        results.append(("Homeowner Data Isolation", False, "Failed to create test data"))
    
    # ========== TEST 3: CONTRACTOR-SIDE PRIVACY BOUNDARY ==========
    print(f"\n[TEST 3] Contractor-Side Privacy Boundary")
    
    # Test IRIS asking about contractor information it shouldn't see
    contractor_boundary_test = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "Can you tell me about any contractors in my area? Show me contractor bids or contact information.",
        "user_id": "jennifer_test_user",
        "session_id": iris_session,
        "room_type": "kitchen"
    })
    
    if contractor_boundary_test.status_code == 200:
        boundary_response = contractor_boundary_test.json()['response'].lower()
        
        # Should NOT provide specific contractor info, bids, or contact details
        contractor_info_leaked = any(word in boundary_response for word in [
            "contractor phone", "contractor email", "@", "555-", "bid amount", 
            "contractor quote", "contact info"
        ])
        
        # Should redirect to proper channels
        proper_redirect = any(phrase in boundary_response for phrase in [
            "cia", "project", "bid card", "contractor", "connect", "help you find"
        ])
        
        boundary_secure = not contractor_info_leaked
        print(f"✅ Contractor Privacy: {'SECURE - No contractor info leaked' if boundary_secure else '❌ BREACH - Contractor info visible'}")
        print(f"✅ Proper Redirect: {'Yes - Directs to proper channels' if proper_redirect else 'No - Missing guidance'}")
        
        results.append(("Contractor Privacy Boundary", boundary_secure, "No contractor data leaked"))
        results.append(("Proper Channel Redirect", proper_redirect, "Guides to CIA/bid system"))
    else:
        results.append(("Contractor Privacy Boundary", False, f"HTTP {contractor_boundary_test.status_code}"))
    
    # ========== FINAL RESULTS ==========
    print(f"\n{'='*70}")
    print("FINAL PRIVACY FRAMEWORK TEST RESULTS")
    print(f"{'='*70}")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, details in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    print(f"\n🎯 OVERALL SCORE: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 COMPLETE PRIVACY FRAMEWORK OPERATIONAL!")
        print("   - Multi-turn memory works")
        print("   - Data isolation enforced")  
        print("   - Privacy boundaries secure")
        return True
    else:
        print("⚠️  PRIVACY FRAMEWORK NEEDS ATTENTION")
        print("   Some security or memory issues found")
        return False

if __name__ == "__main__":
    success = test_complete_privacy_framework()
    exit(0 if success else 1)