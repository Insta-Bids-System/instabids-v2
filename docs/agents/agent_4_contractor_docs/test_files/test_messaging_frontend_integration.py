"""
Test script to verify messaging API integration for frontend
Shows exactly what the React components should be calling
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8008"
HOMEOWNER_ID = "11111111-1111-1111-1111-111111111111"
CONTRACTOR_ID = "22222222-2222-2222-2222-222222222222"
BID_CARD_ID = "36214de5-a068-4dcc-af99-cf33238e7472"

print("=== MESSAGING API INTEGRATION TEST FOR FRONTEND ===\n")

# 1. Test sending a message (what MessageInput should call)
print("1. Testing message sending (for MessageInput component)...")
print("   Frontend should POST to: /api/messages/send")
print("   With body:")

message_data = {
    "content": "Hi, I need help with my kitchen renovation. Please call me at 555-1234",
    "sender_type": "homeowner",
    "sender_id": HOMEOWNER_ID,
    "bid_card_id": BID_CARD_ID,
    "message_type": "text"
}

print(f"   {json.dumps(message_data, indent=4)}")

try:
    response = requests.post(f"{BASE_URL}/api/messages/send", json=message_data)
    print(f"\n   Response Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Message sent successfully!")
        print(f"   Message ID: {result.get('id')}")
        print(f"   Filtered content: {result.get('filtered_content')}")
        print(f"   Content was filtered: {result.get('content_filtered')}")
        conversation_id = result.get('conversation_id')
    else:
        print(f"   ❌ Error: {response.text}")
        conversation_id = None
except Exception as e:
    print(f"   ❌ Connection error: {e}")
    conversation_id = None

print("\n" + "="*60 + "\n")

# 2. Test getting conversations (what ConversationList should call)
print("2. Testing conversation retrieval (for ConversationList component)...")
print(f"   Frontend should GET: /api/messages/conversations?user_type=homeowner&user_id={HOMEOWNER_ID}")

try:
    response = requests.get(
        f"{BASE_URL}/api/messages/conversations",
        params={"user_type": "homeowner", "user_id": HOMEOWNER_ID}
    )
    print(f"\n   Response Status: {response.status_code}")
    if response.status_code == 200:
        conversations = response.json()
        print(f"   ✅ Found {len(conversations)} conversations")
        if conversations:
            print(f"   First conversation:")
            print(f"   - ID: {conversations[0].get('id')}")
            print(f"   - Contractor: {conversations[0].get('contractor_alias')}")
            print(f"   - Last message: {conversations[0].get('last_message_at')}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Connection error: {e}")

print("\n" + "="*60 + "\n")

# 3. Test getting messages in a conversation (what MessageThread should call)
if conversation_id:
    print("3. Testing message retrieval (for MessageThread component)...")
    print(f"   Frontend should GET: /api/messages/{conversation_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/messages/{conversation_id}")
        print(f"\n   Response Status: {response.status_code}")
        if response.status_code == 200:
            messages = response.json()
            print(f"   ✅ Found {len(messages.get('messages', []))} messages")
            if messages.get('messages'):
                print(f"   Latest message:")
                msg = messages['messages'][-1]
                print(f"   - Sender: {msg.get('sender_type')}")
                print(f"   - Filtered content: {msg.get('filtered_content')}")
                print(f"   - Original had contact info: {msg.get('content_filtered')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

print("\n" + "="*60 + "\n")

# Show what NOT to do
print("⚠️  WHAT THE FRONTEND SHOULD NOT DO:")
print("   ❌ Don't use supabase.from('conversations').select() directly")
print("   ❌ Don't use supabase.from('messages').insert() directly")
print("   ❌ Don't bypass the API - you'll miss content filtering!")

print("\n✅ ALWAYS USE THE API ENDPOINTS:")
print("   - POST /api/messages/send - Filters content, manages conversations")
print("   - GET /api/messages/conversations - Gets user's conversations")
print("   - GET /api/messages/{conversation_id} - Gets messages in conversation")
print("   - PUT /api/messages/{message_id}/read - Marks message as read")

print("\n🔧 REQUIRED CHANGES TO REACT COMPONENTS:")
print("   1. MessageInput.tsx - Use fetch() or axios to POST to /api/messages/send")
print("   2. ConversationList.tsx - Use fetch() to GET from /api/messages/conversations")
print("   3. MessageThread.tsx - Use fetch() to GET from /api/messages/{id}")
print("   4. Remove direct Supabase calls - they bypass filtering!")