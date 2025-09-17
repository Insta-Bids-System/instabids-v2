#!/usr/bin/env python3
"""Direct test of COIA conversation persistence via unified API"""

import requests
import uuid
import hashlib

def ensure_uuid(value):
    """Convert string to deterministic UUID - same as in unified_coia_api.py"""
    if not value:
        return "00000000-0000-0000-0000-000000000000"
    try:
        uuid.UUID(value)
        return value
    except ValueError:
        namespace_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        return str(uuid.uuid5(namespace_uuid, value))

# Test contractor
contractor_id = "test-contractor-persistence"
user_uuid = ensure_uuid(contractor_id)

print(f"Testing conversation persistence for: {contractor_id}")
print(f"Deterministic UUID: {user_uuid}")
print("=" * 70)

# 1. Create conversation via unified API
print("\n1. Creating conversation via unified API...")
response = requests.post("http://localhost:8008/api/conversations/create", json={
    "user_id": user_uuid,
    "agent_type": "coia",
    "context": {
        "session_id": contractor_id,
        "contractor_lead_id": contractor_id,
        "interface": "chat"
    }
})

if response.status_code == 200:
    data = response.json()
    conversation_id = data.get("conversation_id")
    print(f"[OK] Created conversation: {conversation_id}")
else:
    print(f"[ERROR] Failed to create conversation: {response.status_code}")
    print(response.text)
    exit(1)

# 2. Add first message
print("\n2. Adding first message...")
response = requests.post("http://localhost:8008/api/conversations/message", json={
    "conversation_id": conversation_id,
    "sender_type": "user",
    "sender_id": user_uuid,
    "content": "Hi, I'm a plumber interested in InstaBids"
})

if response.status_code == 200:
    print(f"[OK] Added user message")
else:
    print(f"[ERROR] Failed to add message: {response.status_code}")

# 3. Add assistant response
print("\n3. Adding assistant response...")
response = requests.post("http://localhost:8008/api/conversations/message", json={
    "conversation_id": conversation_id,
    "sender_type": "agent",
    "sender_id": "coia-agent",
    "content": "Welcome to InstaBids! Let me help you get started."
})

if response.status_code == 200:
    print(f"[OK] Added assistant message")
else:
    print(f"[ERROR] Failed to add message: {response.status_code}")

# 4. Check if conversation can be retrieved
print("\n4. Retrieving conversation for user...")
response = requests.get(f"http://localhost:8008/api/conversations/user/{user_uuid}")

if response.status_code == 200:
    data = response.json()
    if data.get("success") and data.get("conversations"):
        print(f"[OK] Found {len(data['conversations'])} conversation(s)")
        # Check if our conversation is there
        for conv in data["conversations"]:
            if "unified_conversations" in conv:
                conv_data = conv["unified_conversations"]
                if isinstance(conv_data, dict):
                    found_id = conv_data.get("id")
                elif isinstance(conv_data, list) and len(conv_data) > 0:
                    found_id = conv_data[0].get("id")
                else:
                    found_id = None
                    
                if found_id == conversation_id:
                    print(f"[VERIFIED] Conversation {conversation_id} is retrievable!")
                    break
    else:
        print(f"[ERROR] No conversations found")
else:
    print(f"[ERROR] Failed to retrieve: {response.status_code}")

print("\n" + "=" * 70)
print("SUMMARY: Testing complete - check database for verification")