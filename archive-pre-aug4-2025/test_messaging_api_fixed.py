#!/usr/bin/env python3
"""Fixed messaging API test with valid UUIDs"""

import requests
import json
import uuid

API_BASE = "http://localhost:8008/api/messages"

def test_send_message_fixed():
    """Test sending a message with valid UUIDs"""
    print("=== TESTING MESSAGE SENDING (FIXED) ===")
    
    # Use a real bid card ID from database
    bid_card_id = "36214de5-a068-4dcc-af99-cf33238e7472"
    sender_id = str(uuid.uuid4())
    
    message_data = {
        "content": "Hi, I'm interested in your project. Call me at 555-123-4567 or email john@test.com",
        "sender_type": "contractor",
        "sender_id": sender_id,
        "bid_card_id": bid_card_id,
        "message_type": "text"
    }
    
    print(f"Testing with bid_card_id: {bid_card_id}")
    print(f"Original content: {message_data['content']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/send",
            json=message_data,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Message sent successfully!")
            print(f"Message ID: {result['id']}")
            print(f"Conversation ID: {result['conversation_id']}")
            print(f"Filtered Content: {result['filtered_content']}")
            print(f"Content Filtered: {result['content_filtered']}")
            print(f"Filter Reasons: {len(result['filter_reasons'])} filters applied")
            
            # Check if contact info was filtered
            has_phone_filter = any("555-123-4567" in str(reason) for reason in result['filter_reasons'])
            has_email_filter = any("john@test.com" in str(reason) for reason in result['filter_reasons'])
            
            success = (
                "[CONTACT REMOVED]" in result["filtered_content"] or
                "[PHONE REMOVED]" in result["filtered_content"] or
                "[EMAIL REMOVED]" in result["filtered_content"]
            ) and result["content_filtered"]
            
            print(f"Content Filtering: {'✅ PASSED' if success else '❌ FAILED'}")
            print(f"Phone filtered: {'✅' if has_phone_filter else '❌'}")
            print(f"Email filtered: {'✅' if has_email_filter else '❌'}")
            
            return success, result
        else:
            print(f"❌ Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False, None

def test_conversation_retrieval(bid_card_id, user_id):
    """Test retrieving conversations"""
    print(f"\n=== TESTING CONVERSATION RETRIEVAL ===")
    
    try:
        response = requests.get(
            f"{API_BASE}/conversations/{bid_card_id}",
            params={"user_type": "contractor", "user_id": user_id},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ Found {len(conversations)} conversations")
            
            if conversations:
                conv = conversations[0]
                print(f"Conversation ID: {conv['id']}")
                print(f"Contractor Alias: {conv['contractor_alias']}")
                print(f"Status: {conv['status']}")
                return True, conv['id']
            else:
                print("No conversations found")
                return True, None
        else:
            print(f"❌ Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False, None

def test_message_retrieval(conversation_id):
    """Test retrieving messages from conversation"""
    print(f"\n=== TESTING MESSAGE RETRIEVAL ===")
    
    try:
        response = requests.get(
            f"{API_BASE}/conversation/{conversation_id}/messages",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Found {len(messages)} messages")
            
            if messages:
                msg = messages[0]
                print(f"Message ID: {msg['id']}")
                print(f"Sender Type: {msg['sender_type']}")
                print(f"Filtered Content: {msg['filtered_content']}")
                print(f"Content Filtered: {msg['content_filtered']}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def run_complete_test():
    """Run complete messaging test flow"""
    print("=== MESSAGING API COMPLETE TEST (FIXED) ===")
    
    # Test 1: Health check
    print("=== TESTING HEALTH ENDPOINT ===")
    response = requests.get(f"{API_BASE}/health", timeout=10)
    health_ok = response.status_code == 200
    print(f"Health Status: {'✅ PASSED' if health_ok else '❌ FAILED'}")
    
    if not health_ok:
        print("Health check failed - aborting tests")
        return False
    
    # Test 2: Send message
    message_ok, message_result = test_send_message_fixed()
    
    if not message_ok:
        print("Message sending failed - aborting further tests")
        return False
    
    # Test 3: Retrieve conversations
    bid_card_id = "36214de5-a068-4dcc-af99-cf33238e7472"
    sender_id = message_result['sender_id']
    conv_ok, conversation_id = test_conversation_retrieval(bid_card_id, sender_id)
    
    # Test 4: Retrieve messages
    if conv_ok and conversation_id:
        msg_ok = test_message_retrieval(conversation_id)
    else:
        msg_ok = False
        print("❌ Skipping message retrieval - no conversation found")
    
    # Overall results
    all_passed = health_ok and message_ok and conv_ok and msg_ok
    
    print(f"\n=== FINAL TEST RESULTS ===")
    print(f"Health Check: {'✅' if health_ok else '❌'}")
    print(f"Message Sending: {'✅' if message_ok else '❌'}")  
    print(f"Conversation Retrieval: {'✅' if conv_ok else '❌'}")
    print(f"Message Retrieval: {'✅' if msg_ok else '❌'}")
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = run_complete_test()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)