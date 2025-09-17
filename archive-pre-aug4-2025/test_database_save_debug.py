#!/usr/bin/env python3
"""
Test database saving directly 
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Add the ai-agents directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

async def test_database_save():
    """Test if database saving is working"""
    
    print("Testing database conversation saving...")
    
    try:
        # Import the CIA agent
        from agents.cia.agent import CustomerInterfaceAgent
        from dotenv import load_dotenv
        
        load_dotenv(override=True)
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Create CIA agent
        cia = CustomerInterfaceAgent(anthropic_api_key)
        
        print("1. CIA agent initialized")
        
        # Create test state
        session_id = f"debug_session_{int(datetime.now().timestamp())}"
        user_id = "test_user_123" 
        
        test_state = {
            "user_id": user_id,
            "session_id": session_id,
            "messages": [
                {
                    "role": "user",
                    "content": "I need help with kitchen renovation",
                    "metadata": {"timestamp": datetime.now().isoformat()}
                },
                {
                    "role": "assistant", 
                    "content": "I'd be happy to help with your kitchen renovation project!",
                    "metadata": {"timestamp": datetime.now().isoformat()}
                }
            ],
            "collected_info": {
                "project_type": "kitchen renovation"
            },
            "current_phase": "conversation",
            "ready_for_jaa": False
        }
        
        print(f"2. Created test state with {len(test_state['messages'])} messages")
        
        # Test the save method directly
        print("3. Testing _save_conversation_to_database...")
        
        try:
            result = await cia._save_conversation_to_database(test_state, user_id, session_id)
            print(f"   SUCCESS: Save method returned: {result}")
        except Exception as e:
            print(f"   ERROR in save method: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return
        
        # Wait a moment for database write
        await asyncio.sleep(1)
        
        # Test retrieval 
        print("4. Testing conversation retrieval...")
        try:
            from database_simple import db
            conversation_state = await db.load_conversation_state(session_id)
            
            if conversation_state:
                print(f"   SUCCESS: Retrieved conversation state")
                print(f"   Keys: {list(conversation_state.keys())}")
                
                state_data = conversation_state.get('state', {})
                if isinstance(state_data, str):
                    state_data = json.loads(state_data)
                
                messages = state_data.get('messages', []) if isinstance(state_data, dict) else []
                print(f"   Messages in database: {len(messages)}")
                
                if messages:
                    print("   SUCCESS: Messages were saved to database!")
                    for i, msg in enumerate(messages):
                        print(f"     Message {i+1}: {msg.get('role')} - {msg.get('content', '')[:50]}...")
                else:
                    print("   PROBLEM: No messages found in database state")
            else:
                print("   PROBLEM: No conversation state retrieved")
                
        except Exception as e:
            print(f"   ERROR retrieving from database: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
        
        # Test the API endpoint directly
        print("5. Testing API endpoint...")
        try:
            import requests
            response = requests.get(f"http://localhost:8008/api/cia/conversation/{session_id}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   API SUCCESS: {data}")
                if data.get('success') and data.get('messages'):
                    print(f"   API returned {len(data['messages'])} messages")
                else:
                    print(f"   API returned no messages: {data}")
            else:
                print(f"   API ERROR: Status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"   ERROR testing API: {e}")
            
    except Exception as e:
        print(f"OVERALL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_save())