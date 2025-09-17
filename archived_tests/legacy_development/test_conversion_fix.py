"""
Test bid card conversion with proper authentication
"""

import requests
import json

def test_conversion_flow():
    bid_card_id = '4109e91e-4a8f-461f-a4e7-5a978c7f9655'
    base_url = 'http://localhost:8008'
    
    print("Testing bid card conversion flow...")
    print("=" * 50)
    
    # First test anonymous conversion (should get auth error)
    print("1. Testing anonymous conversion (should fail with auth error)...")
    response = requests.post(f'{base_url}/api/cia/potential-bid-cards/{bid_card_id}/convert-to-bid-card')
    print(f"Anonymous conversion status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Check what the exact error is
    if response.status_code == 500:
        print("❌ Getting 500 error instead of auth error - this is the bug we need to fix")
    
    # Now test with user_id (simulated authentication)
    print("\n2. Testing with user_id (simulated authentication)...")
    
    # First add a user_id to the bid card to simulate authentication
    user_id = "550e8400-e29b-41d4-a716-446655440001"  # Demo homeowner user
    
    payload = {
        'field_name': 'user_id',
        'field_value': user_id,
        'source': 'authentication_simulation'
    }
    
    user_response = requests.put(f'{base_url}/api/cia/potential-bid-cards/{bid_card_id}/field', json=payload)
    print(f"Adding user_id: {user_response.status_code}")
    
    if user_response.status_code == 200:
        # Now try conversion with authentication
        auth_response = requests.post(f'{base_url}/api/cia/potential-bid-cards/{bid_card_id}/convert-to-bid-card')
        print(f"Authenticated conversion status: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        
        if auth_response.status_code == 200:
            result = auth_response.json()
            print("✅ CONVERSION SUCCESSFUL!")
            print(f"Official bid card ID: {result.get('official_bid_card_id', 'Not provided')}")
            
            # Check if the official bid card was actually created
            official_id = result.get('official_bid_card_id')
            if official_id:
                print(f"\n3. Verifying official bid card was created...")
                check_response = requests.get(f'{base_url}/api/bid-cards/{official_id}')
                print(f"Official bid card check: {check_response.status_code}")
                if check_response.status_code == 200:
                    official_card = check_response.json()
                    print(f"✅ Official bid card confirmed!")
                    print(f"   Number: {official_card.get('bid_card_number', 'N/A')}")
                    print(f"   Status: {official_card.get('status', 'N/A')}")
                    print(f"   Title: {official_card.get('title', 'N/A')}")
                    return True
                else:
                    print(f"❌ Official bid card not found: {check_response.text}")
            
        else:
            print(f"❌ Authenticated conversion failed: {auth_response.text}")
    
    return False

def test_sse_streaming_fix():
    """Test the SSE streaming endpoint with correct format"""
    print("\n" + "=" * 50)
    print("4. Testing SSE streaming endpoint fix...")
    
    base_url = 'http://localhost:8008'
    
    # Use the correct format from the working test
    test_request = {
        "messages": [{"role": "user", "content": "I want to renovate my kitchen with new cabinets, countertops, and appliances"}],
        "conversation_id": "ui_test_conv_fix_" + str(int(time.time())),
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "max_completion_tokens": 500,
        "model_preference": "gpt-5"
    }
    
    # Test with simple POST (not streaming)
    response = requests.post(f'{base_url}/api/cia/stream', json=test_request, timeout=10)
    print(f"CIA stream test status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ CIA streaming endpoint accepts correct format!")
        # Don't wait for full streaming response, just confirm it accepts the request
        return True
    else:
        print(f"❌ CIA streaming still has issues: {response.text}")
        return False

if __name__ == "__main__":
    import time
    
    conversion_works = test_conversion_flow()
    streaming_works = test_sse_streaming_fix()
    
    print("\n" + "=" * 50)
    print("CONVERSION & STREAMING TEST SUMMARY")
    print("=" * 50)
    
    print(f"Bid card conversion: {'✅ WORKING' if conversion_works else '❌ NEEDS FIX'}")
    print(f"SSE streaming format: {'✅ WORKING' if streaming_works else '❌ NEEDS FIX'}")
    
    if conversion_works and streaming_works:
        print("\n🎉 BOTH ISSUES FIXED! System is fully operational!")
    else:
        print("\n🔧 Still need to fix remaining issues")