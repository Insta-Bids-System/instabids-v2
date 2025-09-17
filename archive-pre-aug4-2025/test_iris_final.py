import time

import requests


# Wait a moment for server to fully start
time.sleep(3)

# Test Iris chat with image generation request
url = "http://localhost:8008/api/iris/chat"

payload = {
    "message": "Can you generate a vision of my kitchen with modern white cabinets?",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3"
}

print("Testing Iris image generation...")
print("=" * 50)

try:
    response = requests.post(url, json=payload, timeout=40)
    print(f"Status Code: {response.status_code}")

    if response.ok:
        result = response.json()
        print(f"\nResponse keys: {list(result.keys())}")

        # Check if image was generated
        if result.get("image_generated"):
            print("\n✅ SUCCESS: Image was actually generated!")
            print(f"Image URL: {result.get('image_url')}")
            print(f"Generation ID: {result.get('generation_id')}")

            # Check if data is included
            if "data" in result:
                print("\nFull generation data available:")
                print(f"- Success: {result['data'].get('success')}")
                print(f"- Message: {result['data'].get('message')}")
                print(f"- Saved as vision: {result['data'].get('saved_as_vision')}")
        else:
            print("\n❌ FAIL: Image was NOT generated")
            print("Response was just text without actual image generation")

        print(f"\nIris Response: {result['response'][:200]}...")

except Exception as e:
    print(f"Error: {e}")

# Test memory persistence
print("\n\nTesting memory persistence...")
print("=" * 50)

payload2 = {
    "message": "What did I just ask you to generate?",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3"
}

try:
    response = requests.post(url, json=payload2, timeout=10)
    if response.ok:
        result = response.json()
        print(f"Memory test response: {result['response'][:200]}...")
except Exception as e:
    print(f"Memory test error: {e}")
