import requests
import base64
import json

# Create a simple test image (1x1 red pixel)
test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

url = "http://localhost:8008/api/iris/unified-chat"
payload = {
    "message": "I've uploaded a backyard photo. Please analyze and help me organize it.",
    "user_id": "11111111-1111-1111-1111-111111111111",
    "session_id": "test-session-001",
    "property_id": "d1ce83f1-900a-4677-bbdc-375db1f7bcca",
    "images": [{
        "data": test_image_base64,
        "filename": "backyard.jpg",
        "size": 1000,
        "type": "image/jpeg"
    }],
    "trigger_image_workflow": True
}

print("Testing IRIS API with image data after JSON fix...")
response = requests.post(url, json=payload, timeout=30)

print(f"\nStatus Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Success: {data.get('success', False)}")
    print(f"Response: {data.get('response', '')[:200]}...")
    if data.get('workflow_questions'):
        print(f"Workflow Questions: {json.dumps(data['workflow_questions'], indent=2)}")
else:
    print(f"Error: {response.text[:500]}")