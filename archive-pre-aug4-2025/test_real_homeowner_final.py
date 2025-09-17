import requests
import json
import uuid
import time

# Create a real homeowner conversation and check database
def test_complete_homeowner_flow():
    url = "http://localhost:8008/api/cia/chat"
    
    # Generate a proper UUID
    user_id = str(uuid.uuid4())
    session_id = f"homeowner-bathroom-{int(time.time())}"
    
    print(f"Creating homeowner with:")
    print(f"  User ID: {user_id}")
    print(f"  Session ID: {session_id}")
    
    # First message - bathroom emergency
    payload = {
        "message": "Hi, I need help with my bathroom. The toilet is leaking and it's causing water damage!",
        "user_id": user_id,
        "session_id": session_id
    }
    
    print("\n1. Initial contact...")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Phase: {data.get('current_phase')}")
    print(f"Ready for JAA: {data.get('ready_for_jaa')}")
    
    # Provide location
    if response.status_code == 200:
        print("\n2. Providing location...")
        payload["message"] = "I'm in Chicago, zip code 60614. The leak is from the base of the toilet and the floor is starting to warp."
        response2 = requests.post(url, json=payload)
        print(f"Status: {response2.status_code}")
        data2 = response2.json()
        print(f"Phase: {data2.get('current_phase')}")
        print(f"Ready for JAA: {data2.get('ready_for_jaa')}")
        
        # Provide contact info to complete
        if response2.status_code == 200:
            print("\n3. Providing contact info...")
            payload["message"] = "My name is Sarah Johnson and my email is sarah.johnson@example.com. I need this fixed ASAP!"
            response3 = requests.post(url, json=payload)
            print(f"Status: {response3.status_code}")
            data3 = response3.json()
            print(f"Phase: {data3.get('current_phase')}")
            print(f"Ready for JAA: {data3.get('ready_for_jaa')}")
            
            # Extract collected info
            print("\n4. COLLECTED INFORMATION:")
            if data3.get('collected_info'):
                info = data3['collected_info']
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print("  No collected_info in response")
                print(f"  Full response keys: {list(data3.keys())}")
                    
            # Check database
            print("\n5. Checking database...")
            import sys
            sys.path.append('C:\\Users\\Not John Or Justin\\Documents\\instabids\\ai-agents')
            from database_simple import db
            
            # Check agent_conversations
            conv_result = db.client.table('agent_conversations').select('*').eq('user_id', user_id).execute()
            if conv_result.data:
                print(f"[FOUND] Conversation in database!")
                conv = conv_result.data[0]
                print(f"  Thread ID: {conv.get('thread_id')}")
                print(f"  Messages: {len(json.loads(conv.get('state', '{}')).get('messages', []))}")
            else:
                print("[NOT FOUND] No conversation in database")
                
            # Check homeowners table
            homeowner_result = db.client.table('homeowners').select('*').eq('user_id', user_id).execute()
            if homeowner_result.data:
                print(f"[FOUND] Homeowner profile!")
                hw = homeowner_result.data[0]
                print(f"  Name: {hw.get('name')}")
                print(f"  Email: {hw.get('email')}")
            else:
                print("[NOT FOUND] No homeowner profile")
    
    return user_id, session_id

if __name__ == "__main__":
    user_id, session_id = test_complete_homeowner_flow()
    print(f"\n\nSUMMARY:")
    print(f"Homeowner User ID: {user_id}")
    print(f"Session ID: {session_id}")