"""
Test CIA with non-streaming to diagnose timeout issues
"""
import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8008"

def test_cia_non_streaming():
    """Test CIA without streaming to check if it completes"""
    
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print(f"Testing CIA non-streaming with session: {session_id}")
    
    # Simple test message
    request_data = {
        "messages": [{"role": "user", "content": "I need to fix my deck in Manhattan 10001"}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    print("Sending request (10 second timeout)...")
    
    try:
        # Try non-streaming endpoint first
        response = requests.post(
            f"{BASE_URL}/api/cia/chat",  # Try the regular chat endpoint
            json=request_data,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response received:")
            print(json.dumps(data, indent=2)[:500])
        else:
            print(f"Error response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("Request timed out after 10 seconds")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cia_non_streaming()