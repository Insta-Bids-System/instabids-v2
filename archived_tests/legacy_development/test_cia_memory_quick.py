#!/usr/bin/env python3
"""
Quick Test: CIA Agent Memory Persistence
Tests if CIA remembers conversation across multiple messages
"""

import asyncio
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8008"
TEST_SESSION_ID = f"memory-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"

async def test_cia_memory():
    """Test CIA memory persistence with 2-message conversation"""
    
    print("=" * 60)
    print("CIA MEMORY TEST")
    print("=" * 60)
    
    # Message 1: Create memorable information
    print("\n[TEST] Sending Message 1 - Creating memory...")
    response1 = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "Hi, I'm John and I need a kitchen remodel for my home",
        "user_id": "test_user_john",
        "session_id": TEST_SESSION_ID
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"✅ Message 1 Response: {result1['response'][:100]}...")
        print(f"✅ Session ID: {result1.get('session_id')}")
        print(f"✅ Current Phase: {result1.get('current_phase')}")
    else:
        print(f"❌ Message 1 Failed: {response1.status_code}")
        return False
    
    # Message 2: Test memory recall
    print("\n[TEST] Sending Message 2 - Testing memory...")
    response2 = requests.post(f"{BASE_URL}/api/cia/chat", json={
        "message": "What did I just tell you about my name and project?",
        "user_id": "test_user_john", 
        "session_id": TEST_SESSION_ID
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        response_text = result2['response'].lower()
        
        print(f"✅ Message 2 Response: {result2['response'][:200]}...")
        
        # Check if CIA remembers key details
        memory_checks = {
            "Remembers name 'John'": "john" in response_text,
            "Remembers 'kitchen'": "kitchen" in response_text,
            "Remembers 'remodel'": "remodel" in response_text or "renovation" in response_text
        }
        
        print(f"\n[MEMORY ANALYSIS]")
        all_passed = True
        for check, passed in memory_checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {check}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 CIA MEMORY TEST PASSED!")
            print(f"CIA successfully remembered conversation details across messages.")
            return True
        else:
            print(f"\n❌ CIA MEMORY TEST FAILED!")
            print(f"CIA did not remember key conversation details.")
            return False
            
    else:
        print(f"❌ Message 2 Failed: {response2.status_code}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_cia_memory())
    exit(0 if result else 1)