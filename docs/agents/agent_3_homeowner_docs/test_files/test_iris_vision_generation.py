#!/usr/bin/env python3
"""
Test Iris AI Vision Generation
Comprehensive test of IRIS system with image generation
"""

import requests
import json

def test_iris_vision_generation():
    """Test Iris AI vision generation with current + inspiration images"""
    
    print("TESTING IRIS AI VISION GENERATION")
    print("=" * 50)
    
    # Test conversation with vision generation request
    test_cases = [
        {
            "name": "Current Space Analysis",
            "message": "Can you analyze my current kitchen space?",
            "expected_keywords": ["current", "kitchen", "analysis", "space"]
        },
        {
            "name": "Inspiration Elements Selection", 
            "message": "I love the exposed brick and pendant lighting from the inspiration images. What elements do you see?",
            "expected_keywords": ["brick", "pendant", "lighting", "elements"]
        },
        {
            "name": "Vision Generation Request",
            "message": "Please generate a new kitchen vision that combines my current layout with the exposed brick and pendant lighting from the inspiration",
            "expected_keywords": ["generate", "vision", "combine", "brick", "lighting"]
        }
    ]
    
    conversation_context = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTEST {i}: {test_case['name']}")
        print("-" * 30)
        
        # API request payload
        payload = {
            "message": test_case["message"],
            "user_id": "550e8400-e29b-41d4-a716-446655440001", 
            "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
            "conversation_context": conversation_context
        }
        
        try:
            # Make API call
            print(f"Sending: {test_case['message']}")
            response = requests.post(
                "http://localhost:8008/api/iris/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                image_generated = result.get("image_generated", False)
                
                print(f"SUCCESS Status: {response.status_code}")
                print(f"Iris Response ({len(ai_response)} chars):")
                print(f"   {ai_response[:200]}..." if len(ai_response) > 200 else f"   {ai_response}")
                print(f"Image Generated: {image_generated}")
                
                # Check for expected keywords
                response_lower = ai_response.lower()
                found_keywords = [kw for kw in test_case["expected_keywords"] if kw.lower() in response_lower]
                print(f"Keywords Found: {found_keywords}")
                
                # Update conversation context
                conversation_context.append({"role": "user", "content": test_case["message"]})
                conversation_context.append({"role": "assistant", "content": ai_response})
                
                # Special handling for vision generation
                if "generate" in test_case["message"].lower() and "vision" in test_case["message"].lower():
                    if image_generated:
                        print("SUCCESS: Image generation triggered!")
                    else:
                        print("NOTE: No image generated (may be expected based on implementation)")
                        
            else:
                print(f"ERROR: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    print(f"\nTESTING COMPLETE")
    print(f"Total conversation turns: {len(conversation_context)}")

def test_backend_image_saving():
    """Test if backend saves generated images to database"""
    
    print(f"\nTESTING BACKEND IMAGE SAVING")
    print("=" * 50)
    
    # Check if new images are added to the demo board
    try:
        response = requests.get(
            "http://localhost:8008/api/demo/inspiration/images?board_id=26cf972b-83e4-484c-98b6-a5d1a4affee3",
            timeout=10
        )
        
        if response.status_code == 200:
            images = response.json()
            print(f"Current images in board: {len(images)}")
            
            # Check for vision images
            vision_images = [img for img in images if "vision" in img.get("tags", [])]
            print(f"Vision images found: {len(vision_images)}")
            
            for i, img in enumerate(vision_images, 1):
                print(f"   Vision {i}: {img.get('ai_analysis', {}).get('description', 'No description')}")
                
        else:
            print(f"Failed to get images: {response.status_code}")
            
    except Exception as e:
        print(f"Error checking images: {e}")

if __name__ == "__main__":
    test_iris_vision_generation()
    test_backend_image_saving()