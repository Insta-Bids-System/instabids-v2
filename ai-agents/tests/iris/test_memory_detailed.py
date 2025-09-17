import requests
import uuid
import time
import json

# Test configuration
BASE_URL = "http://localhost:8008"

print("=" * 60)
print("IRIS MEMORY SYSTEM DETAILED TEST")
print("=" * 60)

# Test 2: Context Memory - Same User, Different Sessions
print("\nTEST 2: Context Memory - Preference Retention")
print("-" * 50)

# Use a specific user ID for continuity testing
TEST_USER_ID = str(uuid.uuid4())
SESSION_1 = str(uuid.uuid4())
SESSION_2 = str(uuid.uuid4())

# First session - establish preferences
print("Session 1: Establishing preferences...")
response1 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
    "user_id": TEST_USER_ID,
    "session_id": SESSION_1,
    "message": "I absolutely love blue colors for my kitchen design"
})

print(f"Status: {response1.status_code}")
if response1.status_code == 200:
    data1 = response1.json()
    print(f"Response: {data1.get('response', '')[:150]}...")
    conversation_id = data1.get('conversation_id', 'unknown')
    print(f"Conversation ID: {conversation_id}")

time.sleep(3)  # Allow time for memory save

# Second message in same session
print("\nSession 1 - Message 2: Testing immediate recall...")
response2 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
    "user_id": TEST_USER_ID,
    "session_id": SESSION_1,
    "message": "What color did I mention for the kitchen?"
})

print(f"Status: {response2.status_code}")
if response2.status_code == 200:
    data2 = response2.json()
    response_text = data2.get('response', '')
    print(f"Response: {response_text[:200]}...")
    
    if 'blue' in response_text.lower():
        print("PASS: Immediate context recall working!")
    else:
        print("FAIL: Context not recalled in same session")

time.sleep(2)

# New session, same user
print("\nSession 2: Testing cross-session memory...")
response3 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
    "user_id": TEST_USER_ID,
    "session_id": SESSION_2,
    "message": "Do you remember my color preferences from before?"
})

print(f"Status: {response3.status_code}")
if response3.status_code == 200:
    data3 = response3.json()
    response_text = data3.get('response', '')
    print(f"Response: {response_text[:200]}...")
    
    if 'blue' in response_text.lower():
        print("PASS: Cross-session memory working!")
    else:
        print("PARTIAL: Cross-session memory may not be working")

# Test 3: Direct Context API
print("\nTEST 3: Direct Context Retrieval API")
print("-" * 50)

context_response = requests.get(f"{BASE_URL}/api/iris/context/{TEST_USER_ID}")
print(f"Context API Status: {context_response.status_code}")

if context_response.status_code == 200:
    context_data = context_response.json()
    print(f"Success: {context_data.get('success')}")
    
    # Check for actual data
    context = context_data.get('context', {})
    if context.get('recent_messages') or context.get('preferences'):
        print("PASS: Context API returning data")
        print(f"Recent messages count: {len(context.get('recent_messages', []))}")
        print(f"Preferences: {context.get('preferences', {})}")
    else:
        print("FAIL: Context API returns empty data")
        print(f"Context structure: {json.dumps(context, indent=2)[:300]}")
else:
    print(f"FAIL: Context API error - {context_response.text[:200]}")