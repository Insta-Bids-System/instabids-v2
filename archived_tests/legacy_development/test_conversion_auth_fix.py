"""
Test the fixed authentication in bid card conversion
"""

import requests
import json

def test_conversion_authentication():
    base_url = 'http://localhost:8008'
    
    print("Testing bid card conversion authentication fix...")
    print("=" * 50)
    
    # First create a fresh potential bid card without user_id (anonymous)
    print("1. Creating anonymous potential bid card...")
    
    create_payload = {
        "conversation_id": "auth_test_conv_123",
        "session_id": "auth_test_session_123", 
        "title": "Authentication Test Project"
    }
    
    create_response = requests.post(f'{base_url}/api/cia/potential-bid-cards', json=create_payload)
    print(f"Create response: {create_response.status_code}")
    
    if create_response.status_code == 200:
        result = create_response.json()
        new_bid_card_id = result['id']
        print(f"Created bid card: {new_bid_card_id}")
        
        # Add some fields to make it ready for conversion
        print("2. Adding required fields...")
        
        required_fields = [
            ('project_type', 'kitchen_remodel'),
            ('project_description', 'Test kitchen renovation'),
            ('zip_code', '98101'),
            ('email_address', 'test@example.com'),
            ('timeline', 'urgent')
        ]
        
        for field_name, field_value in required_fields:
            field_payload = {
                'field_name': field_name,
                'field_value': field_value,
                'source': 'test'
            }
            
            field_response = requests.put(f'{base_url}/api/cia/potential-bid-cards/{new_bid_card_id}/field', json=field_payload)
            print(f"  {field_name}: {field_response.status_code}")
        
        # Now try conversion WITHOUT authentication (should fail)
        print("3. Testing anonymous conversion (should fail with 400)...")
        
        anon_response = requests.post(f'{base_url}/api/cia/potential-bid-cards/{new_bid_card_id}/convert-to-bid-card')
        print(f"Anonymous conversion status: {anon_response.status_code}")
        print(f"Response: {anon_response.text}")
        
        if anon_response.status_code == 400 and "authenticated" in anon_response.text:
            print("[SUCCESS] Authentication properly blocking anonymous conversion!")
            
            # Now add authentication and try again
            print("4. Adding authentication and retrying...")
            
            auth_payload = {
                'field_name': 'user_id',
                'field_value': '550e8400-e29b-41d4-a716-446655440001',
                'source': 'authentication'
            }
            
            auth_response = requests.put(f'{base_url}/api/cia/potential-bid-cards/{new_bid_card_id}/field', json=auth_payload)
            print(f"Add user_id: {auth_response.status_code}")
            
            if auth_response.status_code == 200:
                # Now try conversion with authentication
                auth_convert_response = requests.post(f'{base_url}/api/cia/potential-bid-cards/{new_bid_card_id}/convert-to-bid-card')
                print(f"Authenticated conversion: {auth_convert_response.status_code}")
                
                if auth_convert_response.status_code == 200:
                    convert_result = auth_convert_response.json()
                    print("[SUCCESS] Authenticated conversion works!")
                    print(f"Official bid card ID: {convert_result.get('official_bid_card_id')}")
                    print(f"Bid card number: {convert_result.get('bid_card_number')}")
                    return True
                else:
                    print(f"[ERROR] Authenticated conversion failed: {auth_convert_response.text}")
            
        else:
            print(f"[ERROR] Authentication not working properly. Got {anon_response.status_code} instead of 400")
            
    else:
        print(f"[ERROR] Failed to create bid card: {create_response.text}")
    
    return False

if __name__ == "__main__":
    success = test_conversion_authentication()
    
    print("\n" + "=" * 50)
    print("AUTHENTICATION TEST SUMMARY")
    print("=" * 50)
    
    if success:
        print("[SUCCESS] Authentication fix is working correctly!")
        print("- Anonymous conversion properly blocked with 400 error")
        print("- Authenticated conversion works and creates official bid card")
    else:
        print("[ERROR] Authentication fix needs more work")