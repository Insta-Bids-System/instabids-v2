import requests
import json
import uuid
import time
import sys
import os

# Add the agents directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))
from database_simple import db

async def create_user_profile(user_id):
    """Create a user profile in the database"""
    try:
        # Create profile record with unique email
        profile_data = {
            "id": user_id,
            "email": f"user-{user_id[:8]}@example.com",
            "full_name": "Test User",
            "created_at": "now()",
            "updated_at": "now()"
        }
        
        result = db.client.table('profiles').insert(profile_data).execute()
        if result.data:
            print(f"[SUCCESS] Created user profile: {user_id}")
            return True
    except Exception as e:
        print(f"Error creating profile: {e}")
        # Check if profile already exists
        existing = db.client.table('profiles').select('*').eq('id', user_id).execute()
        if existing.data:
            print(f"[SUCCESS] Profile already exists: {user_id}")
            return True
    
    return False

def test_complete_homeowner_flow():
    """Test complete homeowner creation with profile"""
    print("Testing complete homeowner flow with Claude credits...")
    
    # Generate proper UUID
    user_id = str(uuid.uuid4())
    session_id = f"real-homeowner-{int(time.time())}"
    
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    
    # Create user profile first
    import asyncio
    profile_created = asyncio.run(create_user_profile(user_id))
    
    if not profile_created:
        print("Failed to create user profile")
        return
    
    # Test CIA conversation
    url = "http://localhost:8008/api/cia/chat"
    
    messages = [
        "Hi, I need help renovating my kitchen. I want to update the cabinets and countertops.",
        "I'm in Chicago, zip code 60614. I'd like modern white cabinets with quartz countertops.",
        "My budget is around $15,000-20,000. My name is Sarah Johnson and my email is sarah.johnson@example.com."
    ]
    
    collected_info = None
    
    for i, message in enumerate(messages):
        print(f"\n{'='*60}")
        print(f"Message {i+1}: {message}")
        print('='*60)
        
        payload = {
            "message": message,
            "user_id": user_id,
            "session_id": session_id
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Phase: {data.get('current_phase')}")
            print(f"Ready for JAA: {data.get('ready_for_jaa')}")
            
            if data.get('collected_info'):
                collected_info = data['collected_info']
                print(f"\n🎯 EXTRACTED INFORMATION:")
                for key, value in collected_info.items():
                    if value is not None and value != []:
                        print(f"  {key}: {value}")
            
            # Show response snippet
            response_text = data.get('response', '')
            print(f"\nCIA Response: {response_text[:200]}...")
            
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    
    # Check database
    print(f"\n{'='*60}")
    print("CHECKING DATABASE...")
    print('='*60)
    
    # Check conversation
    conv_result = db.client.table('agent_conversations').select('*').eq('user_id', user_id).execute()
    if conv_result.data:
        print(f"[SUCCESS] Found conversation in database!")
        conv = conv_result.data[0]
        state = conv.get('state', {})
        if isinstance(state, str):
            state = json.loads(state)
        if state.get('collected_info'):
            print(f"[SUCCESS] Database has collected info with {len([k for k,v in state['collected_info'].items() if v])} fields")
    else:
        print("[ERROR] No conversation found in database")
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"Homeowner created: {user_id}")
    print(f"Ready for JAA: {data.get('ready_for_jaa', False) if 'data' in locals() else 'Unknown'}")
    print(f"Information extracted: {'Yes' if collected_info else 'No'}")
    print("='*60")

if __name__ == "__main__":
    test_complete_homeowner_flow()