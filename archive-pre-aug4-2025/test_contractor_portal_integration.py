"""
Test Contractor Portal Frontend Integration - Agent 4 Testing
Purpose: Verify frontend components and API endpoints are working
"""

import os
import requests
import sys
from time import sleep

# Test server endpoints
BASE_URL = "http://localhost:8008"

def test_backend_server():
    """Test if the backend server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_contractor_chat_endpoint():
    """Test the contractor chat endpoint"""
    print("\nTEST: Contractor Chat Endpoint...")
    
    chat_data = {
        "message": "Hi, I'm a contractor looking to join InstaBids",
        "session_id": "test_frontend_integration_001"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/contractor/chat/message",
            json=chat_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Chat endpoint responded")
            print(f"   Response keys: {list(data.keys())}")
            print(f"   Stage: {data.get('stage', 'unknown')}")
            return True
        else:
            print(f"ERROR: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Chat endpoint failed - {e}")
        return False

def test_contractor_routes_exist():
    """Test if contractor routes are properly configured"""
    print("\nTEST: Contractor Routes Configuration...")
    
    # Test various contractor endpoints
    endpoints = [
        "/api/contractor/chat/message",
        # Add other endpoints when available
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            # We expect 422 (validation error) or 200, not 404
            if response.status_code in [200, 422, 500]:
                results.append(True)
                print(f"SUCCESS: {endpoint} - Route exists")
            else:
                results.append(False)
                print(f"ERROR: {endpoint} - HTTP {response.status_code}")
        except Exception as e:
            results.append(False)
            print(f"ERROR: {endpoint} - {e}")
    
    return all(results) if results else False

def main():
    """Run all contractor portal integration tests"""
    print("=" * 60)
    print("AGENT 4 - CONTRACTOR PORTAL INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Backend server
    print("\nTEST: Backend Server Status...")
    if test_backend_server():
        print("SUCCESS: Backend server is running on port 8008")
    else:
        print("ERROR: Backend server not running - start with 'python main.py'")
        return False
    
    # Test 2: Contractor routes
    routes_ok = test_contractor_routes_exist()
    
    # Test 3: Chat endpoint
    chat_ok = test_contractor_chat_endpoint()
    
    # Summary
    print("\n" + "=" * 60)
    if routes_ok and chat_ok:
        print("CONTRACTOR PORTAL INTEGRATION TEST: PASSED")
        print("SUCCESS: All contractor systems operational")
    else:
        print("CONTRACTOR PORTAL INTEGRATION TEST: PARTIAL")
        print("Some contractor systems need attention")
    print("=" * 60)
    
    return routes_ok and chat_ok

if __name__ == "__main__":
    success = main()
    print(f"\nFINAL RESULT: {'SUCCESS' if success else 'NEEDS_WORK'}")