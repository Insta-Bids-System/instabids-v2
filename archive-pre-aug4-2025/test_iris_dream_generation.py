#!/usr/bin/env python3
"""
Test Iris Agent Dream Generation Flow
Tests the complete conversation flow from homeowner request to image generation
"""
import requests
import json
import time
from datetime import datetime

# Demo user and board data
DEMO_HOMEOWNER_ID = "550e8400-e29b-41d4-a716-446655440001"
DEMO_BOARD_ID = "26cf972b-83e4-484c-98b6-a5d1a4affee3"
API_BASE = "http://localhost:8008"

def test_iris_conversation_flow():
    """Test complete Iris conversation flow for dream generation"""
    
    print("Testing Iris Dream Generation Conversation Flow")
    print("=" * 60)
    
    # Step 1: Initial conversation with Iris about dream generation
    print("\n1. Starting conversation with Iris about dream kitchen...")
    
    initial_request = {
        "message": "I want to see what my kitchen would look like with the industrial inspiration",
        "user_id": DEMO_HOMEOWNER_ID,
        "board_id": DEMO_BOARD_ID,
        "conversation_context": []
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/iris/generate-dream-space",
            json=initial_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Iris responded: {result['response'][:100]}...")
            print(f"Suggestions: {result['suggestions']}")
            
            # Should ask for confirmation
            if any(word in result['response'].lower() for word in ["confirm", "proceed", "would you like"]):
                print("SUCCESS: Iris is asking for confirmation - perfect!")
                
                # Step 2: Confirm generation
                print("\n2. Confirming dream generation...")
                
                confirmation_request = {
                    "message": "Yes, generate my dream kitchen with the exposed brick and pendant lights",
                    "user_id": DEMO_HOMEOWNER_ID,
                    "board_id": DEMO_BOARD_ID,
                    "conversation_context": [
                        {"role": "user", "content": initial_request["message"]},
                        {"role": "assistant", "content": result["response"]}
                    ]
                }
                
                generation_response = requests.post(
                    f"{API_BASE}/api/iris/generate-dream-space",
                    json=confirmation_request,
                    timeout=60  # Longer timeout for image generation
                )
                
                if generation_response.status_code == 200:
                    gen_result = generation_response.json()
                    print(f"SUCCESS: Generation response: {gen_result['response'][:100]}...")
                    
                    # Check if it mentions successful generation
                    if any(word in gen_result['response'].lower() for word in ["generated", "created", "vision board"]):
                        print("SUCCESS: Image generation successful!")
                        
                        # Step 3: Verify image appears in demo API
                        print("\n3. Verifying image appears in board...")
                        time.sleep(2)  # Give it a moment to save
                        
                        images_response = requests.get(
                            f"{API_BASE}/api/demo/inspiration/images?board_id={DEMO_BOARD_ID}"
                        )
                        
                        if images_response.status_code == 200:
                            images = images_response.json()
                            print(f"Images: Total images in board: {len(images)}")
                            
                            # Look for vision-tagged images
                            vision_images = [img for img in images if "vision" in img.get("tags", [])]
                            print(f"Vision: Vision images found: {len(vision_images)}")
                            
                            if len(vision_images) > 0:
                                latest_vision = vision_images[-1]  # Get latest
                                print(f"Latest: Latest vision image: {latest_vision['id']}")
                                print(f"Tags: {latest_vision['tags']}")
                                print(f"URL: {latest_vision['image_url'][:50]}...")
                                
                                # Check if it's not a placeholder
                                if "unsplash.com" not in latest_vision['image_url']:
                                    print("SUCCESS: REAL AI-generated image detected!")
                                    return True
                                else:
                                    print("FAIL: Still using placeholder image")
                                    return False
                            else:
                                print("FAIL: No vision images found")
                                return False
                        else:
                            print(f"FAIL: Failed to fetch board images: {images_response.status_code}")
                            return False
                    else:
                        print(f"FAIL: Generation may have failed: {gen_result['response']}")
                        return False
                else:
                    print(f"FAIL: Generation request failed: {generation_response.status_code}")
                    print(f"Error: {generation_response.text}")
                    return False
            else:
                print("FAIL: Iris didn't ask for confirmation as expected")
                return False
        else:
            print(f"FAIL: Initial request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAIL: Error during conversation: {str(e)}")
        return False

def test_board_context():
    """Test that Iris has proper board context"""
    print("\nTesting Iris Board Context...")
    
    try:
        # Check current board images
        response = requests.get(f"{API_BASE}/api/demo/inspiration/images?board_id={DEMO_BOARD_ID}")
        if response.status_code == 200:
            images = response.json()
            current_images = [img for img in images if "current" in img.get("tags", [])]
            inspiration_images = [img for img in images if "inspiration" in img.get("tags", [])]
            
            print(f"Current space images: {len(current_images)}")
            print(f"Inspiration images: {len(inspiration_images)}")
            
            if len(current_images) > 0 and len(inspiration_images) > 0:
                print("SUCCESS: Board has both current and inspiration images - ready for generation")
                return True
            else:
                print("FAIL: Missing required images for generation") 
                return False
        else:
            print(f"FAIL: Failed to fetch board context: {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Error checking board context: {str(e)}")
        return False

def main():
    """Run complete test suite"""
    print("Starting Iris Dream Generation Test Suite")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Test board context first
    if not test_board_context():
        print("\nFAIL: Board context test failed - cannot proceed")
        return
    
    # Test conversation flow
    success = test_iris_conversation_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: ALL TESTS PASSED!")
        print("Real AI image generation is working through Iris agent")
        print("Natural conversation flow confirmed")
        print("Image saved to vision board successfully")
    else:
        print("FAIL: TESTS FAILED")
        print("Check server logs and API endpoints")
    
    print(f"Test completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()