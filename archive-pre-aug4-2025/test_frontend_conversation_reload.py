#!/usr/bin/env python3
"""
Test if frontend loads conversations on page reload
"""
import time
import requests
import json

print("=== FRONTEND CONVERSATION RELOAD TEST ===\n")

# 1. Create a new conversation through the API
print("1. Creating test conversation...")
session_id = f"frontend_test_{int(time.time())}"
test_user_id = "550e8400-e29b-41d4-a716-446655440001"

# Send first message
message1 = {
    "message": "I need to renovate my kitchen",
    "images": [],
    "session_id": session_id,
    "user_id": test_user_id
}

response1 = requests.post(
    "http://localhost:8008/api/cia/chat",
    json=message1,
    timeout=30
)

if response1.status_code == 200:
    print(f"   [SUCCESS] Created session: {session_id}")
else:
    print(f"   [FAILED] Could not create session")
    exit(1)

# Send second message
print("\n2. Adding second message...")
message2 = {
    "message": "It's about 200 square feet",
    "images": [],
    "session_id": session_id,
    "user_id": test_user_id
}

response2 = requests.post(
    "http://localhost:8008/api/cia/chat",
    json=message2,
    timeout=30
)

if response2.status_code == 200:
    print("   [SUCCESS] Added second message")
else:
    print("   [FAILED] Could not add message")

# Wait for database
time.sleep(2)

# 3. Check conversation history API
print("\n3. Checking conversation history API...")
history_response = requests.get(
    f"http://localhost:8008/api/cia/conversation/{session_id}",
    timeout=10
)

if history_response.status_code == 200:
    history_data = history_response.json()
    total_messages = history_data.get('total_messages', 0)
    print(f"   Total messages in database: {total_messages}")
    
    if total_messages >= 4:  # 2 user + 2 assistant
        print("   [SUCCESS] Conversation saved correctly")
    else:
        print("   [FAILED] Not enough messages saved")
        
    # Show messages
    if history_data.get('messages'):
        print("\n   Messages:")
        for msg in history_data['messages']:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:50]
            print(f"     - {role}: {content}...")
else:
    print("   [FAILED] Could not get history")

# 4. Test frontend localStorage simulation
print("\n4. Testing frontend behavior...")
print(f"   Session ID that should be in localStorage: {session_id}")
print(f"   URL to test: http://localhost:5174")
print(f"   API endpoint: http://localhost:8008/api/cia/conversation/{session_id}")

# Make the same request the frontend would make
print("\n5. Simulating frontend conversation load...")
frontend_headers = {
    'Accept': 'application/json',
    'Origin': 'http://localhost:5174',
    'Referer': 'http://localhost:5174/'
}

frontend_response = requests.get(
    f"http://localhost:8008/api/cia/conversation/{session_id}",
    headers=frontend_headers,
    timeout=10
)

if frontend_response.status_code == 200:
    frontend_data = frontend_response.json()
    if frontend_data.get('success') and frontend_data.get('messages'):
        print(f"   [SUCCESS] Frontend would load {len(frontend_data['messages'])} messages")
        print(f"   Messages are ready for display!")
    else:
        print("   [FAILED] Frontend would not load messages")
        print(f"   Response: {frontend_data}")
else:
    print(f"   [FAILED] Frontend request failed: {frontend_response.status_code}")

print("\n=== TEST COMPLETE ===")
print(f"\nTo manually test:")
print(f"1. Open browser console at http://localhost:5174")
print(f"2. Run: localStorage.setItem('cia_session_id', '{session_id}')")
print(f"3. Reload the page")
print(f"4. Check if conversation appears")