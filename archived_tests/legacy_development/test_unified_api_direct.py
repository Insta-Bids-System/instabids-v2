#!/usr/bin/env python3
"""
Test unified conversation API directly
"""

import requests
import json
from datetime import datetime

def test_unified_conversation_api():
    """Test the unified conversation API endpoints directly"""
    
    print("Testing unified conversation API endpoints...")
    print("=" * 60)
    
    # Test 1: Create a conversation
    print("\n1. Testing conversation creation...")
    
    create_request = {
        "tenant_id": "instabids-main",
        "created_by": "test_user_123",
        "conversation_type": "design_inspiration",
        "entity_type": "homeowner",
        "entity_id": "test_user_123",
        "title": "Test Kitchen Design",
        "metadata": {
            "room_type": "kitchen",
            "agent_type": "IRIS"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8008/api/conversations/create",
            json=create_request,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            conversation_id = result.get('conversation_id')
            print(f"SUCCESS: Conversation created with ID: {conversation_id}")
            
            # Test 2: Add a message
            print("\n2. Testing message addition...")
            
            message_request = {
                "conversation_id": conversation_id,
                "sender_type": "user",
                "sender_id": "test_user_123",
                "content": "I want a modern kitchen",
                "content_type": "text"
            }
            
            msg_response = requests.post(
                "http://localhost:8008/api/conversations/message",
                json=message_request,
                timeout=10
            )
            
            print(f"Message status: {msg_response.status_code}")
            
            if msg_response.status_code == 200:
                print("SUCCESS: Message added to conversation")
            else:
                print(f"ERROR adding message: {msg_response.text}")
                
            # Test 3: Get the conversation
            print("\n3. Testing conversation retrieval...")
            
            get_response = requests.get(
                f"http://localhost:8008/api/conversations/{conversation_id}",
                timeout=10
            )
            
            print(f"Get status: {get_response.status_code}")
            
            if get_response.status_code == 200:
                conv_data = get_response.json()
                print("SUCCESS: Conversation retrieved")
                print(f"- Title: {conv_data.get('conversation', {}).get('title')}")
                print(f"- Messages: {len(conv_data.get('messages', []))}")
            else:
                print(f"ERROR getting conversation: {get_response.text}")
                
            return conversation_id
        else:
            print(f"ERROR creating conversation: {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    print("UNIFIED CONVERSATION API TEST")
    print("=" * 60)
    
    conversation_id = test_unified_conversation_api()
    
    print("\n" + "=" * 60)
    if conversation_id:
        print("RESULT: Unified conversation API is WORKING")
        print(f"Test conversation ID: {conversation_id}")
    else:
        print("RESULT: Unified conversation API has issues")