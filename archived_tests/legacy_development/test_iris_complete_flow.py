import requests
import json
import sys

# Force UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Test the complete IRIS flow with photo upload and task creation
user_id = "550e8400-e29b-41d4-a716-446655440001"
api_base = "http://localhost:8008"

print("Testing Complete IRIS Flow with Photo Upload")
print("=" * 60)

# Test message with photo upload context
test_data = {
    "user_id": user_id,
    "message": "I uploaded a photo of my living room with broken vertical blinds. Please save this to both my inspiration board for a living room transformation AND my property documentation. Also add 'fix broken blinds' to my maintenance tasks.",
    "room_type": "living_room",
    "conversation_context": [{
        "type": "photo_upload",
        "filename": "living_room_broken_blinds.jpg",
        "property_documentation": True,
        "inspiration_board": True,
        "room_id": "living_room",
        "image_url": "https://example.com/photo.jpg"
    }]
}

print("\n1. Sending photo upload with dual-context request...")
response = requests.post(f"{api_base}/api/iris/chat", json=test_data)

if response.status_code == 200:
    result = response.json()
    print("\n✅ IRIS Response received")
    # Print first 500 chars to avoid encoding issues
    response_text = result.get('response', 'No response')
    print(f"Response preview: {response_text[:300]}...")
    session_id = result.get('session_id')
    print(f"Session: {session_id}")
else:
    print(f"\n❌ Error: {response.status_code}")
    
print("\n" + "=" * 60)
print("VERIFICATION CHECKLIST:")
print("✓ IRIS responds conversationally about the photo")
print("✓ Photo context processed with dual-saving request")
print("✓ Maintenance task creation triggered")
print("\nDatabase tables to check:")
print("1. inspiration_images - for inspiration board entry")
print("2. property_photos - for property documentation")  
print("3. homeowner_maintenance_tasks - for fix blinds task")