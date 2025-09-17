#!/usr/bin/env python3
"""
Test a real conversation through the API to see where it breaks
"""
import asyncio
import requests
import json

async def test_real_conversation_flow():
    """Test real conversation through API"""
    
    print("Testing real conversation flow through API...")
    
    # Create a session ID 
    session_id = f"real_test_session_{int(asyncio.get_event_loop().time())}"
    print(f"Using session ID: {session_id}")
    
    # Send a test message through the API
    message_data = {
        "message": "I need help with a kitchen renovation project",
        "images": [],
        "session_id": session_id
        # Note: no user_id provided, should use default and convert to real UUID
    }
    
    print("1. Sending message to CIA API...")
    try:
        response = requests.post(
            "http://localhost:8008/api/cia/chat",
            json=message_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   SUCCESS: Got response")
            print(f"   Response: {result.get('response', '')[:100]}...")
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Phase: {result.get('current_phase')}")
        else:
            print(f"   ERROR: Status {response.status_code}: {response.text}")
            return
            
    except Exception as e:
        print(f"   ERROR sending message: {e}")
        return
    
    # Wait a moment for database write
    print("2. Waiting for database write...")
    await asyncio.sleep(2)
    
    # Check conversation history API immediately 
    print("3. Checking conversation history...")
    try:
        history_response = requests.get(
            f"http://localhost:8008/api/cia/conversation/{session_id}",
            timeout=10
        )
        
        if history_response.status_code == 200:
            history_data = history_response.json()
            print(f"   SUCCESS: API responded")
            print(f"   Success: {history_data.get('success')}")
            print(f"   Total messages: {history_data.get('total_messages')}")
            
            if history_data.get('success') and history_data.get('messages'):
                message_count = len(history_data['messages'])
                print(f"   RESULT: Found {message_count} messages!")
                
                for i, msg in enumerate(history_data['messages']):
                    print(f"     Message {i+1}: {msg.get('role')} - {msg.get('content', '')[:50]}...")
                    
                if message_count >= 2:  # Should have user message + assistant response
                    print("   SUCCESS: Real conversation flow is working!")
                else:
                    print("   PROBLEM: Not enough messages (expecting at least 2)")
            else:
                print("   PROBLEM: No messages found")
                print(f"   Full response: {history_data}")
        else:
            print(f"   ERROR: Status {history_response.status_code}: {history_response.text}")
            
    except Exception as e:
        print(f"   ERROR checking history: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_conversation_flow())