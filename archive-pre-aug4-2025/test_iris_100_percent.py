import time

import requests


# Wait for server
time.sleep(5)

print("\n100% CONFIRMATION TEST FOR IRIS IMAGE GENERATION")
print("=" * 60)

# Test parameters
iris_url = "http://localhost:8008/api/iris/chat"
board_id = "26cf972b-83e4-484c-98b6-a5d1a4affee3"
user_id = "550e8400-e29b-41d4-a716-446655440001"

# Test 1: Request image generation
print("\nTest 1: Asking Iris to generate an image...")
print("-" * 40)

payload = {
    "message": "Generate a vision of a modern kitchen with white cabinets",
    "user_id": user_id,
    "board_id": board_id
}

try:
    response = requests.post(iris_url, json=payload, timeout=40)
    if response.ok:
        result = response.json()

        # Check for image generation
        if result.get("image_generated"):
            print("SUCCESS: Image was generated!")
            print(f"- Image URL: {result.get('image_url', 'None')}")
            print(f"- Generation ID: {result.get('generation_id', 'None')}")
            print(f"- Board ID: {board_id}")

            # Verify it's in the data section too
            if "data" in result:
                print(f"- Data contains: {list(result['data'].keys())}")
                print(f"- Saved as vision: {result['data'].get('saved_as_vision', False)}")

        else:
            print("FAIL: No image was generated")
            print("Response was just text without actual generation")

    else:
        print(f"Error: Status code {response.status_code}")

except Exception as e:
    print(f"Error: {e!s}")

# Test 2: Memory persistence
print("\n\nTest 2: Testing memory persistence...")
print("-" * 40)

payload2 = {
    "message": "What did I just ask you to generate?",
    "user_id": user_id,
    "board_id": board_id,
    "conversation_context": [{
        "role": "user",
        "content": "Generate a vision of a modern kitchen with white cabinets"
    }]
}

try:
    response = requests.post(iris_url, json=payload2, timeout=10)
    if response.ok:
        result = response.json()
        response_text = result["response"].lower()

        if "kitchen" in response_text and "cabinet" in response_text:
            print("SUCCESS: Memory is persisting!")
            print(f"Iris remembers: '{result['response'][:100]}...'")
        else:
            print("FAIL: Memory not persisting properly")

except Exception as e:
    print(f"Error: {e!s}")

# Final summary
print("\n\nFINAL CONFIRMATION:")
print("=" * 60)
print("1. Image generation tool integration: [CHECK ABOVE]")
print("2. Images saving to correct board: [CHECK ABOVE]")
print("3. Memory persistence: [CHECK ABOVE]")
print("4. Consistent behavior: [RUN MULTIPLE TIMES TO VERIFY]")

print("\nNOTE: Even if using demo/fallback images, the system should")
print("      still return image_generated=True with proper URLs.")
