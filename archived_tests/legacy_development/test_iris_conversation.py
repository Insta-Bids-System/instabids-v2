import requests
import json
import time

# Test IRIS conversation with the living room blinds scenario
user_id = "550e8400-e29b-41d4-a716-446655440001"
api_base = "http://localhost:8008"

print("Testing IRIS Conversational Flow with Living Room Blinds Photo")
print("=" * 60)

# First message - simulating photo upload context
message1 = {
    "user_id": user_id,
    "message": "I just uploaded a photo of my living room with broken vertical blinds. I want to save this photo both as inspiration for a living room transformation AND as documentation of my current living room that needs repairs. Can you help me organize this and also add 'fixing the broken blinds' to my home maintenance task list?",
    "room_type": "living_room",
    "conversation_context": [{
        "type": "photo_upload",
        "filename": "WhatsApp Image 2025-04-11 at 15.53.01_5b9685d0.jpg",
        "context": "dual_purpose",
        "property_documentation": True,
        "inspiration_board": True,
        "room_id": "living_room_current"
    }]
}

print("\n1. Sending initial message about living room blinds photo...")
response1 = requests.post(f"{api_base}/api/iris/chat", json=message1)
if response1.status_code == 200:
    result = response1.json()
    print(f"IRIS Response: {result.get('response', 'No response')[:500]}...")
    session_id = result.get('session_id')
    print(f"Session ID: {session_id}")
else:
    print(f"Error: {response1.status_code} - {response1.text}")
    session_id = None

# Second message - asking about specific blind repair options
if session_id:
    time.sleep(2)
    message2 = {
        "user_id": user_id,
        "message": "What are my options for fixing or replacing these vertical blinds? I see several slats are broken or hanging incorrectly.",
        "session_id": session_id
    }
    
    print("\n2. Asking about blind repair options...")
    response2 = requests.post(f"{api_base}/api/iris/chat", json=message2)
    if response2.status_code == 200:
        result = response2.json()
        print(f"IRIS Response: {result.get('response', 'No response')[:500]}...")
    else:
        print(f"Error: {response2.status_code} - {response2.text}")

# Third message - confirming task list addition
if session_id:
    time.sleep(2)
    message3 = {
        "user_id": user_id,
        "message": "Great! Please confirm you've added fixing the blinds to my maintenance task list, and that the photo is saved in both my property documentation and inspiration board.",
        "session_id": session_id
    }
    
    print("\n3. Confirming task list and dual-context saving...")
    response3 = requests.post(f"{api_base}/api/iris/chat", json=message3)
    if response3.status_code == 200:
        result = response3.json()
        print(f"IRIS Response: {result.get('response', 'No response')[:500]}...")
    else:
        print(f"Error: {response3.status_code} - {response3.text}")

print("\n" + "=" * 60)
print("Test completed - Check if:")
print("1. IRIS provided conversational responses about the blinds")
print("2. Photo was saved to both inspiration board AND property documentation")
print("3. 'Fixing blinds' was added to maintenance task list")