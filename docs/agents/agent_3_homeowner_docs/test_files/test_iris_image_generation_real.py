"""
Test REAL IRIS image generation with actual board images
This will prove IRIS can generate images from two source images
"""

import requests
import json
import time
from datetime import datetime

# Demo user and board IDs from your database
DEMO_USER_ID = "550e8400-e29b-41d4-a716-446655440001"
BOARD_ID = "26cf972b-83e4-484c-98b6-a5d1a4affee3"
BASE_URL = "http://localhost:8008"

def test_iris_generation_flow():
    print("=== TESTING REAL IRIS IMAGE GENERATION ===")
    print(f"Time: {datetime.now()}")
    
    # Step 1: First, let's check what images are on the board
    print("\n1. Getting board images...")
    
    # Use Supabase to check board images
    import os
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    # Get images for the board
    images_result = supabase.table("inspiration_images").select("*").eq("board_id", BOARD_ID).execute()
    images = images_result.data or []
    
    print(f"Found {len(images)} images on board")
    
    # Check for current and inspiration images
    current_images = [img for img in images if "current" in img.get("tags", [])]
    inspiration_images = [img for img in images if "inspiration" in img.get("tags", []) or "ideal" in img.get("tags", [])]
    
    print(f"- Current space images: {len(current_images)}")
    print(f"- Inspiration images: {len(inspiration_images)}")
    
    if not current_images or not inspiration_images:
        print("\nERROR: Board needs both current and inspiration images!")
        print("Let's add some test images...")
        
        # Add a current space image
        if not current_images:
            current_img = {
                "id": "test-current-" + str(int(time.time())),
                "board_id": BOARD_ID,
                "user_id": DEMO_USER_ID,
                "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800",
                "tags": ["current", "current-state"],
                "category": "current",
                "title": "Current Kitchen Space",
                "ai_analysis": {
                    "description": "Traditional kitchen with white cabinets and limited counter space",
                    "key_features": ["white cabinets", "tile backsplash", "limited counter space"],
                    "style": "Traditional"
                }
            }
            supabase.table("inspiration_images").insert(current_img).execute()
            print("✓ Added current space image")
        
        # Add an inspiration image
        if not inspiration_images:
            inspiration_img = {
                "id": "test-inspiration-" + str(int(time.time())),
                "board_id": BOARD_ID,
                "user_id": DEMO_USER_ID,
                "image_url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800",
                "tags": ["inspiration", "ideal"],
                "category": "ideal",
                "title": "Modern Kitchen Inspiration",
                "ai_analysis": {
                    "description": "Modern industrial kitchen with exposed brick and pendant lighting",
                    "key_features": ["exposed brick", "pendant lights", "open shelving", "industrial style"],
                    "style": "Modern Industrial"
                }
            }
            supabase.table("inspiration_images").insert(inspiration_img).execute()
            print("✓ Added inspiration image")
        
        # Re-fetch images
        images_result = supabase.table("inspiration_images").select("*").eq("board_id", BOARD_ID).execute()
        images = images_result.data or []
        current_images = [img for img in images if "current" in img.get("tags", [])]
        inspiration_images = [img for img in images if "inspiration" in img.get("tags", []) or "ideal" in img.get("tags", [])]
    
    # Step 2: Send generation request to IRIS
    print("\n2. Sending generation request to IRIS...")
    
    iris_request = {
        "message": "Generate my dream kitchen! I want to combine the modern industrial style from my inspiration with my current space layout.",
        "user_id": DEMO_USER_ID,
        "board_id": BOARD_ID,
        "conversation_context": [
            {
                "role": "user",
                "content": "I've selected my current kitchen and a modern industrial inspiration image"
            },
            {
                "role": "assistant", 
                "content": "I can see your current traditional kitchen and the modern industrial inspiration. The exposed brick and pendant lighting would look amazing!"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/iris/chat", json=iris_request)
    
    print(f"\nIRIS Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nIRIS Says: {result['response'][:200]}...")
        
        if result.get('image_generated'):
            print(f"\n✅ IMAGE GENERATED SUCCESSFULLY!")
            print(f"Image URL: {result.get('image_url')}")
            print(f"Generation ID: {result.get('generation_id')}")
            
            # Verify the image was saved to the board
            time.sleep(2)
            vision_images = supabase.table("inspiration_images").select("*").eq("board_id", BOARD_ID).eq("category", "vision").execute()
            if vision_images.data:
                print(f"\n✅ VISION IMAGE SAVED TO DATABASE!")
                print(f"Vision images count: {len(vision_images.data)}")
                latest_vision = vision_images.data[-1]
                print(f"Latest vision URL: {latest_vision['image_url']}")
        else:
            print("\n❌ No image was generated")
    else:
        print(f"\nERROR: {response.text}")
    
    # Step 3: Test the direct generation endpoint
    print("\n\n3. Testing direct image generation endpoint...")
    
    if current_images and inspiration_images:
        generation_request = {
            "board_id": BOARD_ID,
            "current_image_id": current_images[0]["id"],
            "ideal_image_id": inspiration_images[0]["id"],
            "user_preferences": "Modern industrial transformation keeping the same layout"
        }
        
        print(f"Current image ID: {generation_request['current_image_id']}")
        print(f"Inspiration image ID: {generation_request['ideal_image_id']}")
        
        gen_response = requests.post(f"{BASE_URL}/api/image-generation/generate-dream-space", json=generation_request)
        
        print(f"\nDirect Generation Status: {gen_response.status_code}")
        
        if gen_response.status_code == 200:
            gen_result = gen_response.json()
            print(f"\n✅ DIRECT GENERATION SUCCESSFUL!")
            print(f"Success: {gen_result.get('success')}")
            print(f"Generated Image URL: {gen_result.get('generated_image_url')}")
            print(f"Message: {gen_result.get('message', '')[:200]}...")
            
            # Check if it's a real OpenAI URL
            if gen_result.get('generated_image_url', '').startswith('https://oaidalleapi'):
                print("\n✅ CONFIRMED: Real OpenAI DALL-E generated image!")
        else:
            print(f"\nERROR: {gen_response.text[:500]}")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the test
    test_iris_generation_flow()
    
    print("\n=== TEST COMPLETE ===")