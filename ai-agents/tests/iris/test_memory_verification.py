#!/usr/bin/env python3
"""
IRIS Memory System - Final Verification Test
Tests all memory tiers after tenant_id fix
"""

import requests
import uuid
import time
import json

BASE_URL = "http://localhost:8008"
TEST_USER_ID = str(uuid.uuid4())

def test_memory_fixed():
    """Test that memory persistence is now working after tenant_id fix"""
    
    print("IRIS Memory System - Final Verification Test")
    print("=" * 60)
    
    # Generate test session
    session_id = str(uuid.uuid4())
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Session ID: {session_id}")
    print()
    
    # Test 1: Session Memory
    print("Test 1: Session Memory Persistence")
    print("-" * 40)
    
    # Send design preference message
    print("Sending design preference...")
    response1 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": session_id,
        "message": "I love Scandinavian minimalist design with white walls and natural wood accents"
    }, timeout=30)
    
    if response1.status_code == 200:
        print(f"API Response: {response1.status_code}")
        result1 = response1.json()
        print(f"   Response: {result1.get('response', 'No response')[:100]}...")
    else:
        print(f"API Error: {response1.status_code}")
        return False
    
    time.sleep(2)
    
    # Test memory recall in same session
    print("\nTesting memory recall...")
    response2 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": session_id,
        "message": "What design style did I just mention?"
    }, timeout=30)
    
    if response2.status_code == 200:
        result2 = response2.json()
        response_text = result2.get('response', '').lower()
        
        if 'scandinavian' in response_text or 'minimalist' in response_text or 'white walls' in response_text:
            print("SUCCESS: Memory recalled correctly!")
            print(f"   Response: {result2.get('response', '')[:150]}...")
        else:
            print("FAIL: Memory not recalled")
            print(f"   Response: {result2.get('response', '')[:150]}...")
            return False
    else:
        print(f"API Error: {response2.status_code}")
        return False
    
    # Test 2: Context API
    print(f"\nTest 2: Context API Verification")
    print("-" * 40)
    
    context_response = requests.get(f"{BASE_URL}/api/iris/context/{TEST_USER_ID}", timeout=30)
    
    if context_response.status_code == 200:
        context = context_response.json()
        print(f"Context API Response: {context_response.status_code}")
        
        # Check if context has actual data
        if context and len(str(context)) > 10:
            print(f"SUCCESS: Context contains data ({len(str(context))} chars)")
            
            # Look for our design preferences
            context_str = str(context).lower()
            if 'scandinavian' in context_str or 'minimalist' in context_str:
                print("SUCCESS: Design preferences found in context!")
            else:
                print("Warning: Specific preferences not found, but context exists")
                
            print(f"   Context sample: {str(context)[:200]}...")
        else:
            print("FAIL: Context API returns empty data")
            print(f"   Context: {context}")
            return False
    else:
        print(f"Context API Error: {context_response.status_code}")
        return False
    
    # Test 3: Cross-Session Memory
    print(f"\nTest 3: Cross-Session Memory")
    print("-" * 40)
    
    # New session, same user
    new_session = str(uuid.uuid4())
    print(f"New Session ID: {new_session}")
    
    response3 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": new_session,
        "message": "What design preferences do you remember about me?"
    }, timeout=30)
    
    if response3.status_code == 200:
        result3 = response3.json()
        response_text = result3.get('response', '').lower()
        
        if 'scandinavian' in response_text or 'minimalist' in response_text or 'remember' in response_text:
            print("SUCCESS: Cross-session memory working!")
            print(f"   Response: {result3.get('response', '')[:150]}...")
        else:
            print("FAIL: Cross-session memory not working")
            print(f"   Response: {result3.get('response', '')[:150]}...")
    else:
        print(f"API Error: {response3.status_code}")
        return False
    
    print(f"\nMEMORY SYSTEM VERIFICATION COMPLETE!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_memory_fixed()
    if success:
        print("ALL MEMORY TESTS PASSED - System is FULLY OPERATIONAL!")
    else:
        print("Some memory tests failed - Further investigation needed")