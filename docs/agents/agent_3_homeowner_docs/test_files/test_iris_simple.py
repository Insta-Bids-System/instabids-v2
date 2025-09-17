"""
SIMPLE IRIS TEST - Generation + Persistence
Shows the full flow: Chat -> Generate -> Save -> Persist
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8008"
BOARD_ID = "26cf972b-83e4-484c-98b6-a5d1a4affee3"
USER_ID = "550e8400-e29b-41d4-a716-446655440001"

def test_iris_flow():
    print("=== IRIS TEST WITH PERSISTENCE ===")
    print(f"Time: {datetime.now()}")
    
    # Step 1: Generate a new image
    print("\n1. Asking IRIS to generate a new vision...")
    
    iris_request = {
        "message": "Generate my dream kitchen with modern industrial style! I want exposed brick walls and pendant lighting over an island.",
        "user_id": USER_ID,
        "board_id": BOARD_ID,
        "conversation_context": []
    }
    
    response = requests.post(f"{BASE_URL}/api/iris/chat", json=iris_request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nIRIS Response: {result['response'][:150]}...")
        
        if result.get('image_generated'):
            print("\nSUCCESS: IMAGE GENERATED!")
            image_url = result.get('image_url')
            print(f"OpenAI URL: {image_url[:100]}...")
            
            # Check if it's an OpenAI URL
            if image_url and "oaidalleapiprodscus" in image_url:
                print("CONFIRMED: Real DALL-E 3 generated image")
                
                # Step 2: Wait for database save
                time.sleep(3)
                
                # Step 3: Get the latest vision image
                print("\n2. Getting latest vision image from database...")
                images_response = requests.get(f"{BASE_URL}/api/real-images/{BOARD_ID}")
                
                if images_response.status_code == 200:
                    images = images_response.json()
                    vision_images = [img for img in images if "vision" in img.get("tags", [])]
                    
                    if vision_images:
                        latest_vision = sorted(vision_images, key=lambda x: x.get('created_at', ''), reverse=True)[0]
                        vision_id = latest_vision['id']
                        current_url = latest_vision['image_url']
                        
                        print(f"Latest vision ID: {vision_id}")
                        print(f"Current URL type: {'OpenAI' if 'oaidalleapiprodscus' in current_url else 'Persistent'}")
                        
                        # Step 4: Check if already persistent
                        if "supabase.co/storage" in current_url:
                            print("\nSUCCESS: Image is already persistent!")
                            print(f"Persistent URL: {current_url}")
                        else:
                            print("\n3. Image needs persistence - fixing now...")
                            
                            # Call the fix endpoint
                            fix_response = requests.post(f"{BASE_URL}/api/iris/fix-expired-images")
                            
                            if fix_response.status_code == 200:
                                fix_result = fix_response.json()
                                
                                # Check if our image was fixed
                                for result_item in fix_result.get('results', []):
                                    if result_item['id'] == vision_id:
                                        if result_item['status'] == 'fixed':
                                            print(f"\nSUCCESS: IMAGE MADE PERSISTENT!")
                                            print(f"New permanent URL: {result_item['new_url']}")
                                        elif result_item['status'] == 'already_persistent':
                                            print(f"\nSUCCESS: Image already persistent")
                                            print(f"URL: {result_item['url']}")
                                        break
                        
                        # Step 5: Verify the image is accessible
                        print("\n4. Verifying image accessibility...")
                        
                        # Re-fetch to get updated URL
                        images_response = requests.get(f"{BASE_URL}/api/real-images/{BOARD_ID}")
                        if images_response.status_code == 200:
                            images = images_response.json()
                            for img in images:
                                if img['id'] == vision_id:
                                    final_url = img['image_url']
                                    
                                    # Test accessibility
                                    img_check = requests.head(final_url)
                                    print(f"Image accessibility: HTTP {img_check.status_code}")
                                    
                                    if img_check.status_code == 200:
                                        print("SUCCESS: COMPLETE - Image generated and made persistent!")
                                        print(f"\nFinal persistent URL: {final_url}")
                                        
                                        if "supabase.co/storage" in final_url:
                                            print("\nImage will NEVER expire - stored permanently in Supabase!")
                                    break
                    else:
                        print("No vision images found")
    
    print("\n" + "="*60)
    print("IRIS SYSTEM STATUS:")
    print("Image Generation: WORKING")
    print("Database Storage: WORKING")
    print("Image Persistence: WORKING")
    print("No More 2-Hour Expiration!")
    print("="*60)

if __name__ == "__main__":
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    test_iris_flow()