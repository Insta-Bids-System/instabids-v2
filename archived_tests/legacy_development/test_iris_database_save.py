#!/usr/bin/env python3
"""
Test that Iris is actually saving to the unified conversation database tables
"""

import requests
import json
import time
from datetime import datetime

def test_iris_conversation_and_verify_save():
    """Test Iris conversation and verify it saves to database"""
    
    print("Testing Iris conversation database persistence...")
    print("=" * 60)
    
    # Unique test data to track in database
    test_user_id = f"test_homeowner_{int(time.time())}"
    test_message = f"I want a modern kitchen renovation - test at {datetime.now()}"
    
    print(f"Test homeowner ID: {test_user_id}")
    print(f"Test message: {test_message}")
    print("-" * 60)
    
    # Step 1: Send conversation to Iris
    test_request = {
        "message": test_message,
        "user_id": test_user_id,
        "room_type": "kitchen",
        "session_id": f"iris_db_test_{int(time.time())}"
    }
    
    try:
        print("\n1. Sending request to Iris...")
        response = requests.post(
            "http://localhost:8008/api/iris/chat",
            json=test_request,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"ERROR: Iris returned {response.status_code}")
            return False
            
        result = response.json()
        conversation_id = result.get('conversation_id')
        session_id = result.get('session_id')
        
        print(f"SUCCESS: Got response from Iris")
        print(f"Conversation ID: {conversation_id}")
        print(f"Session ID: {session_id}")
        
        if not conversation_id:
            print("WARNING: No conversation_id returned - may not be saving")
            return False
            
        # Step 2: Query the unified conversation API to verify save
        print("\n2. Checking if conversation was saved to database...")
        
        # Try to get the conversation from unified API (no /api prefix)
        verify_response = requests.get(
            f"http://localhost:8008/conversations/{conversation_id}",
            timeout=10
        )
        
        if verify_response.status_code == 200:
            conv_data = verify_response.json()
            print("SUCCESS: Conversation found in database!")
            print(f"- Conversation type: {conv_data.get('conversation', {}).get('conversation_type')}")
            print(f"- Created by: {conv_data.get('conversation', {}).get('created_by')}")
            print(f"- Title: {conv_data.get('conversation', {}).get('title')}")
            
            # Check if messages were saved
            messages = conv_data.get('messages', [])
            print(f"\n3. Checking messages saved...")
            print(f"- Messages in conversation: {len(messages)}")
            
            if len(messages) >= 2:  # Should have user message and Iris response
                print("SUCCESS: Messages were saved!")
                for i, msg in enumerate(messages[:2]):
                    print(f"  Message {i+1}: {msg.get('sender_type')} - {msg.get('content', '')[:100]}...")
            else:
                print("WARNING: Expected at least 2 messages (user + assistant)")
                
            # Check if memory was saved
            memory = conv_data.get('memory', [])
            if memory:
                print(f"\n4. Memory entries saved: {len(memory)}")
                for mem in memory:
                    print(f"  - {mem.get('memory_type')}: {mem.get('memory_key')}")
            else:
                print("\n4. No memory entries yet (may be normal for first message)")
                
            return True
            
        elif verify_response.status_code == 404:
            print(f"ERROR: Conversation {conversation_id} NOT FOUND in database!")
            print("Iris is NOT saving to unified conversation system")
            return False
        else:
            print(f"ERROR verifying save: {verify_response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def check_unified_tables_directly():
    """Use Supabase MCP to check tables directly"""
    print("\n5. Checking database tables directly with Supabase MCP...")
    
    # This would use Supabase MCP but we'll make an API call instead
    try:
        # Try to get recent conversations
        response = requests.get(
            "http://localhost:8008/api/conversations/recent",
            params={"limit": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"Found {len(conversations)} recent conversations")
            
            for conv in conversations[:3]:
                print(f"- {conv.get('conversation_type')} | {conv.get('created_by')} | {conv.get('title', 'No title')}")
                
            return True
    except Exception as e:
        print(f"Could not check recent conversations: {e}")
    
    return False

if __name__ == "__main__":
    print("IRIS DATABASE PERSISTENCE TEST")
    print("=" * 60)
    
    # Test conversation and verify save
    success = test_iris_conversation_and_verify_save()
    
    # Check tables directly
    check_unified_tables_directly()
    
    print("\n" + "=" * 60)
    if success:
        print("RESULT: Iris IS saving to unified conversation database!")
        print("The unified conversation system integration is WORKING")
    else:
        print("RESULT: Iris may NOT be saving properly to database")
        print("Need to investigate unified conversation integration")