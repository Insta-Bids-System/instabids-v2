import requests
import json
import traceback

# Test the messaging API with detailed debugging
BASE_URL = "http://localhost:8008"

def test_messaging_with_debug():
    print("=== DETAILED MESSAGING DEBUG TEST ===")
    
    # Test data
    bid_card_id = "36214de5-a068-4dcc-af99-cf33238e7472"  # Real UUID from database
    user_id = "11111111-1111-1111-1111-111111111111"  # Test UUID
    contractor_id = "22222222-2222-2222-2222-222222222222"  # Test UUID
    
    try:
        # 1. Test health endpoint
        print("1. Testing health endpoint...")
        health_response = requests.get(f"{BASE_URL}/api/messages/health")
        print(f"   Health Status: {health_response.status_code}")
        
        # 2. Test message sending with detailed data
        print("2. Testing message sending...")
        message_data = {
            "bid_card_id": bid_card_id,
            "sender_type": "homeowner",
            "sender_id": user_id,
            "content": "Hi, I'm interested in your project. Call me at 555-123-4567",
            "message_type": "text"
        }
        
        print(f"   Sending data: {json.dumps(message_data, indent=2)}")
        
        message_response = requests.post(
            f"{BASE_URL}/api/messages/send",
            json=message_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Response Status: {message_response.status_code}")
        print(f"   Response Headers: {dict(message_response.headers)}")
        
        if message_response.status_code == 200:
            response_data = message_response.json()
            print(f"   Response Data: {json.dumps(response_data, indent=2)}")
        else:
            print(f"   Error Response: {message_response.text}")
            
        # 3. Check if conversation was created
        print("3. Checking if conversation exists...")
        try:
            conversation_response = requests.get(
                f"{BASE_URL}/api/messages/conversations/{bid_card_id}?user_type=homeowner&user_id={user_id}"
            )
            print(f"   Conversation Status: {conversation_response.status_code}")
            if conversation_response.status_code == 200:
                print(f"   Conversation Data: {json.dumps(conversation_response.json(), indent=2)}")
            else:
                print(f"   Conversation Error: {conversation_response.text}")
        except Exception as e:
            print(f"   Conversation Check Error: {e}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_messaging_with_debug()