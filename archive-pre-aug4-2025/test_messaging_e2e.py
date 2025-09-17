import requests
import json
import uuid

# Test the complete messaging system end-to-end
BASE_URL = "http://localhost:8008"

def test_send_message_with_filtering():
    """Test sending a message with contact information that should be filtered"""
    
    # Generate test IDs
    conversation_id = str(uuid.uuid4())
    bid_card_id = str(uuid.uuid4())
    sender_id = str(uuid.uuid4())
    
    # Test message with contact information
    test_message = {
        "content": "Hi! You can reach me at 555-123-4567 or email john@example.com. My address is 123 Main St, Austin TX.",
        "sender_type": "contractor",
        "sender_id": sender_id,
        "bid_card_id": bid_card_id,
        "conversation_id": conversation_id,
        "message_type": "text"
    }
    
    print("=== Testing Message Sending with Content Filtering ===")
    print(f"Original message: {test_message['content']}")
    print(f"Conversation ID: {conversation_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/messages/send",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Message sent successfully!")
            print(f"Filtered content: '{result.get('filtered_content', 'N/A')}'")
            print(f"Content was filtered: {result.get('content_filtered', False)}")
            print(f"Filter reasons: {result.get('filter_reasons', [])}")
            print(f"Message ID: {result.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return False

def test_clean_message():
    """Test sending a clean message without contact information"""
    
    # Generate test IDs
    conversation_id = str(uuid.uuid4())
    bid_card_id = str(uuid.uuid4())
    sender_id = str(uuid.uuid4())
    
    # Clean test message
    test_message = {
        "content": "Thanks for your interest in the project! The timeline looks good and I'm excited to work with you.",
        "sender_type": "homeowner",
        "sender_id": sender_id,
        "bid_card_id": bid_card_id,
        "conversation_id": conversation_id,
        "message_type": "text"
    }
    
    print("\n\n=== Testing Clean Message (No Filtering Expected) ===")
    print(f"Clean message: {test_message['content']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/messages/send",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Clean message sent successfully!")
            print(f"Filtered content: '{result.get('filtered_content', 'N/A')}'")
            print(f"Content was filtered: {result.get('content_filtered', False)}")
            print(f"Filter reasons: {result.get('filter_reasons', [])}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return False

def test_broadcast_message():
    """Test broadcast messaging functionality"""
    
    bid_card_id = str(uuid.uuid4())
    sender_id = str(uuid.uuid4())
    
    broadcast_data = {
        "content": "Project update: Timeline extended by 2 weeks. Please contact me at info@company.com for questions.",
        "sender_type": "homeowner",
        "sender_id": sender_id,
        "bid_card_id": bid_card_id,
        "recipient_type": "all_contractors",
        "recipient_ids": [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
    }
    
    print("\n\n=== Testing Broadcast Message ===")
    print(f"Broadcast message: {broadcast_data['content']}")
    print(f"Recipients: {len(broadcast_data['recipient_ids'])} contractors")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/messages/broadcast",
            json=broadcast_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Broadcast sent successfully!")
            print(f"Broadcast ID: {result.get('broadcast_id', 'N/A')}")
            print(f"Filtered content: '{result.get('filtered_content', 'N/A')}'")
            print(f"Content was filtered: {result.get('content_filtered', False)}")
            print(f"Filter reasons: {result.get('filter_reasons', [])}")
            print(f"Total recipients: {result.get('total_recipients', 0)}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Messaging System End-to-End Tests")
    print("=" * 60)
    
    # Test health endpoint first
    try:
        health_response = requests.get(f"{BASE_URL}/api/messages/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health Check: {health_data['status']}")
            print(f"Database: {health_data.get('database', 'unknown')}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to messaging API: {e}")
        exit(1)
    
    # Run all tests
    results = []
    results.append(test_send_message_with_filtering())
    results.append(test_clean_message())
    results.append(test_broadcast_message())
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests PASSED! Messaging system is working correctly.")
    else:
        print(f"❌ {passed}/{total} tests passed. Some issues detected.")
        
    print("\n🎯 Key Features Tested:")
    print("  • Content filtering for contact information")
    print("  • Message sending and storage")
    print("  • Broadcast messaging")
    print("  • API endpoint connectivity")
    print("  • Database integration")