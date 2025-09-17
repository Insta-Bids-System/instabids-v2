#!/usr/bin/env python3
"""
Quick Test: IRIS Agent Memory Persistence
Tests if IRIS remembers conversation across multiple messages
"""

import asyncio
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8008"
TEST_SESSION_ID = f"iris-memory-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"

async def test_iris_memory():
    """Test IRIS memory persistence with 2-message conversation"""
    
    print("=" * 60)
    print("IRIS MEMORY TEST")
    print("=" * 60)
    
    # Message 1: Create memorable information
    print("\n[TEST] Sending Message 1 - Creating memory...")
    response1 = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "Hi, I'm Sarah and I'm working on a modern farmhouse kitchen renovation",
        "user_id": "test_user_sarah",
        "session_id": TEST_SESSION_ID,
        "room_type": "kitchen"
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"[OK] Message 1 Response: {result1['response'][:100]}...")
        print(f"[OK] Session ID: {result1.get('session_id')}")
        print(f"[OK] Suggestions: {result1.get('suggestions', [])}")
    else:
        print(f"[FAILED] Message 1 Failed: {response1.status_code} - {response1.text}")
        return False
    
    # Message 2: Test memory recall
    print("\n[TEST] Sending Message 2 - Testing memory...")
    response2 = requests.post(f"{BASE_URL}/api/iris/chat", json={
        "message": "What did I just tell you about my name and what room I'm renovating?",
        "user_id": "test_user_sarah", 
        "session_id": TEST_SESSION_ID,
        "room_type": "kitchen"
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        response_text = result2['response'].lower()
        
        print(f"[OK] Message 2 Response: {result2['response'][:200]}...")
        
        # Check if IRIS remembers key details
        memory_checks = {
            "Remembers name 'Sarah'": "sarah" in response_text,
            "Remembers 'kitchen'": "kitchen" in response_text,
            "Remembers 'modern farmhouse'": "modern" in response_text and ("farmhouse" in response_text or "farm" in response_text),
            "Remembers 'renovation'": "renovation" in response_text or "renovate" in response_text or "remodel" in response_text
        }
        
        print(f"\n[MEMORY ANALYSIS]")
        all_passed = True
        for check, passed in memory_checks.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} - {check}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n[SUCCESS] IRIS MEMORY TEST PASSED!")
            print(f"IRIS successfully remembered conversation details across messages.")
            return True
        else:
            print(f"\n[FAILED] IRIS MEMORY TEST FAILED!")
            print(f"IRIS did not remember key conversation details.")
            return False
            
    else:
        print(f"[FAILED] Message 2 Failed: {response2.status_code} - {response2.text}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_iris_memory())
    exit(0 if result else 1)