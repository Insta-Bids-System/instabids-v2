import requests
import uuid
import time
import json

# Test configuration
BASE_URL = "http://localhost:8008"
TEST_USER_ID = str(uuid.uuid4())
TEST_SESSION_ID = str(uuid.uuid4())

print("=" * 60)
print("IRIS MEMORY SYSTEM COMPREHENSIVE TEST SUITE")
print("=" * 60)

# Test 1: Session Memory - Conversation Message Persistence
print("\nTEST 1: Session Memory - Conversation Message Persistence")
print("-" * 50)

# Send first message
response1 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
    "user_id": TEST_USER_ID,
    "session_id": TEST_SESSION_ID,
    "message": "I love modern minimalist designs with lots of natural light"
})

print(f"First message status: {response1.status_code}")
if response1.status_code == 200:
    data1 = response1.json()
    print(f"Success: {data1.get('success')}")
    print(f"Response preview: {data1.get('response', '')[:150]}...")
    print("PASS: First message sent successfully")
else:
    print(f"FAIL: Error {response1.status_code} - {response1.text[:200]}")

time.sleep(2)  # Allow time for database save

# Send second message in same session
response2 = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
    "user_id": TEST_USER_ID,
    "session_id": TEST_SESSION_ID,
    "message": "Can you remind me what style I mentioned earlier?"
})

print(f"\nSecond message status: {response2.status_code}")
if response2.status_code == 200:
    data2 = response2.json()
    response_text = data2.get('response', '').lower()
    if 'minimalist' in response_text or 'natural light' in response_text:
        print("PASS: Session memory working - previous context remembered!")
    else:
        print("FAIL: Session memory not working - context not recalled")
        print(f"Response: {data2.get('response', '')[:200]}")
else:
    print(f"FAIL: Error {response2.status_code}")