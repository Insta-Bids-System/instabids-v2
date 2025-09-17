#!/usr/bin/env python3
"""
Test if conversation messages are being saved to database
"""
import asyncio
import requests
import json

async def test_conversation_saving():
    """Test if messages are being saved properly"""
    
    print("Testing conversation saving to database...")
    
    # Test session ID
    session_id = "test_session_" + str(int(asyncio.get_event_loop().time()))
    print(f"Using session ID: {session_id}")
    
    # Send a test message
    message_data = {
        "message": "I need help with a kitchen renovation project",
        "images": [],
        "session_id": session_id
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
            print(f"   SUCCESS: Message sent, got response: {result.get('response', '')[:100]}...")
        else:
            print(f"   ERROR: Status {response.status_code}: {response.text}")
            return
            
    except Exception as e:
        print(f"   ERROR sending message: {e}")
        return
    
    # Wait a moment for database write
    print("2. Waiting for database write...")
    await asyncio.sleep(2)
    
    # Check if conversation was saved
    print("3. Checking conversation history API...")
    try:
        history_response = requests.get(
            f"http://localhost:8008/api/cia/conversation/{session_id}",
            timeout=10
        )
        
        if history_response.status_code == 200:
            history_data = history_response.json()
            print(f"   SUCCESS: Got response: {history_data}")
            
            if history_data.get('success') and history_data.get('messages'):
                message_count = len(history_data['messages'])
                print(f"   RESULT: Found {message_count} messages in database")
                
                if message_count > 0:
                    print("   SUCCESS: Conversation was saved to database!")
                    for i, msg in enumerate(history_data['messages']):
                        print(f"     Message {i+1}: {msg.get('role')} - {msg.get('content', '')[:50]}...")
                else:
                    print("   PROBLEM: No messages found in database")
            else:
                print("   PROBLEM: API returned success=False or no messages")
                print(f"   Details: {history_data}")
        else:
            print(f"   ERROR: Status {history_response.status_code}: {history_response.text}")
            
    except Exception as e:
        print(f"   ERROR checking history: {e}")
    
    # Test the database directly
    print("4. Testing database directly...")
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))
        
        from database_simple import db
        
        # Check conversation state
        conversation_state = await db.load_conversation_state(session_id)
        if conversation_state:
            print(f"   SUCCESS: Found conversation state in database")
            print(f"   State keys: {list(conversation_state.keys())}")
            
            state_data = conversation_state.get('state', {})
            if isinstance(state_data, str):
                import json
                state_data = json.loads(state_data)
            
            messages = state_data.get('messages', []) if isinstance(state_data, dict) else []
            print(f"   Messages in state: {len(messages)}")
            
            if messages:
                for i, msg in enumerate(messages):
                    print(f"     DB Message {i+1}: {msg.get('role')} - {msg.get('content', '')[:50]}...")
            else:
                print("   PROBLEM: No messages in conversation state")
        else:
            print("   PROBLEM: No conversation state found in database")
            
    except Exception as e:
        print(f"   ERROR checking database directly: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conversation_saving())