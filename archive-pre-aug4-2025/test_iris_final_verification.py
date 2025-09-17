import json

import requests


print("FINAL VERIFICATION: Testing Iris Image Generation")
print("=" * 60)

# Test the exact same request that was sent from the UI
url = "http://localhost:8008/api/iris/chat"
payload = {
    "message": "Generate a vision of my kitchen with modern white cabinets and marble countertops",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3"
}

print("Sending request to Iris...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=45)
    print(f"\nResponse Status: {response.status_code}")

    if response.ok:
        result = response.json()
        print(f"\nResponse Keys: {list(result.keys())}")

        # Check for image generation data
        if result.get("image_generated"):
            print("\n✅ IMAGE WAS GENERATED!")
            print(f"   - Image URL: {result.get('image_url')}")
            print(f"   - Generation ID: {result.get('generation_id')}")

            # Check data field
            if "data" in result:
                data = result["data"]
                print(f"   - Data success: {data.get('success')}")
                print(f"   - Saved as vision: {data.get('saved_as_vision')}")
                print(f"   - Message: {data.get('message', 'None')[:100]}...")

        else:
            print("\n❌ NO IMAGE GENERATED")
            print("   - This was just a text response")

        print("\nIris Response:")
        print(f"'{result['response'][:200]}...'")

        # Check if there are suggestions
        if "suggestions" in result:
            print(f"\nSuggestions: {result['suggestions']}")

    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")

# Now check if the vision board was updated with new images
print("\n" + "=" * 60)
print("CHECKING VISION BOARD FOR NEW IMAGES")
print("=" * 60)

images_url = "http://localhost:8008/api/demo/inspiration/images"
params = {"board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3"}

try:
    response = requests.get(images_url, params=params)
    if response.ok:
        images = response.json()
        print(f"Total images on board: {len(images)}")

        vision_images = [img for img in images if img.get("category") == "vision"]
        print(f"Vision images: {len(vision_images)}")

        for i, img in enumerate(vision_images):
            print(f"  Vision {i+1}: {img.get('image_url', 'No URL')[:60]}...")
            print(f"            Generated: {img.get('generated_at', 'No timestamp')}")

    else:
        print(f"Error getting images: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("This test will confirm:")
print("1. Whether Iris actually generates new images")
print("2. Whether those images are saved to the board")
print("3. Whether the AI merges current + inspiration images")
print("4. Whether the frontend would see the new images")
