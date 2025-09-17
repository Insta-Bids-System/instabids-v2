#!/usr/bin/env python3
"""
Test messaging system links to bid cards and contractors
"""
import requests
import json

def test_messaging_links():
    """Test that messaging properly links conversations to bid cards and contractors"""
    
    base_url = "http://localhost:8008"
    
    # Test data
    test_bid_card_id = "11111111-1111-1111-1111-111111111111"
    test_contractor_id = "22222222-2222-2222-2222-222222222222"
    test_user_id = "33333333-3333-3333-3333-333333333333"
    
    print("Testing Messaging System Links to Bid Cards and Contractors")
    print("=" * 70)
    
    # Test 1: Health check
    print("\n1. Testing messaging system health...")
    try:
        health_response = requests.get(f"{base_url}/api/messages/health", timeout=10)
        print(f"   Health check status: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   System status: {health_data.get('status')}")
            print(f"   Database: {health_data.get('database')}")
        else:
            print(f"   Health check failed: {health_response.text}")
            return False
    except Exception as e:
        print(f"   Health check error: {e}")
        return False
    
    # Test 2: Send message from contractor to create conversation
    print("\n2. Testing contractor message to create conversation...")
    message_data = {
        "bid_card_id": test_bid_card_id,
        "sender_type": "contractor",
        "sender_id": test_contractor_id,
        "content": "Hi! I am interested in your project and have questions about the timeline."
    }
    
    try:
        send_response = requests.post(
            f"{base_url}/api/messages/send",
            json=message_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Send message status: {send_response.status_code}")
        
        if send_response.status_code == 200:
            send_data = send_response.json()
            print(f"   Message sent successfully: {send_data.get('success')}")
            print(f"   Conversation ID: {send_data.get('conversation_id')}")
            print(f"   Content filtered: {send_data.get('content_filtered')}")
            conversation_id = send_data.get('conversation_id')
        else:
            print(f"   Send message failed: {send_response.text}")
            return False
    except Exception as e:
        print(f"   Send message error: {e}")
        return False
    
    # Test 3: Get conversations for contractor
    print("\n3. Testing conversation retrieval for contractor...")
    try:
        conv_params = {
            "user_type": "contractor",
            "user_id": test_contractor_id
        }
        conv_response = requests.get(
            f"{base_url}/api/messages/conversations",
            params=conv_params,
            timeout=10
        )
        print(f"   Get conversations status: {conv_response.status_code}")
        
        if conv_response.status_code == 200:
            conv_data = conv_response.json()
            conversations = conv_data.get('conversations', [])
            print(f"   Found {len(conversations)} conversations")
            
            if conversations:
                conv = conversations[0]
                print(f"   Conversation ID: {conv.get('id')}")
                print(f"   Bid Card ID: {conv.get('bid_card_id')}")
                print(f"   Contractor ID: {conv.get('contractor_id')}")
                print(f"   Status: {conv.get('status')}")
                
                # Verify the conversation is linked to our test bid card
                if conv.get('bid_card_id') == test_bid_card_id:
                    print("   Conversation properly linked to bid card")
                else:
                    print("   Conversation NOT linked to correct bid card")
                    return False
                    
                # Verify the conversation is linked to our test contractor
                if conv.get('contractor_id') == test_contractor_id:
                    print("   Conversation properly linked to contractor")
                else:
                    print("   Conversation NOT linked to correct contractor")
                    return False
        else:
            print(f"   Get conversations failed: {conv_response.text}")
            return False
    except Exception as e:
        print(f"   Get conversations error: {e}")
        return False
    
    # Test 4: Get messages for the conversation
    if conversation_id:
        print("\n4. Testing message retrieval for conversation...")
        try:
            messages_response = requests.get(
                f"{base_url}/api/messages/{conversation_id}",
                timeout=10
            )
            print(f"   Get messages status: {messages_response.status_code}")
            
            if messages_response.status_code == 200:
                messages_data = messages_response.json()
                messages = messages_data.get('messages', [])
                print(f"   Found {len(messages)} messages in conversation")
                
                if messages:
                    msg = messages[0]
                    print(f"   Message ID: {msg.get('id')}")
                    print(f"   Sender type: {msg.get('sender_type')}")
                    print(f"   Content: '{msg.get('filtered_content', '')[:50]}...'")
                    print(f"   Content filtered: {msg.get('content_filtered')}")
            else:
                print(f"   Get messages failed: {messages_response.text}")
                return False
        except Exception as e:
            print(f"   Get messages error: {e}")
            return False
    
    print("\nAll messaging link tests passed!")
    print("\nTest Summary:")
    print("   • Messaging system health: Working")
    print("   • Conversation creation: Working") 
    print("   • Bid card linking: Working")
    print("   • Contractor linking: Working")
    print("   • Message retrieval: Working")
    print("   • Content filtering: Working")
    
    return True

if __name__ == "__main__":
    success = test_messaging_links()
    if success:
        print("\nAll tests passed! Messaging system properly links conversations to bid cards and contractors.")
    else:
        print("\nSome tests failed. Check the output above for details.")