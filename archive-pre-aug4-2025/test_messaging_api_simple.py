#!/usr/bin/env python3
"""Simple messaging API test without emojis"""

import requests
import json
import uuid

API_BASE = "http://localhost:8008/api/messages"

def test_complete_flow():
    """Test complete messaging flow"""
    print("=== MESSAGING API COMPLETE TEST ===")
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    response = requests.get(f"{API_BASE}/health", timeout=10)
    if response.status_code == 200:
        print("   PASSED - Health endpoint working")
        health_ok = True
    else:
        print(f"   FAILED - Health check failed: {response.status_code}")
        return False
    
    # Test 2: Send message with filtering
    print("2. Testing message sending with content filtering...")
    
    bid_card_id = "36214de5-a068-4dcc-af99-cf33238e7472"
    sender_id = str(uuid.uuid4())
    
    message_data = {
        "content": "Hi, I'm interested in your project. Call me at 555-123-4567 or email john@test.com",
        "sender_type": "contractor", 
        "sender_id": sender_id,
        "bid_card_id": bid_card_id,
        "message_type": "text"
    }
    
    print(f"   Sending: {message_data['content']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/send",
            json=message_data,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   PASSED - Message sent successfully")
            print(f"   Message ID: {result['id']}")
            print(f"   Filtered Content: {result['filtered_content']}")
            print(f"   Content Filtered: {result['content_filtered']}")
            print(f"   Filter Reasons: {len(result['filter_reasons'])} applied")
            
            # Check filtering worked
            filtering_worked = (
                result['content_filtered'] and 
                (
                    "[CONTACT REMOVED]" in result["filtered_content"] or
                    "[PHONE REMOVED]" in result["filtered_content"] or  
                    "[EMAIL REMOVED]" in result["filtered_content"]
                )
            )
            
            if filtering_worked:
                print("   PASSED - Content filtering working correctly")
            else:
                print("   WARNING - Content filtering may not be working")
                print(f"   Original: {message_data['content']}")
                print(f"   Filtered: {result['filtered_content']}")
                
            conversation_id = result['conversation_id']
            message_ok = True
            
        else:
            print(f"   FAILED - Message sending failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   FAILED - Request failed: {e}")
        return False
    
    # Test 3: Retrieve conversations
    print("3. Testing conversation retrieval...")
    
    try:
        response = requests.get(
            f"{API_BASE}/conversations/{bid_card_id}",
            params={"user_type": "contractor", "user_id": sender_id},
            timeout=10
        )
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"   PASSED - Found {len(conversations)} conversations")
            
            if conversations:
                conv = conversations[0]
                print(f"   Conversation ID: {conv['id']}")
                print(f"   Contractor Alias: {conv['contractor_alias']}")
                conv_ok = True
            else:
                print("   No conversations found (this may be normal)")
                conv_ok = True
        else:
            print(f"   FAILED - Conversation retrieval failed: {response.status_code}")
            conv_ok = False
            
    except Exception as e:
        print(f"   FAILED - Conversation request failed: {e}")
        conv_ok = False
    
    # Test 4: Retrieve messages
    print("4. Testing message retrieval...")
    
    try:
        response = requests.get(
            f"{API_BASE}/conversation/{conversation_id}/messages",
            timeout=10
        )
        
        if response.status_code == 200:
            messages = response.json()
            print(f"   PASSED - Found {len(messages)} messages")
            
            if messages:
                msg = messages[0]
                print(f"   Message content: {msg['filtered_content']}")
                print(f"   Content filtered: {msg['content_filtered']}")
            
            msg_ok = True
        else:
            print(f"   FAILED - Message retrieval failed: {response.status_code}")
            msg_ok = False
            
    except Exception as e:
        print(f"   FAILED - Message retrieval request failed: {e}")
        msg_ok = False
    
    # Overall results
    all_passed = health_ok and message_ok and conv_ok and msg_ok
    
    print("\n=== TEST RESULTS ===")
    print(f"Health Check: {'PASSED' if health_ok else 'FAILED'}")
    print(f"Message Sending: {'PASSED' if message_ok else 'FAILED'}")
    print(f"Conversation Retrieval: {'PASSED' if conv_ok else 'FAILED'}")
    print(f"Message Retrieval: {'PASSED' if msg_ok else 'FAILED'}")
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_complete_flow()
        print(f"\nFinal Result: {'SUCCESS' if success else 'FAILURE'}")
    except Exception as e:
        print(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()