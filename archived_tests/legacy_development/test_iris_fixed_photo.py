import requests
import json

# Test the fixed IRIS system with photo upload context
user_id = "550e8400-e29b-41d4-a716-446655440001"
api_base = "http://localhost:8008"

print("Testing Fixed IRIS System with Photo Upload Context")
print("=" * 60)

# Test message with photo upload context
test_data = {
    "user_id": user_id,
    "message": "I just uploaded a photo of my living room with broken vertical blinds. I want to save this photo both as inspiration for a living room transformation AND as documentation of my current living room that needs repairs. Can you help me organize this and also add 'fixing the broken blinds' to my home maintenance task list?",
    "room_type": "living_room",
    "conversation_context": [{
        "type": "photo_upload",
        "filename": "WhatsApp Image 2025-04-11 at 15.53.01_5b9685d0.jpg",
        "property_documentation": True,
        "inspiration_board": True,
        "room_id": "living_room",
        "image_url": "https://xrhgrthdcaymxuqcgrmj.supabase.co/storage/v1/object/public/inspiration/550e8400-e29b-41d4-a716-446655440001_1754964572061.jpg"
    }]
}

print("\nSending photo upload context to IRIS...")
print(f"Photo: {test_data['conversation_context'][0]['filename']}")
print(f"Dual-context: Property={test_data['conversation_context'][0]['property_documentation']}, Inspiration={test_data['conversation_context'][0]['inspiration_board']}")

response = requests.post(f"{api_base}/api/iris/chat", json=test_data)

if response.status_code == 200:
    result = response.json()
    print(f"\n[SUCCESS] IRIS Response:")
    print(f"{result.get('response', 'No response')}")
    print(f"\nSession ID: {result.get('session_id')}")
    print(f"Conversation ID: {result.get('conversation_id')}")
else:
    print(f"\n[ERROR] Status: {response.status_code}")
    print(response.text)

print("\n" + "=" * 60)
print("Test complete - Check database for:")
print("1. property_photos table for new entry")
print("2. manual_followup_tasks table for maintenance task")
print("3. inspiration_images table (should already exist)")