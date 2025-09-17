#!/usr/bin/env python3
"""
Check what the API actually returns
"""
import requests
import json

# Use the same session from our recent test
session_id = "complete_test_1754107461"

print(f"Checking API response for session: {session_id}\n")

# 1. Send a message to get the full response
print("1. Sending a message to see the response structure...")
message_data = {
    "message": "What about the flooring?",
    "images": [],
    "session_id": session_id,
    "user_id": "550e8400-e29b-41d4-a716-446655440001"
}

response = requests.post(
    "http://localhost:8008/api/cia/chat",
    json=message_data,
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    print("API Response keys:", list(result.keys()))
    
    # Check state in response
    if 'state' in result:
        state = result['state']
        if isinstance(state, dict):
            print(f"\nState is a dict with keys: {list(state.keys())}")
            if 'messages' in state:
                messages = state['messages']
                print(f"Messages in state: {len(messages)}")
                
                # Show last 2 messages
                for msg in messages[-2:]:
                    print(f"  - {msg.get('role')}: {msg.get('content', '')[:50]}...")
            else:
                print("No 'messages' key in state")
        else:
            print(f"State is type: {type(state)}")
    else:
        print("No 'state' in response")
        
    # Pretty print the whole response
    print("\n\nFull response structure:")
    print(json.dumps(result, indent=2, default=str)[:1000] + "...")
else:
    print(f"Error: {response.status_code}")
    print(response.text)