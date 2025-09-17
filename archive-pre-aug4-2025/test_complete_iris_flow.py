
import requests


print("COMPLETE IRIS WORKFLOW TEST")
print("=" * 60)

# 1. Test direct image generation API
print("\n1. Testing Image Generation API directly...")
print("-" * 40)

gen_url = "http://localhost:8008/api/image-generation/generate-dream-space"
gen_payload = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "ideal_image_id": "inspiration_1",
    "current_image_id": "current_1",
    "user_preferences": "Modern kitchen with white cabinets"
}

try:
    response = requests.post(gen_url, json=gen_payload, timeout=30)
    if response.ok:
        result = response.json()
        print("✓ Direct API call successful")
        print(f"  - Success: {result.get('success')}")
        print(f"  - Image URL: {result.get('generated_image_url', 'None')[:60]}...")
        print(f"  - Saved as vision: {result.get('saved_as_vision')}")
        direct_image_url = result.get("generated_image_url")
    else:
        print(f"✗ Direct API call failed: {response.status_code}")
except Exception as e:
    print(f"✗ Direct API error: {e}")

# 2. Test Iris chat with generation request
print("\n\n2. Testing Iris Chat with image generation request...")
print("-" * 40)

iris_url = "http://localhost:8008/api/iris/chat"
iris_payload = {
    "message": "Please generate a vision of my kitchen with modern white cabinets",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3"
}

try:
    response = requests.post(iris_url, json=iris_payload, timeout=40)
    if response.ok:
        result = response.json()
        print("✓ Iris response received")
        print(f"  - Response keys: {list(result.keys())}")
        print(f"  - Image generated: {result.get('image_generated', False)}")
        print(f"  - Image URL: {result.get('image_url', 'None')[:60] if result.get('image_url') else 'None'}")
        print(f"  - Generation ID: {result.get('generation_id', 'None')}")

        # Check if Iris returned image data
        if result.get("image_generated"):
            print("\n✓ SUCCESS: Iris is now generating images!")
            if result.get("image_url") == direct_image_url:
                print("✓ VERIFIED: Same image URL as direct API call")
            else:
                print("⚠ WARNING: Different image URL than direct API")
        else:
            print("\n✗ FAIL: Iris did not generate an image")

        print(f"\n  Iris said: '{result['response'][:150]}...'")

    else:
        print(f"✗ Iris call failed: {response.status_code}")
except Exception as e:
    print(f"✗ Iris error: {e}")

# 3. Test memory persistence
print("\n\n3. Testing memory persistence...")
print("-" * 40)

memory_payload = {
    "message": "What did I just ask you about?",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3"
}

try:
    response = requests.post(iris_url, json=memory_payload, timeout=10)
    if response.ok:
        result = response.json()
        response_text = result["response"].lower()

        # Check if Iris remembers the kitchen request
        if any(word in response_text for word in ["kitchen", "cabinets", "vision", "generate"]):
            print("✓ Memory working: Iris remembers the previous request")
        else:
            print("✗ Memory issue: Iris doesn't seem to remember")

        print(f"  Iris said: '{result['response'][:150]}...'")
    else:
        print(f"✗ Memory test failed: {response.status_code}")
except Exception as e:
    print(f"✗ Memory test error: {e}")

# 4. Summary
print("\n\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

print("\nCHECKLIST:")
print("[ ] Image generation API works directly")
print("[ ] Iris calls the image generation API")
print("[ ] Images are saved with correct board ID")
print("[ ] Memory persists between conversations")
print("[ ] Complete end-to-end workflow functions")

print("\nNOTE: Even if using demo/mock images, the system should still")
print("      return proper image URLs and generation IDs.")
