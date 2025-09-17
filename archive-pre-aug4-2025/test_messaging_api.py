import requests
import json
from datetime import datetime

# Test the messaging API endpoints
BASE_URL = "http://localhost:8008"

def test_send_message():
    """Test sending a message with contact information that should be filtered"""
    
    # Test data
    test_message = {
        "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
        "bid_card_id": "123e4567-e89b-12d3-a456-426614174001",
        "sender_id": "123e4567-e89b-12d3-a456-426614174002",
        "sender_type": "contractor",
        "content": "Hi! You can reach me at 555-123-4567 or email john@example.com. My address is 123 Main St."
    }
    
    print("Testing message send endpoint...")
    print(f"Original message: {test_message['content']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/messaging/send",
            json=test_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nSuccess! Message sent.")
            print(f"Filtered content: {result.get('filtered_content', 'N/A')}")
            print(f"Was filtered: {result.get('is_filtered', False)}")
            print(f"Violations found: {result.get('violations_found', [])}")
        else:
            print(f"\nError: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\nError connecting to API: {e}")

def test_get_conversations():
    """Test getting conversations for a user"""
    
    user_id = "123e4567-e89b-12d3-a456-426614174002"
    user_type = "homeowner"
    
    print(f"\n\nTesting get conversations for {user_type} {user_id}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/messaging/conversations",
            params={"user_id": user_id, "user_type": user_type}
        )
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"Found {len(conversations)} conversations")
            for conv in conversations[:3]:  # Show first 3
                print(f"- Conversation {conv['id']}: {conv.get('last_message', 'No messages')}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error connecting to API: {e}")

def test_broadcast_message():
    """Test broadcasting a message to all contractors on a bid card"""
    
    broadcast_data = {
        "bid_card_id": "123e4567-e89b-12d3-a456-426614174001",
        "sender_id": "123e4567-e89b-12d3-a456-426614174002",
        "content": "Update: The project timeline has been extended by 2 weeks. Please update your bids accordingly.",
        "contractor_ids": [
            "123e4567-e89b-12d3-a456-426614174003",
            "123e4567-e89b-12d3-a456-426614174004",
            "123e4567-e89b-12d3-a456-426614174005"
        ]
    }
    
    print(f"\n\nTesting broadcast message...")
    print(f"Message: {broadcast_data['content']}")
    print(f"Sending to {len(broadcast_data['contractor_ids'])} contractors")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/messaging/broadcast",
            json=broadcast_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Broadcast sent.")
            print(f"Broadcast ID: {result.get('broadcast_id', 'N/A')}")
            print(f"Recipients: {result.get('recipient_count', 0)}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error connecting to API: {e}")

if __name__ == "__main__":
    print("=== Testing Messaging API ===")
    test_send_message()
    test_get_conversations()
    test_broadcast_message()
    print("\n=== Tests Complete ===")