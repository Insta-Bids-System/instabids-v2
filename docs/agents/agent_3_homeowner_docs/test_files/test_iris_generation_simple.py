"""
Simple test to prove IRIS can generate images
"""

import requests
import json
import time

BASE_URL = "http://localhost:8008"

# These are the IDs from the board we're testing
BOARD_ID = "26cf972b-83e4-484c-98b6-a5d1a4affee3"
CURRENT_IMAGE_ID = "5d46e708-3f0c-4985-9617-68afd8e2892b"  
INSPIRATION_IMAGE_ID = "115f9265-e462-458f-a159-568790fc6941"
USER_ID = "550e8400-e29b-41d4-a716-446655440001"

def test_iris_with_generation():
    print("=== TESTING IRIS IMAGE GENERATION ===\n")
    
    # Step 1: First simulate clicking on images to add context
    print("1. Simulating image selection context...")
    
    context_messages = [
        {
            "role": "system",
            "content": "User clicked on current space image: Traditional kitchen with white cabinets. Features: white cabinets, tile backsplash, limited counter space"
        },
        {
            "role": "system", 
            "content": "User clicked on inspiration image: Modern industrial kitchen. Features: exposed brick, pendant lights, open shelving"
        }
    ]
    
    # Step 2: Ask IRIS to generate
    print("\n2. Asking IRIS to generate dream space...")
    
    iris_request = {
        "message": "Generate my dream kitchen vision! I want the modern industrial style applied to my current layout.",
        "user_id": USER_ID,
        "board_id": BOARD_ID,
        "conversation_context": context_messages
    }
    
    response = requests.post(f"{BASE_URL}/api/iris/chat", json=iris_request)
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nIRIS Response: {result['response'][:300]}...")
        
        # Check if image was generated
        if 'image_generated' in result and result['image_generated']:
            print("\nSUCCESS: IMAGE WAS GENERATED!")
            print(f"Image URL: {result.get('image_url', 'Not provided')}")
            print(f"Generation ID: {result.get('generation_id', 'Not provided')}")
        else:
            print("\nFAILURE: No image was generated")
            print("IRIS did not generate an image. The system is NOT working.")
    else:
        print(f"\nERROR: {response.text}")
    
    # Step 3: Try direct generation endpoint
    print("\n\n3. Testing direct generation endpoint...")
    
    generation_request = {
        "board_id": BOARD_ID,
        "current_image_id": CURRENT_IMAGE_ID,
        "ideal_image_id": INSPIRATION_IMAGE_ID,
        "user_preferences": "Modern industrial kitchen transformation"
    }
    
    gen_response = requests.post(f"{BASE_URL}/api/image-generation/generate-dream-space", json=generation_request)
    
    print(f"Direct Generation Status: {gen_response.status_code}")
    
    if gen_response.status_code == 200:
        gen_result = gen_response.json()
        print(f"\nDIRECT GENERATION RESPONSE:")
        print(json.dumps(gen_result, indent=2))
        
        # Check for OpenAI URL
        if gen_result.get('generated_image_url', '').startswith('https://oaidalleapi'):
            print("\nCONFIRMED: Real OpenAI DALL-E image generated!")
            print(f"OpenAI Image URL: {gen_result['generated_image_url']}")
            
            # Test if the URL is accessible
            img_response = requests.head(gen_result['generated_image_url'])
            print(f"Image URL Status: {img_response.status_code}")
            if img_response.status_code == 200:
                print("SUCCESS: Image URL is valid and accessible!")
            else:
                print("ERROR: Image URL returned error (might be expired)")
    else:
        print(f"\nDirect Generation Failed: {gen_response.text[:500]}")

if __name__ == "__main__":
    test_iris_with_generation()
    print("\n=== END OF TEST ===")