"""
Simple test of COIA backend API memory persistence
"""

import requests
import json
import time
import sys

# Fix Unicode issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BACKEND_URL = "http://localhost:8008"
TEST_ID = f"test-{int(time.time())}"

def test_coia():
    # Test 1: Send first message
    print("\n" + "=" * 50)
    print("TEST 1: First message with company info")
    print("=" * 50)
    
    response = requests.post(
        f"{BACKEND_URL}/api/coia/chat",
        json={
            "contractor_lead_id": TEST_ID,
            "session_id": TEST_ID,
            "message": "Hi, I'm Bob from Bob's Plumbing. We've been in business for 15 years."
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Mode: {data.get('current_mode')}")
        print(f"Response preview: {data.get('response', '')[:100]}...")
        
        if data.get('contractor_profile'):
            print(f"\nExtracted Profile:")
            profile = data['contractor_profile']
            print(f"  Company: {profile.get('company_name')}")
            print(f"  Years: {profile.get('years_in_business')}")
    else:
        print(f"Error: {response.text}")
    
    # Test 2: Send second message to test memory
    print("\n" + "=" * 50)
    print("TEST 2: Testing memory recall")
    print("=" * 50)
    
    time.sleep(2)
    
    response = requests.post(
        f"{BACKEND_URL}/api/coia/chat",
        json={
            "contractor_lead_id": TEST_ID,
            "session_id": TEST_ID,
            "message": "Can you remind me what I told you about my business?"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        response_text = data.get('response', '').lower()
        
        print(f"Response preview: {response_text[:200]}...")
        
        # Check if memory works
        if "bob's plumbing" in response_text or "bob" in response_text:
            print("\n✅ MEMORY WORKS: Remembers company name!")
        if "15 years" in response_text or "fifteen" in response_text:
            print("✅ MEMORY WORKS: Remembers years in business!")
    else:
        print(f"Error: {response.text}")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    test_coia()