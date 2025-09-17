"""
Debug test for image memory recall
"""

import requests
import json
import base64
import time
import sys

# Fix Unicode output on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Test configuration
BASE_URL = "http://localhost:8008"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440002"  # Valid UUID for testing

# Create a simple test image (1x1 pixel PNG)
TEST_IMAGE_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def test_image_upload_and_recall():
    """Upload an image and immediately test recall"""
    print("\n" + "="*60)
    print("IMAGE UPLOAD AND RECALL DEBUG TEST")
    print("="*60)
    
    session_id = f"debug_session_{int(time.time() * 1000)}"
    
    # Step 1: Upload image
    print("\n1. UPLOADING IMAGE...")
    upload_response = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": session_id,
        "message": "Here's a photo of my kitchen for inspiration",
        "images": [{
            "data": TEST_IMAGE_DATA,
            "filename": "kitchen_test.png"
        }]
    })
    
    if upload_response.status_code == 200:
        upload_result = upload_response.json()
        print(f"✅ Upload successful")
        print(f"Response: {upload_result.get('response', '')[:300]}")
        print(f"Success: {upload_result.get('success')}")
        print(f"Images processed: {upload_result.get('images_processed', 0)}")
    else:
        print(f"❌ Upload failed: {upload_response.status_code}")
        print(f"Error: {upload_response.text}")
        return
    
    # Step 2: Wait for processing
    print("\n2. WAITING FOR PROCESSING...")
    time.sleep(3)
    
    # Step 3: Test recall in same session
    print("\n3. TESTING RECALL IN SAME SESSION...")
    recall_response = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
        "user_id": TEST_USER_ID,
        "session_id": session_id,
        "message": "What images have I uploaded?"
    })
    
    if recall_response.status_code == 200:
        recall_result = recall_response.json()
        response_text = recall_result.get('response', '').lower()
        print(f"Response: {recall_result.get('response', '')[:500]}")
        
        # Check for image-related words
        image_words = ['image', 'photo', 'upload', 'kitchen', 'inspiration', 'picture']
        found_words = [word for word in image_words if word in response_text]
        
        if found_words:
            print(f"✅ Found image-related words: {found_words}")
        else:
            print(f"❌ No image-related words found in response")
    else:
        print(f"❌ Recall failed: {recall_response.status_code}")
    
    # Step 4: Check context API directly
    print("\n4. CHECKING CONTEXT API...")
    context_response = requests.get(f"{BASE_URL}/api/iris/context/{TEST_USER_ID}")
    
    if context_response.status_code == 200:
        context = context_response.json()
        
        # Check for photos in unified system
        photos = context.get('photos_from_unified_system', {})
        inspiration_photos = photos.get('inspiration_photos', [])
        
        print(f"Inspiration photos found: {len(inspiration_photos)}")
        if inspiration_photos:
            print(f"✅ Photos stored in context")
            for photo in inspiration_photos[:2]:
                print(f"  - {photo.get('file_path', 'unknown')}")
        else:
            print(f"⚠️ No photos in context")
        
        # Check inspiration boards
        boards = context.get('inspiration_boards', [])
        print(f"Inspiration boards found: {len(boards)}")
        
        # Check design preferences
        prefs = context.get('design_preferences', {})
        if prefs:
            print(f"Design preferences: {json.dumps(prefs, indent=2)[:200]}")
    else:
        print(f"❌ Context API failed: {context_response.status_code}")
    
    # Step 5: Test with different phrasings
    print("\n5. TESTING DIFFERENT PHRASINGS...")
    test_phrases = [
        "Can you describe the images I showed you?",
        "What was in the kitchen photo?",
        "Tell me about my uploaded photos"
    ]
    
    for phrase in test_phrases:
        print(f"\nTesting: '{phrase}'")
        test_response = requests.post(f"{BASE_URL}/api/iris/unified-chat", json={
            "user_id": TEST_USER_ID,
            "session_id": session_id,
            "message": phrase
        })
        
        if test_response.status_code == 200:
            result = test_response.json()
            response_text = result.get('response', '').lower()
            if 'kitchen' in response_text or 'photo' in response_text or 'image' in response_text:
                print(f"  ✅ Recognized context")
            else:
                print(f"  ❌ Generic response")
        else:
            print(f"  ❌ Request failed")

if __name__ == "__main__":
    test_image_upload_and_recall()