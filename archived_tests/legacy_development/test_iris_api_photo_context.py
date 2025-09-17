import requests
import json

# Test the IRIS API with photo upload context
user_id = "550e8400-e29b-41d4-a716-446655440001"
api_base = "http://localhost:8008"

print("Testing IRIS API with Photo Upload Context")
print("=" * 60)

# Test message with photo upload context matching the WhatsApp image
test_data = {
    "user_id": user_id,
    "message": "I just uploaded a photo of my living room with broken vertical blinds. I want to save this photo both as inspiration for a living room transformation AND as documentation of my current living room that needs repairs. Can you help me organize this and also add 'fixing the broken blinds' to my home maintenance task list?",
    "room_type": "living_room",
    "conversation_context": [{
        "type": "photo_upload",
        "filename": "WhatsApp_living_room_blinds.jpg",  # Has "blind" in name for task trigger
        "property_documentation": True,
        "inspiration_board": True,
        "room_id": "living_room",
        "image_url": "https://xrhgrthdcaymxuqcgrmj.supabase.co/storage/v1/object/public/inspiration/living_room_blinds.jpg"
    }]
}

print("\nSending photo upload context to IRIS...")
print(f"Photo: {test_data['conversation_context'][0]['filename']}")
print(f"Property Documentation: {test_data['conversation_context'][0]['property_documentation']}")
print(f"Inspiration Board: {test_data['conversation_context'][0]['inspiration_board']}")

response = requests.post(f"{api_base}/api/iris/chat", json=test_data, timeout=30)

if response.status_code == 200:
    result = response.json()
    print(f"\n[SUCCESS] IRIS Response:")
    print(f"{result.get('response', 'No response')[:500]}...")  # First 500 chars
    print(f"\nSession ID: {result.get('session_id')}")
    print(f"Conversation ID: {result.get('conversation_id')}")
    
    # Check if dual-context saving was mentioned
    if "saved" in result.get('response', '').lower() or "documentation" in result.get('response', '').lower():
        print("\n✅ IRIS acknowledged dual-context saving!")
else:
    print(f"\n[ERROR] Status: {response.status_code}")
    print(response.text[:500])

print("\n" + "=" * 60)
print("Now check the database to verify:")
print("1. property_photos table - should have new entry")
print("2. inspiration_images table - should have new entry")
print("3. homeowner_maintenance_tasks table - should have 'fix blinds' task")