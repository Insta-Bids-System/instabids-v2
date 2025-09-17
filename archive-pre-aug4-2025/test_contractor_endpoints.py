"""
Test Contractor API Endpoints - Agent 4 Testing
Purpose: Test actual contractor endpoints without requiring health check
"""

import requests
import json

BASE_URL = "http://localhost:8008"

def test_contractor_endpoints():
    """Test the contractor-specific endpoints"""
    print("=" * 60)
    print("AGENT 4 - CONTRACTOR ENDPOINTS TEST")
    print("=" * 60)
    
    # Test 1: Contractor Chat Endpoint
    print("\nTEST 1: Contractor Chat Endpoint")
    try:
        chat_data = {
            "message": "Hi, I'm a contractor looking to join InstaBids",
            "session_id": "test_endpoint_001"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/contractor/chat/message",
            json=chat_data,
            timeout=15
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   SUCCESS: Response keys: {list(data.keys())}")
            print(f"   Stage: {data.get('stage', 'unknown')}")
            print(f"   Response preview: {data.get('response', '')[:100]}...")
        else:
            print(f"   ERROR: {response.text}")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: COIA Direct Integration Test
    print("\nTEST 2: COIA Agent Direct Integration")
    try:
        advanced_chat_data = {
            "message": "I run Advanced Electrical Services in Miami, Florida. I want to create my contractor profile.",
            "session_id": "test_endpoint_002"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/contractor/chat/message",
            json=advanced_chat_data,
            timeout=20
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   SUCCESS: Advanced conversation working")
            print(f"   Stage: {data.get('stage', 'unknown')}")
            print(f"   Contractor ID: {data.get('contractor_id', 'None')}")
        else:
            print(f"   ERROR: {response.text}")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Test other potential endpoints
    print("\nTEST 3: Exploring Available Contractor Routes")
    potential_endpoints = [
        "/api/contractor/profile",
        "/api/contractor/bids",
        "/api/contractor/dashboard"
    ]
    
    for endpoint in potential_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"   {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   {endpoint}: Connection failed")
    
    print("\n" + "=" * 60)
    print("CONTRACTOR ENDPOINTS TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_contractor_endpoints()