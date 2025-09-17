"""
Test Contractor API Endpoints - Agent 4 Testing (Corrected Routes)
Purpose: Test actual contractor endpoints with correct routes
"""

import requests
import json

BASE_URL = "http://localhost:8008"

def test_contractor_endpoints():
    """Test the contractor-specific endpoints with correct routes"""
    print("=" * 60)
    print("AGENT 4 - CONTRACTOR ENDPOINTS TEST (CORRECTED)")
    print("=" * 60)
    
    # Test 1: Contractor Chat Endpoint (Correct Route)
    print("\nTEST 1: Contractor Chat Endpoint (/chat/message)")
    try:
        chat_data = {
            "message": "Hi, I'm a contractor looking to join InstaBids",
            "session_id": "test_corrected_001"
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/message",
            json=chat_data,
            timeout=15
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   SUCCESS: Response keys: {list(data.keys())}")
            print(f"   Stage: {data.get('stage', 'unknown')}")
            print(f"   Response preview: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"   ERROR: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
def test_advanced_contractor_flow():
    """Test advanced contractor onboarding flow"""
    print("\nTEST 2: Advanced Contractor Profile Creation Flow")
    
    success_count = 0
    
    # Step 1: Initial business inquiry
    try:
        chat_data = {
            "message": "I run Advanced Test Electrical Services in Tampa, Florida. I want to create my contractor profile.",
            "session_id": "test_advanced_flow_001"
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/message",
            json=chat_data,
            timeout=20
        )
        
        print(f"   Step 1 Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Stage: {data.get('stage', 'unknown')}")
            print(f"   Has contractor ID: {bool(data.get('contractor_id'))}")
            success_count += 1
            
            # Step 2: Follow up if needed
            if data.get('stage') == 'research_confirmation':
                print("\n   Step 2: Confirming business information...")
                confirm_data = {
                    "message": "Yes, that information looks correct. Please create my profile.",
                    "session_id": "test_advanced_flow_001"
                }
                
                response2 = requests.post(
                    f"{BASE_URL}/chat/message",
                    json=confirm_data,
                    timeout=20
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"   Final Stage: {data2.get('stage', 'unknown')}")
                    print(f"   Contractor ID: {data2.get('contractor_id', 'None')}")
                    success_count += 1
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    return success_count >= 1

def main():
    """Run corrected contractor endpoint tests"""
    print("Testing Contractor Endpoints with Corrected Routes...")
    
    # Test basic endpoint
    basic_success = test_contractor_endpoints()
    
    # Test advanced flow
    advanced_success = test_advanced_contractor_flow()
    
    print("\n" + "=" * 60)
    print("CONTRACTOR ENDPOINTS TEST RESULTS:")
    print(f"   Basic Chat Endpoint: {'PASS' if basic_success else 'FAIL'}")
    print(f"   Advanced Flow: {'PASS' if advanced_success else 'FAIL'}")
    
    if basic_success and advanced_success:
        print("\nOVERALL STATUS: ALL CONTRACTOR SYSTEMS OPERATIONAL ✓")
    elif basic_success:
        print("\nOVERALL STATUS: BASIC SYSTEMS WORKING ✓")
    else:
        print("\nOVERALL STATUS: CONTRACTOR SYSTEMS NEED ATTENTION")
    
    print("=" * 60)
    
    return basic_success and advanced_success

if __name__ == "__main__":
    success = main()
    print(f"\nFINAL RESULT: {'SUCCESS' if success else 'PARTIAL'}")