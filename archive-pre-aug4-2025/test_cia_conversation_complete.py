#!/usr/bin/env python3
"""
Complete test of CIA conversation flow
"""
import asyncio
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Initialize Supabase client
supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

async def test_complete_cia_flow():
    """Test complete CIA conversation flow"""
    
    print("=== COMPLETE CIA CONVERSATION TEST ===\n")
    
    # Create unique session ID
    session_id = f"complete_test_{datetime.now().timestamp():.0f}"
    print(f"1. Using session ID: {session_id}")
    
    # Send message to CIA
    message_data = {
        "message": "I need help renovating my bathroom. It's about 100 square feet.",
        "images": [],
        "session_id": session_id,
        "user_id": "550e8400-e29b-41d4-a716-446655440001"  # Use a real UUID
    }
    
    print("\n2. Sending message to CIA API on port 8008...")
    try:
        response = requests.post(
            "http://localhost:8008/api/cia/chat",
            json=message_data,
            timeout=30
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   SUCCESS: Got response from CIA")
            print(f"   Response preview: {result.get('response', '')[:100]}...")
            print(f"   Current phase: {result.get('current_phase')}")
            print(f"   Ready for JAA: {result.get('ready_for_jaa')}")
        else:
            print(f"   ERROR: {response.text}")
            return
            
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Wait for database write
    print("\n3. Waiting 3 seconds for database write...")
    await asyncio.sleep(3)
    
    # Check database directly
    print("\n4. Checking database directly...")
    try:
        db_response = supabase.table("agent_conversations").select("*").eq(
            "thread_id", session_id
        ).execute()
        
        if db_response.data:
            print(f"   [SUCCESS] FOUND in database!")
            conv = db_response.data[0]
            print(f"   Agent type: {conv.get('agent_type')}")
            print(f"   User ID: {conv.get('user_id')}")
            print(f"   Created: {conv.get('created_at')}")
            
            # Parse state
            state_str = conv.get('state', '{}')
            if state_str:
                try:
                    state = json.loads(state_str)
                    messages = state.get('messages', [])
                    print(f"   Messages in state: {len(messages)}")
                except:
                    print("   ERROR parsing state")
        else:
            print(f"   [FAILED] NOT FOUND in database!")
            print("   This is the problem - CIA is not saving to database")
            
    except Exception as e:
        print(f"   ERROR checking database: {e}")
    
    # Check conversation history API
    print("\n5. Checking conversation history API...")
    try:
        history_response = requests.get(
            f"http://localhost:8008/api/cia/conversation/{session_id}",
            timeout=10
        )
        
        if history_response.status_code == 200:
            history_data = history_response.json()
            print(f"   API success: {history_data.get('success')}")
            print(f"   Total messages: {history_data.get('total_messages')}")
            
            if history_data.get('messages'):
                print("   [SUCCESS] Conversation history API working!")
            else:
                print("   [FAILED] No messages in history API")
        else:
            print(f"   ERROR: {history_response.status_code}")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Send a second message to test conversation continuity
    print("\n6. Sending second message to test continuity...")
    message_data2 = {
        "message": "The bathroom has a standard tub/shower combo that needs replacing",
        "images": [],
        "session_id": session_id,
        "user_id": "550e8400-e29b-41d4-a716-446655440001"
    }
    
    try:
        response2 = requests.post(
            "http://localhost:8008/api/cia/chat",
            json=message_data2,
            timeout=30
        )
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"   SUCCESS: Got second response")
            print(f"   Phase: {result2.get('current_phase')}")
            
            # Check if state has previous messages
            state = result2.get('state', {})
            if isinstance(state, dict):
                messages = state.get('messages', [])
                print(f"   Messages in memory: {len(messages)}")
                if len(messages) >= 3:  # Should have at least 3 (user, assistant, user)
                    print("   [SUCCESS] Conversation memory working!")
                else:
                    print("   [FAILED] Not enough messages in memory")
        else:
            print(f"   ERROR: {response2.text}")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_complete_cia_flow())